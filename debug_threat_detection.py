"""
Debug Script for Threat Detection
Tests detection on a submarine image
"""

import sys
import os
import cv2

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from threat_detection.detector import ThreatDetector
from threat_detection.visualizer import ThreatVisualizer

def debug_detection(image_path):
    """
    Debug threat detection on an image
    Shows ALL detections (including filtered ones)
    """
    print("=" * 60)
    print("🔍 DEBUG MODE - Threat Detection Analysis")
    print("=" * 60)
    
    # Initialize detector with LOWER threshold
    print("\n1. Initializing detector with LOW threshold (0.15)...")
    detector = ThreatDetector(model_size='n', confidence_threshold=0.15)
    
    # Detect ALL objects (no filtering)
    print("\n2. Running YOLOv8 detection...")
    all_detections = detector.detect_objects(image_path)
    
    print(f"\n📊 TOTAL OBJECTS DETECTED: {len(all_detections)}")
    print("-" * 60)
    
    if all_detections:
        for i, det in enumerate(all_detections, 1):
            print(f"\n{i}. Class: {det['class']}")
            print(f"   Confidence: {det['confidence']:.2%}")
            print(f"   BBox: {det['bbox']}")
            print(f"   Center: {det['center']}")
    else:
        print("❌ NO OBJECTS DETECTED AT ALL!")
        print("\nPossible reasons:")
        print("- Image quality too low")
        print("- Object too small")
        print("- Unusual angle/lighting")
    
    # Now filter for threats (with marine life exclusion OFF)
    print("\n" + "=" * 60)
    print("3. Filtering for threats (exclude_marine_life=False)...")
    threats = detector.filter_threats(all_detections, exclude_marine_life=False)
    
    print(f"\n⚠️  POTENTIAL THREATS: {len(threats)}")
    print("-" * 60)
    
    if threats:
        for i, threat in enumerate(threats, 1):
            print(f"\n{i}. Type: {threat['threat_type']}")
            print(f"   Original Class: {threat['original_class']}")
            print(f"   Confidence: {threat['confidence']:.2%}")
            print(f"   Risk Level: {threat['risk_level']}")
    else:
        print("❌ NO THREATS IDENTIFIED!")
        print("\nDetected objects don't match threat categories:")
        print("Expected: boat, ship, person, truck, car, etc.")
    
    # Test with marine life exclusion ON
    print("\n" + "=" * 60)
    print("4. Filtering with marine life exclusion ON...")
    threats_filtered = detector.filter_threats(all_detections, exclude_marine_life=True)
    
    print(f"\n⚠️  THREATS (AFTER MARINE FILTER): {len(threats_filtered)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Total objects detected: {len(all_detections)}")
    print(f"Potential threats (no filter): {len(threats)}")
    print(f"Final threats (with filter): {len(threats_filtered)}")
    
    if len(all_detections) > 0 and len(threats) == 0:
        print("\n⚠️  ISSUE FOUND:")
        print("Objects detected but none match threat categories!")
        print("\nDetected classes:", [d['class'] for d in all_detections])
        print("\nThreat categories:", list(ThreatDetector.THREAT_CLASSES.keys()))
    
    return all_detections, threats_filtered

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Debug threat detection')
    parser.add_argument('image', help='Path to image file')
    args = parser.parse_args()
    
    if not os.path.exists(args.image):
        print(f"❌ Image not found: {args.image}")
        sys.exit(1)
    
    debug_detection(args.image)
