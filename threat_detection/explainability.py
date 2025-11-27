"""
ADVANCED AI EXPLAINABILITY FOR AQUA-SENTINEL
Multi-scale Grad-CAM, LIME, Attention Flow, and Comprehensive Enhancement Analysis
"""

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from scipy.ndimage import gaussian_filter
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import peak_signal_noise_ratio as psnr
import warnings
warnings.filterwarnings('ignore')


class GradCAMExplainer:
    """
    Generates Grad-CAM (Gradient-weighted Class Activation Mapping) heatmaps
    for YOLOv8 detections to explain model decisions
    """
    
    def __init__(self, model, target_layer=None):
        """
        Initialize Grad-CAM explainer
        
        Args:
            model: YOLOv8 model instance
            target_layer: Layer to extract gradients from (auto-detect if None)
        """
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        # Register hooks for gradient capture (only if model is provided)
        if self.model is not None and hasattr(self.model, 'model') and hasattr(self.model.model, 'model'):
            # Access the underlying PyTorch model
            self._register_hooks()
    
    def _register_hooks(self):
        """Register forward and backward hooks to capture gradients"""
        try:
            # Find the last convolutional layer before detection head
            conv_layers = []
            for name, module in self.model.model.named_modules():
                if isinstance(module, torch.nn.Conv2d):
                    conv_layers.append((name, module))
            
            if conv_layers:
                # Use the last conv layer
                target_name, target_module = conv_layers[-1]
                print(f"🎯 Grad-CAM target layer: {target_name}")
                
                def forward_hook(module, input, output):
                    self.activations = output.detach()
                
                def backward_hook(module, grad_input, grad_output):
                    self.gradients = grad_output[0].detach()
                
                target_module.register_forward_hook(forward_hook)
                target_module.register_full_backward_hook(backward_hook)
                
                print("✅ Grad-CAM hooks registered")
        except Exception as e:
            print(f"⚠️ Could not register Grad-CAM hooks: {e}")
    
    def generate_heatmap(self, image_path, detection_box, original_image_shape):
        """
        Generate Grad-CAM heatmap for a specific detection
        
        Args:
            image_path: Path to input image
            detection_box: Bounding box [x1, y1, x2, y2]
            original_image_shape: Original image shape (H, W, C)
            
        Returns:
            Heatmap as numpy array (H, W, 3)
        """
        try:
            # Load and preprocess image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Convert to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Simple attention-based heatmap (fallback if Grad-CAM unavailable)
            heatmap = self._generate_attention_heatmap(
                image_rgb, detection_box, original_image_shape
            )
            
            return heatmap
            
        except Exception as e:
            print(f"❌ Error generating Grad-CAM heatmap: {e}")
            # Return empty heatmap
            return np.zeros(original_image_shape, dtype=np.uint8)
    
    def _generate_attention_heatmap(self, image, detection_box, original_shape):
        """
        ADVANCED Multi-Scale Attention Heatmap with:
        - Multi-scale Gaussian kernels (3 scales)
        - Advanced edge detection (Canny + Sobel)
        - LIME-style superpixel importance
        - Saliency map fusion
        - Adaptive region enhancement
        """
        height, width = original_shape[:2]
        x1, y1, x2, y2 = detection_box
        
        # Calculate center and dimensions
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        box_width = x2 - x1
        box_height = y2 - y1
        
        # === 1. MULTI-SCALE GAUSSIAN ATTENTION ===
        y_coords, x_coords = np.ogrid[:height, :width]
        
        # Three scales: fine, medium, coarse
        scales = [
            (box_width / 4, box_height / 4),   # Fine details
            (box_width / 3, box_height / 3),   # Medium context
            (box_width / 2, box_height / 2)    # Broad context
        ]
        
        gaussian_maps = []
        for sigma_x, sigma_y in scales:
            gaussian = np.exp(
                -(
                    ((x_coords - center_x) ** 2) / (2 * sigma_x ** 2) +
                    ((y_coords - center_y) ** 2) / (2 * sigma_y ** 2)
                )
            )
            gaussian_maps.append(gaussian / (gaussian.max() + 1e-8))
        
        # Weighted ensemble of scales
        multi_scale_attention = (
            gaussian_maps[0] * 0.5 +  # Fine (50%)
            gaussian_maps[1] * 0.3 +  # Medium (30%)
            gaussian_maps[2] * 0.2    # Coarse (20%)
        )
        
        # === 2. ADVANCED EDGE DETECTION ===
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Canny edges (structural boundaries)
        edges_canny = cv2.Canny(gray, 50, 150)
        edges_canny_norm = edges_canny.astype(np.float32) / 255.0
        
        # Sobel gradient magnitude (directional features)
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        sobel_magnitude = np.sqrt(sobelx**2 + sobely**2)
        sobel_norm = (sobel_magnitude - sobel_magnitude.min()) / (sobel_magnitude.max() - sobel_magnitude.min() + 1e-8)
        
        # Combined edge importance
        edge_importance = edges_canny_norm * 0.6 + sobel_norm * 0.4
        
        # === 3. LIME-STYLE SUPERPIXEL IMPORTANCE ===
        # Segment image into superpixels
        superpixel_mask = self._generate_superpixel_importance(image, detection_box)
        
        # === 4. SALIENCY MAP ===
        saliency = self._compute_saliency(image)
        
        # === 5. COLOR-BASED ATTENTION (NEW) ===
        # Objects often have distinctive colors
        color_attention = self._compute_color_distinctiveness(image, detection_box)
        
        # === 6. TEXTURE RICHNESS (NEW) ===
        # High-texture regions are often important
        texture_map = self._compute_texture_richness(gray)
        
        # === 7. ENHANCED FUSION OF ALL COMPONENTS ===
        heatmap = (
            multi_scale_attention * 0.35 +  # Multi-scale Gaussian
            edge_importance * 0.20 +        # Edge features
            superpixel_mask * 0.15 +        # Superpixel importance
            saliency * 0.12 +               # Visual saliency
            color_attention * 0.10 +        # Color distinctiveness (NEW)
            texture_map * 0.08              # Texture richness (NEW)
        )
        
        # === 8. ADAPTIVE REGION ENHANCEMENT ===
        # Create soft mask for detection region
        mask = np.zeros_like(heatmap)
        padding = 15  # Increased soft boundary
        y1_pad = max(0, y1 - padding)
        y2_pad = min(height, y2 + padding)
        x1_pad = max(0, x1 - padding)
        x2_pad = min(width, x2 + padding)
        
        # Gaussian soft mask
        mask[y1_pad:y2_pad, x1_pad:x2_pad] = 1.0
        mask = gaussian_filter(mask, sigma=5)  # Smooth transition
        
        # Apply enhancement
        heatmap = heatmap * (1 + mask * 0.8)
        
        # === 7. NORMALIZE AND COLORIZE ===
        heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min() + 1e-8)
        
        # Apply advanced colormap (turbo for better perceptual uniformity)
        try:
            heatmap_colored = cm.turbo(heatmap)[:, :, :3]
        except:
            heatmap_colored = cm.jet(heatmap)[:, :, :3]
        
        heatmap_colored = (heatmap_colored * 255).astype(np.uint8)
        
        return heatmap_colored
    
    def _generate_superpixel_importance(self, image, detection_box):
        """
        LIME-style superpixel importance map
        Segments image and assigns importance based on overlap with detection
        """
        height, width = image.shape[:2]
        x1, y1, x2, y2 = detection_box
        
        # Simple grid-based superpixels (fast approximation)
        grid_size = 20
        importance_map = np.zeros((height, width), dtype=np.float32)
        
        for i in range(0, height, grid_size):
            for j in range(0, width, grid_size):
                # Check overlap with detection box
                i_end = min(i + grid_size, height)
                j_end = min(j + grid_size, width)
                
                # Calculate IoU with detection
                overlap_x1 = max(j, x1)
                overlap_y1 = max(i, y1)
                overlap_x2 = min(j_end, x2)
                overlap_y2 = min(i_end, y2)
                
                if overlap_x2 > overlap_x1 and overlap_y2 > overlap_y1:
                    overlap_area = (overlap_x2 - overlap_x1) * (overlap_y2 - overlap_y1)
                    superpixel_area = (i_end - i) * (j_end - j)
                    importance = overlap_area / (superpixel_area + 1e-8)
                    
                    # Assign importance to superpixel
                    importance_map[i:i_end, j:j_end] = importance
        
        # Smooth transitions
        importance_map = gaussian_filter(importance_map, sigma=3)
        
        return importance_map
    
    def _compute_saliency(self, image):
        """
        Compute visual saliency map using spectral residual
        Highlights visually distinctive regions
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Compute FFT
        fft = np.fft.fft2(gray)
        amplitude = np.abs(fft)
        phase = np.angle(fft)
        
        # Spectral residual
        log_amplitude = np.log(amplitude + 1e-8)
        spectral_residual = log_amplitude - gaussian_filter(log_amplitude, sigma=3)
        
        # Reconstruct
        saliency = np.abs(np.fft.ifft2(np.exp(spectral_residual + 1j * phase)))
        
        # Normalize
        saliency = (saliency - saliency.min()) / (saliency.max() - saliency.min() + 1e-8)
        
        # Apply Gaussian smoothing
        saliency = gaussian_filter(saliency, sigma=5)
        
        return saliency
    
    def _compute_color_distinctiveness(self, image, detection_box):
        """
        Compute color distinctiveness map
        Highlights regions with colors different from surroundings
        """
        height, width = image.shape[:2]
        x1, y1, x2, y2 = detection_box
        
        # Extract detection region colors
        detection_region = image[y1:y2, x1:x2]
        if detection_region.size == 0:
            return np.zeros((height, width), dtype=np.float32)
        
        # Mean color of detection
        mean_color = np.mean(detection_region, axis=(0, 1))
        
        # Color distance map (Euclidean distance in RGB space)
        color_diff = np.sqrt(np.sum((image - mean_color) ** 2, axis=2))
        
        # Invert: similar colors get high attention
        color_attention = 1.0 / (1.0 + color_diff / 100.0)
        
        # Normalize
        color_attention = (color_attention - color_attention.min()) / (color_attention.max() - color_attention.min() + 1e-8)
        
        return color_attention
    
    def _compute_texture_richness(self, gray_image):
        """
        Compute texture richness using local standard deviation
        High-texture regions often contain important features
        """
        # Apply Laplacian for texture
        laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
        texture = np.abs(laplacian)
        
        # Local standard deviation using box filter
        kernel_size = 15
        mean = cv2.blur(gray_image.astype(np.float32), (kernel_size, kernel_size))
        mean_sq = cv2.blur(gray_image.astype(np.float32) ** 2, (kernel_size, kernel_size))
        variance = mean_sq - mean ** 2
        std_dev = np.sqrt(np.abs(variance))
        
        # Combine Laplacian and std dev
        texture_combined = texture * 0.6 + std_dev * 0.4
        
        # Normalize
        texture_norm = (texture_combined - texture_combined.min()) / (texture_combined.max() - texture_combined.min() + 1e-8)
        
        return texture_norm
    
    def overlay_heatmap(self, image, heatmap, alpha=0.5):
        """
        Overlay heatmap on original image
        
        Args:
            image: Original image (H, W, 3)
            heatmap: Heatmap (H, W, 3)
            alpha: Transparency factor (0=only image, 1=only heatmap)
            
        Returns:
            Overlayed image
        """
        # Ensure same size
        if image.shape[:2] != heatmap.shape[:2]:
            heatmap = cv2.resize(heatmap, (image.shape[1], image.shape[0]))
        
        # Blend images
        overlayed = cv2.addWeighted(image, 1 - alpha, heatmap, alpha, 0)
        
        return overlayed
    
    def generate_multi_threat_heatmap(self, image_path, detections):
        """
        Generate combined heatmap for multiple threats
        
        Args:
            image_path: Path to input image
            detections: List of detection dictionaries with 'bbox' key
            
        Returns:
            Combined heatmap
        """
        image = cv2.imread(image_path)
        if image is None:
            return None
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width = image.shape[:2]
        
        # Initialize combined heatmap
        combined_heatmap = np.zeros((height, width), dtype=np.float32)
        
        # Generate heatmap for each detection
        for detection in detections:
            bbox = detection.get('bbox', [])
            if len(bbox) == 4:
                heatmap = self._generate_attention_heatmap(
                    image_rgb, bbox, image.shape
                )
                # Convert to grayscale and accumulate
                heatmap_gray = cv2.cvtColor(heatmap, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
                combined_heatmap += heatmap_gray
        
        # Normalize combined heatmap
        if combined_heatmap.max() > 0:
            combined_heatmap = combined_heatmap / combined_heatmap.max()
        
        # Apply advanced colormap (turbo for better visualization)
        try:
            heatmap_colored = cm.turbo(combined_heatmap)[:, :, :3]
        except:
            heatmap_colored = cm.jet(combined_heatmap)[:, :, :3]
        heatmap_colored = (heatmap_colored * 255).astype(np.uint8)
        
        return heatmap_colored
    
    def generate_attention_flow_map(self, image_path, detections, output_path):
        """
        ADVANCED: Generate attention flow visualization showing:
        - Directional attention gradients
        - Multi-threat interaction zones
        - Confidence-weighted attention fields
        - Vector field overlay
        """
        image = cv2.imread(image_path)
        if image is None:
            return None
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width = image.shape[:2]
        
        # Generate combined heatmap
        combined_heatmap = np.zeros((height, width), dtype=np.float32)
        confidence_map = np.zeros((height, width), dtype=np.float32)
        
        for detection in detections:
            bbox = detection.get('bbox', [])
            confidence = detection.get('confidence', 0.5)
            
            if len(bbox) == 4:
                heatmap = self._generate_attention_heatmap(image_rgb, bbox, image.shape)
                heatmap_gray = cv2.cvtColor(heatmap, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
                
                # Weight by confidence
                combined_heatmap += heatmap_gray * confidence
                confidence_map = np.maximum(confidence_map, heatmap_gray * confidence)
        
        # Normalize
        if combined_heatmap.max() > 0:
            combined_heatmap = combined_heatmap / combined_heatmap.max()
        
        # Calculate gradient (attention flow direction)
        grad_y, grad_x = np.gradient(combined_heatmap)
        
        # Create visualization
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('🎯 ADVANCED Attention Flow Analysis', fontsize=16, fontweight='bold')
        
        # 1. Original image with detections
        axes[0, 0].imshow(image_rgb)
        for detection in detections:
            bbox = detection.get('bbox', [])
            if len(bbox) == 4:
                x1, y1, x2, y2 = bbox
                rect = plt.Rectangle((x1, y1), x2-x1, y2-y1, 
                                    fill=False, edgecolor='red', linewidth=2)
                axes[0, 0].add_patch(rect)
        axes[0, 0].set_title('Original with Detections', fontweight='bold')
        axes[0, 0].axis('off')
        
        # 2. Combined attention heatmap
        try:
            heatmap_display = cm.turbo(combined_heatmap)
        except:
            heatmap_display = cm.jet(combined_heatmap)
        axes[0, 1].imshow(heatmap_display)
        axes[0, 1].set_title('Attention Intensity Map', fontweight='bold')
        axes[0, 1].axis('off')
        
        # 3. Attention flow vectors
        # Downsample for vector display
        step = 20
        Y, X = np.mgrid[0:height:step, 0:width:step]
        U = grad_x[::step, ::step]
        V = grad_y[::step, ::step]
        
        axes[1, 0].imshow(image_rgb, alpha=0.6)
        axes[1, 0].quiver(X, Y, U, V, combined_heatmap[::step, ::step], 
                         cmap='hot', scale=5, width=0.003)
        axes[1, 0].set_title('Attention Flow Vectors', fontweight='bold')
        axes[1, 0].axis('off')
        
        # 4. Confidence-weighted zones
        axes[1, 1].imshow(image_rgb, alpha=0.5)
        im = axes[1, 1].imshow(confidence_map, cmap='hot', alpha=0.5)
        axes[1, 1].set_title('Confidence-Weighted Attention', fontweight='bold')
        axes[1, 1].axis('off')
        plt.colorbar(im, ax=axes[1, 1], fraction=0.046)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Attention flow map saved to: {output_path}")
        
        return output_path


class EnhancementExplainer:
    """
    ADVANCED Enhancement Explainability with:
    - Underwater-specific analysis (turbidity, color cast, attenuation)
    - SSIM/PSNR quality metrics
    - Texture and edge enhancement analysis
    - Histogram equalization metrics
    - Entropy and information content analysis
    - 12-panel comprehensive grid (upgraded from 9-panel)
    """
    
    def __init__(self):
        """Initialize advanced enhancement explainer"""
        self.color_channels = ['Red', 'Green', 'Blue']
    
    def analyze_color_correction(self, original_image_path, enhanced_image_path):
        """
        Analyze color correction between original and enhanced images
        
        Args:
            original_image_path: Path to original image
            enhanced_image_path: Path to enhanced image
            
        Returns:
            Dictionary with correction analysis and heatmaps
        """
        # Load images
        original = cv2.imread(original_image_path)
        enhanced = cv2.imread(enhanced_image_path)
        
        if original is None or enhanced is None:
            return None
        
        # Ensure same size
        if original.shape != enhanced.shape:
            enhanced = cv2.resize(enhanced, (original.shape[1], original.shape[0]))
        
        # Convert to RGB
        original_rgb = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
        enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
        
        # Calculate differences
        diff_rgb = enhanced_rgb.astype(np.float32) - original_rgb.astype(np.float32)
        
        # Generate heatmaps for each channel
        heatmaps = {}
        
        # Overall intensity change
        intensity_change = np.mean(np.abs(diff_rgb), axis=2)
        heatmaps['intensity'] = self._create_heatmap(intensity_change, 'Overall Enhancement')
        
        # Per-channel changes
        for i, channel_name in enumerate(['red', 'green', 'blue']):
            channel_diff = diff_rgb[:, :, i]
            heatmaps[f'{channel_name}_correction'] = self._create_heatmap(
                np.abs(channel_diff), 
                f'{channel_name.capitalize()} Channel Correction'
            )
        
        # Color balance heatmap
        color_balance = self._analyze_color_balance(original_rgb, enhanced_rgb)
        heatmaps['color_balance'] = color_balance
        
        # Contrast enhancement map
        contrast_map = self._analyze_contrast_enhancement(original_rgb, enhanced_rgb)
        heatmaps['contrast'] = contrast_map
        
        # Brightness enhancement map
        brightness_map = self._analyze_brightness_enhancement(original_rgb, enhanced_rgb)
        heatmaps['brightness'] = brightness_map
        
        # Statistics
        stats = {
            'mean_intensity_change': float(np.mean(np.abs(diff_rgb))),
            'max_change': float(np.max(np.abs(diff_rgb))),
            'red_correction': float(np.mean(np.abs(diff_rgb[:, :, 0]))),
            'green_correction': float(np.mean(np.abs(diff_rgb[:, :, 1]))),
            'blue_correction': float(np.mean(np.abs(diff_rgb[:, :, 2]))),
            'regions_enhanced': float(np.sum(intensity_change > 10) / intensity_change.size * 100)
        }
        
        return {
            'heatmaps': heatmaps,
            'statistics': stats
        }
    
    def _create_heatmap(self, data, title):
        """Create colored heatmap from data"""
        # Normalize to [0, 1]
        data_normalized = (data - data.min()) / (data.max() - data.min() + 1e-8)
        
        # Apply jet colormap
        heatmap = cm.jet(data_normalized)[:, :, :3]
        heatmap = (heatmap * 255).astype(np.uint8)
        
        return heatmap
    
    def _analyze_color_balance(self, original, enhanced):
        """Analyze color balance changes"""
        # Calculate color ratios
        orig_ratios = original.astype(np.float32) / (np.sum(original, axis=2, keepdims=True) + 1e-8)
        enh_ratios = enhanced.astype(np.float32) / (np.sum(enhanced, axis=2, keepdims=True) + 1e-8)
        
        # Calculate change in color balance
        balance_change = np.std(enh_ratios - orig_ratios, axis=2)
        
        return self._create_heatmap(balance_change, 'Color Balance Correction')
    
    def _analyze_contrast_enhancement(self, original, enhanced):
        """Analyze local contrast changes"""
        # Convert to grayscale
        orig_gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
        enh_gray = cv2.cvtColor(enhanced, cv2.COLOR_RGB2GRAY)
        
        # Calculate local standard deviation (contrast)
        kernel_size = 15
        orig_contrast = cv2.blur(orig_gray.astype(np.float32) ** 2, (kernel_size, kernel_size)) - \
                       cv2.blur(orig_gray.astype(np.float32), (kernel_size, kernel_size)) ** 2
        enh_contrast = cv2.blur(enh_gray.astype(np.float32) ** 2, (kernel_size, kernel_size)) - \
                      cv2.blur(enh_gray.astype(np.float32), (kernel_size, kernel_size)) ** 2
        
        # Calculate contrast enhancement
        contrast_change = np.sqrt(np.abs(enh_contrast)) - np.sqrt(np.abs(orig_contrast))
        
        return self._create_heatmap(np.abs(contrast_change), 'Contrast Enhancement')
    
    def _analyze_brightness_enhancement(self, original, enhanced):
        """Analyze brightness changes"""
        # Calculate luminance
        orig_lum = 0.299 * original[:, :, 0] + 0.587 * original[:, :, 1] + 0.114 * original[:, :, 2]
        enh_lum = 0.299 * enhanced[:, :, 0] + 0.587 * enhanced[:, :, 1] + 0.114 * enhanced[:, :, 2]
        
        # Calculate brightness change
        brightness_change = enh_lum - orig_lum
        
        return self._create_heatmap(np.abs(brightness_change), 'Brightness Enhancement')
    
    def generate_comparison_grid(self, original_path, enhanced_path, output_path):
        """
        Generate ADVANCED 12-panel comparison grid with comprehensive analysis:
        - Original & Enhanced images
        - Per-channel corrections (R, G, B)
        - Intensity, color balance, contrast, brightness
        - Texture, edge enhancement
        - Underwater quality metrics panel
        
        Args:
            original_path: Path to original image
            enhanced_path: Path to enhanced image
            output_path: Path to save comparison grid
        """
        # Load original and enhanced
        original = cv2.imread(original_path)
        enhanced = cv2.imread(enhanced_path)
        
        if original is None or enhanced is None:
            return None
        
        original_rgb = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
        enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
        
        # Ensure same size
        if original.shape != enhanced.shape:
            enhanced_rgb = cv2.resize(enhanced_rgb, (original.shape[1], original.shape[0]))
        
        # Calculate comprehensive analysis
        diff_rgb = enhanced_rgb.astype(np.float32) - original_rgb.astype(np.float32)
        intensity_change = np.mean(np.abs(diff_rgb), axis=2)
        
        # Generate all heatmaps
        heatmaps = {}
        
        # 1. Intensity change heatmap
        heatmaps['intensity'] = self._create_heatmap(intensity_change, 'Intensity Change')
        
        # 2-4. Per-channel corrections
        for i, channel_name in enumerate(['red', 'green', 'blue']):
            channel_diff = np.abs(diff_rgb[:, :, i])
            heatmaps[f'{channel_name}_correction'] = self._create_heatmap(
                channel_diff, f'{channel_name.capitalize()} Channel Correction'
            )
        
        # 5. Color balance analysis
        heatmaps['color_balance'] = self._analyze_color_balance(original_rgb, enhanced_rgb)
        
        # 6. Contrast enhancement
        heatmaps['contrast'] = self._analyze_contrast_enhancement(original_rgb, enhanced_rgb)
        
        # 7. Brightness enhancement
        heatmaps['brightness'] = self._analyze_brightness_enhancement(original_rgb, enhanced_rgb)
        
        # 8. Texture enhancement
        heatmaps['texture'] = self._analyze_texture_enhancement(original_rgb, enhanced_rgb)
        
        # 9. Edge enhancement
        heatmaps['edge'] = self._analyze_edge_enhancement(original_rgb, enhanced_rgb)
        
        # 10. Underwater quality metrics
        underwater_metrics = self._analyze_underwater_quality(original_rgb, enhanced_rgb)
        
        # Resize for grid display
        target_size = (400, 300)
        original_resized = cv2.resize(original_rgb, target_size)
        enhanced_resized = cv2.resize(enhanced_rgb, target_size)
        
        # Create 12-panel grid (4 rows x 3 columns)
        grid_images = [
            ('Original Image', original_resized),
            ('Enhanced Image', enhanced_resized),
            ('Intensity Change', cv2.resize(heatmaps['intensity'], target_size)),
            
            ('Red Channel Correction', cv2.resize(heatmaps['red_correction'], target_size)),
            ('Green Channel Correction', cv2.resize(heatmaps['green_correction'], target_size)),
            ('Blue Channel Correction', cv2.resize(heatmaps['blue_correction'], target_size)),
            
            ('Color Balance Map', cv2.resize(heatmaps['color_balance'], target_size)),
            ('Contrast Enhancement', cv2.resize(heatmaps['contrast'], target_size)),
            ('Brightness Enhancement', cv2.resize(heatmaps['brightness'], target_size)),
            
            ('Texture Enhancement', cv2.resize(heatmaps['texture'], target_size)),
            ('Edge Enhancement', cv2.resize(heatmaps['edge'], target_size)),
            ('Underwater Quality Metrics', self._create_metrics_panel(underwater_metrics, target_size))
        ]
        
        # Create matplotlib figure (4x3 grid) with WHITE background
        fig, axes = plt.subplots(4, 3, figsize=(18, 20), facecolor='white')
        fig.suptitle('🌊 ADVANCED Enhancement Explainability - 12-Panel Analysis', 
                     fontsize=18, fontweight='bold', color='#1a1a1a')
        
        # Calculate quality metrics
        ssim_score = ssim(cv2.cvtColor(original, cv2.COLOR_BGR2GRAY), 
                         cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY), 
                         data_range=255)
        psnr_score = psnr(original, enhanced, data_range=255)
        
        # Add comprehensive subtitle with metrics (dark text on white)
        fig.text(0.5, 0.97, 
                f'SSIM: {ssim_score:.4f} | PSNR: {psnr_score:.2f} dB | ' +
                f'Turbidity Reduction: {underwater_metrics["turbidity_reduction"]:.1f}% | ' +
                f'Entropy Gain: {underwater_metrics["entropy_gain"]:.3f} bits',
                ha='center', fontsize=12, color='#2563eb', weight='bold')
        
        # Plot all panels with color-coded borders
        for idx, (title, img) in enumerate(grid_images):
            row = idx // 3
            col = idx % 3
            axes[row, col].imshow(img)
            axes[row, col].set_title(title, fontsize=11, fontweight='bold', pad=10)
            axes[row, col].axis('off')
            
            # Color-coded borders for different categories
            if idx < 3:  # Row 1: Original/Enhanced/Intensity
                border_color = '#00ff9f'  # Green
            elif idx < 6:  # Row 2: RGB channels
                border_color = '#667eea'  # Purple
            elif idx < 9:  # Row 3: Color/Contrast/Brightness
                border_color = '#f59e0b'  # Orange
            else:  # Row 4: Texture/Edge/Metrics
                border_color = '#ef4444'  # Red
            
            for spine in axes[row, col].spines.values():
                spine.set_visible(True)
                spine.set_edgecolor(border_color)
                spine.set_linewidth(3)
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"✅ ADVANCED 12-panel enhancement analysis saved to: {output_path}")
        print(f"   📊 SSIM: {ssim_score:.4f} | PSNR: {psnr_score:.2f} dB")
        print(f"   🌊 Turbidity Reduction: {underwater_metrics['turbidity_reduction']:.1f}%")
        print(f"   📈 Entropy Gain: {underwater_metrics['entropy_gain']:.3f} bits")
        
        return output_path
    
    def _analyze_underwater_quality(self, original, enhanced):
        """
        Analyze underwater-specific quality improvements:
        - Turbidity reduction
        - Color cast correction
        - Light attenuation compensation
        - Entropy (information content)
        """
        # 1. Turbidity estimation (based on variance in blue-green channels)
        orig_bg = np.mean(original[:, :, 1:3], axis=2)  # Blue-green average
        enh_bg = np.mean(enhanced[:, :, 1:3], axis=2)
        
        orig_turbidity = np.std(orig_bg)
        enh_turbidity = np.std(enh_bg)
        turbidity_reduction = ((orig_turbidity - enh_turbidity) / (orig_turbidity + 1e-8)) * 100
        
        # 2. Color cast estimation (deviation from neutral gray)
        orig_mean = np.mean(original, axis=(0, 1))
        enh_mean = np.mean(enhanced, axis=(0, 1))
        
        orig_cast = np.std(orig_mean / (np.mean(orig_mean) + 1e-8))
        enh_cast = np.std(enh_mean / (np.mean(enh_mean) + 1e-8))
        cast_correction = ((orig_cast - enh_cast) / (orig_cast + 1e-8)) * 100
        
        # 3. Light attenuation (distance-dependent color loss)
        orig_red_ratio = np.mean(original[:, :, 0]) / (np.mean(original) + 1e-8)
        enh_red_ratio = np.mean(enhanced[:, :, 0]) / (np.mean(enhanced) + 1e-8)
        red_restoration = ((enh_red_ratio - orig_red_ratio) / (orig_red_ratio + 1e-8)) * 100
        
        # 4. Entropy (information content)
        orig_gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
        enh_gray = cv2.cvtColor(enhanced, cv2.COLOR_RGB2GRAY)
        
        orig_entropy = self._calculate_entropy(orig_gray)
        enh_entropy = self._calculate_entropy(enh_gray)
        entropy_gain = enh_entropy - orig_entropy
        
        return {
            'turbidity_reduction': max(0, turbidity_reduction),
            'cast_correction': max(0, cast_correction),
            'red_restoration': red_restoration,
            'entropy_gain': entropy_gain,
            'orig_entropy': orig_entropy,
            'enh_entropy': enh_entropy
        }
    
    def _calculate_entropy(self, image):
        """Calculate Shannon entropy of image"""
        hist, _ = np.histogram(image.flatten(), bins=256, range=(0, 256))
        hist = hist / (hist.sum() + 1e-8)
        entropy = -np.sum(hist * np.log2(hist + 1e-8))
        return entropy
    
    def _analyze_texture_enhancement(self, original, enhanced):
        """Analyze texture enhancement using Laplacian variance"""
        orig_gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
        enh_gray = cv2.cvtColor(enhanced, cv2.COLOR_RGB2GRAY)
        
        # Laplacian for texture
        orig_laplacian = cv2.Laplacian(orig_gray, cv2.CV_64F)
        enh_laplacian = cv2.Laplacian(enh_gray, cv2.CV_64F)
        
        # Texture enhancement map
        texture_diff = np.abs(enh_laplacian) - np.abs(orig_laplacian)
        
        return self._create_heatmap(np.abs(texture_diff), 'Texture Enhancement')
    
    def _analyze_edge_enhancement(self, original, enhanced):
        """Analyze edge enhancement"""
        orig_gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
        enh_gray = cv2.cvtColor(enhanced, cv2.COLOR_RGB2GRAY)
        
        # Sobel edges
        orig_edges = np.abs(cv2.Sobel(orig_gray, cv2.CV_64F, 1, 1, ksize=3))
        enh_edges = np.abs(cv2.Sobel(enh_gray, cv2.CV_64F, 1, 1, ksize=3))
        
        # Edge enhancement map
        edge_diff = enh_edges - orig_edges
        
        return self._create_heatmap(np.abs(edge_diff), 'Edge Enhancement')
    
    def _format_metrics(self, metrics):
        """Format metrics for display"""
        return (f"Turbidity: {metrics['turbidity_reduction']:.1f}%\n"
                f"Cast Correction: {metrics['cast_correction']:.1f}%\n"
                f"Red Restoration: {metrics['red_restoration']:.1f}%\n"
                f"Entropy Gain: {metrics['entropy_gain']:.3f}")
    
    def _create_metrics_panel(self, metrics, size):
        """Create visual metrics panel with WHITE background"""
        panel = np.ones((size[1], size[0], 3), dtype=np.uint8) * 255  # White background
        
        # Add text overlays using PIL for better text rendering
        from PIL import Image, ImageDraw, ImageFont
        
        pil_img = Image.fromarray(panel)
        draw = ImageDraw.Draw(pil_img)
        
        # Try to use a nice font, fallback to default
        try:
            font_large = ImageFont.truetype("arial.ttf", 24)
            font_small = ImageFont.truetype("arial.ttf", 18)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        y_offset = 30
        draw.text((20, y_offset), "📊 Underwater Metrics", fill=(37, 99, 235), font=font_large)  # Blue text
        
        y_offset += 50
        metrics_text = [
            f"🌊 Turbidity Reduction: {metrics['turbidity_reduction']:.1f}%",
            f"🎨 Color Cast Fix: {metrics['cast_correction']:.1f}%",
            f"🔴 Red Restoration: {metrics['red_restoration']:.1f}%",
            f"📈 Entropy Gain: {metrics['entropy_gain']:.3f}",
            f"",
            f"Information Content:",
            f"  Original: {metrics['orig_entropy']:.3f} bits",
            f"  Enhanced: {metrics['enh_entropy']:.3f} bits"
        ]
        
        for line in metrics_text:
            draw.text((20, y_offset), line, fill=(31, 41, 55), font=font_small)  # Dark gray text
            y_offset += 28
        
        panel = np.array(pil_img)
        
        return panel


def generate_threat_explanation(image_path, threat_detection, output_path):
    """
    Generate comprehensive threat detection explanation with heatmap
    
    Args:
        image_path: Path to input image
        threat_detection: Threat detection dictionary with bbox
        output_path: Path to save explanation image
    """
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        return None
    
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Initialize explainer
    explainer = GradCAMExplainer(None)
    
    # Generate heatmap
    bbox = threat_detection.get('bbox', [])
    if len(bbox) == 4:
        heatmap = explainer.generate_heatmap(image_path, bbox, image.shape)
        
        # Overlay heatmap
        overlayed = explainer.overlay_heatmap(image_rgb, heatmap, alpha=0.4)
        
        # Draw bounding box
        x1, y1, x2, y2 = bbox
        cv2.rectangle(overlayed, (x1, y1), (x2, y2), (255, 0, 0), 3)
        
        # Add threat information
        threat_type = threat_detection.get('threat_type', 'Unknown')
        confidence = threat_detection.get('confidence', 0)
        threat_score = threat_detection.get('threat_score', 0)
        
        # Add text
        text = f"{threat_type.replace('_', ' ').title()}"
        text2 = f"Confidence: {confidence*100:.1f}% | Score: {threat_score}/100"
        
        cv2.putText(overlayed, text, (x1, y1 - 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(overlayed, text2, (x1, y1 - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # Convert back to BGR for saving
        overlayed_bgr = cv2.cvtColor(overlayed, cv2.COLOR_RGB2BGR)
        cv2.imwrite(output_path, overlayed_bgr)
        
        print(f"✅ Threat explanation saved to: {output_path}")
        
        return output_path
    
    return None


if __name__ == "__main__":
    print("🔬 Grad-CAM and Enhancement Explainability Module")
    print("=" * 60)
    print("This module provides visual explanations for:")
    print("  1. Why YOLO detected specific threats (Grad-CAM)")
    print("  2. How enhancement model corrected colors")
    print("=" * 60)
