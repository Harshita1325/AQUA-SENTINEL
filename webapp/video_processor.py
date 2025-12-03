"""
Video Processing Module for DeepWater Web Application
Handles frame-by-frame enhancement of underwater videos with threat detection
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

# Import threat detection
from threat_detection.detector import ThreatDetector

class VideoProcessor:
    """
    Process underwater videos frame-by-frame using enhancement models
    """
    
    def __init__(self, model_type='uieb', enable_threat_detection=False):
        """
        Initialize video processor with specified model
        
        Args:
            model_type: 'uieb', 'euvp', or 'sr2x/sr3x/sr4x'
            enable_threat_detection: Enable YOLO threat detection on frames
        """
        self.model_type = model_type
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.enable_threat_detection = enable_threat_detection
        self.threat_detector = None
        self.threat_tracker = {}  # Track threats across frames {track_id: {info}}
        self.next_track_id = 1
        self.yolo_model = None
        
        self.load_model()
        
        # Initialize YOLO for threat detection if enabled
        if self.enable_threat_detection:
            print("🛡️ Initializing fast YOLO threat detection for video...")
            try:
                from ultralytics import YOLO
                self.yolo_model = YOLO('yolov8n.pt')
                print("✅ YOLO loaded for real-time detection")
            except Exception as e:
                print(f"⚠️ Could not load YOLO: {e}")
        
    def load_model(self):
        """Load the enhancement model"""
        try:
            # Get the base directory
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Use the existing model processor approach
            if self.model_type == 'uieb':
                # Use uw_video_processing model (original architecture)
                video_path = os.path.join(base_dir, 'uw_video_processing')
                if video_path not in sys.path:
                    sys.path.insert(0, video_path)
                
                import importlib
                import models as uieb_models
                importlib.reload(uieb_models)
                
                self.model = uieb_models.CC_Module()
                model_path = os.path.join(base_dir, 'uw_video_processing', 'ckpts', 'netG_295.pt')
                
                # Remove from path after import
                if video_path in sys.path:
                    sys.path.remove(video_path)
                
            elif self.model_type == 'euvp':
                # Add EUVP path and import
                euvp_path = os.path.join(base_dir, 'uie_euvp')
                if euvp_path not in sys.path:
                    sys.path.insert(0, euvp_path)
                
                import importlib
                import models as euvp_models
                importlib.reload(euvp_models)
                
                self.model = euvp_models.CC_Module()
                
                # Find latest EUVP checkpoint
                ckpt_dir = os.path.join(base_dir, 'uie_euvp', 'ckpts')
                if os.path.exists(ckpt_dir):
                    ckpt_files = [f for f in os.listdir(ckpt_dir) if f.startswith('netG_') and f.endswith('.pt') and 'old' not in f.lower() and 'backup' not in f.lower()]
                    if ckpt_files:
                        # Sort by epoch number to get latest
                        ckpt_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]) if x.split('_')[1].split('.')[0].isdigit() else -1, reverse=True)
                        model_path = os.path.join(ckpt_dir, ckpt_files[0])
                        print(f"📦 Using EUVP checkpoint: {ckpt_files[0]}")
                    else:
                        # No EUVP checkpoint, fallback to UIEB
                        print("⚠️ No EUVP checkpoint found, using UIEB model instead")
                        if euvp_path in sys.path:
                            sys.path.remove(euvp_path)
                        video_path = os.path.join(base_dir, 'uw_video_processing')
                        sys.path.insert(0, video_path)
                        import models as video_models
                        importlib.reload(video_models)
                        self.model = video_models.CC_Module()
                        model_path = os.path.join(base_dir, 'uw_video_processing', 'ckpts', 'netG_295.pt')
                        sys.path.remove(video_path)
                else:
                    raise FileNotFoundError(f"EUVP checkpoint directory not found: {ckpt_dir}")
                
                # Remove from path after import
                if euvp_path in sys.path:
                    sys.path.remove(euvp_path)
                
            elif self.model_type.startswith('sr'):
                # SR models have architecture mismatch - use UIEB instead
                print(f"⚠️ SR models disabled, using UIEB model instead")
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
    
    def _detect_threats_fast(self, frame):
        """Fast YOLO-based threat detection directly on frame (no file I/O)"""
        try:
            # Threat class mappings (simplified for video)
            THREAT_MAP = {
                'boat': 'submarine', 'ship': 'submarine', 'car': 'submarine', 
                'bus': 'submarine', 'truck': 'submarine',
                'person': 'human_diver',
                'train': 'missile', 'airplane': 'missile',
                'bird': 'shark', 'cat': 'shark', 'dog': 'shark',
                'horse': 'monster', 'cow': 'monster', 'elephant': 'monster', 'bear': 'monster'
            }
            
            # Run YOLO detection (BGR format from OpenCV)
            results = self.yolo_model(frame, conf=0.25, verbose=False)
            
            detections = []
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    # Get class name
                    cls_id = int(box.cls[0])
                    class_name = self.yolo_model.names[cls_id]
                    
                    # Check if it's a threat
                    if class_name in THREAT_MAP:
                        threat_class = THREAT_MAP[class_name]
                        confidence = float(box.conf[0])
                        
                        # Get bbox coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        
                        detections.append({
                            'class': threat_class,
                            'confidence': confidence,
                            'bbox': [float(x1), float(y1), float(x2), float(y2)]
                        })
            
            # Track detections across frames
            if detections:
                detections = self._track_threats(detections)
            
            return detections
        except Exception as e:
            print(f"⚠️ Detection error: {e}")
            return []
    
    def _track_threats(self, detections):
        """Track threats across frames using IoU matching"""
        if not detections:
            return detections
        
        # Match current detections with existing tracks
        for detection in detections:
            bbox = detection['bbox']
            threat_class = detection['class']
            matched = False
            best_iou = 0.3  # Minimum IoU threshold for matching
            best_track_id = None
            
            # Try to match with existing tracks
            for track_id, track_info in self.threat_tracker.items():
                if track_info['class'] == threat_class:
                    iou = self._calculate_iou(bbox, track_info['bbox'])
                    if iou > best_iou:
                        best_iou = iou
                        best_track_id = track_id
                        matched = True
            
            # Assign track ID
            if matched:
                detection['track_id'] = best_track_id
                self.threat_tracker[best_track_id]['bbox'] = bbox
                self.threat_tracker[best_track_id]['frames_tracked'] += 1
            else:
                # Create new track
                detection['track_id'] = self.next_track_id
                self.threat_tracker[self.next_track_id] = {
                    'class': threat_class,
                    'bbox': bbox,
                    'frames_tracked': 1
                }
                self.next_track_id += 1
        
        return detections
    
    def _calculate_iou(self, bbox1, bbox2):
        """Calculate Intersection over Union between two bounding boxes"""
        x1_min, y1_min, x1_max, y1_max = bbox1
        x2_min, y2_min, x2_max, y2_max = bbox2
        
        # Calculate intersection area
        x_left = max(x1_min, x2_min)
        y_top = max(y1_min, y2_min)
        x_right = min(x1_max, x2_max)
        y_bottom = min(y1_max, y2_max)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        
        # Calculate union area
        bbox1_area = (x1_max - x1_min) * (y1_max - y1_min)
        bbox2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = bbox1_area + bbox2_area - intersection_area
        
        return intersection_area / union_area if union_area > 0 else 0.0
    
    def _draw_threat_boxes(self, frame, detections):
        """Draw threat detection bounding boxes on frame"""
        try:
            for detection in detections:
                # Get bounding box coordinates
                x1, y1, x2, y2 = detection['bbox']
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                # Get threat info
                threat_class = detection['class']
                confidence = detection['confidence']
                track_id = detection.get('track_id', 0)
                
                # Color based on threat level - BRIGHT COLORS
                if threat_class in ['submarine', 'missile', 'shark']:
                    color = (0, 0, 255)  # Bright Red - Critical
                    thickness = 4
                elif threat_class == 'human_diver':
                    color = (0, 165, 255)  # Orange - High risk  
                    thickness = 3
                else:
                    color = (0, 255, 255)  # Yellow - Moderate
                    thickness = 3
                
                # Draw THICK bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
                
                # Draw corner markers for better visibility
                corner_len = 15
                # Top-left
                cv2.line(frame, (x1, y1), (x1 + corner_len, y1), color, thickness + 1)
                cv2.line(frame, (x1, y1), (x1, y1 + corner_len), color, thickness + 1)
                # Top-right
                cv2.line(frame, (x2, y1), (x2 - corner_len, y1), color, thickness + 1)
                cv2.line(frame, (x2, y1), (x2, y1 + corner_len), color, thickness + 1)
                # Bottom-left
                cv2.line(frame, (x1, y2), (x1 + corner_len, y2), color, thickness + 1)
                cv2.line(frame, (x1, y2), (x1, y2 - corner_len), color, thickness + 1)
                # Bottom-right
                cv2.line(frame, (x2, y2), (x2 - corner_len, y2), color, thickness + 1)
                cv2.line(frame, (x2, y2), (x2, y2 - corner_len), color, thickness + 1)
                
                # Prepare label with tracking ID
                label = f"ID:{track_id} {threat_class.upper()}"
                conf_text = f"{confidence*100:.0f}%"
                
                # Draw label background (larger)
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
                cv2.rectangle(frame, (x1, y1 - label_size[1] - 15), 
                            (x1 + label_size[0] + 15, y1), color, -1)
                
                # Draw label text (larger)
                cv2.putText(frame, label, (x1 + 7, y1 - 7), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                
                # Draw confidence below box (larger)
                cv2.putText(frame, conf_text, (x1, y2 + 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            return frame
        except Exception as e:
            print(f"⚠️ Error drawing threat boxes: {e}")
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
        
        # Process frames (skip every other frame for 2x speed)
        print("🔄 Processing frames (optimized mode - 2x faster)...")
        enhanced_frames = []
        frame_times = []
        last_detections = []  # Cache detections for skipped frames
        
        for i, frame in enumerate(frames):
            try:
                frame_start = time.time()
                
                # Only print every 10 frames
                if i % 10 == 0:
                    print(f"   Processing frame {i+1}/{total_frames}...")
                
                # Enhance frame
                enhanced_frame = self.enhance_frame(frame)
                
                # Apply threat detection (only on even frames for speed)
                detections = []
                if self.enable_threat_detection and self.yolo_model and i % 2 == 0:
                    # Fast YOLO detection directly on frame
                    detections = self._detect_threats_fast(enhanced_frame)
                    last_detections = detections  # Cache for next frame
                elif self.enable_threat_detection and last_detections:
                    # Use cached detections for odd frames
                    detections = last_detections
                
                # Draw bounding boxes if threats found
                if detections:
                    enhanced_frame = self._draw_threat_boxes(enhanced_frame, detections)
                
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
            
            except Exception as e:
                print(f"   ❌ ERROR processing frame {i+1}: {str(e)}")
                import traceback
                traceback.print_exc()
                # Use original frame on error
                enhanced_frames.append(frame)
        
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
        
        print(f" Video processing complete!")
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
