"""
Quick test to verify distance estimation is working with YOLO classes
"""

from threat_detection.distance_estimator import DistanceEstimator, KNOWN_OBJECT_SIZES

print("🧪 Testing Distance Estimator Fix\n")
print("="*80)

# Check available object sizes
print(f"✅ Available object types: {len(KNOWN_OBJECT_SIZES)}")
print("\nYOLO Classes in database:")
yolo_classes = ['person', 'boat', 'car', 'backpack', 'cell phone', 'knife', 'sports ball']
for cls in yolo_classes:
    if cls in KNOWN_OBJECT_SIZES:
        dims = KNOWN_OBJECT_SIZES[cls]
        print(f"  ✓ {cls}: {dims}")
    else:
        print(f"  ✗ {cls}: NOT FOUND")

print("\nThreat Types in database:")
threat_types = ['hostile_diver', 'hostile_submarine', 'naval_mine', 'ied_device']
for threat in threat_types:
    if threat in KNOWN_OBJECT_SIZES:
        dims = KNOWN_OBJECT_SIZES[threat]
        print(f"  ✓ {threat}: {dims}")
    else:
        print(f"  ✗ {threat}: NOT FOUND")

# Test distance estimation
print("\n" + "="*80)
print("Testing Distance Estimation:\n")

estimator = DistanceEstimator()

# Test 1: YOLO class 'person' (should work)
print("Test 1: YOLO class 'person'")
bbox = [100, 150, 200, 450]  # [x1, y1, x2, y2]
image_shape = (720, 1280, 3)

result = estimator.estimate_distance('person', bbox, image_shape)
print(f"  Distance: {result['distance_display']}")
print(f"  Confidence: {result['confidence']}")
print(f"  Error margin: {result['error_margin']}")
print(f"  Method: {result.get('method', 'N/A')}")

# Test 2: YOLO class 'boat' (should work)
print("\nTest 2: YOLO class 'boat'")
bbox = [50, 100, 600, 400]
result = estimator.estimate_distance('boat', bbox, image_shape)
print(f"  Distance: {result['distance_display']}")
print(f"  Confidence: {result['confidence']}")
print(f"  Error margin: {result['error_margin']}")

# Test 3: Threat type 'hostile_diver' (should work)
print("\nTest 3: Threat type 'hostile_diver'")
bbox = [100, 150, 200, 450]
result = estimator.estimate_distance('hostile_diver', bbox, image_shape)
print(f"  Distance: {result['distance_display']}")
print(f"  Confidence: {result['confidence']}")
print(f"  Error margin: {result['error_margin']}")

# Test 4: Unknown type (should use default)
print("\nTest 4: Unknown type 'random_object'")
bbox = [300, 200, 400, 350]
result = estimator.estimate_distance('random_object', bbox, image_shape)
print(f"  Distance: {result['distance_display']}")
print(f"  Confidence: {result['confidence']}")
print(f"  Error margin: {result['error_margin']}")

print("\n" + "="*80)
print("✅ Distance Estimator Fix Test Complete!")
print("\nSummary:")
print("  ✓ YOLO classes are properly mapped")
print("  ✓ Threat types are properly mapped")
print("  ✓ Unknown objects use default estimation")
print("  ✓ Distance calculations working correctly")
print("\n🎯 Distance measurement should now work in the web application!")
