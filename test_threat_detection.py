"""
Quick Test Script for Threat Detection System
Run this to verify the installation and basic functionality
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from threat_detection.detector import ThreatDetector
        print("✅ ThreatDetector imported successfully")
    except Exception as e:
        print(f"❌ Failed to import ThreatDetector: {e}")
        return False
    
    try:
        from threat_detection.visualizer import ThreatVisualizer
        print("✅ ThreatVisualizer imported successfully")
    except Exception as e:
        print(f"❌ Failed to import ThreatVisualizer: {e}")
        return False
    
    try:
        from ultralytics import YOLO
        print("✅ YOLOv8 (ultralytics) imported successfully")
    except Exception as e:
        print(f"❌ Failed to import ultralytics: {e}")
        return False
    
    return True

def test_model_loading():
    """Test YOLOv8 model loading"""
    print("\n🚀 Testing YOLOv8 model loading...")
    
    try:
        from threat_detection.detector import ThreatDetector
        detector = ThreatDetector(model_size='n', confidence_threshold=0.25)
        print("✅ YOLOv8 nano model loaded successfully")
        print(f"   Device: {detector.device}")
        return True
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return False

def test_threat_classes():
    """Test threat class mapping"""
    print("\n📋 Testing threat class mappings...")
    
    from threat_detection.detector import ThreatDetector
    
    threat_classes = ThreatDetector.THREAT_CLASSES
    high_risk = ThreatDetector.HIGH_RISK
    medium_risk = ThreatDetector.MEDIUM_RISK
    
    print(f"✅ Total threat mappings: {len(threat_classes)}")
    print(f"   High-risk threats: {len(high_risk)}")
    print(f"   Medium-risk threats: {len(medium_risk)}")
    print("\n   Sample mappings:")
    for i, (yolo_class, threat_type) in enumerate(list(threat_classes.items())[:5]):
        print(f"   - {yolo_class} → {threat_type}")
    
    return True

def test_visualizer():
    """Test visualizer initialization"""
    print("\n🎨 Testing visualizer...")
    
    try:
        from threat_detection.visualizer import ThreatVisualizer
        visualizer = ThreatVisualizer()
        print("✅ ThreatVisualizer initialized successfully")
        print(f"   Risk colors: {len(visualizer.COLORS)} levels")
        print(f"   Circle thickness: {visualizer.circle_thickness}px")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize visualizer: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🎯 THREAT DETECTION SYSTEM - VERIFICATION TEST")
    print("=" * 60)
    
    results = []
    
    # Test 1: Imports
    results.append(("Imports", test_imports()))
    
    # Test 2: Model Loading
    results.append(("Model Loading", test_model_loading()))
    
    # Test 3: Threat Classes
    results.append(("Threat Classes", test_threat_classes()))
    
    # Test 4: Visualizer
    results.append(("Visualizer", test_visualizer()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed ({(passed/total)*100:.0f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - System is ready!")
        print("\nYou can now:")
        print("1. Run: python webapp/app.py")
        print("2. Open: http://localhost:5000")
        print("3. Upload an underwater image")
        print("4. Toggle: 🎯 Enable AI Threat Detection")
        print("5. Watch threats get highlighted in red circles!")
    else:
        print("⚠️  Some tests failed - check errors above")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
