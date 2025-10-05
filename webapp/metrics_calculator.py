"""
Image Quality Metrics Calculator
Calculates PSNR, SSIM, UIQM for underwater image enhancement evaluation
"""

import cv2
import numpy as np
import math
from typing import Dict, Tuple
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import peak_signal_noise_ratio as psnr


class ImageQualityMetrics:
    """
    Comprehensive image quality assessment for underwater images
    """
    
    def __init__(self):
        self.metrics = {}
        
    def calculate_all_metrics(self, original_image: np.ndarray, 
                             enhanced_image: np.ndarray,
                             has_reference: bool = True) -> Dict:
        """
        Calculate all quality metrics
        
        Args:
            original_image: Original underwater image (BGR)
            enhanced_image: Enhanced underwater image (BGR)
            has_reference: Whether to calculate reference-based metrics
            
        Returns:
            Dictionary containing all calculated metrics
        """
        results = {}
        
        try:
            # Ensure images are same size
            if original_image.shape != enhanced_image.shape:
                enhanced_image = cv2.resize(enhanced_image, 
                                           (original_image.shape[1], original_image.shape[0]))
            
            # Convert to RGB for processing
            original_rgb = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
            enhanced_rgb = cv2.cvtColor(enhanced_image, cv2.COLOR_BGR2RGB)
            
            # Initialize all metrics to default values
            results['psnr'] = 0.0
            results['ssim'] = 0.0
            
            # Reference-based metrics (if ground truth available)
            if has_reference:
                results['psnr'] = self.calculate_psnr(original_rgb, enhanced_rgb)
                results['ssim'] = self.calculate_ssim(original_rgb, enhanced_rgb)
            
            # No-reference metrics (always calculate for enhanced image)
            results['uiqm'] = self.calculate_uiqm(enhanced_rgb)
            results['uciqe'] = self.calculate_uciqe(enhanced_rgb)
            
            # Additional quality indicators
            results['sharpness'] = self.calculate_sharpness(enhanced_rgb)
            results['contrast'] = self.calculate_contrast(enhanced_rgb)
            results['colorfulness'] = self.calculate_colorfulness(enhanced_rgb)
            
            # Overall quality score (normalized 0-100)
            results['overall_score'] = self._calculate_overall_score(results)
            
            # Enhancement improvement percentage
            if has_reference:
                original_uiqm = self.calculate_uiqm(original_rgb)
                results['improvement'] = ((results['uiqm'] - original_uiqm) / original_uiqm * 100)
            
            return results
            
        except Exception as e:
            print(f"Error calculating metrics: {str(e)}")
            return self._get_default_metrics()
    
    def calculate_psnr(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        Calculate Peak Signal-to-Noise Ratio
        Higher is better (typically 20-50 dB for images)
        """
        try:
            # Ensure images are in [0, 255] range
            if img1.max() <= 1.0:
                img1 = (img1 * 255).astype(np.uint8)
            if img2.max() <= 1.0:
                img2 = (img2 * 255).astype(np.uint8)
            
            psnr_value = psnr(img1, img2, data_range=255)
            return round(float(psnr_value), 2)
        except Exception as e:
            print(f"PSNR calculation error: {e}")
            return 0.0
    
    def calculate_ssim(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        Calculate Structural Similarity Index
        Range: [-1, 1], higher is better (1 means identical)
        """
        try:
            # Ensure images are in [0, 255] range
            if img1.max() <= 1.0:
                img1 = (img1 * 255).astype(np.uint8)
            if img2.max() <= 1.0:
                img2 = (img2 * 255).astype(np.uint8)
            
            # Calculate SSIM for each channel and average
            ssim_values = []
            for i in range(3):
                ssim_val = ssim(img1[:, :, i], img2[:, :, i], data_range=255)
                ssim_values.append(ssim_val)
            
            return round(float(np.mean(ssim_values)), 4)
        except Exception as e:
            print(f"SSIM calculation error: {e}")
            return 0.0
    
    def calculate_uiqm(self, image: np.ndarray) -> float:
        """
        Calculate Underwater Image Quality Measure (UIQM)
        Combines colorfulness, sharpness, and contrast
        Higher is better (typically 0-4)
        """
        try:
            # Normalize image to [0, 1]
            if image.max() > 1.0:
                image = image.astype(np.float32) / 255.0
            
            # Calculate UICM (Underwater Image Colorfulness Measure)
            uicm = self._calculate_uicm(image)
            
            # Calculate UISM (Underwater Image Sharpness Measure)
            uism = self._calculate_uism(image)
            
            # Calculate UIConM (Underwater Image Contrast Measure)
            uiconm = self._calculate_uiconm(image)
            
            # Weighted combination
            uiqm = (0.0282 * uicm) + (0.2953 * uism) + (3.5753 * uiconm)
            
            return round(float(uiqm), 4)
        except Exception as e:
            print(f"UIQM calculation error: {e}")
            return 0.0
    
    def calculate_uciqe(self, image: np.ndarray) -> float:
        """
        Calculate Underwater Color Image Quality Evaluation (UCIQE)
        Based on chroma, saturation, and contrast
        Higher is better (typically 0.4-0.7)
        """
        try:
            # Normalize image
            if image.max() > 1.0:
                image = image.astype(np.float32) / 255.0
            
            # Convert to CIELab color space
            lab = cv2.cvtColor((image * 255).astype(np.uint8), cv2.COLOR_RGB2LAB)
            lab = lab.astype(np.float32) / 255.0
            
            # Calculate chroma
            chroma = np.sqrt(lab[:,:,1]**2 + lab[:,:,2]**2)
            
            # Calculate saturation
            saturation = chroma / np.sqrt(chroma**2 + lab[:,:,0]**2 + 1e-12)
            
            # Calculate contrast
            l_std = np.std(lab[:,:,0])
            
            # UCIQE formula
            c1 = 0.4680
            c2 = 0.2745
            c3 = 0.2576
            
            uciqe = (c1 * np.std(chroma)) + (c2 * np.mean(saturation)) + (c3 * l_std)
            
            return round(float(uciqe), 4)
        except Exception as e:
            print(f"UCIQE calculation error: {e}")
            return 0.0
    
    def calculate_sharpness(self, image: np.ndarray) -> float:
        """
        Calculate image sharpness using Laplacian variance
        Higher is better
        """
        try:
            if image.max() > 1.0:
                image = image.astype(np.uint8)
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            return round(float(laplacian_var), 2)
        except Exception as e:
            print(f"Sharpness calculation error: {e}")
            return 0.0
    
    def calculate_contrast(self, image: np.ndarray) -> float:
        """
        Calculate image contrast (standard deviation of intensity)
        Higher is better
        """
        try:
            if image.max() > 1.0:
                image = image.astype(np.uint8)
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            contrast = float(gray.std())
            return round(contrast, 2)
        except Exception as e:
            print(f"Contrast calculation error: {e}")
            return 0.0
    
    def calculate_colorfulness(self, image: np.ndarray) -> float:
        """
        Calculate image colorfulness metric
        Higher is better
        """
        try:
            if image.max() > 1.0:
                image = image.astype(np.float32) / 255.0
            
            R, G, B = image[:,:,0], image[:,:,1], image[:,:,2]
            
            rg = R - G
            yb = 0.5 * (R + G) - B
            
            std_rg = np.std(rg)
            std_yb = np.std(yb)
            mean_rg = np.mean(rg)
            mean_yb = np.mean(yb)
            
            colorfulness = np.sqrt(std_rg**2 + std_yb**2) + 0.3 * np.sqrt(mean_rg**2 + mean_yb**2)
            
            return round(float(colorfulness), 4)
        except Exception as e:
            print(f"Colorfulness calculation error: {e}")
            return 0.0
    
    def _calculate_uicm(self, image: np.ndarray) -> float:
        """Underwater Image Colorfulness Measure"""
        R, G, B = image[:,:,0], image[:,:,1], image[:,:,2]
        RG = R - G
        YB = (R + G) / 2 - B
        
        alpha_L = np.sqrt(RG.var() + YB.var())
        alpha_R = RG.mean()**2 + YB.mean()**2
        
        return -0.0268 * np.sqrt(alpha_L + alpha_R)
    
    def _calculate_uism(self, image: np.ndarray) -> float:
        """Underwater Image Sharpness Measure"""
        gray = cv2.cvtColor((image * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
        
        # Sobel edge detection
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        # Edge magnitude
        edges = np.sqrt(sobel_x**2 + sobel_y**2)
        
        # EME (Enhancement Measure Estimation)
        return float(edges.mean())
    
    def _calculate_uiconm(self, image: np.ndarray) -> float:
        """Underwater Image Contrast Measure"""
        gray = cv2.cvtColor((image * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
        return float(gray.std() / 255.0)
    
    def _calculate_overall_score(self, metrics: Dict) -> float:
        """
        Calculate overall quality score (0-100)
        Weighted combination of all metrics
        """
        score = 0.0
        weights = {
            'uiqm': 25,
            'uciqe': 20,
            'sharpness': 15,
            'contrast': 15,
            'colorfulness': 15,
            'ssim': 10  # if available
        }
        
        if 'uiqm' in metrics:
            score += min(metrics['uiqm'] / 4.0 * weights['uiqm'], weights['uiqm'])
        
        if 'uciqe' in metrics:
            score += min(metrics['uciqe'] / 0.7 * weights['uciqe'], weights['uciqe'])
        
        if 'sharpness' in metrics:
            score += min(metrics['sharpness'] / 1000.0 * weights['sharpness'], weights['sharpness'])
        
        if 'contrast' in metrics:
            score += min(metrics['contrast'] / 100.0 * weights['contrast'], weights['contrast'])
        
        if 'colorfulness' in metrics:
            score += min(metrics['colorfulness'] * weights['colorfulness'], weights['colorfulness'])
        
        if 'ssim' in metrics and metrics['ssim'] > 0:
            score += metrics['ssim'] * weights['ssim']
        
        return round(score, 2)
    
    def _get_default_metrics(self) -> Dict:
        """Return default metrics in case of error"""
        return {
            'psnr': 0.0,
            'ssim': 0.0,
            'uiqm': 0.0,
            'uciqe': 0.0,
            'sharpness': 0.0,
            'contrast': 0.0,
            'colorfulness': 0.0,
            'overall_score': 0.0,
            'improvement': 0.0
        }
    
    def generate_histograms(self, image: np.ndarray) -> Dict:
        """
        Generate color histograms for visualization
        
        Returns:
            Dictionary with histogram data for R, G, B channels
        """
        try:
            if image.max() > 1.0:
                image = image.astype(np.uint8)
            else:
                image = (image * 255).astype(np.uint8)
            
            histograms = {}
            colors = ['red', 'green', 'blue']
            
            for i, color in enumerate(colors):
                hist = cv2.calcHist([image], [i], None, [256], [0, 256])
                hist = hist.flatten().tolist()
                histograms[color] = hist
            
            return histograms
        except Exception as e:
            print(f"Histogram generation error: {e}")
            return {'red': [], 'green': [], 'blue': []}
    
    def get_color_statistics(self, image: np.ndarray) -> Dict:
        """
        Get detailed color distribution statistics
        """
        try:
            if image.max() > 1.0:
                image = image.astype(np.float32) / 255.0
            
            R, G, B = image[:,:,0], image[:,:,1], image[:,:,2]
            
            stats = {
                'red': {
                    'mean': round(float(R.mean()), 4),
                    'std': round(float(R.std()), 4),
                    'min': round(float(R.min()), 4),
                    'max': round(float(R.max()), 4)
                },
                'green': {
                    'mean': round(float(G.mean()), 4),
                    'std': round(float(G.std()), 4),
                    'min': round(float(G.min()), 4),
                    'max': round(float(G.max()), 4)
                },
                'blue': {
                    'mean': round(float(B.mean()), 4),
                    'std': round(float(B.std()), 4),
                    'min': round(float(B.min()), 4),
                    'max': round(float(B.max()), 4)
                },
                'dominance': self._get_dominant_color(image)
            }
            
            return stats
        except Exception as e:
            print(f"Color statistics error: {e}")
            return {}
    
    def _get_dominant_color(self, image: np.ndarray) -> str:
        """Determine dominant color channel"""
        R, G, B = image[:,:,0].mean(), image[:,:,1].mean(), image[:,:,2].mean()
        
        if R > G and R > B:
            return 'red'
        elif G > R and G > B:
            return 'green'
        else:
            return 'blue'


# Global metrics calculator instance
_metrics_calculator = None

def get_metrics_calculator():
    """Get or create the global metrics calculator instance"""
    global _metrics_calculator
    if _metrics_calculator is None:
        _metrics_calculator = ImageQualityMetrics()
    return _metrics_calculator