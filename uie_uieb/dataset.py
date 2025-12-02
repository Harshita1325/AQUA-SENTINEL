import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.autograd import Variable
import cv2
import os
import numpy as np
from options import opt
import torchvision
import torchvision.transforms.functional as F
import numbers
import random
from PIL import Image
import glob



class ToTensor(object):
    def __call__(self, sample):
        hazy_image, clean_image = sample['hazy'], sample['clean']
        hazy_image = torch.from_numpy(np.array(hazy_image).astype(np.float32))
        hazy_image = torch.transpose(torch.transpose(hazy_image, 2, 0), 1, 2)
        # hazy_image = hazy_image / 255.0
        clean_image = torch.from_numpy(np.array(clean_image).astype(np.float32))
        clean_image = torch.transpose(torch.transpose(clean_image, 2, 0), 1, 2)
        # clean_image = clean_image / 255.0
        return {'hazy': hazy_image,
                'clean': clean_image}


class Dataset_Load(Dataset):
    def __init__(self, hazy_path, clean_path=None, transform=None, mode='paired'):
        self.hazy_dir = hazy_path
        self.clean_dir = clean_path
        self.transform = transform
        self.mode = mode
        
        # Load all image files from hazy directory
        if os.path.isdir(hazy_path):
            self.hazy_files = sorted(glob.glob(os.path.join(hazy_path, '*.*')))
            self.hazy_files = [f for f in self.hazy_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        else:
            self.hazy_files = []
        
        # Load clean images if in paired mode
        if mode == 'paired' and clean_path and os.path.isdir(clean_path):
            self.clean_files = sorted(glob.glob(os.path.join(clean_path, '*.*')))
            self.clean_files = [f for f in self.clean_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        else:
            self.clean_files = self.hazy_files  # Use same images for self-supervised
      
    def __len__(self):
        return len(self.hazy_files)

    def __getitem__(self, index):
        # Load hazy/underwater image
        hazy_im = cv2.imread(self.hazy_files[index % len(self.hazy_files)])
        if hazy_im is None:
            hazy_im = np.zeros((512, 512, 3), dtype=np.uint8)
        hazy_im = cv2.resize(hazy_im, (512, 512), interpolation=cv2.INTER_AREA)
        hazy_im = hazy_im[:, :, ::-1]  # BGR to RGB
        
        # Load clean/target image
        if self.mode == 'paired' and index < len(self.clean_files):
            clean_im = cv2.imread(self.clean_files[index % len(self.clean_files)])
            if clean_im is None:
                clean_im = hazy_im.copy()
            clean_im = cv2.resize(clean_im, (512, 512), interpolation=cv2.INTER_AREA)
            clean_im = clean_im[:, :, ::-1]  # BGR to RGB
        else:
            # Self-supervised: create pseudo-clean by enhancing the input
            clean_im = cv2.cvtColor(hazy_im, cv2.COLOR_RGB2LAB)
            clean_im[:,:,0] = cv2.equalizeHist(clean_im[:,:,0])
            clean_im = cv2.cvtColor(clean_im, cv2.COLOR_LAB2RGB)
        
        # Simple data augmentation (horizontal flip)
        if random.random() > 0.5:
            hazy_im = np.fliplr(hazy_im).copy()
            clean_im = np.fliplr(clean_im).copy()
        
        # Random brightness adjustment
        if random.random() > 0.5:
            factor = random.uniform(0.8, 1.2)
            hazy_im = np.clip(hazy_im * factor, 0, 255).astype(np.uint8)
        
        # Normalize to [0, 1]
        hazy_im = np.float32(hazy_im) / 255.0
        clean_im = np.float32(clean_im) / 255.0

        sample = {'hazy': hazy_im, 'clean': clean_im}    
        if self.transform is not None:
            sample = self.transform(sample)
    
        return sample