"""
Advanced Preprocessing Module for Underwater Image Enhancement
Handles dark, blurry, and dull images with state-of-the-art techniques
"""

import cv2
import numpy as np
from typing import Tuple, Dict

class AdvancedPreprocessor:
    """
    Advanced preprocessing for extreme image conditions
    - Dark images: CLAHE, gamma correction
    - Blurry images: Sharpening, denoising
    - Dull colors: White balance, color correction
    """
    
    def __init__(self):
        print(" Advanced Preprocessor initialized")
        
        # CLAHE parameters
        self.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        
        # Denoising parameters
        self.denoise_params = {
            'h': 10,
            'hColor': 10,
            'templateWindowSize': 7,
            'searchWindowSize': 21
        }
    
    def assess_image_quality(self, image: np.ndarray) -> Dict:
        """
        Assess image quality to determine what enhancements are needed
        
        Args:
            image: Input image (RGB, 0-255)
            
        Returns:
            Dictionary with quality metrics and enhancement flags
        """
        # Convert to grayscale for some metrics
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # 1. Brightness (mean intensity)
        brightness = float(np.mean(gray))
        
        # 2. Sharpness (Laplacian variance)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = float(laplacian.var())
        
        # 3. Contrast (standard deviation)
        contrast = float(gray.std())
        
        # 4. Color saturation
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        saturation = float(np.mean(hsv[:, :, 1]))
        
        # 5. Noise level (high frequency components)
        noise = float(np.std(cv2.GaussianBlur(gray, (5, 5), 0) - gray))
        
        # Determine what enhancements are needed
        needs_brightness = brightness < 90
        needs_sharpening = sharpness < 150
        needs_contrast = contrast < 35
        needs_color = saturation < 60
        needs_denoising = noise > 15
        
        quality_score = (
            (brightness / 255) * 0.3 +
            (min(sharpness / 500, 1.0)) * 0.3 +
            (contrast / 100) * 0.2 +
            (saturation / 255) * 0.2
        ) * 100
        
        return {
            'brightness': brightness,
            'sharpness': sharpness,
            'contrast': contrast,
            'saturation': saturation,
            'noise': noise,
            'quality_score': quality_score,
            'needs': {
                'brightness': needs_brightness,
                'sharpening': needs_sharpening,
                'contrast': needs_contrast,
                'color': needs_color,
                'denoising': needs_denoising
            },
            'is_poor_quality': quality_score < 50
        }
    
    def apply_clahe(self, image: np.ndarray, clip_limit: float = 3.0) -> np.ndarray:
        """
        Apply Contrast Limited Adaptive Histogram Equalization
        Dramatically improves dark images
        
        Args:
            image: Input RGB image (0-255)
            clip_limit: Clipping limit for CLAHE (higher = more aggressive)
            
        Returns:
            Enhanced image
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        
        # Apply CLAHE to L channel only
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        
        # Convert back to RGB
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        
        return enhanced
    
    def white_balance(self, image: np.ndarray, method: str = 'gray_world') -> np.ndarray:
        """
        Automatic white balance to fix color casts
        
        Args:
            image: Input RGB image (0-255)
            method: 'gray_world' or 'white_patch'
            
        Returns:
            White balanced image
        """
        if method == 'gray_world':
            # Gray World algorithm
            result = cv2.cvtColor(image, cv2.COLOR_RGB2LAB).astype(np.float32)
            
            # Calculate average a and b values
            avg_a = np.mean(result[:, :, 1])
            avg_b = np.mean(result[:, :, 2])
            
            # Shift to neutral gray (128 in LAB)
            result[:, :, 1] = result[:, :, 1] - ((avg_a - 128) * 0.9)
            result[:, :, 2] = result[:, :, 2] - ((avg_b - 128) * 0.9)
            
            result = np.clip(result, 0, 255).astype(np.uint8)
            balanced = cv2.cvtColor(result, cv2.COLOR_LAB2RGB)
            
        elif method == 'white_patch':
            # White Patch algorithm (von Kries)
            result = image.astype(np.float32)
            
            for i in range(3):
                max_val = np.percentile(result[:, :, i], 99)
                if max_val > 0:
                    result[:, :, i] = result[:, :, i] * (255.0 / max_val)
            
            balanced = np.clip(result, 0, 255).astype(np.uint8)
        
        else:
            balanced = image
        
        return balanced
    
    def adaptive_sharpen(self, image: np.ndarray, strength: float = 1.5) -> np.ndarray:
        """
        Adaptive unsharp masking for blur correction
        
        Args:
            image: Input RGB image (0-255)
            strength: Sharpening strength (0.5-3.0)
            
        Returns:
            Sharpened image
        """
        # Gaussian blur
        gaussian = cv2.GaussianBlur(image, (0, 0), 2)
        
        # Unsharp mask
        sharp = cv2.addWeighted(image, 1.0 + strength, gaussian, -strength, 0)
        
        # Clip to valid range
        sharp = np.clip(sharp, 0, 255).astype(np.uint8)
        
        return sharp
    
    def denoise(self, image: np.ndarray, strength: str = 'medium') -> np.ndarray:
        """
        Advanced denoising for noisy/low-light images
        
        Args:
            image: Input RGB image (0-255)
            strength: 'light', 'medium', or 'heavy'
            
        Returns:
            Denoised image
        """
        params = {
            'light': {'h': 6, 'hColor': 6},
            'medium': {'h': 10, 'hColor': 10},
            'heavy': {'h': 15, 'hColor': 15}
        }
        
        h = params[strength]['h']
        hColor = params[strength]['hColor']
        
        denoised = cv2.fastNlMeansDenoisingColored(
            image, None,
            h=h,
            hColor=hColor,
            templateWindowSize=7,
            searchWindowSize=21
        )
        
        return denoised
    
    def gamma_correction(self, image: np.ndarray, gamma: float = 1.5) -> np.ndarray:
        """
        Apply gamma correction for brightness adjustment
        
        Args:
            image: Input RGB image (0-255)
            gamma: Gamma value (< 1 = darker, > 1 = brighter)
            
        Returns:
            Gamma corrected image
        """
        # Build lookup table
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255
                          for i in range(256)]).astype(np.uint8)
        
        # Apply lookup table
        corrected = cv2.LUT(image, table)
        
        return corrected
    
    def enhance_contrast(self, image: np.ndarray, method: str = 'adaptive') -> np.ndarray:
        """
        Enhance image contrast
        
        Args:
            image: Input RGB image (0-255)
            method: 'adaptive' or 'histogram'
            
        Returns:
            Contrast enhanced image
        """
        if method == 'adaptive':
            # Adaptive contrast in LAB space
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB).astype(np.float32)
            l = lab[:, :, 0]
            
            # Calculate adaptive parameters
            mean_l = np.mean(l)
            std_l = np.std(l)
            
            # Adjust based on current state
            alpha = 1.0 + (100 - mean_l) / 100 * 0.5  # More if dark
            beta = std_l / 50  # Based on current contrast
            
            lab[:, :, 0] = np.clip(l * alpha + beta, 0, 255)
            
            enhanced = cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2RGB)
            
        elif method == 'histogram':
            # Histogram equalization per channel
            enhanced = image.copy()
            for i in range(3):
                enhanced[:, :, i] = cv2.equalizeHist(image[:, :, i])
        
        else:
            enhanced = image
        
        return enhanced
    
    def boost_saturation(self, image: np.ndarray, factor: float = 1.3) -> np.ndarray:
        """
        Boost color saturation for dull images
        
        Args:
            image: Input RGB image (0-255)
            factor: Saturation multiplier (1.0-2.0)
            
        Returns:
            Color-boosted image
        """
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)
        
        # Boost saturation channel
        hsv[:, :, 1] = hsv[:, :, 1] * factor
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
        
        # Slightly boost value for brightness
        hsv[:, :, 2] = hsv[:, :, 2] * 1.05
        hsv[:, :, 2] = np.clip(hsv[:, :, 2], 0, 255)
        
        # Convert back to RGB
        boosted = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        
        return boosted
    
    def preprocess_pipeline(self, image: np.ndarray, 
                           auto: bool = True,
                           quality_info: Dict = None) -> Tuple[np.ndarray, Dict]:
        """
        Complete preprocessing pipeline with automatic enhancement selection
        
        Args:
            image: Input RGB image (0-255)
            auto: If True, automatically determine what enhancements to apply
            quality_info: Pre-computed quality assessment (optional)
            
        Returns:
            Tuple of (enhanced_image, processing_log)
        """
        if quality_info is None:
            quality_info = self.assess_image_quality(image)
        
        processed = image.copy()
        log = {
            'original_quality': quality_info['quality_score'],
            'steps_applied': []
        }
        
        if auto:
            needs = quality_info['needs']
            
            # Step 1: Fix brightness (CLAHE for dark images)
            if needs['brightness']:
                processed = self.apply_clahe(processed, clip_limit=3.5)
                log['steps_applied'].append('CLAHE (brightness enhancement)')
                print("  ✓ Applied CLAHE for dark image")
            
            # Step 2: Denoise if noisy
            if needs['denoising']:
                processed = self.denoise(processed, strength='medium')
                log['steps_applied'].append('Denoising')
                print("  ✓ Applied denoising")
            
            # Step 3: White balance for color correction
            if needs['color']:
                processed = self.white_balance(processed, method='gray_world')
                log['steps_applied'].append('White balance')
                print("  ✓ Applied white balance")
            
            # Step 4: Sharpen if blurry
            if needs['sharpening']:
                processed = self.adaptive_sharpen(processed, strength=1.3)
                log['steps_applied'].append('Adaptive sharpening')
                print("  ✓ Applied sharpening for blur")
            
            # Step 5: Enhance contrast
            if needs['contrast']:
                processed = self.enhance_contrast(processed, method='adaptive')
                log['steps_applied'].append('Adaptive contrast')
                print("  ✓ Applied contrast enhancement")
            
            # Step 6: Boost saturation for dull colors
            if needs['color'] or quality_info['saturation'] < 80:
                processed = self.boost_saturation(processed, factor=1.4)
                log['steps_applied'].append('Saturation boost')
                print("  ✓ Boosted color saturation")
        
        # Assess final quality
        final_quality = self.assess_image_quality(processed)
        log['final_quality'] = final_quality['quality_score']
        log['improvement'] = final_quality['quality_score'] - quality_info['quality_score']
        
        return processed, log
    
    def preprocess_for_extreme_cases(self, image: np.ndarray) -> np.ndarray:
        """
        Aggressive preprocessing for very poor quality images
        (dark + blurry + dull)
        
        Args:
            image: Input RGB image (0-255)
            
        Returns:
            Heavily enhanced image
        """
        print(" Applying EXTREME enhancement mode...")
        
        # Step 1: Strong CLAHE
        processed = self.apply_clahe(image, clip_limit=4.0)
        print("  ✓ Strong CLAHE")
        
        # Step 2: Gamma correction
        processed = self.gamma_correction(processed, gamma=1.3)
        print("  ✓ Gamma boost")
        
        # Step 3: Aggressive denoising
        processed = self.denoise(processed, strength='heavy')
        print("  ✓ Heavy denoising")
        
        # Step 4: White balance
        processed = self.white_balance(processed, method='white_patch')
        print("  ✓ White patch balance")
        
        # Step 5: Strong sharpening
        processed = self.adaptive_sharpen(processed, strength=2.0)
        print("  ✓ Strong sharpening")
        
        # Step 6: Histogram equalization
        processed = self.enhance_contrast(processed, method='histogram')
        print("  ✓ Histogram equalization")
        
        # Step 7: Maximum saturation boost
        processed = self.boost_saturation(processed, factor=1.8)
        print("  ✓ Maximum color boost")
        
        return processed


# Utility functions
def estimate_noise_level(image: np.ndarray) -> float:
    """Estimate noise level in image"""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    noise = np.std(cv2.GaussianBlur(gray, (5, 5), 0) - gray)
    return float(noise)


def is_underexposed(image: np.ndarray, threshold: float = 90) -> bool:
    """Check if image is underexposed (dark)"""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    mean_brightness = np.mean(gray)
    return mean_brightness < threshold


def is_blurry(image: np.ndarray, threshold: float = 150) -> bool:
    """Check if image is blurry using Laplacian variance"""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var < threshold


def is_low_saturation(image: np.ndarray, threshold: float = 60) -> bool:
    """Check if image has dull colors"""
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    mean_saturation = np.mean(hsv[:, :, 1])
    return mean_saturation < threshold


# Quick test
if __name__ == "__main__":
    print(" Testing Advanced Preprocessor\n")
    
    preprocessor = AdvancedPreprocessor()
    
    # Create test image (simulated poor quality)
    test_image = np.random.randint(20, 80, (480, 640, 3), dtype=np.uint8)  # Dark image
    
    print(" Assessing image quality...")
    quality = preprocessor.assess_image_quality(test_image)
    
    print(f"\n Quality Assessment:")
    print(f"  Brightness: {quality['brightness']:.1f}/255")
    print(f"  Sharpness: {quality['sharpness']:.1f}")
    print(f"  Contrast: {quality['contrast']:.1f}")
    print(f"  Saturation: {quality['saturation']:.1f}")
    print(f"  Quality Score: {quality['quality_score']:.1f}/100")
    
    print(f"\n Needs:")
    for need, value in quality['needs'].items():
        if value:
            print(f"    {need.replace('_', ' ').title()}")
    
    print("\n Applying preprocessing pipeline...")
    enhanced, log = preprocessor.preprocess_pipeline(test_image)
    
    print(f"\n Results:")
    print(f"  Original quality: {log['original_quality']:.1f}")
    print(f"  Final quality: {log['final_quality']:.1f}")
    print(f"  Improvement: +{log['improvement']:.1f} points")
    
    print(f"\n Steps applied: {len(log['steps_applied'])}")
    for step in log['steps_applied']:
        print(f"  • {step}")
    
    print("\n Advanced Preprocessor ready!")
