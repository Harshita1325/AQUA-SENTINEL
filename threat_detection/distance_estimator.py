"""
Distance Estimation Module for Threat Detection
Estimates distance to detected underwater threats using pinhole camera model
"""

import math
import numpy as np

# Known object sizes in meters (real-world dimensions)
KNOWN_OBJECT_SIZES = {
    'submarine': {
        'length': 50.0,    # meters (average submarine length)
        'width': 10.0,     # meters (average submarine width)
        'height': 8.0      # meters (average submarine height)
    },
    'diver': {
        'height': 1.75,    # meters (average human height with gear)
        'width': 0.6,      # meters (average human width)
        'depth': 0.3       # meters (human depth front-to-back)
    },
    'mine': {
        'diameter': 1.5,   # meters (typical naval mine diameter)
        'radius': 0.75     # meters
    },
    'underwater_vehicle': {
        'length': 3.0,     # meters (ROV/AUV average)
        'width': 1.5,      # meters
        'height': 1.2      # meters
    }
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
            return {
                'distance_m': None,
                'distance_display': 'Unknown',
                'confidence': 'unknown',
                'error_margin': 'N/A',
                'method': 'object_size_unknown'
            }
        
        # Extract bounding box dimensions
        x1, y1, x2, y2 = bbox
        bbox_width_px = x2 - x1
        bbox_height_px = y2 - y1
        
        # Get known object dimensions
        obj_dims = KNOWN_OBJECT_SIZES[threat_type]
        
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
