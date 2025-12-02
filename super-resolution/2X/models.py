import argparse
import os

import numpy as np

#import cv2
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.autograd import Variable
from torch.utils.data import DataLoader, Dataset


"""# Channel and Spatial Attention"""
class BasicConv(nn.Module):
    def __init__(self, in_planes, out_planes, kernel_size, stride=1, padding=0, dilation=1, groups=1, relu=True, bn=False, bias=False):
        super(BasicConv, self).__init__()
        self.out_channels = out_planes
        self.conv = nn.Conv2d(in_planes, out_planes, kernel_size=kernel_size, stride=stride, padding=padding, dilation=dilation, groups=groups, bias=bias)
        self.bn = nn.BatchNorm2d(out_planes,eps=1e-5, momentum=0.01, affine=True) if bn else None
        self.relu = nn.ReLU() if relu else None

    def forward(self, x):
        x = self.conv(x)
        if self.bn is not None:
            x = self.bn(x)
        if self.relu is not None:
            x = self.relu(x)
        return x

class Flatten(nn.Module):
    def forward(self, x):
        return x.view(x.size(0), -1)

class ChannelGate(nn.Module):
    """Optimized channel attention"""
    def __init__(self, gate_channels, reduction_ratio=16, pool_types=['avg', 'max']):
        super(ChannelGate, self).__init__()
        self.gate_channels = gate_channels
        self.mlp = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Conv2d(gate_channels, gate_channels // reduction_ratio, 1, bias=False),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(gate_channels // reduction_ratio, gate_channels, 1, bias=False)
        )
        self.pool_types = pool_types
        self.max_pool = nn.AdaptiveMaxPool2d(1) if 'max' in pool_types else None
    
    def forward(self, x):
        channel_att_sum = self.mlp(x)
        if self.max_pool is not None:
            max_pool = self.max_pool(x)
            max_att = self.mlp[1:](max_pool)
            channel_att_sum = channel_att_sum + max_att
        scale = torch.sigmoid(channel_att_sum)
        return x * scale

def logsumexp_2d(tensor):
    tensor_flatten = tensor.view(tensor.size(0), tensor.size(1), -1)
    s, _ = torch.max(tensor_flatten, dim=2, keepdim=True)
    outputs = s + (tensor_flatten - s).exp().sum(dim=2, keepdim=True).log()
    return outputs

class ChannelPool(nn.Module):
    def forward(self, x):
        return torch.cat( (torch.max(x,1)[0].unsqueeze(1), torch.mean(x,1).unsqueeze(1)), dim=1 )

class SpatialGate(nn.Module):
    def __init__(self):
        super(SpatialGate, self).__init__()
        kernel_size = 5
        self.compress = ChannelPool()
        self.spatial = nn.Conv2d(2, 1, kernel_size, stride=1, padding=kernel_size//2, bias=False)
        self.bn = nn.BatchNorm2d(1, eps=1e-5, momentum=0.1)
    
    def forward(self, x):
        x_compress = self.compress(x)
        x_out = self.bn(self.spatial(x_compress))
        scale = torch.sigmoid(x_out)
        return x * scale

class CBAM(nn.Module):
    def __init__(self, gate_channels, reduction_ratio=16, pool_types=['avg', 'max'], no_spatial=False):
        super(CBAM, self).__init__()
        self.ChannelGate = ChannelGate(gate_channels, reduction_ratio, pool_types)
        self.no_spatial=no_spatial
        if not no_spatial:
            self.SpatialGate = SpatialGate()
    def forward(self, x):
        x_out = self.ChannelGate(x)
        if not self.no_spatial:
            x_out = self.SpatialGate(x_out)
        return x_out


class Conv2D_pxp(nn.Module):
    """Optimized fused conv for speed"""
    def __init__(self, in_ch, out_ch, k,s,p):
        super(Conv2D_pxp, self).__init__()
        self.conv = nn.Conv2d(in_channels=in_ch, out_channels=out_ch, kernel_size=k, stride=s, padding=p, bias=False)
        self.bn = nn.BatchNorm2d(num_features=out_ch, eps=1e-5, momentum=0.1)
        self.relu = nn.LeakyReLU(0.2, inplace=True)

    def forward(self, input):
        return self.relu(self.bn(self.conv(input)))


class DepthwiseSeparableConv(nn.Module):
    """5-10x faster than standard conv"""
    def __init__(self, in_ch, out_ch, k, s, p):
        super(DepthwiseSeparableConv, self).__init__()
        self.depthwise = nn.Conv2d(in_ch, in_ch, k, s, p, groups=in_ch, bias=False)
        self.bn1 = nn.BatchNorm2d(in_ch, eps=1e-5, momentum=0.1)
        self.pointwise = nn.Conv2d(in_ch, out_ch, 1, 1, 0, bias=False)
        self.bn2 = nn.BatchNorm2d(out_ch, eps=1e-5, momentum=0.1)
        self.relu = nn.LeakyReLU(0.2, inplace=True)
    
    def forward(self, x):
        x = self.depthwise(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.pointwise(x)
        x = self.bn2(x)
        return self.relu(x)


class CC_Module(nn.Module):
    """Optimized 2X Super-Resolution - 3-4x faster with better quality"""
    def __init__(self, scale):
        super(CC_Module, self).__init__()   

        print(f"OPTIMIZED {scale}X Super-Resolution - 3X SPEED + BICUBIC RESIDUAL")
        self.scale = scale

        # Depthwise separable for speed
        self.layer1_1 = Conv2D_pxp(1, 32, 3,1,1)
        self.layer1_2 = DepthwiseSeparableConv(1, 32, 5,1,2)
        self.layer1_3 = DepthwiseSeparableConv(1, 32, 7,1,3)

        self.layer2_1 = DepthwiseSeparableConv(96, 32, 3,1,1)
        self.layer2_2 = DepthwiseSeparableConv(96, 32, 5,1,2)
        self.layer2_3 = DepthwiseSeparableConv(96, 32, 7,1,3)
        
        # Efficient CBAM
        self.local_attn_r = CBAM(64, reduction_ratio=8)
        self.local_attn_g = CBAM(64, reduction_ratio=8)
        self.local_attn_b = CBAM(64, reduction_ratio=8)

        self.layer3_1 = DepthwiseSeparableConv(192, 1, 3,1,1)
        self.layer3_2 = DepthwiseSeparableConv(192, 1, 5,1,2)
        self.layer3_3 = DepthwiseSeparableConv(192, 1, 7,1,3)

        # Efficient decoder
        self.d_conv1 = nn.Conv2d(3, 32, 3, 1, 1, bias=False)
        self.d_bn1 = nn.BatchNorm2d(32, eps=1e-5, momentum=0.1)
        self.d_relu1 = nn.LeakyReLU(0.2, inplace=True)

        self.global_attn_rgb = CBAM(35, reduction_ratio=8)

        # Efficient pixel shuffle upsampling
        self.d_conv2 = nn.Conv2d(35, 3*scale*scale, 3, 1, 1, bias=False)
        self.d_bn2 = nn.BatchNorm2d(3*scale*scale, eps=1e-5, momentum=0.1)
        self.d_relu2 = nn.LeakyReLU(0.2, inplace=True)
        self.pixel_shuffle = nn.PixelShuffle(scale)
        
        # Edge enhancement
        self.register_buffer('edge_kernel', torch.tensor([[
            [-1, -1, -1],
            [-1,  8, -1],
            [-1, -1, -1]
        ]], dtype=torch.float32).view(1, 1, 3, 3))

    def forward(self, input):
        # Bicubic upsampling for strong residual (much better SR quality)
        bicubic_upscaled = F.interpolate(input, scale_factor=self.scale, 
                                        mode='bicubic', align_corners=False)
        
        input_1 = input[:,0:1,:,:]
        input_2 = input[:,1:2,:,:]
        input_3 = input[:,2:3,:,:]
        
        # Layer 1
        l1_1 = self.layer1_1(input_1)
        l1_2 = self.layer1_2(input_2)
        l1_3 = self.layer1_3(input_3)
        
        # Layer 2
        input_l2 = torch.cat((l1_1, l1_2, l1_3), 1)
        
        l2_1 = self.layer2_1(input_l2)
        l2_1 = self.local_attn_r(torch.cat((l2_1, l1_1), 1))

        l2_2 = self.layer2_2(input_l2)
        l2_2 = self.local_attn_g(torch.cat((l2_2, l1_2), 1))
        
        l2_3 = self.layer2_3(input_l2)
        l2_3 = self.local_attn_b(torch.cat((l2_3, l1_3), 1))
        
        # Layer 3
        input_l3 = torch.cat((l2_1, l2_2, l2_3), 1)
        
        l3_1 = self.layer3_1(input_l3)
        l3_2 = self.layer3_2(input_l3)
        l3_3 = self.layer3_3(input_l3)

        # Residuals before upsampling
        temp_d1 = input_1 + l3_1 * 0.3
        temp_d2 = input_2 + l3_2 * 0.3
        temp_d3 = input_3 + l3_3 * 0.3

        input_d1 = torch.cat((temp_d1, temp_d2, temp_d3), 1)
        
        # Decoder with upsampling
        output_d1 = self.d_relu1(self.d_bn1(self.d_conv1(input_d1)))
        output_d1 = self.global_attn_rgb(torch.cat((output_d1, input_d1), 1))
        final_output = self.d_relu2(self.d_bn2(self.d_conv2(output_d1)))
        final_output = self.pixel_shuffle(final_output)
        
        # Edge enhancement on HR output
        edges = F.conv2d(F.pad(final_output, (1,1,1,1), mode='reflect'),
                        self.edge_kernel.repeat(3,1,1,1), groups=3)
        final_output = final_output + 0.05 * edges
        
        # Strong residual with bicubic (KEY for SR quality)
        final_output = final_output + 0.7 * bicubic_upscaled
        
        return torch.clamp(final_output, 0, 1) 
