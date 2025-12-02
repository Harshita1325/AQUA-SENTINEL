"""
Formal PDF Report Generator for Defence Research and Development Organisation (DRDO)
Underwater Threat Detection and Image Enhancement System - Aqua Sentinel

This module generates comprehensive, military-grade PDF reports with:
- Official header/footer with government logos
- Mission metadata and operational parameters
- Threat intelligence analysis
- Image enhancement quality metrics

- Formal summary and recommended actions
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    PageBreak, Image, KeepTogether, Frame, PageTemplate
)
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor


class DRDOReportCanvas(canvas.Canvas):
    """Custom canvas for DRDO report with header and footer"""
    
    def __init__(self, *args, **kwargs):
        self.logo_path = kwargs.pop('logo_path', None)
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._page_count = 0
        
    def showPage(self):
        self._page_count += 1
        self._draw_header_footer()
        canvas.Canvas.showPage(self)
        
    def _draw_header_footer(self):
        """Draw header with logos and footer with classification"""
        page_width = letter[0]
        page_height = letter[1]
        
        # Header section
        self.saveState()
        self.setStrokeColor(colors.black)
        self.setLineWidth(2)
        self.line(0.5*inch, page_height - 1*inch, page_width - 0.5*inch, page_height - 1*inch)
        
        # Add government logos if available
        if self.logo_path:
            try:
                # Government of India logo (left)
                gov_logo = os.path.join(self.logo_path, "government-of-india.jpg")
                if os.path.exists(gov_logo):
                    self.drawImage(gov_logo, 0.75*inch, page_height - 0.95*inch, 
                                 width=0.6*inch, height=0.6*inch, preserveAspectRatio=True)
                
                # Navy logo (right)
                navy_logo = os.path.join(self.logo_path, "navy logo.png")
                if os.path.exists(navy_logo):
                    self.drawImage(navy_logo, page_width - 1.35*inch, page_height - 0.95*inch,
                                 width=0.6*inch, height=0.6*inch, preserveAspectRatio=True)
            except Exception as e:
                print(f"Warning: Could not load logos - {e}")
        
        # Header text
        self.setFont("Helvetica-Bold", 14)
        self.drawCentredString(page_width/2, page_height - 0.55*inch, 
                              "DEFENCE RESEARCH AND DEVELOPMENT ORGANISATION")
        self.setFont("Helvetica", 10)
        self.drawCentredString(page_width/2, page_height - 0.75*inch,
                              "Underwater Threat Detection & Enhancement System - Aqua Sentinel")
        
        # Footer section
        self.setLineWidth(1)
        self.line(0.5*inch, 0.75*inch, page_width - 0.5*inch, 0.75*inch)
        
        # Classification marking
        self.setFont("Helvetica-Bold", 9)
        self.setFillColor(colors.red)
        self.drawCentredString(page_width/2, 0.55*inch, "RESTRICTED - For Official Use Only")
        
        # Page number and timestamp
        self.setFillColor(colors.black)
        self.setFont("Helvetica", 8)
        timestamp = datetime.now().strftime("%d %B %Y, %H:%M:%S IST")
        self.drawString(0.75*inch, 0.55*inch, f"Generated: {timestamp}")
        self.drawRightString(page_width - 0.75*inch, 0.55*inch, f"Page {self._page_count}")
        
        self.restoreState()


class FormalPDFReportGenerator:
    """
    Generate formal military-grade PDF reports for underwater threat detection operations
    """
    
    def __init__(self, logo_folder_path=None):
        """
        Initialize report generator
        
        Args:
            logo_folder_path: Path to folder containing government logos
        """
        self.logo_folder = logo_folder_path
        self.styles = self._create_styles()
        
    def _create_styles(self):
        """Create formal paragraph styles for military report"""
        styles = getSampleStyleSheet()
        
        # Custom styles
        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#2563eb'),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=HexColor('#2563eb'),
            borderPadding=5,
            backColor=HexColor('#eff6ff')
        ))
        
        styles.add(ParagraphStyle(
            name='SubHeading',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=HexColor('#1e40af'),
            spaceAfter=8,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='FormalBodyText',
            parent=styles['Normal'],
            fontSize=10,
            textColor=HexColor('#1f2937'),
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            leading=14
        ))
        
        styles.add(ParagraphStyle(
            name='ThreatAlert',
            parent=styles['Normal'],
            fontSize=10,
            textColor=HexColor('#991b1b'),
            spaceAfter=6,
            fontName='Helvetica-Bold',
            backColor=HexColor('#fee2e2'),
            borderWidth=1,
            borderColor=HexColor('#991b1b'),
            borderPadding=5
        ))
        
        styles.add(ParagraphStyle(
            name='MetricsText',
            parent=styles['Normal'],
            fontSize=9,
            textColor=HexColor('#374151'),
            spaceAfter=4,
            fontName='Helvetica'
        ))
        
        return styles
    
    def generate_report(self, output_path, report_data):
        """
        Generate comprehensive PDF report
        
        Args:
            output_path: Path where PDF will be saved
            report_data: Dictionary containing all report information:
                - metadata: dict with timestamp, gps, depth, turbidity
                - threats: list of detected threat objects
                - images: dict with paths to visualization images
                - metrics: dict with quality metrics (PSNR, SSIM, UIQM)
                - summary: dict with mission summary and recommendations
        """
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1.25*inch,
            bottomMargin=1*inch
        )
        
        # Build story (content)
        story = []
        
        # Title Page
        story.extend(self._create_title_page(report_data))
        story.append(PageBreak())
        
        # Section A: Metadata
        story.extend(self._create_metadata_section(report_data.get('metadata', {})))
        story.append(Spacer(1, 0.3*inch))
        
        # Section B: Threat Details
        story.extend(self._create_threat_details_section(report_data.get('threats', [])))
        story.append(PageBreak())
        
        # Section C: Visual Report
        story.extend(self._create_visual_report_section(
            report_data.get('images', {}),
            report_data.get('metrics', {})
        ))
        story.append(PageBreak())
        
        # Section D: Final Summary
        story.extend(self._create_summary_section(report_data.get('summary', {})))
        
        # Build PDF with custom canvas
        doc.build(
            story,
            canvasmaker=lambda *args, **kwargs: DRDOReportCanvas(
                *args, logo_path=self.logo_folder, **kwargs
            )
        )
        
        return output_path
    
    def _create_title_page(self, report_data):
        """Create formal title page"""
        elements = []
        
        elements.append(Spacer(1, 1.5*inch))
        
        # Main title
        title = Paragraph(
            "OPERATIONAL THREAT INTELLIGENCE REPORT",
            self.styles['ReportTitle']
        )
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Subtitle
        subtitle = Paragraph(
            "Underwater Image Enhancement and Threat Detection Analysis",
            self.styles['SubHeading']
        )
        elements.append(subtitle)
        elements.append(Spacer(1, 1*inch))
        
        # Report details table
        metadata = report_data.get('metadata', {})
        report_info = [
            ['Report ID:', metadata.get('report_id', 'N/A')],
            ['Operation Timestamp:', metadata.get('timestamp', 'N/A')],
            ['Mission Coordinates:', metadata.get('gps_coords', 'N/A')],
            ['Deployment Depth:', f"{metadata.get('depth_m', 'N/A')} meters"],
            ['Classification:', 'RESTRICTED'],
        ]
        
        info_table = Table(report_info, colWidths=[2.5*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
            ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#1e40af')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [HexColor('#f9fafb'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#d1d5db')),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(info_table)
        
        elements.append(Spacer(1, 1*inch))
        
        # Authority statement
        authority = Paragraph(
            "<b>ISSUING AUTHORITY:</b> Defence Research and Development Organisation (DRDO)<br/>"
            "<b>DISTRIBUTION:</b> Authorized Personnel Only<br/>"
            "<b>VALIDITY:</b> Operational Intelligence - Time Sensitive",
            self.styles['FormalBodyText']
        )
        elements.append(authority)
        
        return elements
    
    def _create_metadata_section(self, metadata):
        """Section A: Operational Metadata"""
        elements = []
        
        # Section header
        header = Paragraph("SECTION A: OPERATIONAL METADATA", self.styles['SectionHeading'])
        elements.append(header)
        
        # Mission parameters
        elements.append(Paragraph("<b>Mission Parameters</b>", self.styles['SubHeading']))
        
        params_text = f"""
        <b>Timestamp:</b> {metadata.get('timestamp', 'N/A')}<br/>
        <b>GPS Coordinates:</b> {metadata.get('gps_coords', 'N/A')}<br/>
        <b>Camera Deployment Depth:</b> {metadata.get('depth_m', 'N/A')} meters<br/>
        <b>Water Turbidity Score:</b> {metadata.get('turbidity_score', 'N/A')}/10<br/>
        <b>Visibility Conditions:</b> {metadata.get('visibility', 'N/A')}<br/>
        <b>Water Temperature:</b> {metadata.get('water_temp', 'N/A')}°C<br/>
        <b>Current Speed:</b> {metadata.get('current_speed', 'N/A')} knots
        """
        elements.append(Paragraph(params_text, self.styles['FormalBodyText']))
        
        return elements
    
    def _create_threat_details_section(self, threats):
        """Section B: Threat Intelligence Details"""
        elements = []
        
        # Section header
        header = Paragraph("SECTION B: THREAT INTELLIGENCE ANALYSIS", self.styles['SectionHeading'])
        elements.append(header)
        
        if not threats:
            no_threats = Paragraph(
                "No hostile threats detected in operational area. Area classified as CLEAR.",
                self.styles['FormalBodyText']
            )
            elements.append(no_threats)
            return elements
        
        # Threat summary
        summary = Paragraph(
            f"<b>ALERT:</b> Total {len(threats)} potential threat(s) detected and analyzed. "
            f"Detailed assessment follows:",
            self.styles['ThreatAlert']
        )
        elements.append(summary)
        elements.append(Spacer(1, 0.2*inch))
        
        # Individual threat details
        for idx, threat in enumerate(threats, 1):
            elements.append(Paragraph(f"<b>THREAT #{idx}</b>", self.styles['SubHeading']))
            
            # Threat details table
            threat_info = [
                ['Object Type:', threat.get('class', 'Unknown')],
                ['Confidence Level:', f"{threat.get('confidence', 0)*100:.1f}%"],
                ['Distance from Camera:', f"{threat.get('distance', {}).get('distance_m', 'N/A')} meters"],
                ['Risk Assessment Score:', f"{threat.get('risk_score', 'N/A')}/10"],
                ['Priority Level:', threat.get('priority', 'MEDIUM')],
                ['Detection Method:', threat.get('detection_method', 'YOLOv8-X Deep Learning')],
                ['Bounding Box (x,y,w,h):', f"{threat.get('bbox', 'N/A')}"],
            ]
            
            threat_table = Table(threat_info, colWidths=[2*inch, 4.5*inch])
            threat_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
                ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#1e40af')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, HexColor('#f9fafb')]),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#d1d5db')),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(threat_table)
            elements.append(Spacer(1, 0.15*inch))
        
        return elements
    
    def _create_visual_report_section(self, images, metrics):
        """Section C: Visual Analysis and Explainability"""
        elements = []
        
        # Section header
        header = Paragraph("SECTION C: VISUAL INTELLIGENCE REPORT", self.styles['SectionHeading'])
        elements.append(header)
        
        # C.1: Before-After Enhancement Quad Comparison
        elements.append(Paragraph("<b>C.1 Comprehensive Image Processing Workflow</b>", self.styles['SubHeading']))
        
        enhancement_text = """
        This four-panel comparison illustrates the complete image processing and threat detection 
        workflow: <b>Top-Left Panel (Original):</b> Raw underwater image as captured by the camera 
        system, exhibiting typical underwater degradation including blue-green color cast, reduced 
        contrast, hazy appearance, and attenuated red spectrum. <b>Top-Right Panel (Enhanced):</b> 
        Deep learning-enhanced image processed through the Deep WaveNet architecture with UIEB model, 
        demonstrating restored color fidelity, improved contrast, reduced scattering effects, and 
        recovered visual information. <b>Bottom-Left Panel (Threat Detection):</b> YOLOv8-X neural 
        network output showing detected objects with bounding boxes, classification labels, and 
        confidence scores - the foundation for tactical threat assessment. <b>Bottom-Right Panel 
        (Distance Measurement):</b> Calculated distance estimations from camera to each detected 
        threat using monocular depth estimation techniques, displaying range in meters with confidence 
        intervals and error margins. This quad view provides operators with complete situational 
        awareness from raw capture through processed intelligence.
        """
        elements.append(Paragraph(enhancement_text, self.styles['FormalBodyText']))
        
        # Add quad comparison image
        if 'before_after' in images and os.path.exists(images['before_after']):
            try:
                img = Image(images['before_after'], width=6*inch, height=3*inch)
                elements.append(img)
                elements.append(Paragraph(
                    "<i>Figure 1: Four-panel workflow - Original | Enhanced | Threat Detection | Distance Measurement</i>",
                    self.styles['MetricsText']
                ))
            except Exception as e:
                elements.append(Paragraph(f"Image loading error: {e}", self.styles['MetricsText']))
        else:
            elements.append(Paragraph(
                "Quad comparison image not available for this analysis.",
                self.styles['MetricsText']
            ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # C.5: Quality Metrics
        elements.append(Paragraph("<b>C.5 Quantitative Image Quality Assessment</b>", self.styles['SubHeading']))
        
        metrics_explanation = """
        Objective image quality metrics provide quantitative assessment of enhancement performance. 
        <b>PSNR (Peak Signal-to-Noise Ratio)</b> measures pixel-level accuracy in decibels, with 
        higher values indicating better preservation of image information (typically 25-35 dB for 
        good quality). <b>SSIM (Structural Similarity Index)</b> evaluates structural information 
        preservation on a 0-1 scale, where values above 0.8 indicate excellent similarity. 
        <b>UIQM (Underwater Image Quality Measure)</b> is a specialized metric for underwater imagery, 
        combining colorfulness, sharpness, and contrast into a unified score (2.5-4.0 indicates good 
        underwater quality). <b>Turbidity Reduction</b> quantifies the decrease in water cloudiness 
        and particulate interference. <b>Entropy Gain</b> measures the increase in information content, 
        with positive values indicating successful detail recovery from degraded underwater conditions.
        """
        elements.append(Paragraph(metrics_explanation, self.styles['FormalBodyText']))
        elements.append(Spacer(1, 0.1*inch))
        
        metrics_data = [
            ['Metric', 'Value', 'Assessment'],
            ['PSNR (Peak Signal-to-Noise Ratio)', 
             f"{metrics.get('psnr', 'N/A')} dB", 
             self._assess_psnr(metrics.get('psnr', 0))],
            ['SSIM (Structural Similarity Index)', 
             f"{metrics.get('ssim', 'N/A')}", 
             self._assess_ssim(metrics.get('ssim', 0))],
            ['UIQM (Underwater Image Quality Measure)', 
             f"{metrics.get('uiqm', 'N/A')}", 
             self._assess_uiqm(metrics.get('uiqm', 0))],
            ['Turbidity Reduction', 
             f"{metrics.get('turbidity_reduction', 'N/A')}%", 
             'Improvement'],
            ['Entropy Gain', 
             f"{metrics.get('entropy_gain', 'N/A')}", 
             'Information Recovery'],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2.5*inch, 1.5*inch, 2.5*inch])
        metrics_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
            ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f3f4f6')]),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#9ca3af')),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(metrics_table)
        
        return elements
    
    def _create_summary_section(self, summary):
        """Section D: Mission Summary and Recommendations"""
        elements = []
        
        # Section header
        header = Paragraph("SECTION D: MISSION SUMMARY AND RECOMMENDATIONS", self.styles['SectionHeading'])
        elements.append(header)
        
        # Mission summary
        elements.append(Paragraph("<b>Mission Summary</b>", self.styles['SubHeading']))
        
        summary_text = summary.get('mission_summary', 
            'Underwater surveillance operation completed with AI-enhanced threat detection and image analysis.')
        elements.append(Paragraph(summary_text, self.styles['FormalBodyText']))
        
        elements.append(Spacer(1, 0.15*inch))
        
        # Recommended actions
        elements.append(Paragraph("<b>Recommended Operator Actions</b>", self.styles['SubHeading']))
        
        actions = summary.get('recommended_actions', [
            'Continue surveillance protocol',
            'Monitor detected threats',
            'Report findings to command center'
        ])
        
        for action in actions:
            elements.append(Paragraph(f"• {action}", self.styles['FormalBodyText']))
        
        elements.append(Spacer(1, 0.15*inch))
        
        # Severity assessment
        elements.append(Paragraph("<b>Severity Rating</b>", self.styles['SubHeading']))
        
        severity = summary.get('severity_rating', 'MEDIUM')
        severity_colors = {
            'LOW': HexColor('#10b981'),
            'MEDIUM': HexColor('#f59e0b'),
            'HIGH': HexColor('#ef4444'),
            'CRITICAL': HexColor('#991b1b')
        }
        
        severity_color = severity_colors.get(severity, HexColor('#6b7280'))
        
        severity_table = Table(
            [[severity]], 
            colWidths=[2*inch],
            rowHeights=[0.4*inch]
        )
        severity_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica-Bold', 14),
            ('BACKGROUND', (0, 0), (-1, -1), severity_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(severity_table)
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Final statement
        final_statement = Paragraph(
            "<b>REPORT STATUS:</b> COMPLETE<br/>"
            "<b>VERIFICATION:</b> AI-Generated Intelligence Report<br/>"
            "<b>AUTHORIZATION:</b> Aqua Sentinel Automated Threat Detection System",
            self.styles['FormalBodyText']
        )
        elements.append(final_statement)
        
        return elements
    
    def _assess_psnr(self, value):
        """Assess PSNR quality"""
        if value == 'N/A' or value == 0:
            return 'Not Available'
        if value > 30:
            return 'Excellent Quality'
        elif value > 25:
            return 'Good Quality'
        elif value > 20:
            return 'Acceptable Quality'
        else:
            return 'Poor Quality'
    
    def _assess_ssim(self, value):
        """Assess SSIM quality"""
        if value == 'N/A' or value == 0:
            return 'Not Available'
        if value > 0.9:
            return 'Excellent Similarity'
        elif value > 0.8:
            return 'Good Similarity'
        elif value > 0.7:
            return 'Acceptable Similarity'
        else:
            return 'Poor Similarity'
    
    def _assess_uiqm(self, value):
        """Assess UIQM quality"""
        if value == 'N/A' or value == 0:
            return 'Not Available'
        if value > 3.0:
            return 'Excellent UW Quality'
        elif value > 2.5:
            return 'Good UW Quality'
        elif value > 2.0:
            return 'Acceptable UW Quality'
        else:
            return 'Poor UW Quality'
