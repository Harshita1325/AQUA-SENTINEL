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

# Import threat detection modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from threat_detection.detector import ThreatDetector
from threat_detection.visualizer import ThreatVisualizer

class DeepWaveNetProcessor:
    def __init__(self):
        self.models = {}
        self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        self.threat_detector = None
        self.threat_visualizer = None
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
    
    def detect_environment(self, image_path):
        """
        Detect underwater environment type based on image characteristics
        Returns: 'clear', 'turbid', 'deep', or 'night'
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return 'clear'  # Default
            
            # Convert to different color spaces
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            
            # Calculate various metrics
            
            # 1. Brightness (average of V channel in HSV)
            brightness = np.mean(hsv[:, :, 2])
            
            # 2. Color cast - check blue/green dominance
            r_mean = np.mean(rgb[:, :, 0])
            g_mean = np.mean(rgb[:, :, 1])
            b_mean = np.mean(rgb[:, :, 2])
            
            # 3. Contrast (standard deviation of luminance)
            contrast = np.std(lab[:, :, 0])
            
            # 4. Color saturation
            saturation = np.mean(hsv[:, :, 1])
            
            # 5. Blue-green ratio
            blue_green_ratio = b_mean / (g_mean + 1e-6)
            green_red_ratio = g_mean / (r_mean + 1e-6)
            
            # Decision logic based on characteristics
            
            # NIGHT: Very low brightness
            if brightness < 60:
                return 'night'
            
            # DEEP: High blue dominance, low brightness
            elif blue_green_ratio > 1.3 and brightness < 100:
                return 'deep'
            
            # TURBID: High green dominance, low contrast, low saturation
            elif green_red_ratio > 1.4 and contrast < 30 and saturation < 80:
                return 'turbid'
            
            # CLEAR: Balanced colors, good brightness and contrast
            else:
                return 'clear'
                
        except Exception as e:
            print(f"Error detecting environment: {str(e)}")
            return 'clear'  # Default fallback
    
    def apply_adaptive_enhancement(self, input_path, output_path, environment='auto'):
        """
        Apply adaptive enhancement based on environment
        
        Args:
            input_path: Path to input image
            output_path: Path to save output
            environment: 'auto', 'clear', 'turbid', 'deep', or 'night'
        """
        # Detect environment if auto mode
        if environment == 'auto':
            detected_env = self.detect_environment(input_path)
            print(f"🔍 Auto-detected environment: {detected_env.upper()}")
        else:
            detected_env = environment.lower()
            print(f"🎯 Manual environment selection: {detected_env.upper()}")
        
        # Load image
        image = cv2.imread(input_path)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        img_float = rgb.astype(np.float32) / 255.0
        
        # Apply environment-specific preprocessing
        if detected_env == 'clear':
            # Minimal adjustment, use standard enhancement
            adjusted = img_float
            strength = 1.0
            
        elif detected_env == 'turbid':
            # Reduce green cast, increase contrast
            adjusted = img_float.copy()
            adjusted[:, :, 1] *= 0.85  # Reduce green channel
            adjusted[:, :, 0] *= 1.1   # Boost red slightly
            adjusted = np.clip(adjusted, 0, 1)
            strength = 1.3
            
        elif detected_env == 'deep':
            # Compensate for blue dominance, warm up colors
            adjusted = img_float.copy()
            adjusted[:, :, 2] *= 0.75  # Reduce blue
            adjusted[:, :, 0] *= 1.25  # Increase red
            adjusted[:, :, 1] *= 1.1   # Increase green
            adjusted = np.clip(adjusted, 0, 1)
            strength = 1.4
            
        elif detected_env == 'night':
            # Brighten, enhance contrast, reduce noise
            adjusted = np.power(img_float, 0.7)  # Gamma correction
            adjusted = np.clip(adjusted, 0, 1)
            strength = 1.5
        
        else:
            adjusted = img_float
            strength = 1.0
        
        # Convert back and save preprocessed
        preprocessed = (adjusted * 255).astype(np.uint8)
        preprocessed_bgr = cv2.cvtColor(preprocessed, cv2.COLOR_RGB2BGR)
        temp_path = input_path.replace('.', f'_preprocessed_{detected_env}.')
        cv2.imwrite(temp_path, preprocessed_bgr)
        
        # Process with model
        result_path = self.process_image(temp_path, output_path, 'uieb')
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return result_path, detected_env
    
    def load_threat_detector(self, model_size='n'):
        """
        Load YOLOv8 threat detection model
        
        Args:
            model_size: YOLOv8 model size ('n', 's', 'm', 'l', 'x')
        """
        try:
            if self.threat_detector is None:
                print("🔍 Loading threat detection system...")
                self.threat_detector = ThreatDetector(model_size=model_size, confidence_threshold=0.2)
                self.threat_visualizer = ThreatVisualizer()
                print("✅ Threat detection system ready (threshold: 20%)")
            return True
        except Exception as e:
            print(f"❌ Error loading threat detector: {str(e)}")
            return False
    
    def detect_and_highlight_threats(self, input_path, output_path, 
                                     enhance_first=True, exclude_marine_life=True):
        """
        Detect and highlight underwater threats
        
        Args:
            input_path: Path to input image
            output_path: Path to save output with threat highlights
            enhance_first: If True, enhance image before detection
            exclude_marine_life: Filter out fish and natural objects
            
        Returns:
            Tuple of (output_path, threats_list, summary_dict)
        """
        try:
            # Load threat detector if not loaded
            if self.threat_detector is None:
                self.load_threat_detector()
            
            # Step 1: Enhance image first if requested
            if enhance_first:
                print("🌊 Enhancing image for better threat detection...")
                enhanced_path = input_path.replace('.', '_enhanced.')
                self.process_image(input_path, enhanced_path, 'uieb')
                detection_input = enhanced_path
            else:
                detection_input = input_path
            
            # Step 2: Detect threats
            print("🔍 Scanning for underwater threats...")
            threats = self.threat_detector.detect_threats(
                detection_input, 
                exclude_marine_life=exclude_marine_life
            )
            
            # Step 3: Generate summary
            summary = self.threat_detector.get_threat_summary(threats)
            
            # Step 4: Visualize threats
            if threats:
                print(f"⚠️  {summary['total']} threat(s) detected - drawing highlights...")
                self.threat_visualizer.draw_all_threats(
                    detection_input,
                    threats,
                    output_path,
                    draw_circles=True,
                    draw_boxes=True,
                    draw_labels=True
                )
            else:
                print("✅ No threats detected - image is clear")
                # Copy input to output if no threats
                import shutil
                shutil.copy(detection_input, output_path)
            
            # Clean up enhanced temp file if created
            if enhance_first and os.path.exists(enhanced_path):
                os.remove(enhanced_path)
            
            return output_path, threats, summary
            
        except Exception as e:
            print(f"❌ Error in threat detection: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def process_with_threat_detection(self, input_path, output_path, 
                                      model_type='uieb', detect_threats=True):
        """
        Complete pipeline: Enhancement + Threat Detection
        
        Args:
            input_path: Path to input image
            output_path: Path to save final output
            model_type: Enhancement model to use
            detect_threats: Enable threat detection
            
        Returns:
            Dictionary with results
        """
        try:
            results = {
                'enhanced_path': None,
                'threats_detected': False,
                'threat_count': 0,
                'threats': [],
                'summary': {}
            }
            
            if detect_threats:
                # Run full pipeline with threat detection
                enhanced_path = input_path.replace('.', '_enhanced_temp.')
                self.process_image(input_path, enhanced_path, model_type)
                
                output_with_threats, threats, summary = self.detect_and_highlight_threats(
                    enhanced_path,
                    output_path,
                    enhance_first=False  # Already enhanced
                )
                
                results['enhanced_path'] = output_with_threats
                results['threats_detected'] = len(threats) > 0
                results['threat_count'] = len(threats)
                results['threats'] = threats
                results['summary'] = summary
                
                # Clean up temp file
                if os.path.exists(enhanced_path):
                    os.remove(enhanced_path)
            else:
                # Standard enhancement only
                self.process_image(input_path, output_path, model_type)
                results['enhanced_path'] = output_path
            
            return results
            
        except Exception as e:
            print(f"❌ Error in processing pipeline: {str(e)}")
            raise
    
    def get_model_info(self):
        """Get information about loaded models"""
        return {
            'models_loaded': len(self.models),
            'available_models': list(self.models.keys()),
            'device': self.device,
            'threat_detection_enabled': self.threat_detector is not None,
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