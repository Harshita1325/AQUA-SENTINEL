"""
Advanced Post-Processing Module for Underwater Image Enhancement
Refines model output with tone mapping, detail enhancement, and color grading
"""

import cv2
import numpy as np
from typing import Tuple, Dict

class AdvancedPostprocessor:
    """
    Advanced post-processing for model output refinement
    - Tone mapping for HDR effect
    - Detail enhancement
    - Color grading
    - Final polish
    """
    
    def __init__(self):
        print(" Advanced Postprocessor initialized")
    
    def tone_map(self, image: np.ndarray, method: str = 'reinhard', 
                 gamma: float = 1.5) -> np.ndarray:
        """
        Apply tone mapping for better dynamic range
        
        Args:
            image: Input RGB image (0-255)
            method: 'reinhard', 'drago', or 'mantiuk'
            gamma: Gamma correction factor
            
        Returns:
            Tone mapped image
        """
        # Convert to float32 [0, 1]
        img_float = image.astype(np.float32) / 255.0
        
        if method == 'reinhard':
            # Reinhard tone mapping
            tonemap = cv2.createTonemapReinhard(
                gamma=gamma,
                intensity=0,
                light_adapt=0.8,
                color_adapt=0
            )
        elif method == 'drago':
            # Drago tone mapping (better for high contrast)
            tonemap = cv2.createTonemapDrago(
                gamma=gamma,
                saturation=1.0,
                bias=0.85
            )
        elif method == 'mantiuk':
            # Mantiuk tone mapping (perceptual based)
            tonemap = cv2.createTonemapMantiuk(
                gamma=gamma,
                scale=0.75,
                saturation=1.2
            )
        else:
            return image
        
        # Apply tone mapping
        result = tonemap.process(img_float)
        result = np.clip(result * 255, 0, 255).astype(np.uint8)
        
        return result
    
    def enhance_details(self, image: np.ndarray, strength: float = 0.5) -> np.ndarray:
        """
        Enhance fine details and textures
        
        Args:
            image: Input RGB image (0-255)
            strength: Enhancement strength (0.0-1.0)
            
        Returns:
            Detail-enhanced image
        """
        # High-pass filter using gaussian blur
        gaussian = cv2.GaussianBlur(image, (0, 0), 2.0)
        detail = cv2.addWeighted(image, 1.0 + strength, gaussian, -strength, 0)
        
        # Edge enhancement
        gray = cv2.cvtColor(detail, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 30, 100)
        edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB).astype(np.float32) / 255.0
        
        # Subtle edge overlay
        detail_float = detail.astype(np.float32)
        enhanced = detail_float + edges_colored * 20.0 * strength
        enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)
        
        return enhanced
    
    def color_grade(self, image: np.ndarray, style: str = 'vibrant') -> np.ndarray:
        """
        Apply color grading for aesthetic enhancement
        
        Args:
            image: Input RGB image (0-255)
            style: 'vibrant', 'natural', 'cool', or 'warm'
            
        Returns:
            Color graded image
        """
        result = image.astype(np.float32)
        
        if style == 'vibrant':
            # Boost saturation and slightly increase contrast
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)
            hsv[:, :, 1] = hsv[:, :, 1] * 1.3  # Saturation
            hsv[:, :, 2] = hsv[:, :, 2] * 1.05  # Value
            hsv = np.clip(hsv, 0, 255).astype(np.uint8)
            result = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB).astype(np.float32)
            
        elif style == 'natural':
            # Balanced, minimal adjustment
            result = result * 1.02
            
        elif style == 'cool':
            # Blue-teal tint
            result[:, :, 0] = result[:, :, 0] * 0.95  # Reduce red
            result[:, :, 1] = result[:, :, 1] * 1.05  # Boost green slightly
            result[:, :, 2] = result[:, :, 2] * 1.1   # Boost blue
            
        elif style == 'warm':
            # Orange-yellow tint
            result[:, :, 0] = result[:, :, 0] * 1.15  # Boost red
            result[:, :, 1] = result[:, :, 1] * 1.05  # Boost green
            result[:, :, 2] = result[:, :, 2] * 0.9   # Reduce blue
        
        result = np.clip(result, 0, 255).astype(np.uint8)
        return result
    
    def sharpen_advanced(self, image: np.ndarray, method: str = 'unsharp') -> np.ndarray:
        """
        Advanced sharpening techniques
        
        Args:
            image: Input RGB image (0-255)
            method: 'unsharp', 'laplacian', or 'bilateral'
            
        Returns:
            Sharpened image
        """
        if method == 'unsharp':
            # Unsharp masking
            gaussian = cv2.GaussianBlur(image, (5, 5), 1.0)
            sharpened = cv2.addWeighted(image, 1.5, gaussian, -0.5, 0)
            
        elif method == 'laplacian':
            # Laplacian sharpening
            laplacian = cv2.Laplacian(image, cv2.CV_64F)
            sharpened = image - laplacian * 0.3
            sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
            
        elif method == 'bilateral':
            # Bilateral filter (edge-preserving)
            bilateral = cv2.bilateralFilter(image, 9, 75, 75)
            sharpened = cv2.addWeighted(image, 1.3, bilateral, -0.3, 0)
        
        else:
            sharpened = image
        
        return sharpened
    
    def adjust_exposure(self, image: np.ndarray, exposure: float = 1.2) -> np.ndarray:
        """
        Adjust overall exposure
        
        Args:
            image: Input RGB image (0-255)
            exposure: Exposure multiplier (0.5-2.0)
            
        Returns:
            Exposure-adjusted image
        """
        adjusted = image.astype(np.float32) * exposure
        adjusted = np.clip(adjusted, 0, 255).astype(np.uint8)
        return adjusted
    
    def vibrance_boost(self, image: np.ndarray, amount: float = 30) -> np.ndarray:
        """
        Boost vibrance (saturation of muted colors only)
        Better than saturation for natural look
        
        Args:
            image: Input RGB image (0-255)
            amount: Vibrance increase amount (0-100)
            
        Returns:
            Vibrance-boosted image
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)
        
        # Get current saturation
        sat = hsv[:, :, 1]
        
        # Calculate boost (more for less saturated pixels)
        sat_factor = (255 - sat) / 255.0  # Inverse saturation
        boost = sat_factor * amount
        
        # Apply boost
        hsv[:, :, 1] = sat + boost
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
        
        result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        return result
    
    def clarity_enhance(self, image: np.ndarray, strength: float = 1.0) -> np.ndarray:
        """
        Enhance mid-tone contrast (clarity effect)
        
        Args:
            image: Input RGB image (0-255)
            strength: Clarity strength (0.0-2.0)
            
        Returns:
            Clarity-enhanced image
        """
        # Convert to LAB
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB).astype(np.float32)
        l = lab[:, :, 0]
        
        # Create mask for mid-tones (around 128)
        mid_tone_mask = 1.0 - np.abs(l - 128.0) / 128.0
        mid_tone_mask = np.clip(mid_tone_mask, 0, 1)
        
        # Apply local contrast enhancement to mid-tones
        blurred = cv2.GaussianBlur(l, (0, 0), 10)
        contrast = (l - blurred) * strength * mid_tone_mask
        
        lab[:, :, 0] = np.clip(l + contrast, 0, 255)
        
        result = cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2RGB)
        return result
    
    def reduce_color_cast(self, image: np.ndarray) -> np.ndarray:
        """
        Remove remaining color casts
        
        Args:
            image: Input RGB image (0-255)
            
        Returns:
            Color cast corrected image
        """
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB).astype(np.float32)
        
        # Calculate average a and b
        avg_a = np.mean(lab[:, :, 1])
        avg_b = np.mean(lab[:, :, 2])
        
        # Shift towards neutral
        lab[:, :, 1] = lab[:, :, 1] - (avg_a - 128) * 0.7
        lab[:, :, 2] = lab[:, :, 2] - (avg_b - 128) * 0.7
        
        lab = np.clip(lab, 0, 255).astype(np.uint8)
        result = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        
        return result
    
    def final_polish(self, image: np.ndarray) -> np.ndarray:
        """
        Final polish pass with subtle enhancements
        
        Args:
            image: Input RGB image (0-255)
            
        Returns:
            Polished image
        """
        # 1. Subtle sharpening
        polished = self.sharpen_advanced(image, method='unsharp')
        
        # 2. Micro-contrast enhancement
        lab = cv2.cvtColor(polished, cv2.COLOR_RGB2LAB).astype(np.float32)
        l = lab[:, :, 0]
        l_blur = cv2.GaussianBlur(l, (0, 0), 3)
        lab[:, :, 0] = l + (l - l_blur) * 0.3
        lab[:, :, 0] = np.clip(lab[:, :, 0], 0, 255)
        polished = cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2RGB)
        
        # 3. Slight vibrance boost
        polished = self.vibrance_boost(polished, amount=15)
        
        # 4. Final exposure tweak
        polished = self.adjust_exposure(polished, exposure=1.02)
        
        return polished
    
    def postprocess_pipeline(self, image: np.ndarray, 
                            aggressive: bool = False) -> Tuple[np.ndarray, Dict]:
        """
        Complete post-processing pipeline
        
        Args:
            image: Input RGB image (0-255) from model
            aggressive: If True, apply more aggressive enhancements
            
        Returns:
            Tuple of (enhanced_image, processing_log)
        """
        processed = image.copy()
        log = {'steps_applied': []}
        
        # Step 1: Tone mapping for dynamic range
        processed = self.tone_map(processed, method='reinhard', gamma=1.5)
        log['steps_applied'].append('Tone mapping (Reinhard)')
        print("  ✓ Applied tone mapping")
        
        # Step 2: Enhance details
        detail_strength = 0.7 if aggressive else 0.5
        processed = self.enhance_details(processed, strength=detail_strength)
        log['steps_applied'].append(f'Detail enhancement ({detail_strength})')
        print("  ✓ Enhanced details")
        
        # Step 3: Clarity enhancement
        clarity_str = 1.2 if aggressive else 0.8
        processed = self.clarity_enhance(processed, strength=clarity_str)
        log['steps_applied'].append(f'Clarity enhancement ({clarity_str})')
        print("  ✓ Enhanced clarity")
        
        # Step 4: Color grading
        processed = self.color_grade(processed, style='vibrant')
        log['steps_applied'].append('Color grading (vibrant)')
        print("  ✓ Applied color grading")
        
        # Step 5: Remove any remaining color cast
        processed = self.reduce_color_cast(processed)
        log['steps_applied'].append('Color cast removal')
        print("  ✓ Removed color cast")
        
        # Step 6: Final polish
        processed = self.final_polish(processed)
        log['steps_applied'].append('Final polish')
        print("  ✓ Applied final polish")
        
        return processed, log
    
    def extreme_postprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Aggressive post-processing for images that need maximum enhancement
        
        Args:
            image: Input RGB image (0-255)
            
        Returns:
            Heavily enhanced image
        """
        print("⚡ Applying EXTREME post-processing...")
        
        # Step 1: Strong tone mapping
        processed = self.tone_map(image, method='drago', gamma=1.8)
        print("  ✓ Strong tone mapping")
        
        # Step 2: Maximum detail enhancement
        processed = self.enhance_details(processed, strength=1.0)
        print("  ✓ Maximum detail enhancement")
        
        # Step 3: Strong clarity
        processed = self.clarity_enhance(processed, strength=1.5)
        print("  ✓ Strong clarity")
        
        # Step 4: Vibrant color grading
        processed = self.color_grade(processed, style='vibrant')
        print("  ✓ Vibrant color grading")
        
        # Step 5: High vibrance boost
        processed = self.vibrance_boost(processed, amount=40)
        print("  ✓ High vibrance boost")
        
        # Step 6: Advanced sharpening
        processed = self.sharpen_advanced(processed, method='bilateral')
        print("  ✓ Advanced sharpening")
        
        # Step 7: Exposure boost
        processed = self.adjust_exposure(processed, exposure=1.15)
        print("  ✓ Exposure boost")
        
        return processed


# Utility functions
def calculate_histogram_statistics(image: np.ndarray) -> Dict:
    """Calculate histogram statistics for image"""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    
    return {
        'mean': float(np.mean(gray)),
        'std': float(np.std(gray)),
        'min': float(np.min(gray)),
        'max': float(np.max(gray)),
        'median': float(np.median(gray))
    }


# Quick test
if __name__ == "__main__":
    print(" Testing Advanced Postprocessor\n")
    
    postprocessor = AdvancedPostprocessor()
    
    # Create test image (simulated model output)
    test_image = np.random.randint(80, 180, (480, 640, 3), dtype=np.uint8)
    
    print(" Input image statistics:")
    stats = calculate_histogram_statistics(test_image)
    print(f"  Mean: {stats['mean']:.1f}")
    print(f"  Std: {stats['std']:.1f}")
    print(f"  Range: {stats['min']:.0f} - {stats['max']:.0f}")
    
    print("\n Applying post-processing pipeline...")
    enhanced, log = postprocessor.postprocess_pipeline(test_image)
    
    print(f"\n Output image statistics:")
    stats_out = calculate_histogram_statistics(enhanced)
    print(f"  Mean: {stats_out['mean']:.1f}")
    print(f"  Std: {stats_out['std']:.1f}")
    print(f"  Range: {stats_out['min']:.0f} - {stats_out['max']:.0f}")
    
    print(f"\n Steps applied: {len(log['steps_applied'])}")
    for step in log['steps_applied']:
        print(f"  • {step}")
    
    print("\n Advanced Postprocessor ready!")
