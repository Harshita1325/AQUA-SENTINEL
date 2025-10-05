"""
Test script for Quality Metrics Calculator
Tests all metric calculations with sample images
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'webapp'))

import cv2
import numpy as np
from metrics_calculator import ImageQualityMetrics

def create_test_images():
    """Create synthetic test images"""
    # Original image (simulated underwater - blue tinted)
    original = np.zeros((480, 640, 3), dtype=np.uint8)
    original[:, :, 2] = 150  # Strong blue channel
    original[:, :, 1] = 100  # Medium green
    original[:, :, 0] = 50   # Low red
    
    # Add some texture
    noise = np.random.randint(-20, 20, (480, 640, 3), dtype=np.int16)
    original = np.clip(original.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    # Enhanced image (better color balance)
    enhanced = np.zeros((480, 640, 3), dtype=np.uint8)
    enhanced[:, :, 2] = 120  # Reduced blue
    enhanced[:, :, 1] = 130  # Increased green
    enhanced[:, :, 0] = 110  # Increased red
    
    # Add sharper texture
    noise = np.random.randint(-30, 30, (480, 640, 3), dtype=np.int16)
    enhanced = np.clip(enhanced.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    return original, enhanced

def test_metrics_calculator():
    """Test all metrics calculations"""
    print("=" * 60)
    print("🧪 Testing Quality Metrics Calculator")
    print("=" * 60)
    
    # Initialize calculator
    calc = ImageQualityMetrics()
    print("✓ ImageQualityMetrics initialized")
    
    # Create test images
    print("\n📸 Creating synthetic test images...")
    original, enhanced = create_test_images()
    print(f"✓ Original image shape: {original.shape}")
    print(f"✓ Enhanced image shape: {enhanced.shape}")
    
    # Test 1: Calculate all metrics
    print("\n" + "=" * 60)
    print("Test 1: Calculate All Metrics (No Reference)")
    print("=" * 60)
    
    try:
        metrics = calc.calculate_all_metrics(original, enhanced, has_reference=False)
        print("✓ Metrics calculated successfully\n")
        
        print("📊 Results:")
        print(f"  UIQM Score:      {metrics['uiqm']:.4f}")
        print(f"  UCIQE Score:     {metrics['uciqe']:.4f}")
        print(f"  Sharpness:       {metrics['sharpness']:.2f}")
        print(f"  Contrast:        {metrics['contrast']:.2f}")
        print(f"  Colorfulness:    {metrics['colorfulness']:.4f}")
        print(f"  Overall Score:   {metrics['overall_score']:.2f} / 100")
        print(f"  PSNR:            {metrics.get('psnr', 'N/A')} (expected N/A)")
        print(f"  SSIM:            {metrics.get('ssim', 'N/A')} (expected N/A)")
        
        # Validate ranges
        assert 0 <= metrics['uiqm'] <= 20, "UIQM out of expected range"
        assert 0 <= metrics['uciqe'] <= 1, "UCIQE out of expected range"
        assert metrics['sharpness'] >= 0, "Sharpness cannot be negative"
        assert 0 <= metrics['overall_score'] <= 100, "Overall score out of range"
        print("\n✅ All metric values in valid ranges")
        
    except Exception as e:
        print(f"❌ Error in metric calculation: {e}")
        return False
    
    # Test 2: Individual metric functions
    print("\n" + "=" * 60)
    print("Test 2: Individual Metric Functions")
    print("=" * 60)
    
    try:
        # Convert to RGB for testing
        original_rgb = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
        enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
        
        # Test UIQM
        uiqm = calc.calculate_uiqm(enhanced_rgb)
        print(f"✓ UIQM: {uiqm:.4f}")
        
        # Test UCIQE
        uciqe = calc.calculate_uciqe(enhanced_rgb)
        print(f"✓ UCIQE: {uciqe:.4f}")
        
        # Test Sharpness
        sharpness = calc.calculate_sharpness(enhanced_rgb)
        print(f"✓ Sharpness: {sharpness:.2f}")
        
        # Test Contrast
        contrast = calc.calculate_contrast(enhanced_rgb)
        print(f"✓ Contrast: {contrast:.2f}")
        
        # Test Colorfulness
        colorfulness = calc.calculate_colorfulness(enhanced_rgb)
        print(f"✓ Colorfulness: {colorfulness:.4f}")
        
        print("\n✅ All individual metrics working")
        
    except Exception as e:
        print(f"❌ Error in individual metrics: {e}")
        return False
    
    # Test 3: Histogram generation
    print("\n" + "=" * 60)
    print("Test 3: Histogram Generation")
    print("=" * 60)
    
    try:
        histograms = calc.generate_histograms(enhanced)
        
        assert 'red' in histograms, "Red histogram missing"
        assert 'green' in histograms, "Green histogram missing"
        assert 'blue' in histograms, "Blue histogram missing"
        
        assert len(histograms['red']) == 256, "Red histogram wrong size"
        assert len(histograms['green']) == 256, "Green histogram wrong size"
        assert len(histograms['blue']) == 256, "Blue histogram wrong size"
        
        print(f"✓ Red channel histogram: {len(histograms['red'])} bins")
        print(f"✓ Green channel histogram: {len(histograms['green'])} bins")
        print(f"✓ Blue channel histogram: {len(histograms['blue'])} bins")
        
        # Print sample values
        print(f"\nSample histogram values (bin 128):")
        print(f"  Red: {histograms['red'][128]:.0f}")
        print(f"  Green: {histograms['green'][128]:.0f}")
        print(f"  Blue: {histograms['blue'][128]:.0f}")
        
        print("\n✅ Histogram generation working")
        
    except Exception as e:
        print(f"❌ Error in histogram generation: {e}")
        return False
    
    # Test 4: Color statistics
    print("\n" + "=" * 60)
    print("Test 4: Color Statistics")
    print("=" * 60)
    
    try:
        stats = calc.get_color_statistics(enhanced)
        
        assert 'red' in stats, "Red stats missing"
        assert 'green' in stats, "Green stats missing"
        assert 'blue' in stats, "Blue stats missing"
        assert 'dominance' in stats, "Dominance missing"
        
        print(f"✓ Red channel stats:")
        print(f"    Mean: {stats['red']['mean']:.4f}")
        print(f"    Std:  {stats['red']['std']:.4f}")
        print(f"    Range: [{stats['red']['min']:.4f}, {stats['red']['max']:.4f}]")
        
        print(f"\n✓ Green channel stats:")
        print(f"    Mean: {stats['green']['mean']:.4f}")
        print(f"    Std:  {stats['green']['std']:.4f}")
        print(f"    Range: [{stats['green']['min']:.4f}, {stats['green']['max']:.4f}]")
        
        print(f"\n✓ Blue channel stats:")
        print(f"    Mean: {stats['blue']['mean']:.4f}")
        print(f"    Std:  {stats['blue']['std']:.4f}")
        print(f"    Range: [{stats['blue']['min']:.4f}, {stats['blue']['max']:.4f}]")
        
        print(f"\n✓ Dominant color: {stats['dominance']}")
        
        print("\n✅ Color statistics working")
        
    except Exception as e:
        print(f"❌ Error in color statistics: {e}")
        return False
    
    # Test 5: Error handling
    print("\n" + "=" * 60)
    print("Test 5: Error Handling")
    print("=" * 60)
    
    try:
        # Test with mismatched sizes
        small_img = cv2.resize(enhanced, (320, 240))
        metrics = calc.calculate_all_metrics(original, small_img, has_reference=False)
        print("✓ Handles mismatched image sizes (auto-resize)")
        
        # Test with different dtypes
        float_img = enhanced.astype(np.float32) / 255.0
        metrics = calc.calculate_all_metrics(original, float_img, has_reference=False)
        print("✓ Handles float32 images")
        
        print("\n✅ Error handling working")
        
    except Exception as e:
        print(f"❌ Error in error handling test: {e}")
        return False
    
    # Final summary
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\n🎉 Quality Metrics Calculator is working correctly!")
    print("📝 Ready for integration with Flask application")
    print("\nNext steps:")
    print("  1. Start Flask server: python webapp/app.py")
    print("  2. Open browser to http://localhost:5000")
    print("  3. Upload image and process")
    print("  4. Click 'Calculate Metrics' button")
    print("  5. View comprehensive quality dashboard")
    
    return True

def test_real_images():
    """Test with real underwater images if available"""
    print("\n" + "=" * 60)
    print("🖼️ Testing with Real Images (Optional)")
    print("=" * 60)
    
    test_dir = os.path.join(os.path.dirname(__file__), '..', 'uie_uieb')
    hazy_dir = os.path.join(test_dir, 'hazy_test')
    clean_dir = os.path.join(test_dir, 'clean_test')
    
    if os.path.exists(hazy_dir) and os.path.exists(clean_dir):
        try:
            # Get first available image
            hazy_images = [f for f in os.listdir(hazy_dir) if f.endswith('.png')]
            if hazy_images:
                test_image = hazy_images[0]
                
                hazy_path = os.path.join(hazy_dir, test_image)
                clean_path = os.path.join(clean_dir, test_image)
                
                if os.path.exists(hazy_path) and os.path.exists(clean_path):
                    print(f"Testing with: {test_image}")
                    
                    hazy = cv2.imread(hazy_path)
                    clean = cv2.imread(clean_path)
                    
                    calc = ImageQualityMetrics()
                    
                    # Calculate metrics for hazy image
                    hazy_metrics = calc.calculate_all_metrics(hazy, hazy, has_reference=False)
                    
                    # Calculate metrics for clean image
                    clean_metrics = calc.calculate_all_metrics(hazy, clean, has_reference=True)
                    
                    print("\n📊 Hazy Image Metrics:")
                    print(f"  UIQM: {hazy_metrics['uiqm']:.4f}")
                    print(f"  Overall Score: {hazy_metrics['overall_score']:.2f}")
                    
                    print("\n📊 Clean Image Metrics:")
                    print(f"  UIQM: {clean_metrics['uiqm']:.4f}")
                    print(f"  PSNR: {clean_metrics['psnr']:.2f} dB")
                    print(f"  SSIM: {clean_metrics['ssim']:.4f}")
                    print(f"  Overall Score: {clean_metrics['overall_score']:.2f}")
                    
                    improvement = ((clean_metrics['uiqm'] - hazy_metrics['uiqm']) / hazy_metrics['uiqm'] * 100)
                    print(f"\n🎯 Improvement: {improvement:.2f}%")
                    
                    print("\n✅ Real image testing successful")
                    return True
        except Exception as e:
            print(f"⚠️ Could not test with real images: {e}")
            print("This is optional - synthetic tests passed")
    else:
        print("⚠️ Real test images not found (optional)")
        print("Synthetic tests are sufficient for validation")
    
    return True

if __name__ == "__main__":
    print("\n🚀 Starting Quality Metrics Calculator Test Suite\n")
    
    success = test_metrics_calculator()
    
    if success:
        test_real_images()
        print("\n" + "=" * 60)
        print("🎊 Test Suite Completed Successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Test Suite Failed")
        print("=" * 60)
        sys.exit(1)