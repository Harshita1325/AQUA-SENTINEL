"""
Distance Estimation Module for Threat Detection
Estimates distance to detected underwater threats using pinhole camera model
"""

import math
import numpy as np

# Known object sizes in meters (real-world dimensions)
# Maps both YOLO class names and threat types to real-world dimensions
KNOWN_OBJECT_SIZES = {
    # YOLO Original Classes
    'person': {'height': 1.75, 'width': 0.6, 'depth': 0.3},
    'boat': {'length': 50.0, 'width': 10.0, 'height': 8.0},
    'ship': {'length': 150.0, 'width': 25.0, 'height': 40.0},
    'car': {'length': 4.5, 'width': 1.8, 'height': 1.5},
    'bus': {'length': 12.0, 'width': 2.5, 'height': 3.0},
    'truck': {'length': 8.0, 'width': 2.5, 'height': 3.5},
    'motorcycle': {'length': 2.0, 'width': 0.8, 'height': 1.2},
    'bicycle': {'length': 1.8, 'width': 0.6, 'height': 1.1},
    'airplane': {'length': 15.0, 'width': 12.0, 'height': 4.0},
    'train': {'length': 25.0, 'width': 3.0, 'height': 4.0},
    
    # Sports & Weapons
    'sports ball': {'diameter': 1.5, 'radius': 0.75},
    'frisbee': {'diameter': 0.8, 'radius': 0.4},
    'kite': {'length': 1.2, 'width': 1.2, 'height': 0.1},
    'baseball bat': {'length': 1.0, 'width': 0.07, 'height': 0.07},
    'tennis racket': {'length': 0.7, 'width': 0.3, 'height': 0.05},
    'knife': {'length': 0.3, 'width': 0.03, 'height': 0.02},
    'scissors': {'length': 0.2, 'width': 0.08, 'height': 0.02},
    'fork': {'length': 0.2, 'width': 0.03, 'height': 0.01},
    'spoon': {'length': 0.18, 'width': 0.04, 'height': 0.01},
    
    # Containers & Packages
    'backpack': {'length': 0.5, 'width': 0.35, 'height': 0.2},
    'suitcase': {'length': 0.7, 'width': 0.5, 'height': 0.25},
    'handbag': {'length': 0.4, 'width': 0.3, 'height': 0.15},
    'bottle': {'height': 0.3, 'width': 0.08, 'depth': 0.08},
    'cup': {'height': 0.15, 'width': 0.08, 'depth': 0.08},
    'bowl': {'height': 0.1, 'width': 0.2, 'depth': 0.2},
    'vase': {'height': 0.3, 'width': 0.15, 'depth': 0.15},
    
    # Electronics
    'cell phone': {'length': 0.15, 'width': 0.075, 'height': 0.01},
    'laptop': {'length': 0.35, 'width': 0.25, 'height': 0.025},
    'keyboard': {'length': 0.45, 'width': 0.15, 'height': 0.03},
    'mouse': {'length': 0.1, 'width': 0.06, 'height': 0.04},
    'remote': {'length': 0.2, 'width': 0.05, 'height': 0.025},
    'tv': {'length': 1.2, 'width': 0.7, 'height': 0.1},
    'microwave': {'length': 0.5, 'width': 0.4, 'height': 0.3},
    'oven': {'length': 0.6, 'width': 0.6, 'height': 0.6},
    'toaster': {'length': 0.3, 'width': 0.2, 'height': 0.2},
    'refrigerator': {'length': 0.7, 'width': 0.7, 'height': 1.8},
    
    # Furniture & Structures
    'chair': {'length': 0.5, 'width': 0.5, 'height': 0.9},
    'couch': {'length': 2.0, 'width': 0.9, 'height': 0.85},
    'bed': {'length': 2.0, 'width': 1.5, 'height': 0.5},
    'dining table': {'length': 1.8, 'width': 0.9, 'height': 0.75},
    'bench': {'length': 1.5, 'width': 0.5, 'height': 0.5},
    
    # Outdoor Objects
    'traffic light': {'height': 0.8, 'width': 0.3, 'depth': 0.3},
    'fire hydrant': {'height': 0.7, 'width': 0.3, 'depth': 0.3},
    'stop sign': {'height': 0.75, 'width': 0.75, 'depth': 0.05},
    'parking meter': {'height': 1.5, 'width': 0.3, 'depth': 0.3},
    'umbrella': {'diameter': 1.0, 'radius': 0.5},
    
    # Boards & Platforms
    'skateboard': {'length': 0.8, 'width': 0.2, 'height': 0.15},
    'surfboard': {'length': 2.0, 'width': 0.5, 'height': 0.08},
    'snowboard': {'length': 1.5, 'width': 0.25, 'height': 0.05},
    
    # Other Items
    'book': {'length': 0.25, 'width': 0.18, 'height': 0.03},
    'clock': {'diameter': 0.3, 'radius': 0.15},
    'potted plant': {'height': 0.5, 'width': 0.3, 'depth': 0.3},
    'tie': {'length': 1.4, 'width': 0.1, 'height': 0.005},
    'sink': {'length': 0.6, 'width': 0.5, 'height': 0.2},
    
    # Animals (for reference)
    'bird': {'length': 0.3, 'width': 0.4, 'height': 0.15},
    'cat': {'length': 0.5, 'width': 0.25, 'height': 0.25},
    'dog': {'length': 0.8, 'width': 0.4, 'height': 0.6},
    'horse': {'length': 2.4, 'width': 0.6, 'height': 1.6},
    'sheep': {'length': 1.5, 'width': 0.5, 'height': 1.0},
    'cow': {'length': 2.5, 'width': 0.8, 'height': 1.5},
    'elephant': {'length': 6.0, 'width': 3.0, 'height': 3.5},
    'bear': {'length': 2.0, 'width': 1.0, 'height': 1.5},
    'zebra': {'length': 2.5, 'width': 0.6, 'height': 1.4},
    'giraffe': {'length': 2.5, 'width': 0.8, 'height': 5.0},
    
    # Mapped Threat Types (for backward compatibility)
    'hostile_diver': {'height': 1.75, 'width': 0.6, 'depth': 0.3},
    'hostile_submarine': {'length': 50.0, 'width': 10.0, 'height': 8.0},
    'enemy_warship': {'length': 150.0, 'width': 25.0, 'height': 40.0},
    'midget_submarine': {'length': 4.5, 'width': 1.8, 'height': 1.5},
    'submersible': {'length': 12.0, 'width': 2.5, 'height': 3.0},
    'autonomous_underwater_vehicle': {'length': 8.0, 'width': 2.5, 'height': 3.5},
    'underwater_scooter': {'length': 2.0, 'width': 0.8, 'height': 1.2},
    'small_underwater_vehicle': {'length': 1.8, 'width': 0.6, 'height': 1.1},
    'aerial_drone': {'length': 15.0, 'width': 12.0, 'height': 4.0},
    'torpedo': {'length': 25.0, 'width': 3.0, 'height': 4.0},
    'naval_mine': {'diameter': 1.5, 'radius': 0.75},
    'limpet_mine': {'diameter': 0.8, 'radius': 0.4},
    'floating_mine': {'diameter': 1.2, 'radius': 0.6},
    'ied_device': {'length': 0.5, 'width': 0.35, 'height': 0.2},
    'explosive_package': {'length': 0.7, 'width': 0.5, 'height': 0.25},
    'suspicious_container': {'length': 0.4, 'width': 0.3, 'height': 0.15},
    'spear_gun': {'length': 1.0, 'width': 0.07, 'height': 0.07},
    'underwater_weapon': {'length': 0.7, 'width': 0.3, 'height': 0.05},
    'combat_knife': {'length': 0.3, 'width': 0.03, 'height': 0.02},
    'communication_device': {'length': 0.15, 'width': 0.075, 'height': 0.01},
    'electronic_equipment': {'length': 0.35, 'width': 0.25, 'height': 0.025},
    'control_device': {'length': 0.2, 'width': 0.05, 'height': 0.025},
}


class DistanceEstimator:
    """
    Estimates distance to detected objects using pinhole camera model.
    
    Distance = (Real Object Size × Focal Length) / Pixel Size
    """
    
    def __init__(self, focal_length_px=None, sensor_width_mm=None, image_width_px=None):
        """
        Initialize distance estimator.
        
        Args:
            focal_length_px (float): Camera focal length in pixels (if known)
            sensor_width_mm (float): Camera sensor width in mm (default: 6.17mm for smartphone)
            image_width_px (int): Image width in pixels
        """
        self.focal_length_px = focal_length_px
        self.sensor_width_mm = sensor_width_mm or 6.17  # iPhone/smartphone typical
        self.image_width_px = image_width_px
        
        # Underwater refraction correction factor (water refractive index ≈ 1.33)
        self.refraction_factor = 1.33
        
        print(f"📏 Distance Estimator initialized")
        print(f"   Sensor width: {self.sensor_width_mm}mm")
        if focal_length_px:
            print(f"   Focal length: {focal_length_px}px")
        else:
            print(f"   Focal length: Will be estimated from image")
    
    def _estimate_focal_length(self, image_width_px):
        """
        Estimate focal length if not provided.
        Assumes typical underwater camera with 35mm equivalent of ~26mm.
        
        Args:
            image_width_px (int): Image width in pixels
            
        Returns:
            float: Estimated focal length in pixels
        """
        # Typical underwater camera focal length: 24-28mm (35mm equivalent)
        focal_length_mm = 26.0
        
        # Convert to pixels using sensor dimensions
        focal_length_px = (focal_length_mm * image_width_px) / self.sensor_width_mm
        
        return focal_length_px
    
    def estimate_distance(self, threat_type, bbox, image_shape):
        """
        Estimate distance to detected threat using pinhole camera model.
        
        Args:
            threat_type (str): Type of threat ('submarine', 'diver', 'mine', etc.)
            bbox (list): Bounding box coordinates [x1, y1, x2, y2]
            image_shape (tuple): Image dimensions (height, width, channels)
        
        Returns:
            dict: {
                'distance_m': Distance in meters (float),
                'distance_display': Formatted string for display,
                'confidence': Confidence level ('high', 'medium', 'low'),
                'error_margin': Error margin string (e.g., '±20%'),
                'method': Estimation method used,
                'focal_length_px': Focal length used (for debugging),
                'object_size_m': Real object size used (for debugging),
                'pixel_size': Detected size in pixels (for debugging)
            }
        """
        # Check if object size is known
        if threat_type not in KNOWN_OBJECT_SIZES:
            # Try with underscores replaced
            threat_type_normalized = threat_type.replace('-', '_').replace(' ', '_').lower()
            if threat_type_normalized not in KNOWN_OBJECT_SIZES:
                print(f"  ⚠️ Distance estimation: Unknown object type '{threat_type}'")
                print(f"     Using default estimation (1.0m reference)")
                # Use a default generic object size
                obj_dims = {'length': 1.0, 'width': 0.5, 'height': 0.5}
                use_default = True
            else:
                obj_dims = KNOWN_OBJECT_SIZES[threat_type_normalized]
                use_default = False
        else:
            obj_dims = KNOWN_OBJECT_SIZES[threat_type]
            use_default = False
        
        # Extract bounding box dimensions
        x1, y1, x2, y2 = bbox
        bbox_width_px = x2 - x1
        bbox_height_px = y2 - y1
        
        # Update image width and calculate focal length if needed
        img_height, img_width = image_shape[:2]
        if self.image_width_px is None or self.focal_length_px is None:
            self.image_width_px = img_width
            self.focal_length_px = self._estimate_focal_length(img_width)
        
        # Determine which dimension to use based on object type
        # For divers: use height (vertical)
        # For submarines/vehicles/mines: use width (horizontal)
        if threat_type == 'diver':
            real_size_m = obj_dims['height']
            pixel_size = bbox_height_px
            dimension_used = 'height'
        else:
            # Use width for horizontal objects
            real_size_m = obj_dims.get('width', obj_dims.get('length', obj_dims.get('diameter', 1.0)))
            pixel_size = bbox_width_px
            dimension_used = 'width'
        
        # Prevent division by zero
        if pixel_size <= 0:
            return {
                'distance_m': None,
                'distance_display': 'Error',
                'confidence': 'unknown',
                'error_margin': 'N/A',
                'method': 'invalid_bbox'
            }
        
        # Calculate distance using pinhole camera model
        # Distance = (Real_Size × Focal_Length) / Pixel_Size
        distance_px_model = (real_size_m * self.focal_length_px) / pixel_size
        
        # Apply underwater refraction correction (objects appear closer than they are)
        distance_m = distance_px_model * (self.refraction_factor / 1.0)
        
        # Calculate confidence based on detection quality
        confidence, error_margin = self._calculate_confidence(
            bbox_width_px, bbox_height_px, img_width, img_height, distance_m
        )
        
        # Reduce confidence if using default object size
        if use_default:
            if confidence == 'high':
                confidence = 'medium'
            elif confidence == 'medium':
                confidence = 'low'
            error_margin = '±50%'
        
        # Format display string
        distance_display = self._format_distance(distance_m, confidence)
        
        return {
            'distance_m': round(distance_m, 1),
            'distance_display': distance_display,
            'confidence': confidence,
            'error_margin': error_margin,
            'method': 'pinhole_camera_model',
            'focal_length_px': round(self.focal_length_px, 1),
            'object_size_m': real_size_m,
            'pixel_size': round(pixel_size, 1),
            'dimension_used': dimension_used
        }
    
    def _calculate_confidence(self, bbox_width, bbox_height, img_width, img_height, distance_m):
        """
        Calculate confidence level based on detection quality.
        
        Args:
            bbox_width (float): Bounding box width in pixels
            bbox_height (float): Bounding box height in pixels
            img_width (int): Image width
            img_height (int): Image height
            distance_m (float): Calculated distance in meters
            
        Returns:
            tuple: (confidence_level, error_margin_string)
        """
        # Calculate percentage of image occupied by detection
        bbox_area = bbox_width * bbox_height
        image_area = img_width * img_height
        area_percentage = (bbox_area / image_area) * 100
        
        # Calculate aspect ratio (should be reasonable for real objects)
        aspect_ratio = bbox_width / bbox_height if bbox_height > 0 else 0
        aspect_reasonable = 0.2 < aspect_ratio < 5.0  # Reasonable range
        
        # Determine confidence level
        # High confidence: Large object, reasonable aspect ratio, close distance
        if area_percentage > 5 and aspect_reasonable and distance_m < 50:
            return 'high', '±15%'
        
        # Medium confidence: Medium-sized object or further away
        elif area_percentage > 1 and aspect_reasonable and distance_m < 100:
            return 'medium', '±25%'
        
        # Low confidence: Small object, far away, or unusual aspect ratio
        elif area_percentage > 0.3:
            return 'low', '±40%'
        
        # Very low confidence: Tiny object or very far
        else:
            return 'very_low', '±50%'
    
    def _format_distance(self, distance_m, confidence):
        """
        Format distance for display.
        
        Args:
            distance_m (float): Distance in meters
            confidence (str): Confidence level
            
        Returns:
            str: Formatted distance string
        """
        # Add tilde (~) to indicate estimation
        prefix = '~'
        
        # Format based on distance magnitude
        if distance_m < 1:
            # Show in centimeters for very close objects
            return f"{prefix}{distance_m * 100:.0f}cm"
        elif distance_m < 1000:
            # Show in meters for normal range
            return f"{prefix}{distance_m:.1f}m"
        else:
            # Show in kilometers for far objects
            return f"{prefix}{distance_m / 1000:.2f}km"
    
    def get_distance_info_text(self, distance_info):
        """
        Generate detailed distance information text for UI display.
        
        Args:
            distance_info (dict): Distance information dictionary
            
        Returns:
            str: Formatted text for display
        """
        if distance_info.get('distance_m') is None:
            return "Distance: Unknown"
        
        dist = distance_info['distance_display']
        error = distance_info['error_margin']
        conf = distance_info['confidence'].upper()
        
        return f"Distance: {dist} ({error}) [{conf}]"
    
    def apply_refraction_correction(self, distance_air, water_depth=None):
        """
        Apply more sophisticated refraction correction if water depth is known.
        
        Args:
            distance_air (float): Distance calculated in air
            water_depth (float): Depth of water (optional)
            
        Returns:
            float: Corrected distance
        """
        # Simple correction using refractive index
        # More sophisticated models could account for:
        # - Water salinity
        # - Temperature
        # - Pressure (depth)
        # - Viewing angle
        
        if water_depth and water_depth > 10:
            # For deep water, use slightly different correction
            correction = 1.34  # Slightly higher for deep water
        else:
            correction = self.refraction_factor
        
        return distance_air * correction


# Utility function for batch distance estimation
def estimate_distances_batch(threats, image_shape, focal_length_px=None):
    """
    Estimate distances for multiple threats in batch.
    
    Args:
        threats (list): List of threat dictionaries with 'threat_type' and 'bbox'
        image_shape (tuple): Image dimensions
        focal_length_px (float): Optional focal length
        
    Returns:
        list: Threats with added distance information
    """
    estimator = DistanceEstimator(focal_length_px=focal_length_px)
    
    for threat in threats:
        if 'threat_type' in threat and 'bbox' in threat:
            distance_info = estimator.estimate_distance(
                threat_type=threat['threat_type'],
                bbox=threat['bbox'],
                image_shape=image_shape
            )
            threat['distance'] = distance_info
    
    return threats


if __name__ == "__main__":
    # Test the distance estimator
    print("🧪 Testing Distance Estimator\n")
    
    # Create estimator
    estimator = DistanceEstimator()
    
    # Test case 1: Submarine detection
    print("Test 1: Submarine Detection")
    bbox_submarine = [100, 200, 500, 350]  # [x1, y1, x2, y2]
    image_shape = (720, 1280, 3)  # HD image
    
    result = estimator.estimate_distance('submarine', bbox_submarine, image_shape)
    print(f"  Distance: {result['distance_display']}")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Error margin: {result['error_margin']}")
    print(f"  Method: {result['method']}\n")
    
    # Test case 2: Diver detection
    print("Test 2: Diver Detection")
    bbox_diver = [300, 150, 380, 350]  # Tall vertical box
    
    result = estimator.estimate_distance('diver', bbox_diver, image_shape)
    print(f"  Distance: {result['distance_display']}")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Error margin: {result['error_margin']}\n")
    
    # Test case 3: Mine detection
    print("Test 3: Mine Detection")
    bbox_mine = [600, 400, 700, 500]  # Small square box
    
    result = estimator.estimate_distance('mine', bbox_mine, image_shape)
    print(f"  Distance: {result['distance_display']}")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Error margin: {result['error_margin']}\n")
    
    print("✅ Distance Estimator tests complete!")
