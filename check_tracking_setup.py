"""
Debug script - Check if bounding boxes will work
"""

import os
import sys

def check_dependencies():
    """Check all required packages"""
    print("🔍 Checking dependencies...")
    
    issues = []
    
    # Check OpenCV
    try:
        import cv2
        print(f"✅ OpenCV: {cv2.__version__}")
        
        # Check for legacy trackers
        try:
            tracker = cv2.legacy.TrackerKCF_create()
            print("✅ OpenCV legacy trackers available")
        except AttributeError:
            issues.append("❌ OpenCV legacy trackers NOT available (need opencv-contrib-python)")
    except ImportError:
        issues.append("❌ OpenCV not installed")
    
    # Check YOLO
    try:
        from ultralytics import YOLO
        model = YOLO('yolov8n.pt')
        print(f"✅ YOLOv8 available")
    except ImportError:
        issues.append("❌ Ultralytics not installed")
    except Exception as e:
        issues.append(f"❌ YOLO error: {e}")
    
    # Check PyTorch
    try:
        import torch
        print(f"✅ PyTorch: {torch.__version__}")
        print(f"   CUDA available: {torch.cuda.is_available()}")
    except ImportError:
        issues.append("❌ PyTorch not installed")
    
    # Check NumPy
    try:
        import numpy as np
        print(f"✅ NumPy: {np.__version__}")
    except ImportError:
        issues.append("❌ NumPy not installed")
    
    return issues


def check_files():
    """Check if required files exist"""
    print("\n📁 Checking files...")
    
    issues = []
    
    files_to_check = [
        'webapp/video_processor_v2.py',
        'webapp/app.py',
        'yolov8n.pt',
        'uw_video_processing/models.py',
        'uw_video_processing/ckpts/UIEB_UIEB.pth'
    ]
    
    for file in files_to_check:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            issues.append(f"❌ Missing: {file}")
    
    return issues


def check_webapp_integration():
    """Check if webapp will use the new processor"""
    print("\n🔧 Checking webapp integration...")
    
    issues = []
    
    try:
        with open('webapp/app.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
            if 'VideoProcessorV2' in content:
                print("✅ app.py imports VideoProcessorV2")
            else:
                issues.append("❌ app.py NOT using VideoProcessorV2")
            
            if 'enable_threat_detection' in content:
                print("✅ app.py has enable_threat_detection parameter")
            else:
                issues.append("❌ app.py missing enable_threat_detection")
    except Exception as e:
        issues.append(f"❌ Error reading app.py: {e}")
    
    return issues


def test_simple_detection():
    """Test YOLO detection on a simple image"""
    print("\n🧪 Testing YOLO detection...")
    
    try:
        from ultralytics import YOLO
        import cv2
        import numpy as np
        
        # Load YOLO
        model = YOLO('yolov8n.pt')
        
        # Create a test image (blank)
        test_img = np.zeros((640, 640, 3), dtype=np.uint8)
        
        # Run detection
        results = model(test_img, conf=0.25, verbose=False)
        
        print(f"✅ YOLO detection works (found {len(results[0].boxes)} objects in blank image)")
        print("   Ready to detect threats in video!")
        
        return []
    except Exception as e:
        return [f"❌ YOLO test failed: {e}"]


def test_tracker_creation():
    """Test OpenCV tracker creation"""
    print("\n🎯 Testing OpenCV tracker...")
    
    try:
        import cv2
        
        # Try to create tracker
        tracker = cv2.legacy.TrackerKCF_create()
        print("✅ KCF tracker created successfully")
        
        # Create test image
        import numpy as np
        test_img = np.zeros((640, 640, 3), dtype=np.uint8)
        
        # Initialize tracker with dummy bbox
        bbox = (100, 100, 200, 200)
        tracker.init(test_img, bbox)
        print("✅ Tracker initialization works")
        
        # Try to update
        success, new_bbox = tracker.update(test_img)
        print(f"✅ Tracker update works (success: {success})")
        
        return []
    except Exception as e:
        return [f"❌ Tracker test failed: {e}"]


def main():
    """Run all checks"""
    print("=" * 70)
    print("🚀 DEEPWATER VIDEO TRACKING - SYSTEM CHECK")
    print("=" * 70)
    print()
    
    all_issues = []
    
    # Run checks
    all_issues.extend(check_dependencies())
    all_issues.extend(check_files())
    all_issues.extend(check_webapp_integration())
    all_issues.extend(test_simple_detection())
    all_issues.extend(test_tracker_creation())
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    if not all_issues:
        print("✅ ALL CHECKS PASSED!")
        print()
        print("🎉 Your system is ready for video tracking with bounding boxes!")
        print()
        print("Next steps:")
        print("1. Start the server: cd webapp && python app.py")
        print("2. Upload a video with 'Enable Threat Detection' ✅")
        print("3. Watch bounding boxes follow threats in the output!")
        print()
        return 0
    else:
        print("⚠️  ISSUES FOUND:")
        print()
        for issue in all_issues:
            print(f"  {issue}")
        print()
        print("Please fix the issues above before processing videos.")
        print()
        
        # Suggestions
        if any("opencv-contrib" in issue.lower() for issue in all_issues):
            print("💡 To fix OpenCV tracker issue:")
            print("   pip uninstall opencv-python")
            print("   pip install opencv-contrib-python")
            print()
        
        if any("ultralytics" in issue.lower() for issue in all_issues):
            print("💡 To fix YOLO issue:")
            print("   pip install ultralytics")
            print()
        
        return 1


if __name__ == "__main__":
    exit(main())
