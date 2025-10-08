# 📏 Distance Estimation for Detected Threats

## 🎯 Overview
Calculate the distance between the camera and detected underwater threats (submarines, divers, mines).

---

## 🔬 Methods Available

### **Method 1: Known Object Size (RECOMMENDED)** ⭐
**Best for:** Real-world applications with known object dimensions

**Requirements:**
- Known real-world size of the object (e.g., submarine = 50 meters long)
- Camera focal length (can estimate from image metadata or calibration)
- Object's bounding box in pixels

**Formula:**
```
Distance (meters) = (Real Object Width × Focal Length) / Pixel Width
```

**Example:**
- Submarine real width: 10 meters
- Focal length: 1000 pixels
- Detected width in image: 200 pixels
- **Distance = (10 × 1000) / 200 = 50 meters**

**Accuracy:** ±10-20% (good for practical use)

---

### **Method 2: Depth from Stereo (ADVANCED)**
**Best for:** Systems with 2 cameras (stereo vision)

**Requirements:**
- Two synchronized cameras (left + right)
- Known distance between cameras (baseline)
- Calibrated camera parameters

**How it works:**
- Compare same object in left & right images
- Calculate disparity (pixel shift)
- Use triangulation to compute depth

**Accuracy:** ±5-15% (very good)
**Complexity:** HIGH (need hardware setup)

---

### **Method 3: Monocular Depth Estimation (AI-BASED)**
**Best for:** Single camera without known object size

**Requirements:**
- Pre-trained depth estimation model (MiDaS, DPT, etc.)
- Single image input

**How it works:**
- Neural network predicts relative depth for each pixel
- Extract depth value at threat location
- Converts to metric distance (needs scale calibration)

**Accuracy:** ±20-40% (relative depth, needs calibration)
**Complexity:** MEDIUM

---

### **Method 4: Underwater Attenuation (PHYSICS-BASED)**
**Best for:** Clear water conditions

**Requirements:**
- Water clarity/visibility data
- Color channel analysis
- Calibration with known distances

**How it works:**
- Analyze red light attenuation (absorbed faster underwater)
- More blue/green = further away
- Use Beer-Lambert law

**Formula:**
```
I(d) = I₀ × e^(-c×d)
where:
  I(d) = intensity at distance d
  I₀ = initial intensity
  c = attenuation coefficient
  d = distance
```

**Accuracy:** ±30-50% (depends on water clarity)
**Complexity:** MEDIUM-HIGH

---

## 🚀 Recommended Implementation: Method 1 (Known Object Size)

### **Step 1: Define Object Dimensions**

```python
# threat_detection/distance_estimator.py

KNOWN_OBJECT_SIZES = {
    'submarine': {
        'length': 50.0,    # meters (average submarine)
        'width': 10.0,     # meters
        'height': 8.0      # meters
    },
    'diver': {
        'height': 1.8,     # meters (average human)
        'width': 0.6       # meters
    },
    'mine': {
        'diameter': 1.5,   # meters (naval mine)
        'radius': 0.75
    },
    'underwater_vehicle': {
        'length': 3.0,     # meters (ROV/AUV)
        'width': 1.5
    }
}
```

### **Step 2: Create Distance Estimator Class**

```python
import math
import cv2
import numpy as np

class DistanceEstimator:
    def __init__(self, focal_length_px=None, sensor_width_mm=None, image_width_px=None):
        """
        Initialize distance estimator.
        
        Args:
            focal_length_px: Camera focal length in pixels (if known)
            sensor_width_mm: Camera sensor width in mm (default: 6.17mm for smartphone)
            image_width_px: Image width in pixels
        """
        self.focal_length_px = focal_length_px
        self.sensor_width_mm = sensor_width_mm or 6.17  # iPhone/smartphone typical
        self.image_width_px = image_width_px
        
        # If focal length not provided, estimate it
        if focal_length_px is None and image_width_px:
            # Assume 35mm equivalent focal length of ~26mm (typical underwater camera)
            focal_length_mm = 26.0
            self.focal_length_px = (focal_length_mm * image_width_px) / self.sensor_width_mm
    
    def estimate_distance(self, threat_type, bbox, image_shape):
        """
        Estimate distance to detected threat.
        
        Args:
            threat_type: Type of threat ('submarine', 'diver', 'mine', etc.)
            bbox: Bounding box [x1, y1, x2, y2]
            image_shape: Image dimensions (height, width)
        
        Returns:
            dict: {
                'distance_m': distance in meters,
                'confidence': confidence level ('high', 'medium', 'low'),
                'method': estimation method used
            }
        """
        if threat_type not in KNOWN_OBJECT_SIZES:
            return {
                'distance_m': None,
                'confidence': 'unknown',
                'method': 'object_size_unknown'
            }
        
        # Extract bounding box dimensions
        x1, y1, x2, y2 = bbox
        bbox_width_px = x2 - x1
        bbox_height_px = y2 - y1
        
        # Get known object dimensions
        obj_dims = KNOWN_OBJECT_SIZES[threat_type]
        
        # Update image width if not set
        if self.image_width_px is None:
            self.image_width_px = image_shape[1]
            # Recalculate focal length
            focal_length_mm = 26.0
            self.focal_length_px = (focal_length_mm * self.image_width_px) / self.sensor_width_mm
        
        # Determine which dimension to use (prefer width for most objects)
        if threat_type == 'diver':
            real_size_m = obj_dims['height']
            pixel_size = bbox_height_px
        else:
            real_size_m = obj_dims.get('width', obj_dims.get('length', obj_dims.get('diameter', 1.0)))
            pixel_size = bbox_width_px
        
        # Calculate distance using pinhole camera model
        # Distance = (Real_Size × Focal_Length) / Pixel_Size
        distance_m = (real_size_m * self.focal_length_px) / pixel_size
        
        # Determine confidence based on bounding box quality
        confidence = self._calculate_confidence(bbox_width_px, bbox_height_px, image_shape)
        
        return {
            'distance_m': round(distance_m, 1),
            'confidence': confidence,
            'method': 'pinhole_camera_model',
            'focal_length_px': round(self.focal_length_px, 1),
            'object_size_m': real_size_m,
            'pixel_size': round(pixel_size, 1)
        }
    
    def _calculate_confidence(self, bbox_width, bbox_height, image_shape):
        """Calculate confidence based on detection quality."""
        img_height, img_width = image_shape[:2]
        
        # Calculate percentage of image occupied
        bbox_area = bbox_width * bbox_height
        image_area = img_width * img_height
        area_percentage = (bbox_area / image_area) * 100
        
        # Confidence levels
        if area_percentage > 5:  # Object occupies >5% of image
            return 'high'
        elif area_percentage > 1:  # 1-5%
            return 'medium'
        else:  # <1%
            return 'low'
    
    def format_distance_display(self, distance_info):
        """
        Format distance information for display.
        
        Returns:
            str: Formatted distance string (e.g., "~25.3m ±20%")
        """
        if distance_info['distance_m'] is None:
            return "Unknown"
        
        dist = distance_info['distance_m']
        conf = distance_info['confidence']
        
        # Error margins based on confidence
        error_margins = {
            'high': '±15%',
            'medium': '±25%',
            'low': '±40%'
        }
        
        error = error_margins.get(conf, '±50%')
        
        if dist < 1:
            return f"~{dist*100:.0f}cm {error}"
        elif dist < 1000:
            return f"~{dist:.1f}m {error}"
        else:
            return f"~{dist/1000:.2f}km {error}"
```

### **Step 3: Integrate into Threat Detector**

```python
# In threat_detection/detector.py

from .distance_estimator import DistanceEstimator, KNOWN_OBJECT_SIZES

class ThreatDetector:
    def __init__(self, model_size='n', confidence_threshold=0.25, 
                 estimate_distance=True, focal_length_px=None):
        # ... existing code ...
        
        # Distance estimation
        self.estimate_distance = estimate_distance
        self.distance_estimator = DistanceEstimator(focal_length_px=focal_length_px) if estimate_distance else None
    
    def detect_threats(self, image_path):
        """Detect threats with distance estimation."""
        # ... existing detection code ...
        
        threats = []
        for detection in filtered_detections:
            threat_info = {
                'class': detection['class'],
                'threat_type': detection['threat_type'],
                'confidence': detection['confidence'],
                'bbox': detection['bbox'],
                'threat_level': detection['threat_level']
            }
            
            # Add distance estimation
            if self.estimate_distance:
                distance_info = self.distance_estimator.estimate_distance(
                    threat_type=detection['threat_type'],
                    bbox=detection['bbox'],
                    image_shape=image.shape
                )
                threat_info['distance'] = distance_info
            
            threats.append(threat_info)
        
        return threats, image
```

### **Step 4: Update Visualizer to Show Distance**

```python
# In threat_detection/visualizer.py

def draw_threat_label(self, image, threat, position='top'):
    """Draw threat label with distance information."""
    # ... existing code ...
    
    # Add distance to label
    if 'distance' in threat and threat['distance']['distance_m']:
        dist_info = threat['distance']
        dist_str = self.format_distance(dist_info)
        label_text += f" | 📏 {dist_str}"
    
    # ... rest of drawing code ...

def format_distance(self, distance_info):
    """Format distance for display."""
    dist = distance_info['distance_m']
    conf = distance_info['confidence']
    
    if dist < 1:
        return f"{dist*100:.0f}cm"
    elif dist < 1000:
        return f"{dist:.1f}m"
    else:
        return f"{dist/1000:.2f}km"
```

---

## 🎨 UI Display Examples

### **Threat Label with Distance:**
```
🎯 SUBMARINE [HIGH] 85% | 📏 45.2m
🎯 DIVER [MEDIUM] 72% | 📏 12.8m
🎯 MINE [HIGH] 91% | 📏 8.3m
```

### **Threat Summary Panel:**
```
⚠️ 3 Threats Detected

🎯 SUBMARINE [HIGH]
   Confidence: 85%
   Distance: ~45.2m (±20%)
   Method: Pinhole model

🎯 DIVER [MEDIUM]
   Confidence: 72%
   Distance: ~12.8m (±25%)
   Method: Pinhole model

🎯 MINE [HIGH]
   Confidence: 91%
   Distance: ~8.3m (±15%)
   Method: Pinhole model
```

---

## 📊 Accuracy Factors

### **What Affects Accuracy:**

1. **Object Orientation** ⚠️
   - Side view = Good accuracy
   - Front/back view = Lower accuracy
   - Angled view = Medium accuracy

2. **Water Clarity** 🌊
   - Clear water = Better detection & accuracy
   - Turbid water = Worse accuracy
   - Deep water = Color distortion affects size perception

3. **Object Size Variation** 📏
   - Submarines: 20m - 100m+ (huge range!)
   - Divers: 1.6m - 2.0m (small range, better accuracy)
   - Mines: 0.5m - 2.0m (medium range)

4. **Camera Calibration** 📷
   - Calibrated camera = ±10-15% error
   - Uncalibrated (estimated) = ±20-30% error
   - Unknown focal length = ±30-50% error

---

## 🛠️ Calibration Tips

### **How to Get Better Accuracy:**

1. **Calibrate Camera:**
   ```python
   # Use OpenCV calibration
   import cv2
   
   # Capture calibration images (chessboard pattern)
   # Run calibration
   ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(...)
   
   # Extract focal length
   focal_length_px = mtx[0][0]  # fx value
   ```

2. **Test with Known Distances:**
   - Place object at known distance (e.g., 10m)
   - Detect and calculate
   - Adjust focal length estimation if needed

3. **Use Reference Objects:**
   - Include object of known size in scene
   - Calibrate scale based on reference
   - Improves accuracy for other objects

---

## 🚀 Quick Implementation

Want me to implement this? I can:

1. ✅ Create `distance_estimator.py` module
2. ✅ Integrate into existing threat detector
3. ✅ Update visualizer to show distances
4. ✅ Add distance info to UI threat panel
5. ✅ Add calibration tool (optional)

**Estimated implementation time:** 30-45 minutes

**Result:** Every detected threat will show:
- Threat type & confidence
- **Estimated distance** (e.g., "~45.2m")
- Confidence level (high/medium/low)
- Error margin (±15-40%)

---

## 📝 Example Output

```json
{
  "threats": [
    {
      "class": "boat",
      "threat_type": "submarine",
      "confidence": 0.85,
      "bbox": [120, 200, 450, 380],
      "threat_level": "high",
      "distance": {
        "distance_m": 45.2,
        "confidence": "medium",
        "method": "pinhole_camera_model",
        "error_margin": "±25%"
      }
    }
  ]
}
```

---

## ⚠️ Important Notes

1. **Underwater Refraction:** Water bends light, can cause ~30% distance error
   - Solution: Apply refraction correction factor (1.33× for water)

2. **Object Size Assumptions:** We assume standard sizes
   - Mini-sub vs nuclear sub = huge difference!
   - Consider adding size categories (small/medium/large)

3. **Not Real-Time:** Distance calculation adds ~5-10ms per threat
   - Still fast enough for real-time video

4. **Relative vs Absolute:** Without calibration, distances are estimates
   - Good for: threat prioritization, relative distances
   - Not good for: precise targeting, navigation

---

**Want me to implement this feature? Just say "yes" and I'll add distance estimation to your threat detection system! 🚀**
