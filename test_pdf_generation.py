"""
Test script for DRDO PDF Report Generation
This script tests the PDF generation functionality with sample data
"""

import sys
import os

# Add webapp directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'webapp'))

from pdf_report_generator import FormalPDFReportGenerator

# Sample test data
test_data = {
    'metadata': {
        'report_id': 'TEST_001_2025',
        'timestamp': '27 November 2025, 14:30:00 IST',
        'gps_coords': '19.0760°N, 72.8777°E',
        'depth_m': 45,
        'turbidity_score': 6.8,
        'visibility': 'Moderate',
        'water_temp': 24.5,
        'current_speed': 1.8
    },
    'threats': [
        {
            'class': 'submarine',
            'confidence': 0.92,
            'distance': {'distance_m': 150.5},
            'risk_score': 8,
            'priority': 'HIGH',
            'detection_method': 'YOLOv8-X Deep Learning',
            'bbox': [100, 200, 300, 400]
        },
        {
            'class': 'boat',
            'confidence': 0.87,
            'distance': {'distance_m': 85.2},
            'risk_score': 6,
            'priority': 'MEDIUM',
            'detection_method': 'YOLOv8-X Deep Learning',
            'bbox': [400, 150, 600, 350]
        }
    ],
    'images': {
        'before_after': 'webapp/results/test_quad_comparison.jpg',
        'threat_detection': 'webapp/results/test_distance_visualization.jpg',
        'gradcam': 'webapp/results/test_gradcam_heatmap.jpg',
        'attention_flow': 'webapp/results/test_attention_flow.png',
        'enhancement_grid': 'webapp/results/test_enhancement_analysis.png'
    },
    'metrics': {
        'psnr': 28.5,
        'ssim': 0.89,
        'uiqm': 2.85,
        'turbidity_reduction': 65.3,
        'entropy_gain': 0.245
    },
    'summary': {
        'mission_summary': 'Underwater surveillance operation conducted at depth 45 meters. AI-enhanced image processing detected 2 potential threats in the operational area.',
        'recommended_actions': [
            'Maintain continuous surveillance of detected threat locations',
            'Verify threat classification with secondary sensors',
            'Report findings to naval operations command center'
        ],
        'severity_rating': 'HIGH'
    }
}

# Test PDF generation
print("Testing DRDO PDF Report Generation...")
print("=" * 60)

try:
    logo_folder = os.path.join(os.path.dirname(__file__), 'webapp', 'photos')
    pdf_generator = FormalPDFReportGenerator(logo_folder_path=logo_folder)
    
    output_path = os.path.join(os.path.dirname(__file__), 'TEST_DRDO_Report.pdf')
    
    pdf_generator.generate_report(output_path, test_data)
    
    print(f"SUCCESS: PDF report generated at: {output_path}")
    print(f"File size: {os.path.getsize(output_path) / 1024:.2f} KB")
    print("\nVerification:")
    print(f"  - File exists: {os.path.exists(output_path)}")
    print(f"  - Is PDF: {output_path.endswith('.pdf')}")
    print("\nOpen the PDF to verify:")
    print(f"  - DRDO header with logos")
    print(f"  - All 4 sections (A-D)")
    print(f"  - Formal language (no emojis)")
    print(f"  - Footer with classification")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
