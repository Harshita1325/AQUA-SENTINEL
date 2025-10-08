"""
Threat Visualization Module
Draws bounding boxes, circles, and labels for detected threats
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

class ThreatVisualizer:
    """
    Visualize detected threats on underwater images
    """
    
    # Color scheme for different risk levels (BGR format for OpenCV)
    COLORS = {
        'HIGH': (0, 0, 255),      # Red
        'MEDIUM': (0, 165, 255),  # Orange
        'LOW': (0, 255, 255)      # Yellow
    }
    
    # Risk level symbols
    SYMBOLS = {
        'HIGH': '🔴',
        'MEDIUM': '🟠',
        'LOW': '🟡'
    }
    
    def __init__(self, circle_thickness=3, box_thickness=2):
        """
        Initialize visualizer
        
        Args:
            circle_thickness: Thickness of circle outline
            box_thickness: Thickness of bounding box
        """
        self.circle_thickness = circle_thickness
        self.box_thickness = box_thickness
    
    def draw_threat_circle(self, image, threat, radius_multiplier=1.2):
        """
        Draw red circle around detected threat
        
        Args:
            image: OpenCV image (BGR)
            threat: Threat detection dictionary
            radius_multiplier: Scale factor for circle size
            
        Returns:
            Modified image
        """
        center = threat['center']
        bbox = threat['bbox']
        risk_level = threat['risk_level']
        
        # Calculate circle radius based on bounding box
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        radius = int(max(width, height) * radius_multiplier / 2)
        
        # Get color based on risk level
        color = self.COLORS.get(risk_level, (0, 0, 255))
        
        # Draw circle
        cv2.circle(
            image, 
            center, 
            radius, 
            color, 
            self.circle_thickness
        )
        
        # Draw crosshair at center
        crosshair_size = 10
        cv2.line(
            image,
            (center[0] - crosshair_size, center[1]),
            (center[0] + crosshair_size, center[1]),
            color,
            2
        )
        cv2.line(
            image,
            (center[0], center[1] - crosshair_size),
            (center[0], center[1] + crosshair_size),
            color,
            2
        )
        
        return image
    
    def draw_bounding_box(self, image, threat):
        """
        Draw bounding box around threat
        
        Args:
            image: OpenCV image (BGR)
            threat: Threat detection dictionary
            
        Returns:
            Modified image
        """
        bbox = threat['bbox']
        risk_level = threat['risk_level']
        color = self.COLORS.get(risk_level, (0, 0, 255))
        
        # Draw rectangle
        cv2.rectangle(
            image,
            (bbox[0], bbox[1]),
            (bbox[2], bbox[3]),
            color,
            self.box_thickness
        )
        
        return image
    
    def draw_label(self, image, threat):
        """
        Draw label with threat type and confidence (NO distance on image)
        
        Args:
            image: OpenCV image (BGR)
            threat: Threat detection dictionary
            
        Returns:
            Modified image
        """
        bbox = threat['bbox']
        threat_type = threat['threat_type'].replace('_', ' ').title()
        confidence = threat['confidence']
        risk_level = threat['risk_level']
        color = self.COLORS.get(risk_level, (0, 0, 255))
        
        # Create label text WITHOUT distance (distance shown in UI card only)
        label = f"{threat_type} {confidence:.0%}"
        
        risk_label = f"[{risk_level}]"
        
        # Calculate label position (above bounding box)
        label_x = bbox[0]
        label_y = bbox[1] - 10
        
        # Ensure label stays within image bounds
        if label_y < 20:
            label_y = bbox[3] + 20
        
        # Get text size
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        font_thickness = 2
        
        (label_width, label_height), baseline = cv2.getTextSize(
            label, font, font_scale, font_thickness
        )
        
        # Draw background rectangle for label
        cv2.rectangle(
            image,
            (label_x, label_y - label_height - 5),
            (label_x + label_width + 10, label_y + 5),
            color,
            -1  # Filled
        )
        
        # Draw label text
        cv2.putText(
            image,
            label,
            (label_x + 5, label_y),
            font,
            font_scale,
            (255, 255, 255),  # White text
            font_thickness,
            cv2.LINE_AA
        )
        
        # Draw risk level badge
        risk_x = label_x + label_width + 15
        cv2.rectangle(
            image,
            (risk_x, label_y - label_height - 5),
            (risk_x + len(risk_label) * 10, label_y + 5),
            color,
            -1
        )
        cv2.putText(
            image,
            risk_label,
            (risk_x + 5, label_y),
            font,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )
        
        return image
    
    def draw_all_threats(self, image_path, threats, output_path, 
                        draw_circles=True, draw_boxes=True, draw_labels=True):
        """
        Draw all threat indicators on image
        
        Args:
            image_path: Path to input image
            threats: List of threat detections
            output_path: Path to save annotated image
            draw_circles: Draw circles around threats
            draw_boxes: Draw bounding boxes
            draw_labels: Draw labels with threat info
            
        Returns:
            Path to annotated image
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Draw each threat
        for threat in threats:
            if draw_circles:
                image = self.draw_threat_circle(image, threat)
            
            if draw_boxes:
                image = self.draw_bounding_box(image, threat)
            
            if draw_labels:
                image = self.draw_label(image, threat)
        
        # Add threat count overlay
        if threats:
            image = self.draw_threat_count(image, threats)
        
        # Save annotated image
        success = cv2.imwrite(output_path, image)
        if not success:
            raise Exception(f"Failed to save annotated image: {output_path}")
        
        print(f"💾 Saved threat visualization to: {output_path}")
        return output_path
    
    def draw_threat_count(self, image, threats):
        """
        Draw threat count summary in corner
        
        Args:
            image: OpenCV image
            threats: List of threats
            
        Returns:
            Modified image
        """
        height, width = image.shape[:2]
        
        # Count threats by risk level
        high_risk = sum(1 for t in threats if t['risk_level'] == 'HIGH')
        medium_risk = sum(1 for t in threats if t['risk_level'] == 'MEDIUM')
        low_risk = sum(1 for t in threats if t['risk_level'] == 'LOW')
        
        # Create overlay panel
        panel_width = 250
        panel_height = 120
        panel_x = width - panel_width - 20
        panel_y = 20
        
        # Semi-transparent background
        overlay = image.copy()
        cv2.rectangle(
            overlay,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (0, 0, 0),
            -1
        )
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)
        
        # Draw border
        cv2.rectangle(
            image,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (255, 255, 255),
            2
        )
        
        # Draw title
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(
            image,
            "THREATS DETECTED",
            (panel_x + 10, panel_y + 25),
            font,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )
        
        # Draw threat counts
        y_offset = 50
        
        # High risk
        cv2.circle(image, (panel_x + 20, panel_y + y_offset), 8, self.COLORS['HIGH'], -1)
        cv2.putText(
            image,
            f"High Risk: {high_risk}",
            (panel_x + 40, panel_y + y_offset + 5),
            font,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )
        
        # Medium risk
        y_offset += 25
        cv2.circle(image, (panel_x + 20, panel_y + y_offset), 8, self.COLORS['MEDIUM'], -1)
        cv2.putText(
            image,
            f"Medium Risk: {medium_risk}",
            (panel_x + 40, panel_y + y_offset + 5),
            font,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )
        
        # Low risk
        y_offset += 25
        cv2.circle(image, (panel_x + 20, panel_y + y_offset), 8, self.COLORS['LOW'], -1)
        cv2.putText(
            image,
            f"Low Risk: {low_risk}",
            (panel_x + 40, panel_y + y_offset + 5),
            font,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )
        
        return image
    
    def create_side_by_side_comparison(self, original_path, annotated_path, output_path):
        """
        Create side-by-side comparison of original and annotated images
        
        Args:
            original_path: Path to original image
            annotated_path: Path to annotated image
            output_path: Path to save comparison
            
        Returns:
            Path to comparison image
        """
        original = cv2.imread(original_path)
        annotated = cv2.imread(annotated_path)
        
        # Resize if needed to match heights
        if original.shape[0] != annotated.shape[0]:
            height = min(original.shape[0], annotated.shape[0])
            original = cv2.resize(original, (int(original.shape[1] * height / original.shape[0]), height))
            annotated = cv2.resize(annotated, (int(annotated.shape[1] * height / annotated.shape[0]), height))
        
        # Add labels
        cv2.putText(original, "ORIGINAL", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 
                    1.2, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(annotated, "THREATS DETECTED", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 
                    1.2, (0, 0, 255), 3, cv2.LINE_AA)
        
        # Concatenate horizontally
        comparison = np.hstack([original, annotated])
        
        # Save
        cv2.imwrite(output_path, comparison)
        print(f"💾 Saved comparison to: {output_path}")
        
        return output_path
