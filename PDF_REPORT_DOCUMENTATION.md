# DRDO PDF Report Generation - Implementation Guide

## Overview
This document describes the formal PDF report generation feature for the Aqua Sentinel underwater threat detection system. The reports are designed for Defence Research and Development Organisation (DRDO) with military-grade formatting and comprehensive threat intelligence analysis.

## Features

### PDF Report Contents

#### Section A: Operational Metadata
- Mission timestamp (IST)
- GPS coordinates (simulated)
- Camera deployment depth
- Water turbidity score (0-10 scale)
- Visibility conditions
- Water temperature
- Current speed

#### Section B: Threat Intelligence Analysis
- Total threat count and severity
- Individual threat details:
  - Object type classification
  - AI confidence level
  - Distance from camera (meters)
  - Risk assessment score (0-10)
  - Priority level (LOW/MEDIUM/HIGH/CRITICAL)
  - Detection method (YOLOv8-X)
  - Bounding box coordinates

#### Section C: Visual Intelligence Report
1. **Image Enhancement Analysis**
   - Before-after comparison
   - Quality improvement metrics

2. **Threat Detection Overlay**
   - Annotated image with bounding boxes
   - Distance measurements

3. **AI Explainability - Grad-CAM**
   - Multi-scale heatmap visualization
   - Model attention regions
   - 6-component analysis (edges, superpixels, saliency, color, texture)

4. **12-Panel Enhancement Grid**
   - Comprehensive analysis across multiple dimensions
   - Intensity, RGB channels, color balance, contrast, brightness
   - Texture preservation, edge definition
   - Underwater quality metrics

5. **Quality Metrics Table**
   - PSNR (Peak Signal-to-Noise Ratio)
   - SSIM (Structural Similarity Index)
   - UIQM (Underwater Image Quality Measure)
   - Turbidity reduction percentage
   - Entropy gain (information recovery)

#### Section D: Mission Summary and Recommendations
- Mission summary narrative
- Recommended operator actions
- Severity rating with color-coded badge
- Report completion status

### Professional Formatting

#### Header
- Government of India logo (left)
- Indian Navy logo (right)
- DRDO organization name
- System identifier: "Aqua Sentinel"
- Horizontal separator line

#### Footer
- Classification marking: "RESTRICTED - For Official Use Only" (red text)
- Generation timestamp with IST timezone
- Page numbers
- Horizontal separator line

#### Styling
- Military-grade formal language
- **NO EMOJIS** (professional report)
- Blue accent colors (#2563eb)
- Structured tables with alternating row colors
- High-quality images at 200 DPI
- Letter size (8.5" x 11") pages

## Technical Implementation

### Files Modified/Created

1. **webapp/pdf_report_generator.py** (NEW)
   - `FormalPDFReportGenerator` class
   - `DRDOReportCanvas` custom canvas for headers/footers
   - Professional paragraph styles
   - Multi-section report builder

2. **webapp/app.py** (MODIFIED)
   - Added imports: `FormalPDFReportGenerator`, `datetime`, `random`
   - New route: `/generate_pdf_report` (POST)
   - New route: `/download_pdf_report/<filename>` (GET)
   - Metadata simulation for demonstration

3. **webapp/templates/index.html** (MODIFIED)
   - Added "Generate DRDO PDF Report" button
   - JavaScript function: `generateDRDOPDFReport()`
   - Auto-download functionality
   - Button state management

4. **installation/requirements.txt** (MODIFIED)
   - Added: `reportlab>=3.6.0`

### Dependencies
- **reportlab**: PDF generation library
  - Canvas for low-level drawing
  - Platypus for high-level document structure
  - Tables, paragraphs, images
  - Custom styling support

### Logo Assets
Location: `webapp/photos/`
- `government-of-india.jpg` - Government of India logo
- `navy logo.png` - Indian Navy logo
- `gov logo.png` - Additional government logo

## Usage Guide

### For End Users

1. **Upload and Process Image**
   - Upload underwater image through web interface
   - Enable "Enhance First" option
   - Run threat detection

2. **Generate PDF Report**
   - After threat detection completes
   - Click "🛡️ Generate DRDO PDF Report" button
   - Wait for processing (3-5 seconds)
   - PDF automatically downloads

3. **Review Report**
   - Open PDF with any PDF viewer
   - Verify all sections are complete
   - Check explainability images
   - Review threat assessments

### For Developers

#### API Endpoint Usage

```javascript
// POST /generate_pdf_report
{
    "unique_id": "20251127_143000_abc123",
    "threats": [
        {
            "class": "submarine",
            "confidence": 0.92,
            "distance": {"distance_m": 150.5},
            "risk_score": 8,
            "priority": "HIGH",
            "detection_method": "YOLOv8-X Deep Learning",
            "bbox": [100, 200, 300, 400]
        }
    ],
    "metrics": {
        "psnr": 28.5,
        "ssim": 0.89,
        "uiqm": 2.85,
        "turbidity_reduction": 65.3,
        "entropy_gain": 0.245
    }
}

// Response
{
    "success": true,
    "pdf_filename": "20251127_143000_abc123_DRDO_ThreatReport.pdf",
    "message": "PDF report generated successfully"
}
```

#### Testing PDF Generation

Run the test script:
```bash
python test_pdf_generation.py
```

This generates a sample PDF: `TEST_DRDO_Report.pdf`

### Customization

#### Modifying Report Sections

Edit `webapp/pdf_report_generator.py`:

1. **Add new metadata fields**:
   ```python
   def _create_metadata_section(self, metadata):
       # Add your custom fields
       params_text = f"""
       ...
       <b>Your Custom Field:</b> {metadata.get('custom_field', 'N/A')}<br/>
       """
   ```

2. **Customize threat assessment**:
   ```python
   def _create_threat_details_section(self, threats):
       # Modify threat_info table
       threat_info = [
           ['Your Field:', threat.get('your_field', 'N/A')],
           ...
       ]
   ```

3. **Change styling**:
   ```python
   def _create_styles(self):
       # Modify colors, fonts, spacing
       styles.add(ParagraphStyle(
           name='YourStyle',
           fontSize=12,
           textColor=HexColor('#yourcolor'),
           ...
       ))
   ```

#### Updating Logos

Replace files in `webapp/photos/`:
- Recommended size: 600x600 pixels
- Supported formats: PNG, JPG
- Transparent backgrounds work best

Update logo paths in `DRDOReportCanvas._draw_header_footer()`:
```python
gov_logo = os.path.join(self.logo_path, "your-logo-file.png")
```

## Troubleshooting

### Common Issues

1. **"Style 'BodyText' already defined"**
   - Fixed: Use `FormalBodyText` instead
   - Avoid conflicts with ReportLab default styles

2. **Images not appearing in PDF**
   - Check file paths exist
   - Verify image file formats (JPG, PNG)
   - Ensure images are not corrupted

3. **Logos not displaying**
   - Verify files exist in `webapp/photos/`
   - Check file permissions
   - Try different image formats

4. **PDF generation fails**
   - Check reportlab installation: `pip install reportlab`
   - Verify disk space available
   - Check write permissions in `results/` folder

### Debug Mode

Enable detailed logging in `webapp/app.py`:
```python
print(f"Generating PDF with data: {report_data}")
pdf_generator.generate_report(pdf_path, report_data)
print(f"PDF saved to: {pdf_path}")
```

## Security Considerations

1. **Classification Markings**
   - Default: "RESTRICTED - For Official Use Only"
   - Modify in `DRDOReportCanvas._draw_header_footer()`

2. **Data Sanitization**
   - User inputs are sanitized in Flask routes
   - File paths validated before access

3. **Access Control**
   - Implement authentication for PDF download routes
   - Consider adding digital signatures

## Performance

- **Generation Time**: 2-4 seconds per report
- **File Size**: 400-600 KB (typical)
- **Concurrent Requests**: Limited by Flask (use production WSGI server)

## Future Enhancements

1. **Digital Signatures**
   - Add cryptographic signatures to PDFs
   - Verify report authenticity

2. **Real Sensor Data**
   - Replace simulated GPS/depth with actual sensor inputs
   - Integrate with underwater vehicle telemetry

3. **Batch Processing**
   - Generate reports for multiple images
   - Mission summary reports

4. **Export Formats**
   - Add DOCX export option
   - HTML report generation

## References

- ReportLab Documentation: https://www.reportlab.com/docs/
- DRDO Official: https://www.drdo.gov.in/
- YOLOv8 Documentation: https://docs.ultralytics.com/

## Support

For issues or questions:
1. Check this documentation
2. Review test_pdf_generation.py for examples
3. Examine webapp/pdf_report_generator.py code
4. Contact system administrator

---

**Document Version**: 1.0  
**Last Updated**: 27 November 2025  
**Classification**: UNCLASSIFIED
