"""
Enhanced Video Processing Module with OpenCV Tracking
Optimized for real-time threat detection and tracking in underwater videos
"""

import os
import sys
import cv2
import torch
import numpy as np
from typing import Tuple, Optional, Callable, List, Dict
import time
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class VideoProcessorV2:
    """
    Fast video processor with OpenCV-based object tracking
    """
    
    def __init__(self, model_type='uieb', enable_threat_detection=False):
        """
        Initialize video processor
        
        Args:
            model_type: 'uieb', 'euvp', or 'sr2x/sr3x/sr4x'
            enable_threat_detection: Enable YOLO threat detection and tracking
        """
        self.model_type = model_type
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.enable_threat_detection = enable_threat_detection
        self.yolo_model = None
        
        # OpenCV tracking
        self.trackers = []  # List of (tracker, threat_info) tuples
        self.next_track_id = 1
        
        # Alert system
        self.alert_system = None
        if enable_threat_detection:
            try:
                from alert_system import get_alert_system
                self.alert_system = get_alert_system()
                print("✅ Alert system initialized")
            except Exception as e:
                print(f"⚠️ Could not initialize alert system: {e}")
        
        # Threat class mappings
        self.THREAT_MAP = {
            'boat': 'submarine', 'ship': 'submarine', 'car': 'submarine',
            'bus': 'submarine', 'truck': 'submarine',
            'person': 'human_diver',
            'train': 'missile', 'airplane': 'missile',
            'bird': 'shark', 'cat': 'shark', 'dog': 'shark', 'fish': 'shark',
            'horse': 'monster', 'cow': 'monster', 'elephant': 'monster', 'bear': 'monster'
        }
        
        print(f"🎬 Initializing VideoProcessorV2 (model: {model_type}, threats: {enable_threat_detection})")
        self.load_model()
        
        # Initialize YOLO if threat detection enabled
        if self.enable_threat_detection:
            print("🛡️ Loading YOLO for threat detection...")
            try:
                from ultralytics import YOLO
                self.yolo_model = YOLO('yolov8n.pt')
                print("✅ YOLO loaded successfully")
            except Exception as e:
                print(f"⚠️ Could not load YOLO: {e}")
                self.enable_threat_detection = False
    
    def load_model(self):
        """Load the enhancement model"""
        try:
            # Add uw_video_processing to path
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            video_path = os.path.join(base_dir, 'uw_video_processing')
            if video_path not in sys.path:
                sys.path.insert(0, video_path)
            
            # Import and reload models
            import importlib
            import models as video_models
            importlib.reload(video_models)
            
            # Use CC_Module (the correct class name)
            self.model = video_models.CC_Module()
            
            # Find checkpoint
            checkpoint_path = None
            if self.model_type == 'uieb':
                checkpoint_path = os.path.join(base_dir, 'uw_video_processing', 'ckpts', 'netG_295.pt')
            elif self.model_type == 'euvp':
                # Find latest EUVP checkpoint
                euvp_ckpt_dir = os.path.join(base_dir, 'uie_euvp', 'ckpts')
                if os.path.exists(euvp_ckpt_dir):
                    ckpt_files = [f for f in os.listdir(euvp_ckpt_dir) if f.startswith('netG_') and f.endswith('.pt') and 'old' not in f.lower() and 'backup' not in f.lower()]
                    if ckpt_files:
                        ckpt_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]) if x.split('_')[1].split('.')[0].isdigit() else -1, reverse=True)
                        checkpoint_path = os.path.join(euvp_ckpt_dir, ckpt_files[0])
                        print(f"📦 Using EUVP: {ckpt_files[0]}")
                    else:
                        print("⚠️ No EUVP checkpoint, using UIEB")
                        checkpoint_path = os.path.join(base_dir, 'uw_video_processing', 'ckpts', 'netG_295.pt')
                else:
                    print("⚠️ EUVP ckpts not found, using UIEB")
                    checkpoint_path = os.path.join(base_dir, 'uw_video_processing', 'ckpts', 'netG_295.pt')
            
            # Load checkpoint
            if checkpoint_path and os.path.exists(checkpoint_path):
                print(f"📦 Loading {self.model_type.upper()} model from {os.path.basename(checkpoint_path)}")
                checkpoint = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
                if 'model_state_dict' in checkpoint:
                    self.model.load_state_dict(checkpoint['model_state_dict'])
                else:
                    self.model.load_state_dict(checkpoint)
                self.model.to(self.device)
                self.model.eval()
                print("✅ Model loaded successfully")
            else:
                print(f"⚠️ Checkpoint not found: {checkpoint_path}")
                self.model = None
            
            # Remove from path
            if video_path in sys.path:
                sys.path.remove(video_path)
                
        except Exception as e:
            print(f"⚠️ Error loading model: {e}")
            import traceback
            traceback.print_exc()
            self.model = None
    
    def enhance_frame(self, frame):
        """Enhance a single frame"""
        if self.model is None:
            return frame
        
        try:
            # Prepare frame
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = torch.from_numpy(img).float() / 255.0
            img = img.permute(2, 0, 1).unsqueeze(0).to(self.device)
            
            # Enhance
            with torch.no_grad():
                enhanced = self.model(img)
            
            # Convert back
            enhanced = enhanced.squeeze(0).permute(1, 2, 0).cpu().numpy()
            enhanced = np.clip(enhanced * 255, 0, 255).astype(np.uint8)
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_RGB2BGR)
            
            return enhanced
        except Exception as e:
            print(f"⚠️ Enhancement error: {e}")
            return frame
    
    def detect_threats(self, frame) -> List[Dict]:
        """
        Detect threats in frame using YOLO
        
        Returns:
            List of detections: [{'class': str, 'confidence': float, 'bbox': [x1,y1,x2,y2]}]
        """
        if not self.yolo_model:
            return []
        
        try:
            # Run YOLO detection
            results = self.yolo_model(frame, conf=0.20, verbose=False)  # Lower threshold for better detection
            
            detections = []
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    class_name = self.yolo_model.names[cls_id]
                    
                    # Check if it's a threat
                    if class_name in self.THREAT_MAP:
                        threat_class = self.THREAT_MAP[class_name]
                        confidence = float(box.conf[0])
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        
                        detections.append({
                            'class': threat_class,
                            'confidence': confidence,
                            'bbox': [int(x1), int(y1), int(x2), int(y2)]
                        })
            
            return detections
        except Exception as e:
            print(f"⚠️ Detection error: {e}")
            return []
    
    def initialize_trackers(self, frame, detections):
        """
        Initialize OpenCV trackers for detected threats
        
        Args:
            frame: Current video frame
            detections: List of threat detections
        """
        self.trackers = []
        
        for detection in detections:
            try:
                # Create new tracker (CSRT is accurate, KCF is faster)
                tracker = cv2.legacy.TrackerKCF_create()  # Fast tracker
                
                # Get bbox
                x1, y1, x2, y2 = detection['bbox']
                bbox = (x1, y1, x2 - x1, y2 - y1)  # OpenCV format: (x, y, width, height)
                
                # Initialize tracker
                tracker.init(frame, bbox)
                
                # Store tracker with threat info
                threat_info = {
                    'track_id': self.next_track_id,
                    'class': detection['class'],
                    'confidence': detection['confidence'],
                    'bbox': detection['bbox']
                }
                self.next_track_id += 1
                
                self.trackers.append((tracker, threat_info))
                
            except Exception as e:
                print(f"⚠️ Tracker init error: {e}")
    
    def update_trackers(self, frame):
        """
        Update all active trackers
        
        Args:
            frame: Current video frame
            
        Returns:
            List of tracked threats with updated positions
        """
        tracked_threats = []
        valid_trackers = []
        
        for tracker, threat_info in self.trackers:
            try:
                # Update tracker
                success, bbox = tracker.update(frame)
                
                if success:
                    # Convert bbox back to [x1, y1, x2, y2]
                    x, y, w, h = [int(v) for v in bbox]
                    threat_info['bbox'] = [x, y, x + w, y + h]
                    tracked_threats.append(threat_info)
                    valid_trackers.append((tracker, threat_info))
                
            except Exception as e:
                print(f"⚠️ Tracker update error: {e}")
        
        # Keep only valid trackers
        self.trackers = valid_trackers
        
        return tracked_threats
    
    def draw_threat_boxes(self, frame, threats):
        """
        Draw bounding boxes and labels for threats
        
        Args:
            frame: Video frame (will be modified in-place)
            threats: List of threat dictionaries
        """
        for threat in threats:
            try:
                x1, y1, x2, y2 = threat['bbox']
                threat_class = threat['class']
                confidence = threat['confidence']
                track_id = threat.get('track_id', 0)
                
                # Color based on threat level - BRIGHT AND VISIBLE
                if threat_class in ['submarine', 'missile', 'shark']:
                    color = (0, 0, 255)  # RED - Critical
                    thickness = 5
                elif threat_class == 'human_diver':
                    color = (0, 165, 255)  # ORANGE - High risk
                    thickness = 4
                else:
                    color = (0, 255, 255)  # YELLOW - Moderate
                    thickness = 4
                
                # Draw THICK bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
                
                # Draw corner markers for visibility
                corner_len = 20
                corner_thick = thickness + 2
                # Top-left corner
                cv2.line(frame, (x1, y1), (x1 + corner_len, y1), color, corner_thick)
                cv2.line(frame, (x1, y1), (x1, y1 + corner_len), color, corner_thick)
                # Top-right corner
                cv2.line(frame, (x2, y1), (x2 - corner_len, y1), color, corner_thick)
                cv2.line(frame, (x2, y1), (x2, y1 + corner_len), color, corner_thick)
                # Bottom-left corner
                cv2.line(frame, (x1, y2), (x1 + corner_len, y2), color, corner_thick)
                cv2.line(frame, (x1, y2), (x1, y2 - corner_len), color, corner_thick)
                # Bottom-right corner
                cv2.line(frame, (x2, y2), (x2 - corner_len, y2), color, corner_thick)
                cv2.line(frame, (x2, y2), (x2, y2 - corner_len), color, corner_thick)
                
                # Draw center crosshair
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                cross_len = 15
                cv2.line(frame, (center_x - cross_len, center_y), (center_x + cross_len, center_y), color, 3)
                cv2.line(frame, (center_x, center_y - cross_len), (center_x, center_y + cross_len), color, 3)
                
                # Prepare label
                label = f"ID:{track_id} {threat_class.upper()}"
                conf_text = f"{confidence*100:.0f}%"
                
                # Draw label background - LARGE and VISIBLE
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.9
                font_thick = 3
                (label_w, label_h), baseline = cv2.getTextSize(label, font, font_scale, font_thick)
                
                # Label above box
                cv2.rectangle(frame, (x1, y1 - label_h - 20), 
                            (x1 + label_w + 20, y1), color, -1)
                cv2.putText(frame, label, (x1 + 10, y1 - 10), 
                           font, font_scale, (255, 255, 255), font_thick)
                
                # Confidence below box
                cv2.putText(frame, conf_text, (x1, y2 + 30),
                           font, 0.8, color, 3)
                
            except Exception as e:
                print(f"⚠️ Draw error: {e}")
    
    def process_video(self, 
                     input_path: str, 
                     output_path: str,
                     progress_callback: Optional[Callable] = None,
                     create_comparison: bool = True) -> dict:
        """
        Process video with enhancement and threat tracking
        
        Args:
            input_path: Path to input video
            output_path: Path to save enhanced video
            progress_callback: Function to call with progress updates
            create_comparison: Create side-by-side comparison
            
        Returns:
            Processing statistics dictionary
        """
        start_time = time.time()
        
        # Open video
        print(f"📹 Opening video: {input_path}")
        cap = cv2.VideoCapture(input_path)
        
        if not cap.isOpened():
            print("❌ Error: Could not open video")
            return {'success': False, 'error': 'Could not open video'}
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"📊 Video info: {total_frames} frames @ {fps} FPS, {width}x{height}")
        print(f"🛡️ Threat detection: {'ENABLED' if self.enable_threat_detection else 'DISABLED'}")
        
        # Read all frames
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        
        print(f"✅ Loaded {len(frames)} frames")
        
        # Process frames
        print("🔄 Processing frames with tracking...")
        enhanced_frames = []
        frame_times = []
        detection_interval = 10  # Detect every N frames, track in between
        
        for i, frame in enumerate(frames):
            try:
                frame_start = time.time()
                
                # Enhance frame
                enhanced_frame = self.enhance_frame(frame)
                
                # Threat detection and tracking
                if self.enable_threat_detection and self.yolo_model:
                    # Run detection every N frames
                    if i % detection_interval == 0:
                        detections = self.detect_threats(enhanced_frame)
                        if detections:
                            print(f"   🎯 Frame {i}: Detected {len(detections)} threats - Initializing trackers")
                            self.initialize_trackers(enhanced_frame, detections)
                            self.draw_threat_boxes(enhanced_frame, detections)
                            
                            # Create alerts for new threats
                            if self.alert_system:
                                for detection in detections:
                                    self.alert_system.create_alert(
                                        threat=detection,
                                        video_id=os.path.basename(output_path),
                                        frame_number=i
                                    )
                    else:
                        # Update trackers on other frames
                        tracked_threats = self.update_trackers(enhanced_frame)
                        if tracked_threats:
                            self.draw_threat_boxes(enhanced_frame, tracked_threats)
                
                enhanced_frames.append(enhanced_frame)
                
                frame_time = time.time() - frame_start
                frame_times.append(frame_time)
                
                # Progress update
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
                    print(f"   ⏳ Progress: {progress:.1f}% | FPS: {avg_fps:.2f}")
                
            except Exception as e:
                print(f"   ❌ Error frame {i}: {e}")
                enhanced_frames.append(frame)
        
        # Save video
        print("💾 Saving enhanced video...")
        
        # Notify that saving is starting
        if progress_callback:
            progress_callback({
                'progress': 100,
                'current_frame': total_frames,
                'total_frames': total_frames,
                'fps': avg_fps,
                'eta': 0,
                'status': 'saving'
            })
        
        if create_comparison:
            self._save_comparison_video(frames, enhanced_frames, output_path, fps)
        else:
            self._save_video(enhanced_frames, output_path, fps)
        
        # Calculate quality metrics on sample frames
        print("📊 Calculating quality metrics...")
        metrics_results = self._calculate_video_metrics(frames, enhanced_frames)
        
        # Stats
        processing_time = time.time() - start_time
        avg_fps = total_frames / processing_time
        threat_count = len(self.trackers)
        
        stats = {
            'success': True,
            'total_frames': total_frames,
            'processing_time': processing_time,
            'average_fps': avg_fps,
            'resolution': f"{width}x{height}",
            'threats_detected': threat_count > 0,
            'threat_count': threat_count,
            'psnr': metrics_results['psnr'],
            'ssim': metrics_results['ssim'],
            'uiqm': metrics_results['uiqm'],
            'uciqe': metrics_results.get('uciqe', 0.0),
            'sharpness': metrics_results.get('sharpness', 0.0),
            'contrast': metrics_results.get('contrast', 0.0),
            'improvement': metrics_results.get('improvement', 0.0)
        }
        
        print(f"✅ Processing complete!")
        print(f"   Total time: {processing_time:.2f}s")
        print(f"   Average FPS: {avg_fps:.2f}")
        print(f"   Threats tracked: {threat_count}")
        print(f"   Quality: PSNR={stats['psnr']:.2f} SSIM={stats['ssim']:.4f} UIQM={stats['uiqm']:.4f}")
        
        return stats
    
    def _save_video(self, frames, output_path, fps):
        """Save frames as video in MP4 format"""
        # Ensure output path has .mp4 extension
        if not output_path.lower().endswith('.mp4'):
            output_path = output_path.rsplit('.', 1)[0] + '.mp4'
        
        height, width = frames[0].shape[:2]
        
        # Use mp4v codec - most reliable for Windows without external DLLs
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            print("⚠️ mp4v failed, trying XVID")
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            output_path = output_path.rsplit('.', 1)[0] + '.avi'
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        for frame in frames:
            out.write(frame)
        
        out.release()
        print(f"✅ Video saved: {output_path}")
    
    def _save_comparison_video(self, original_frames, enhanced_frames, output_path, fps):
        """Save side-by-side comparison video in MP4 format"""
        # Ensure output path has .mp4 extension
        if not output_path.lower().endswith('.mp4'):
            output_path = output_path.rsplit('.', 1)[0] + '.mp4'
        
        height, width = original_frames[0].shape[:2]
        
        # Use mp4v codec - most reliable for Windows without external DLLs
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width * 2, height))
        
        if not out.isOpened():
            print("⚠️ mp4v failed for comparison, trying XVID")
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            output_path = output_path.rsplit('.', 1)[0] + '.avi'
            out = cv2.VideoWriter(output_path, fourcc, fps, (width * 2, height))
        
        for orig, enh in zip(original_frames, enhanced_frames):
            comparison = np.hstack([orig, enh])
            out.write(comparison)
        
        out.release()
        print(f"✅ Comparison video saved: {output_path}")
    
    def _calculate_video_metrics(self, original_frames, enhanced_frames):
        """
        Calculate quality metrics by sampling frames from the video
        """
        try:
            from metrics_calculator import get_metrics_calculator
            
            calculator = get_metrics_calculator()
            
            # Sample frames (every 10% of the video)
            num_samples = min(10, len(original_frames))
            indices = np.linspace(0, len(original_frames) - 1, num_samples, dtype=int)
            
            all_psnr = []
            all_ssim = []
            all_uiqm = []
            all_uciqe = []
            all_sharpness = []
            all_contrast = []
            
            for idx in indices:
                orig_frame = original_frames[idx]
                enh_frame = enhanced_frames[idx]
                
                # Calculate metrics for this frame
                metrics = calculator.calculate_all_metrics(orig_frame, enh_frame, has_reference=True)
                
                if metrics['psnr'] > 0:
                    all_psnr.append(metrics['psnr'])
                if metrics['ssim'] > 0:
                    all_ssim.append(metrics['ssim'])
                if metrics['uiqm'] > 0:
                    all_uiqm.append(metrics['uiqm'])
                if metrics.get('uciqe', 0) > 0:
                    all_uciqe.append(metrics['uciqe'])
                if metrics.get('sharpness', 0) > 0:
                    all_sharpness.append(metrics['sharpness'])
                if metrics.get('contrast', 0) > 0:
                    all_contrast.append(metrics['contrast'])
            
            # Average the metrics
            result = {
                'psnr': round(np.mean(all_psnr), 2) if all_psnr else 0.0,
                'ssim': round(np.mean(all_ssim), 4) if all_ssim else 0.0,
                'uiqm': round(np.mean(all_uiqm), 4) if all_uiqm else 0.0,
                'uciqe': round(np.mean(all_uciqe), 4) if all_uciqe else 0.0,
                'sharpness': round(np.mean(all_sharpness), 2) if all_sharpness else 0.0,
                'contrast': round(np.mean(all_contrast), 2) if all_contrast else 0.0,
                'improvement': 0.0
            }
            
            # Calculate improvement percentage
            if all_uiqm and len(all_uiqm) > 0:
                # Compare first and last frame UIQM
                orig_first_uiqm = calculator.calculate_uiqm(
                    cv2.cvtColor(original_frames[0], cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
                )
                if orig_first_uiqm > 0:
                    result['improvement'] = round((result['uiqm'] - orig_first_uiqm) / orig_first_uiqm * 100, 2)
            
            return result
            
        except Exception as e:
            print(f"⚠️ Metrics calculation error: {e}")
            return {
                'psnr': 0.0,
                'ssim': 0.0,
                'uiqm': 0.0,
                'uciqe': 0.0,
                'sharpness': 0.0,
                'contrast': 0.0,
                'improvement': 0.0
            }


if __name__ == "__main__":
    # Test the processor
    processor = VideoProcessorV2(model_type='uieb', enable_threat_detection=True)
    
    test_video = "uploads/test_video.mp4"
    output_video = "results/tracked_video.mp4"
    
    if os.path.exists(test_video):
        stats = processor.process_video(test_video, output_video, create_comparison=True)
        print(f"\n📊 Final stats: {stats}")
    else:
        print(f"⚠️ Test video not found: {test_video}")
