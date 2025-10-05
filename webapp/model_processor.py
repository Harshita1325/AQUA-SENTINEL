"""
Model integration for Deep WaveNet web application
Handles loading and inference for all model types
"""

import os
import sys
import torch
import cv2
import numpy as np
from PIL import Image

class DeepWaveNetProcessor:
    def __init__(self):
        self.models = {}
        self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        print(f"🔧 Initializing processor on device: {self.device}")
        
    def load_models(self):
        """Load all Deep WaveNet models"""
        try:
            # Get the parent directory (DeepWater)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Load UIEB Enhancement Model
            print("📦 Loading UIEB enhancement model...")
            
            # Add UIEB path and import
            uieb_path = os.path.join(base_dir, 'uie_uieb')
            if uieb_path not in sys.path:
                sys.path.insert(0, uieb_path)
            
            import importlib
            import models as uieb_models
            importlib.reload(uieb_models)
            
            self.models['uieb'] = uieb_models.CC_Module()
            checkpoint_path = os.path.join(base_dir, 'uie_uieb', 'ckpts', 'netG_295.pt')
            checkpoint = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
            self.models['uieb'].load_state_dict(checkpoint['model_state_dict'])
            self.models['uieb'].eval()
            self.models['uieb'].to(self.device)
            print("✅ UIEB model loaded")
            
            # Remove UIEB path to avoid conflicts
            sys.path.remove(uieb_path)
            
            # Load Super-Resolution Models
            for scale in [2, 3, 4]:
                print(f"📦 Loading {scale}X super-resolution model...")
                model_key = f'sr{scale}x'
                
                # Import the model class for this scale
                sr_dir = os.path.join(base_dir, 'super-resolution', f'{scale}X')
                if sr_dir not in sys.path:
                    sys.path.insert(0, sr_dir)
                
                # Import and create model
                import models as sr_models
                importlib.reload(sr_models)
                self.models[model_key] = sr_models.CC_Module(scale)
                
                # Load checkpoint
                if scale == 2:
                    checkpoint_file = 'netG_859.pt'
                elif scale == 3:
                    checkpoint_file = 'netG_1603.pt'
                else:  # scale == 4
                    checkpoint_file = 'netG_2320.pt'
                
                checkpoint_path = os.path.join(sr_dir, 'ckpt', checkpoint_file)
                checkpoint = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
                self.models[model_key].load_state_dict(checkpoint['model_state_dict'])
                self.models[model_key].eval()
                self.models[model_key].to(self.device)
                print(f"✅ {scale}X super-resolution model loaded")
                
                # Remove from path to avoid conflicts
                sys.path.remove(sr_dir)
            
            print(f"🎉 All {len(self.models)} models loaded successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error loading models: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def preprocess_image(self, image_path):
        """Preprocess image for model input"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image from {image_path}")
            
            # Convert BGR to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            original_shape = image.shape
            
            # Convert to tensor and normalize
            image_tensor = torch.from_numpy(image).float()
            image_tensor = image_tensor.permute(2, 0, 1).unsqueeze(0)  # HWC -> BCHW
            image_tensor = image_tensor / 255.0  # Normalize to [0, 1]
            
            return image_tensor.to(self.device), original_shape
            
        except Exception as e:
            raise Exception(f"Error preprocessing image: {str(e)}")
    
    def postprocess_image(self, tensor, output_path):
        """Convert tensor back to image and save"""
        try:
            # Convert tensor to numpy
            if tensor.dim() == 4:
                tensor = tensor.squeeze(0)  # Remove batch dimension
            
            output = tensor.permute(1, 2, 0).cpu().detach().numpy()  # CHW -> HWC
            output = np.clip(output * 255.0, 0, 255).astype(np.uint8)
            
            # Convert RGB to BGR for OpenCV
            output_bgr = cv2.cvtColor(output, cv2.COLOR_RGB2BGR)
            
            # Save image
            success = cv2.imwrite(output_path, output_bgr)
            if not success:
                raise Exception(f"Failed to save image to {output_path}")
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Error postprocessing image: {str(e)}")
    
    def process_image(self, input_path, output_path, model_type):
        """Process image with selected model"""
        try:
            if model_type not in self.models:
                raise ValueError(f"Model '{model_type}' not available. Available models: {list(self.models.keys())}")
            
            print(f"🔄 Processing image with {model_type} model...")
            
            # Preprocess
            input_tensor, original_shape = self.preprocess_image(input_path)
            print(f"📐 Input shape: {original_shape}")
            
            # Run inference
            with torch.no_grad():
                model = self.models[model_type]
                output_tensor = model(input_tensor)
            
            print(f"📐 Output tensor shape: {output_tensor.shape}")
            
            # Postprocess and save
            result_path = self.postprocess_image(output_tensor, output_path)
            print(f"💾 Saved result to: {result_path}")
            
            return result_path
            
        except Exception as e:
            raise Exception(f"Error processing image with {model_type}: {str(e)}")
    
    def get_model_info(self):
        """Get information about loaded models"""
        return {
            'models_loaded': len(self.models),
            'available_models': list(self.models.keys()),
            'device': self.device,
            'model_descriptions': {
                'uieb': 'Underwater Image Enhancement (UIEB Dataset)',
                'sr2x': '2X Super-Resolution',
                'sr3x': '3X Super-Resolution', 
                'sr4x': '4X Super-Resolution'
            }
        }

# Global processor instance
processor = None

def get_processor():
    """Get or create the global processor instance"""
    global processor
    if processor is None:
        processor = DeepWaveNetProcessor()
        if not processor.load_models():
            raise Exception("Failed to initialize models")
    return processor