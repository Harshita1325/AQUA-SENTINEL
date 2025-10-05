"""
Video Processing Module for DeepWater Web Application
Handles frame-by-frame enhancement of underwater videos
"""

import os
import sys
import cv2
import torch
import numpy as np
from typing import Tuple, Optional, Callable
import time
from pathlib import Path

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class VideoProcessor:
    """
    Process underwater videos frame-by-frame using enhancement models
    """
    
    def __init__(self, model_type='uieb'):
        """
        Initialize video processor with specified model
        
        Args:
            model_type: 'uieb', 'euvp', or 'sr2x/sr3x/sr4x'
        """
        self.model_type = model_type
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.load_model()
        
    def load_model(self):
        """Load the enhancement model"""
        try:
            # Get the base directory
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Use the existing model processor approach
            if self.model_type == 'uieb':
                # Add UIEB path and import
                uieb_path = os.path.join(base_dir, 'uie_uieb')
                if uieb_path not in sys.path:
                    sys.path.insert(0, uieb_path)
                
                import importlib
                import models as uieb_models
                importlib.reload(uieb_models)
                
                self.model = uieb_models.CC_Module()
                model_path = os.path.join(base_dir, 'uie_uieb', 'ckpts', 'netG_295.pt')
                
                # Remove from path after import
                if uieb_path in sys.path:
                    sys.path.remove(uieb_path)
                
            elif self.model_type == 'euvp':
                # Add EUVP path and import
                euvp_path = os.path.join(base_dir, 'uie_euvp')
                if euvp_path not in sys.path:
                    sys.path.insert(0, euvp_path)
                
                import importlib
                import models as euvp_models
                importlib.reload(euvp_models)
                
                self.model = euvp_models.CC_Module()
                model_path = os.path.join(base_dir, 'uie_euvp', 'ckpts', 'netG_295.pt')
                
                # Remove from path after import
                if euvp_path in sys.path:
                    sys.path.remove(euvp_path)
                
            elif self.model_type.startswith('sr'):
                scale = int(self.model_type[-2])  # Extract scale: 2, 3, or 4
                sr_dir = os.path.join(base_dir, 'super-resolution', f'{scale}X')
                
                if sr_dir not in sys.path:
                    sys.path.insert(0, sr_dir)
                
                import importlib
                import models as sr_models
                importlib.reload(sr_models)
                
                self.model = sr_models.CC_Module(scale)
                
                # Determine checkpoint file
                if scale == 2:
                    checkpoint_file = 'netG_859.pt'
                elif scale == 3:
                    checkpoint_file = 'netG_1603.pt'
                else:  # scale == 4
                    checkpoint_file = 'netG_2320.pt'
                
                model_path = os.path.join(sr_dir, 'ckpt', checkpoint_file)
                
                # Remove from path after import
                if sr_dir in sys.path:
                    sys.path.remove(sr_dir)
            
            else:
                # Default to video processing model (CC_Module from uw_video_processing)
                video_path = os.path.join(base_dir, 'uw_video_processing')
                if video_path not in sys.path:
                    sys.path.insert(0, video_path)
                
                import importlib
                import models as video_models
                importlib.reload(video_models)
                
                self.model = video_models.CC_Module()
                model_path = os.path.join(base_dir, 'uw_video_processing', 'ckpts', 'netG_295.pt')
                
                # Remove from path after import
                if video_path in sys.path:
                    sys.path.remove(video_path)
            
            # Load checkpoint
            if os.path.exists(model_path):
                checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
                if 'model_state_dict' in checkpoint:
                    self.model.load_state_dict(checkpoint['model_state_dict'])
                else:
                    self.model.load_state_dict(checkpoint)
                
                self.model.eval()
                self.model.to(self.device)
                print(f"✅ Model loaded: {self.model_type}")
            else:
                print(f"⚠️ Model checkpoint not found at {model_path}")
                raise FileNotFoundError(f"Model checkpoint not found: {model_path}")
                
        except Exception as e:
            print(f"❌ Error loading model: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def extract_frames(self, video_path: str) -> Tuple[list, float, dict]:
        """
        Extract frames from video
        
        Returns:
            frames: List of frames (numpy arrays)
            fps: Original video FPS
            info: Video metadata
        """
        frames = []
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        info = {
            'fps': fps,
            'frame_count': frame_count,
            'width': width,
            'height': height,
            'duration': frame_count / fps if fps > 0 else 0
        }
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        
        cap.release()
        return frames, fps, info
    
    def enhance_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Enhance a single frame
        
        Args:
            frame: Input frame (BGR format, numpy array)
            
        Returns:
            Enhanced frame (BGR format, numpy array)
        """
        try:
            # Convert BGR to RGB
            img = frame[:, :, ::-1]
            img = np.float32(img) / 255.0
            h, w, c = img.shape
            
            # Prepare input tensor
            train_x = np.zeros((1, 3, h, w)).astype(np.float32)
            train_x[0, 0, :, :] = img[:, :, 0]
            train_x[0, 1, :, :] = img[:, :, 1]
            train_x[0, 2, :, :] = img[:, :, 2]
            
            # Convert to tensor
            dataset_torchx = torch.from_numpy(train_x).to(self.device)
            
            # Process
            with torch.no_grad():
                output = self.model(dataset_torchx)
            
            # Convert back to numpy
            output_img = output[0].cpu().numpy()
            output_img = np.transpose(output_img, (1, 2, 0))
            output_img = np.clip(output_img * 255.0, 0, 255).astype(np.uint8)
            
            # Convert RGB back to BGR
            output_img = output_img[:, :, ::-1]
            
            return output_img
            
        except Exception as e:
            print(f"Error enhancing frame: {str(e)}")
            return frame
    
    def process_video(self, 
                     input_path: str, 
                     output_path: str,
                     progress_callback: Optional[Callable] = None,
                     create_comparison: bool = True) -> dict:
        """
        Process entire video frame-by-frame
        
        Args:
            input_path: Path to input video
            output_path: Path to save enhanced video
            progress_callback: Function to call with progress updates
            create_comparison: Create side-by-side comparison video
            
        Returns:
            Dictionary with processing statistics
        """
        print(f"🎬 Starting video processing: {input_path}")
        start_time = time.time()
        
        # Extract frames
        print("📹 Extracting frames...")
        frames, fps, info = self.extract_frames(input_path)
        total_frames = len(frames)
        
        print(f"   Total frames: {total_frames}")
        print(f"   FPS: {fps}")
        print(f"   Resolution: {info['width']}x{info['height']}")
        print(f"   Duration: {info['duration']:.2f}s")
        
        # Process frames
        print("🔄 Processing frames...")
        enhanced_frames = []
        frame_times = []
        
        for i, frame in enumerate(frames):
            frame_start = time.time()
            
            # Enhance frame
            enhanced_frame = self.enhance_frame(frame)
            enhanced_frames.append(enhanced_frame)
            
            frame_time = time.time() - frame_start
            frame_times.append(frame_time)
            
            # Progress callback
            progress = (i + 1) / total_frames * 100
            avg_fps = (i + 1) / sum(frame_times) if sum(frame_times) > 0 else 0
            
            if progress_callback:
                progress_callback({
                    'progress': progress,
                    'current_frame': i + 1,
                    'total_frames': total_frames,
                    'fps': avg_fps,
                    'eta': (total_frames - i - 1) / avg_fps if avg_fps > 0 else 0
                })
            
            # Print progress every 10%
            if (i + 1) % max(1, total_frames // 10) == 0:
                print(f"   Progress: {progress:.1f}% | FPS: {avg_fps:.2f} | ETA: {(total_frames - i - 1) / avg_fps if avg_fps > 0 else 0:.1f}s")
        
        # Save video
        print("💾 Saving enhanced video...")
        if create_comparison:
            self._save_comparison_video(frames, enhanced_frames, output_path, fps)
        else:
            self._save_video(enhanced_frames, output_path, fps)
        
        # Calculate statistics
        processing_time = time.time() - start_time
        avg_fps = total_frames / processing_time
        
        stats = {
            'success': True,
            'total_frames': total_frames,
            'processing_time': processing_time,
            'average_fps': avg_fps,
            'original_fps': fps,
            'input_resolution': f"{info['width']}x{info['height']}",
            'duration': info['duration'],
            'output_path': output_path
        }
        
        print(f"✅ Video processing complete!")
        print(f"   Processing time: {processing_time:.2f}s")
        print(f"   Average FPS: {avg_fps:.2f}")
        print(f"   Output: {output_path}")
        
        return stats
    
    def _save_video(self, frames: list, output_path: str, fps: float):
        """Save frames as video"""
        if not frames:
            raise ValueError("No frames to save")
        
        height, width = frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        for frame in frames:
            out.write(frame)
        
        out.release()
    
    def _save_comparison_video(self, original_frames: list, enhanced_frames: list, 
                               output_path: str, fps: float):
        """Save side-by-side comparison video"""
        if not original_frames or not enhanced_frames:
            raise ValueError("No frames to save")
        
        height, width = original_frames[0].shape[:2]
        
        # Create comparison frames
        comparison_frames = []
        for orig, enhanced in zip(original_frames, enhanced_frames):
            # Resize if dimensions don't match
            if enhanced.shape != orig.shape:
                enhanced = cv2.resize(enhanced, (width, height))
            
            # Concatenate horizontally
            comparison = cv2.hconcat([orig, enhanced])
            comparison_frames.append(comparison)
        
        # Save video
        comp_height, comp_width = comparison_frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (comp_width, comp_height))
        
        for frame in comparison_frames:
            out.write(frame)
        
        out.release()


# Global video processor instance
_video_processor = None

def get_video_processor(model_type='uieb'):
    """Get or create the global video processor instance"""
    global _video_processor
    if _video_processor is None or _video_processor.model_type != model_type:
        _video_processor = VideoProcessor(model_type)
    return _video_processor


if __name__ == '__main__':
    # Test the video processor
    processor = VideoProcessor('uieb')
    
    test_video = os.path.join('..', 'uw_video_processing', 'degraded_video.mp4')
    output_video = 'test_enhanced_video.mp4'
    
    if os.path.exists(test_video):
        stats = processor.process_video(test_video, output_video, create_comparison=True)
        print(stats)
    else:
        print(f"Test video not found: {test_video}")
