"""
Threat Detection Module using YOLOv8
Detects underwater threats like submarines, mines, divers, drones
"""

import torch
import cv2
import numpy as np
from ultralytics import YOLO
import os
from .distance_estimator import DistanceEstimator

class ThreatDetector:
    """
    YOLOv8-based threat detection for underwater imagery
    """
    
    # Threat-related classes from COCO dataset
    THREAT_CLASSES = {
        # Direct threats
        'boat': 'submarine',
        'ship': 'submarine', 
        'person': 'diver',
        'truck': 'underwater_vehicle',
        'car': 'underwater_vehicle',
        'motorcycle': 'underwater_drone',
        'airplane': 'drone',
        'bird': 'drone',
        
        # Potential threats (we'll filter these)
        'backpack': 'suspicious_object',
        'suitcase': 'suspicious_object',
        'handbag': 'mine',
        'sports ball': 'mine',
    }
    
    # High-risk threat categories
    HIGH_RISK = ['submarine', 'mine', 'underwater_vehicle', 'suspicious_object']
    MEDIUM_RISK = ['diver', 'underwater_drone', 'drone']
    
    def __init__(self, model_size='n', confidence_threshold=0.25, estimate_distance=True, focal_length_px=None):
        """
        Initialize YOLOv8 detector
        
        Args:
            model_size: 'n' (nano), 's' (small), 'm' (medium), 'l' (large), 'x' (xlarge)
            confidence_threshold: Minimum confidence for detections (0-1)
            estimate_distance: Enable distance estimation (default: True)
            focal_length_px: Camera focal length in pixels (optional, will be estimated if not provided)
        """
        self.confidence_threshold = confidence_threshold
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.estimate_distance = estimate_distance
        
        print(f"🔍 Initializing YOLOv8 Threat Detector ({model_size})...")
        print(f"📱 Device: {self.device}")
        
        try:
            # Load pre-trained YOLOv8 model
            model_name = f'yolov8{model_size}.pt'
            self.model = YOLO(model_name)
            self.model.to(self.device)
            print(f"✅ YOLOv8 model loaded: {model_name}")
            
            # Initialize distance estimator if enabled
            if self.estimate_distance:
                self.distance_estimator = DistanceEstimator(focal_length_px=focal_length_px)
                print(f"✅ Distance estimation enabled")
            else:
                self.distance_estimator = None
            
        except Exception as e:
            print(f"❌ Error loading YOLOv8: {str(e)}")
            raise
    
    def detect_objects(self, image_path):
        """
        Detect all objects in image using YOLOv8
        
        Args:
            image_path: Path to input image
            
        Returns:
            List of detections with format:
            [{
                'class': str,
                'confidence': float,
                'bbox': [x1, y1, x2, y2],
                'center': (cx, cy)
            }]
        """
        try:
            # Run YOLOv8 inference
            results = self.model(
                image_path, 
                conf=self.confidence_threshold,
                verbose=False
            )
            
            detections = []
            
            for result in results:
                boxes = result.boxes
                
                for box in boxes:
                    # Extract detection info
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = result.names[class_id]
                    
                    # Calculate center point
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    
                    detections.append({
                        'class': class_name,
                        'confidence': confidence,
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'center': (cx, cy)
                    })
            
            return detections
            
        except Exception as e:
            print(f"❌ Detection error: {str(e)}")
            return []
    
    def filter_threats(self, detections, exclude_marine_life=True):
        """
        Filter detections to keep only potential threats
        
        Args:
            detections: List of all detections
            exclude_marine_life: If True, filter out fish and natural objects
            
        Returns:
            List of threat detections with threat_type and risk_level added
        """
        threats = []
        
        # Classes to exclude (marine life, natural objects)
        exclude_classes = [
            'fish', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
            'elephant', 'bear', 'zebra', 'giraffe', 'kite', 'frisbee'
        ] if exclude_marine_life else []
        
        for detection in detections:
            obj_class = detection['class'].lower()
            
            # Skip excluded classes
            if obj_class in exclude_classes:
                continue
            
            # Check if it's a potential threat
            if obj_class in self.THREAT_CLASSES:
                threat_type = self.THREAT_CLASSES[obj_class]
                
                # Determine risk level
                if threat_type in self.HIGH_RISK:
                    risk_level = 'HIGH'
                elif threat_type in self.MEDIUM_RISK:
                    risk_level = 'MEDIUM'
                else:
                    risk_level = 'LOW'
                
                threats.append({
                    **detection,
                    'threat_type': threat_type,
                    'risk_level': risk_level,
                    'original_class': obj_class
                })
        
        return threats
    
    def detect_threats(self, image_path, exclude_marine_life=True):
        """
        Complete threat detection pipeline with distance estimation
        
        Args:
            image_path: Path to input image
            exclude_marine_life: Filter out fish and natural objects
            
        Returns:
            List of detected threats with distance information
        """
        print(f"🔍 Scanning for threats in: {os.path.basename(image_path)}")
        print(f"   Confidence threshold: {self.confidence_threshold:.0%}")
        
        # Load image for distance estimation
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        image_shape = image.shape
        
        # Detect all objects
        detections = self.detect_objects(image_path)
        print(f"📊 Total objects detected: {len(detections)}")
        
        # Show what was detected
        if detections:
            detected_classes = {}
            for det in detections:
                cls = det['class']
                detected_classes[cls] = detected_classes.get(cls, 0) + 1
            print(f"   Detected classes: {detected_classes}")
        
        # Filter to threats only
        threats = self.filter_threats(detections, exclude_marine_life)
        print(f"⚠️  Threats identified: {len(threats)}")
        
        # Add distance estimation to each threat
        if self.estimate_distance and self.distance_estimator and threats:
            print(f"📏 Estimating distances...")
            for threat in threats:
                distance_info = self.distance_estimator.estimate_distance(
                    threat_type=threat['threat_type'],
                    bbox=threat['bbox'],
                    image_shape=image_shape
                )
                threat['distance'] = distance_info
        
        # Print threat summary with distances
        if threats:
            for threat in threats:
                dist_str = ""
                if 'distance' in threat and threat['distance'].get('distance_m'):
                    dist_str = f" | 📏 {threat['distance']['distance_display']}"
                
                print(f"  🎯 {threat['threat_type'].upper()} "
                      f"[{threat['risk_level']}] - "
                      f"Confidence: {threat['confidence']:.2%}{dist_str}")
        
        return threats
    
    def get_threat_summary(self, threats):
        """
        Generate summary statistics for detected threats
        
        Args:
            threats: List of threat detections
            
        Returns:
            Dictionary with threat statistics
        """
        if not threats:
            return {
                'total': 0,
                'high_risk': 0,
                'medium_risk': 0,
                'low_risk': 0,
                'types': {}
            }
        
        summary = {
            'total': len(threats),
            'high_risk': sum(1 for t in threats if t['risk_level'] == 'HIGH'),
            'medium_risk': sum(1 for t in threats if t['risk_level'] == 'MEDIUM'),
            'low_risk': sum(1 for t in threats if t['risk_level'] == 'LOW'),
            'types': {}
        }
        
        # Count by threat type
        for threat in threats:
            threat_type = threat['threat_type']
            summary['types'][threat_type] = summary['types'].get(threat_type, 0) + 1
        
        return summary
