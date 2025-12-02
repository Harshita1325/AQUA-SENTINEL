import argparse
import cv2
import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torchvision
import dataset as dataset
from vgg import *
from torch.utils.data import Dataset, DataLoader
from torch.autograd import Variable
from options import opt, device
from models import *
from misc import *
import re
import sys


def get_lr(optimizer):
	for param_group in optimizer.param_groups:
		return param_group['lr']

if __name__ == '__main__':
	
	print("="*50)
	print("Starting EUVP Model Training with Dehazing Module")
	print("="*50)
	
	# Set torch cache to writable location
	os.environ['TORCH_HOME'] = os.path.join(os.getcwd(), '.torch_cache')
	os.makedirs(os.environ['TORCH_HOME'], exist_ok=True)
		
	netG = CC_Module()
	netG.to(device)
	
	# Try FP16 for faster training
	try:
		netG = netG.half()
		use_fp16 = True
		print("✓ Using FP16 mixed precision for faster training")
	except:
		use_fp16 = False
		print("✗ FP16 not available, using FP32")

	mse_loss = nn.MSELoss()
	l1_loss = nn.L1Loss()
	vgg = Vgg16(requires_grad=False).to(device)

	optim_g = optim.Adam(netG.parameters(), 
						 lr=opt.learning_rate_g, 
						 betas = (opt.beta1, opt.beta2), 
						 weight_decay=opt.wd_g)
	
	# Learning rate scheduler
	scheduler = optim.lr_scheduler.ReduceLROnPlateau(optim_g, mode='min', factor=0.5, patience=5)

		
	dataset = dataset.Dataset_Load(data_path = opt.data_path,
								   transform=dataset.ToTensor()
								   )
	batches = int(dataset.len / opt.batch_size)

	dataloader = DataLoader(dataset, batch_size=opt.batch_size, shuffle=True, 
						   num_workers=0, pin_memory=False)  # Windows compatibility
	
	if not os.path.exists(opt.checkpoints_dir):
		os.makedirs(opt.checkpoints_dir)
	
	models_loaded = getLatestCheckpointName()    
	latest_checkpoint_G = models_loaded
	
	print('Loading model checkpoint: ', latest_checkpoint_G)
	
	if latest_checkpoint_G == None:
		start_epoch = 1
		best_loss = float('inf')
		print('✗ No checkpoints found! Starting fresh training')
	
	else:
		checkpoint_g = torch.load(os.path.join(opt.checkpoints_dir, latest_checkpoint_G), 
								 map_location=device, weights_only=False)    
		start_epoch = checkpoint_g['epoch'] + 1
		netG.load_state_dict(checkpoint_g['model_state_dict'], strict=False)  # Allow new architecture
		try:
			optim_g.load_state_dict(checkpoint_g['optimizer_state_dict'])
		except:
			print("⚠ Optimizer state mismatch, using fresh optimizer")
		best_loss = checkpoint_g.get('total_loss', float('inf'))
			
		print(f'✓ Resumed from epoch {start_epoch}, Best loss: {best_loss:.6f}')
	
	print(f"\nDataset: {dataset.len} images, Batch size: {opt.batch_size}, Batches per epoch: {len(dataloader)}")
	print(f"Training from epoch {start_epoch} to {opt.end_epoch}\n")
	
	netG.train()


	for epoch in range(start_epoch, opt.end_epoch + 1):

		opt.total_mse_loss = 0.0
		opt.total_vgg_loss = 0.0
		opt.total_l1_loss = 0.0
		opt.total_G_loss = 0.0
		
		netG.train()
			
		for i_batch, sample_batched in enumerate(dataloader):

			hazy_batch = sample_batched['hazy']
			clean_batch = sample_batched['clean']

			hazy_batch = hazy_batch.to(device)
			clean_batch = clean_batch.to(device)
			
			if use_fp16:
				hazy_batch = hazy_batch.half()
				clean_batch = clean_batch.half()

			optim_g.zero_grad()

			pred_batch = netG(hazy_batch)
			
			# MSE Loss
			batch_mse_loss = torch.mul(opt.lambda_mse, mse_loss(pred_batch, clean_batch))
			batch_mse_loss.backward(retain_graph=True)
			
			# L1 Loss
			batch_l1_loss = torch.mul(0.5, l1_loss(pred_batch, clean_batch))
			batch_l1_loss.backward(retain_graph=True)
			
			# VGG Perceptual Loss
			clean_vgg_feats = vgg(normalize_batch(clean_batch.float()))
			pred_vgg_feats = vgg(normalize_batch(pred_batch.float()))
			batch_vgg_loss = torch.mul(opt.lambda_vgg, mse_loss(pred_vgg_feats.relu2_2, clean_vgg_feats.relu2_2))
			batch_vgg_loss.backward()
			
			opt.batch_mse_loss = batch_mse_loss.item()
			opt.total_mse_loss += opt.batch_mse_loss

			opt.batch_vgg_loss = batch_vgg_loss.item()
			opt.total_vgg_loss += opt.batch_vgg_loss
			
			opt.batch_l1_loss = batch_l1_loss.item()
			opt.total_l1_loss += opt.batch_l1_loss
			
			opt.batch_G_loss = opt.batch_mse_loss + opt.batch_vgg_loss + opt.batch_l1_loss
			opt.total_G_loss += opt.batch_G_loss
			
			optim_g.step()

			print(f'\r Epoch: {epoch} | ({i_batch+1}/{len(dataloader)}) | MSE: {opt.batch_mse_loss:.6f} | VGG: {opt.batch_vgg_loss:.6f} | L1: {opt.batch_l1_loss:.6f}', end='', flush=True)
			
		print(f'\n✓ Epoch {epoch} complete | LR: {get_lr(optim_g):.6f} | Total MSE: {opt.total_mse_loss:.6f} | Total VGG: {opt.total_vgg_loss:.6f} | Total L1: {opt.total_l1_loss:.6f} | Total: {opt.total_G_loss:.6f}')
		
		# Update learning rate
		scheduler.step(opt.total_G_loss)
		
		# Save best model
		if opt.total_G_loss < best_loss:
			best_loss = opt.total_G_loss
			torch.save({'epoch':epoch, 
						'model_state_dict':netG.state_dict(), 
						'optimizer_state_dict':optim_g.state_dict(), 
						'mse_loss':opt.total_mse_loss, 
						'vgg_loss':opt.total_vgg_loss,
						'l1_loss':opt.total_l1_loss, 
						'opt':opt,
						'total_loss':opt.total_G_loss}, os.path.join(opt.checkpoints_dir, 'netG_best.pt'))
			print(f'★ Best model saved! Loss: {best_loss:.6f}')
			
		torch.save({'epoch':epoch, 
					'model_state_dict':netG.state_dict(), 
					'optimizer_state_dict':optim_g.state_dict(), 
					'mse_loss':opt.total_mse_loss, 
					'vgg_loss':opt.total_vgg_loss,
					'l1_loss':opt.total_l1_loss, 
					'opt':opt,
					'total_loss':opt.total_G_loss}, os.path.join(opt.checkpoints_dir, 'netG_' + str(epoch) + '.pt'))
	
	print("\n" + "="*50)
	print("Training Complete! Best loss:", best_loss)
	print("="*50)