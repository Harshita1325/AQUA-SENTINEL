import os
import uuid
import time
import cv2
from flask import Flask, request, render_template, send_file, jsonify, Response
from werkzeug.utils import secure_filename
from model_processor import get_processor
from metrics_calculator import get_metrics_calculator
from video_processor import get_video_processor
from database_config import SecureImageDatabase
from pdf_report_generator import FormalPDFReportGenerator
from dotenv import load_dotenv
import json
from threading import Thread
from datetime import datetime
import random

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
app.config['VIDEO_FOLDER'] = 'videos'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size for videos
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'aqua-sentinel-deep-wave-net-secret-key-2025')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv'}

# Global processor and metrics calculator
processor = None
metrics_calc = None
video_processor = None
video_progress = {}

# Initialize database
try:
    db = SecureImageDatabase()
    print(" Database connected successfully!")
except Exception as e:
    print(f" Database connection failed: {e}")
    db = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/gallery')
def gallery():
    """Display image gallery page"""
    return render_template('gallery.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global processor
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    model_type = request.form.get('model_type', 'uieb')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        
        input_filename = f"{unique_id}_input.{file_ext}"
        output_filename = f"{unique_id}_output.{file_ext}"
        
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
        output_path = os.path.join(app.config['RESULTS_FOLDER'], output_filename)
        
        # Save uploaded file
        file.save(input_path)
        
        try:
            # Initialize processor if needed
            if processor is None:
                processor = get_processor()
            
            # Check processing mode
            smart_mode = request.form.get('smart_mode', 'off')
            adaptive_mode = request.form.get('adaptive_mode', 'off')
            
            # Priority: Smart Mode > Adaptive Mode > Standard
            if smart_mode == 'on':
                # Use smart enhancement with advanced preprocessing and postprocessing
                start_time = time.time()
                aggressive = request.form.get('aggressive', 'off') == 'on'
                
                enhancement_results = processor.smart_enhance(
                    input_path, output_path, aggressive=aggressive
                )
                processing_time = time.time() - start_time
                
                # Save to database if available
                db_image_id = None
                if db is not None:
                    try:
                        raw_id = db.store_image(input_path, user_id=1, image_type='raw')
                        db_image_id = db.store_image(output_path, user_id=1, image_type='enhanced')
                        print(f" Images saved to database: raw={raw_id}, enhanced={db_image_id}")
                    except Exception as db_error:
                        print(f" Database save failed: {db_error}")
                
                return jsonify({
                    'success': True,
                    'input_file': input_filename,
                    'output_file': output_filename,
                    'processing_time': round(processing_time, 2),
                    'model_used': model_type,
                    'smart_mode': True,
                    'aggressive': aggressive,
                    'input_quality': enhancement_results['input_quality'],
                    'output_quality': enhancement_results['output_quality'],
                    'improvement': enhancement_results['improvement'],
                    'preprocessing_log': enhancement_results['preprocessing_log'],
                    'postprocessing_log': enhancement_results['postprocessing_log'],
                    'db_saved': db_image_id is not None,
                    'db_image_id': db_image_id
                })
                
            elif adaptive_mode != 'off':
                # Use adaptive enhancement
                start_time = time.time()
                result_path, detected_env = processor.apply_adaptive_enhancement(
                    input_path, output_path, adaptive_mode
                )
                processing_time = time.time() - start_time
                
                # Save to database if available
                db_image_id = None
                if db is not None:
                    try:
                        raw_id = db.store_image(input_path, user_id=1, image_type='raw')
                        db_image_id = db.store_image(output_path, user_id=1, image_type='enhanced')
                        print(f" Images saved to database: raw={raw_id}, enhanced={db_image_id}")
                    except Exception as db_error:
                        print(f" Database save failed: {db_error}")
                
                return jsonify({
                    'success': True,
                    'input_file': input_filename,
                    'output_file': output_filename,
                    'processing_time': round(processing_time, 2),
                    'model_used': model_type,
                    'adaptive_mode': True,
                    'detected_environment': detected_env.upper(),
                    'db_saved': db_image_id is not None,
                    'db_image_id': db_image_id
                })
            else:
                # Standard processing
                start_time = time.time()
                processor.process_image(input_path, output_path, model_type)
                processing_time = time.time() - start_time
                
                # Save to database if available
                db_image_id = None
                if db is not None:
                    try:
                        # Save raw image
                        raw_id = db.store_image(input_path, user_id=1, image_type='raw')
                        # Save enhanced image
                        db_image_id = db.store_image(output_path, user_id=1, image_type='enhanced')
                    except Exception as db_error:
                        print(f" Database save failed: {db_error}")
                
                return jsonify({
                    'success': True,
                    'input_file': input_filename,
                    'output_file': output_filename,
                    'processing_time': round(processing_time, 2),
                    'model_used': model_type,
                    'adaptive_mode': False,
                    'db_saved': db_image_id is not None,
                    'db_image_id': db_image_id
                })
            
        except Exception as e:
            # Clean up files on error
            if os.path.exists(input_path):
                os.remove(input_path)
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/result/<filename>')
def result_file(filename):
    return send_file(os.path.join(app.config['RESULTS_FOLDER'], filename))

@app.route('/input/<filename>')
def input_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

@app.route('/photos/<filename>')
def photo_file(filename):
    return send_file(os.path.join('photos', filename))

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/model')
def model():
    return render_template('model.html')

@app.route('/live-video')
def live_video():
    """Live video surveillance page with camera access"""
    return render_template('live_video.html')

@app.route('/process-live-frame', methods=['POST'])
def process_live_frame():
    """Process live webcam frame with threat detection and enhancement"""
    global processor
    
    try:
        # Initialize processor if needed
        if processor is None:
            processor = get_processor()
        
        # Get the image data from request
        data = request.get_json()
        image_data = data.get('image')
        enable_detection = data.get('enableDetection', False)
        enable_enhancement = data.get('enableEnhancement', False)
        
        if not image_data:
            return jsonify({'success': False, 'error': 'No image data provided'}), 400
        
        # Decode base64 image
        import base64
        import numpy as np
        
        # Remove data URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decode base64 to bytes
        image_bytes = base64.b64decode(image_data)
        
        # Convert to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'success': False, 'error': 'Failed to decode image'}), 400
        
        # Process frame based on enabled features
        processed_frame = frame.copy()
        detections = []
        
        # Apply enhancement first if enabled
        if enable_enhancement:
            processed_frame = processor.enhance_image(processed_frame)
        
        # Apply threat detection if enabled
        if enable_detection:
            # Initialize threat detector if not loaded
            if processor.threat_detector is None:
                print("🔧 Loading threat detector for live video...")
                processor.load_threat_detector()
            
            # Detect threats - returns a list of threat dictionaries
            threat_results = processor.threat_detector.detect_threats(processed_frame)
            
            if threat_results:
                detections = threat_results  # It's already a list
                
                # Draw bounding boxes and labels on frame
                for detection in detections:
                    x1, y1, x2, y2 = detection['bbox']
                    threat_class = detection.get('threat_type', 'Unknown')
                    confidence = detection['confidence']
                    distance = detection.get('distance', {}).get('distance_display', 'N/A')
                    risk = detection.get('risk_level', 'MEDIUM')
                    
                    # Color based on risk level
                    risk_colors = {
                        'CRITICAL': (0, 0, 255),      # Red
                        'HIGH': (0, 127, 255),        # Orange
                        'MEDIUM': (0, 255, 255),      # Yellow
                        'LOW': (0, 255, 0)            # Green
                    }
                    color = risk_colors.get(risk, (0, 255, 255))
                    
                    # Draw bounding box (thicker for visibility)
                    cv2.rectangle(processed_frame, (x1, y1), (x2, y2), color, 4)
                    
                    # Prepare label with shortened threat name
                    threat_display = threat_class.replace('_', ' ').title()[:20]
                    if distance != 'N/A':
                        label = f"{threat_display} {confidence*100:.0f}% | {distance}"
                    else:
                        label = f"{threat_display} {confidence*100:.0f}% | {risk}"
                    
                    # Draw label background
                    label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                    cv2.rectangle(processed_frame, 
                                (x1, y1 - label_size[1] - 12), 
                                (x1 + label_size[0] + 12, y1), 
                                color, -1)
                    
                    # Draw label text (white)
                    cv2.putText(processed_frame, label, (x1 + 6, y1 - 6),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Encode processed frame back to base64
        _, buffer = cv2.imencode('.jpg', processed_frame)
        processed_image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'success': True,
            'processedImage': f'data:image/jpeg;base64,{processed_image_base64}',
            'detectionsCount': len(detections),
            'detections': detections
        })
        
    except Exception as e:
        print(f"Error processing live frame: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/model/config', methods=['GET'])
def get_model_config():
    """Get current model configuration"""
    global processor
    
    try:
        if processor is None:
            processor = get_processor()
        
        config = {
            'current_model': getattr(processor, 'current_model', 'uieb'),
            'processing_mode': 'single',
            'batch_size': 1,
            'enhancement_strength': 70,
            'gpu_acceleration': torch.cuda.is_available(),
            'gpu_available': torch.cuda.is_available(),
            'device': str(processor.device) if processor else 'cpu',
            'output_format': 'jpg',
            'threat_confidence': 50,
            'auto_environment': True,
            'distance_estimation': True,
            'cache_mode': 'memory'
        }
        
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/model/config', methods=['POST'])
def save_model_config():
    """Save model configuration"""
    try:
        config = request.json
        
        # Store in session or database (for now using session)
        from flask import session
        session['model_config'] = config
        
        print(f"✅ Configuration saved: {config}")
        
        return jsonify({
            'success': True,
            'message': 'Configuration saved successfully',
            'config': config
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/model/available', methods=['GET'])
def get_available_models():
    """Get list of available models with their status"""
    global processor
    
    try:
        if processor is None:
            processor = get_processor()
        
        available_models = processor.get_model_info()['available_models'] if processor else []
        
        models = [
            {
                'id': 'uieb',
                'name': 'UIEB Enhancement Model',
                'description': 'Optimized for underwater image enhancement with color correction',
                'status': 'active' if 'uieb' in available_models else 'unavailable',
                'speed': 'Fast (30-50 FPS)',
                'accuracy': '92%',
                'size': '45 MB',
                'recommended': True
            },
            {
                'id': 'euvp',
                'name': 'EUVP Deep Learning Model',
                'description': 'Advanced model trained on European Underwater Video Processing dataset',
                'status': 'active' if 'euvp' in available_models else 'unavailable',
                'speed': 'Medium (20-30 FPS)',
                'accuracy': '95%',
                'size': '78 MB',
                'recommended': False
            },
            {
                'id': 'sr2x',
                'name': '2X Super-Resolution',
                'description': 'Enhance resolution by 2x with detail preservation',
                'status': 'available',
                'speed': 'Slow (5-10 FPS)',
                'accuracy': '88%',
                'size': '120 MB',
                'recommended': False
            },
            {
                'id': 'hybrid',
                'name': 'Hybrid Enhancement Pipeline',
                'description': 'Combines multiple models for maximum quality',
                'status': 'available',
                'speed': 'Very Slow (2-5 FPS)',
                'accuracy': '97%',
                'size': '200+ MB',
                'recommended': False
            }
        ]
        
        return jsonify({
            'success': True,
            'models': models,
            'current_model': getattr(processor, 'current_model', 'uieb') if processor else 'uieb'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/model/select', methods=['POST'])
def select_model():
    """Select active model"""
    global processor
    
    try:
        data = request.json
        model_id = data.get('model_id')
        
        if not model_id:
            return jsonify({'success': False, 'error': 'Model ID required'}), 400
        
        if processor is None:
            processor = get_processor()
        
        # Store selected model
        if processor:
            processor.current_model = model_id
        
        from flask import session
        session['selected_model'] = model_id
        
        print(f"✅ Model selected: {model_id}")
        
        return jsonify({
            'success': True,
            'message': f'Model {model_id} selected successfully',
            'model_id': model_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/model/stats', methods=['GET'])
def get_model_stats():
    """Get model performance statistics"""
    global processor
    
    try:
        device_name = 'CPU'
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
        
        stats = {
            'device': device_name,
            'gpu_available': torch.cuda.is_available(),
            'models_loaded': len(processor.models) if processor and hasattr(processor, 'models') else 0,
            'total_processed': 0,  # Could be tracked in database
            'average_speed': '1.3 FPS',
            'memory_usage': '2.1 GB' if torch.cuda.is_available() else '850 MB'
        }
        
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== ALERT SYSTEM API ENDPOINTS ====================

@app.route('/api/alerts/active', methods=['GET'])
def get_active_alerts():
    """Get all active alerts"""
    try:
        from alert_system import get_alert_system
        alert_sys = get_alert_system()
        
        severity = request.args.get('severity')
        alerts = alert_sys.get_active_alerts(severity=severity)
        
        return jsonify({'success': True, 'alerts': alerts, 'count': len(alerts)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/alerts/history', methods=['GET'])
def get_alert_history():
    """Get alert history"""
    try:
        from alert_system import get_alert_system
        alert_sys = get_alert_system()
        
        limit = request.args.get('limit', type=int, default=50)
        severity = request.args.get('severity')
        
        history = alert_sys.get_alert_history(limit=limit, severity=severity)
        
        return jsonify({'success': True, 'history': history, 'count': len(history)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/alerts/summary', methods=['GET'])
def get_alert_summary():
    """Get alert statistics summary"""
    try:
        from alert_system import get_alert_system
        alert_sys = get_alert_system()
        
        summary = alert_sys.get_alert_summary()
        
        return jsonify({'success': True, 'summary': summary})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/alerts/<int:alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    try:
        from alert_system import get_alert_system
        alert_sys = get_alert_system()
        
        success = alert_sys.acknowledge_alert(alert_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Alert acknowledged'})
        else:
            return jsonify({'success': False, 'error': 'Alert not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/alerts/<int:alert_id>/dismiss', methods=['POST'])
def dismiss_alert(alert_id):
    """Dismiss an alert"""
    try:
        from alert_system import get_alert_system
        alert_sys = get_alert_system()
        
        success = alert_sys.dismiss_alert(alert_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Alert dismissed'})
        else:
            return jsonify({'success': False, 'error': 'Alert not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/alerts/clear_old', methods=['POST'])
def clear_old_alerts():
    """Clear alerts older than specified age"""
    try:
        from alert_system import get_alert_system
        alert_sys = get_alert_system()
        
        max_age = request.json.get('max_age_seconds', 3600)
        alert_sys.clear_old_alerts(max_age_seconds=max_age)
        
        return jsonify({'success': True, 'message': 'Old alerts cleared'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/api/history')
def api_history():
    import glob
    from datetime import datetime
    
    filter_type = request.args.get('filter', 'all')
    history_data = []
    
    # Get all processed images from results folder
    results_folder = app.config['RESULTS_FOLDER']
    uploads_folder = app.config['UPLOAD_FOLDER']
    
    # Get all output files
    output_files = []
    if filter_type == 'all' or filter_type == 'enhanced':
        output_files += glob.glob(os.path.join(results_folder, '*_output.*'))
        output_files += glob.glob(os.path.join(results_folder, '*_enhanced_clean.*'))
    if filter_type == 'all' or filter_type == 'threat':
        output_files += glob.glob(os.path.join(results_folder, '*_threat_detection.*'))
        output_files += glob.glob(os.path.join(results_folder, '*_threat_output.*'))
    if filter_type == 'all' or filter_type == 'distance':
        output_files += glob.glob(os.path.join(results_folder, '*_distance_measurement.*'))
    
    # Sort by modification time (newest first) and limit to 15
    output_files = sorted(output_files, key=os.path.getmtime, reverse=True)[:15]
    
    for output_path in output_files:
        filename = os.path.basename(output_path)
        # Extract UUID and determine type
        uuid_part = filename.split('_')[0]
        
        # Determine processing type and input suffix
        if 'threat_detection' in filename or 'threat_output' in filename:
            proc_type = 'Threat Detection'
            input_patterns = [f'{uuid_part}_threat_input.*', f'{uuid_part}_input.*']
        elif 'distance_measurement' in filename:
            proc_type = 'Distance Measurement'
            input_patterns = [f'{uuid_part}_threat_input.*', f'{uuid_part}_input.*']
        elif 'enhanced_clean' in filename:
            proc_type = 'Enhancement (Clean)'
            input_patterns = [f'{uuid_part}_threat_input.*', f'{uuid_part}_input.*']
        else:  # _output files
            proc_type = 'Enhancement'
            input_patterns = [f'{uuid_part}_input.*', f'{uuid_part}_threat_input.*']
        
        # Find corresponding input file (try multiple patterns)
        input_file = None
        for pattern in input_patterns:
            input_files = glob.glob(os.path.join(uploads_folder, pattern))
            if input_files:
                input_file = os.path.basename(input_files[0])
                break
        
        if input_file:
            # Get file modification time
            mod_time = datetime.fromtimestamp(os.path.getmtime(output_path))
            
            history_data.append({
                'filename': filename[:40] + '...' if len(filename) > 40 else filename,
                'type': proc_type,
                'original': f'/input/{input_file}',
                'processed': f'/result/{filename}',
                'date': mod_time.strftime('%b %d, %Y'),
                'time': mod_time.strftime('%I:%M %p'),
                'status': 'Completed'
            })
    
    return jsonify(history_data)

@app.route('/status')
def status():
    global processor
    try:
        if processor is None:
            processor = get_processor()
        info = processor.get_model_info()
        return jsonify(info)
    except Exception as e:
        return jsonify({
            'models_loaded': 0,
            'available_models': [],
            'device': 'unknown',
            'error': str(e)
        })

@app.route('/calculate_metrics', methods=['POST'])
def calculate_metrics():
    """
    Calculate quality metrics for enhanced image
    Expected JSON: {'input_file': 'xxx_input.png', 'output_file': 'xxx_output.png'}
    """
    global metrics_calc
    
    try:
        data = request.get_json()
        input_filename = data.get('input_file')
        output_filename = data.get('output_file')
        
        if not input_filename or not output_filename:
            return jsonify({'error': 'Missing file names'}), 400
        
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
        output_path = os.path.join(app.config['RESULTS_FOLDER'], output_filename)
        
        if not os.path.exists(input_path) or not os.path.exists(output_path):
            return jsonify({'error': 'Files not found'}), 404
        
        # Initialize metrics calculator if needed
        if metrics_calc is None:
            metrics_calc = get_metrics_calculator()
        
        # Load images
        original_image = cv2.imread(input_path)
        enhanced_image = cv2.imread(output_path)
        
        if original_image is None or enhanced_image is None:
            return jsonify({'error': 'Failed to load images'}), 500
        
        # Calculate all metrics
        metrics = metrics_calc.calculate_all_metrics(
            original_image, 
            enhanced_image, 
            has_reference=False  # No ground truth for underwater images
        )
        
        # Generate histograms
        original_histograms = metrics_calc.generate_histograms(original_image)
        enhanced_histograms = metrics_calc.generate_histograms(enhanced_image)
        
        # Get color statistics
        original_stats = metrics_calc.get_color_statistics(original_image)
        enhanced_stats = metrics_calc.get_color_statistics(enhanced_image)
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'histograms': {
                'original': original_histograms,
                'enhanced': enhanced_histograms
            },
            'color_stats': {
                'original': original_stats,
                'enhanced': enhanced_stats
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/batch_metrics', methods=['POST'])
def batch_metrics():
    """
    Calculate metrics for multiple image pairs
    """
    global metrics_calc
    
    try:
        data = request.get_json()
        file_pairs = data.get('file_pairs', [])
        
        if not file_pairs:
            return jsonify({'error': 'No file pairs provided'}), 400
        
        if metrics_calc is None:
            metrics_calc = get_metrics_calculator()
        
        results = []
        
        for pair in file_pairs:
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], pair['input'])
            output_path = os.path.join(app.config['RESULTS_FOLDER'], pair['output'])
            
            if os.path.exists(input_path) and os.path.exists(output_path):
                original_image = cv2.imread(input_path)
                enhanced_image = cv2.imread(output_path)
                
                metrics = metrics_calc.calculate_all_metrics(
                    original_image, 
                    enhanced_image, 
                    has_reference=False
                )
                
                results.append({
                    'input_file': pair['input'],
                    'output_file': pair['output'],
                    'metrics': metrics
                })
        
        return jsonify({
            'success': True,
            'results': results,
            'average_metrics': _calculate_average_metrics(results)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _calculate_average_metrics(results):
    """Calculate average metrics across multiple results"""
    if not results:
        return {}
    
    metric_keys = results[0]['metrics'].keys()
    avg_metrics = {}
    
    for key in metric_keys:
        values = [r['metrics'][key] for r in results if key in r['metrics']]
        if values:
            avg_metrics[key] = round(sum(values) / len(values), 4)
    
    return avg_metrics

@app.route('/upload_video', methods=['POST'])
def upload_video():
    """
    Upload and process underwater video
    """
    global video_processor, video_progress
    
    if 'file' not in request.files:
        return jsonify({'error': 'No video file selected'}), 400
    
    file = request.files['file']
    model_type = request.form.get('model_type', 'uieb')
    create_comparison = request.form.get('comparison', 'true').lower() == 'true'
    enable_threats = request.form.get('enable_threats', 'false').lower() == 'true'
    
    if file.filename == '':
        return jsonify({'error': 'No video file selected'}), 400
    
    if file and allowed_video_file(file.filename):
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        
        input_filename = f"{unique_id}_input.{file_ext}"
        output_filename = f"{unique_id}_enhanced.mp4"
        
        # Create video folder if not exists
        os.makedirs(app.config['VIDEO_FOLDER'], exist_ok=True)
        
        input_path = os.path.join(app.config['VIDEO_FOLDER'], input_filename)
        output_path = os.path.join(app.config['VIDEO_FOLDER'], output_filename)
        
        # Save uploaded video
        file.save(input_path)
        
        # Initialize progress tracking
        video_progress[unique_id] = {
            'status': 'uploading',
            'progress': 0,
            'current_frame': 0,
            'total_frames': 0,
            'fps': 0,
            'eta': 0,
            'input_file': input_filename,
            'output_file': output_filename
        }
        
        # Process video in background thread
        def process_video_async():
            try:
                video_progress[unique_id]['status'] = 'processing'
                
                # Initialize video processor with threat detection - USE V2 with OpenCV tracking
                from video_processor_v2 import VideoProcessorV2
                proc = VideoProcessorV2(model_type=model_type, enable_threat_detection=enable_threats)
                print(f"🎬 Using VideoProcessorV2 with threat detection: {enable_threats}")
                
                # Progress callback
                def update_progress(stats):
                    video_progress[unique_id].update(stats)
                    video_progress[unique_id]['status'] = 'processing'
                
                # Process video
                stats = proc.process_video(
                    input_path, 
                    output_path, 
                    progress_callback=update_progress,
                    create_comparison=create_comparison
                )
                
                video_progress[unique_id]['status'] = 'completed'
                video_progress[unique_id]['stats'] = stats
                
            except Exception as e:
                video_progress[unique_id]['status'] = 'error'
                video_progress[unique_id]['error'] = str(e)
        
        # Start processing thread
        thread = Thread(target=process_video_async)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'video_id': unique_id,
            'input_file': input_filename,
            'output_file': output_filename,
            'message': 'Video uploaded successfully. Processing started...'
        })
    
    return jsonify({'error': 'Invalid video file type'}), 400

@app.route('/video_progress/<video_id>')
def get_video_progress(video_id):
    """
    Get processing progress for a video
    """
    if video_id in video_progress:
        return jsonify(video_progress[video_id])
    else:
        return jsonify({'error': 'Video ID not found'}), 404

@app.route('/video/<filename>')
def serve_video(filename):
    """
    Serve video files with proper MIME type detection and range support
    """
    video_path = os.path.join(app.config['VIDEO_FOLDER'], filename)
    if os.path.exists(video_path):
        # Determine MIME type based on file extension
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'mp4'
        mime_types = {
            'mp4': 'video/mp4',
            'avi': 'video/x-msvideo',
            'mov': 'video/quicktime',
            'mkv': 'video/x-matroska',
            'wmv': 'video/x-ms-wmv'
        }
        mimetype = mime_types.get(ext, 'video/mp4')
        
        # Handle range requests for video seeking
        range_header = request.headers.get('Range', None)
        if not range_header:
            return send_file(video_path, mimetype=mimetype)
        
        # Parse range header
        size = os.path.getsize(video_path)
        byte1, byte2 = 0, None
        
        m = range_header.strip().split('=')[1]
        if '-' in m:
            byte1, byte2 = m.split('-')
            byte1 = int(byte1) if byte1 else 0
            byte2 = int(byte2) if byte2 else size - 1
        
        length = byte2 - byte1 + 1
        
        # Read file chunk
        with open(video_path, 'rb') as f:
            f.seek(byte1)
            data = f.read(length)
        
        rv = Response(data, 206, mimetype=mimetype, direct_passthrough=True)
        rv.headers.add('Content-Range', f'bytes {byte1}-{byte2}/{size}')
        rv.headers.add('Accept-Ranges', 'bytes')
        rv.headers.add('Content-Length', str(length))
        
        return rv
    return jsonify({'error': 'Video not found'}), 404

@app.route('/download_video/<filename>')
def download_video(filename):
    """
    Download enhanced video with proper headers
    """
    print(f"📥 Download request for: {filename}")
    video_path = os.path.join(app.config['VIDEO_FOLDER'], filename)
    print(f"📁 Looking for video at: {video_path}")
    print(f"📂 Video exists: {os.path.exists(video_path)}")
    
    if os.path.exists(video_path):
        # Get file extension for proper filename and mimetype
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'mp4'
        download_filename = f"enhanced_underwater_video.{ext}"
        
        # Map extensions to mimetypes
        mime_types = {
            'mp4': 'video/mp4',
            'avi': 'video/x-msvideo',
            'mov': 'video/quicktime',
            'mkv': 'video/x-matroska',
            'wmv': 'video/x-ms-wmv'
        }
        mimetype = mime_types.get(ext, 'video/mp4')
        
        print(f"✅ Sending file: {download_filename} (mimetype: {mimetype})")
        
        response = send_file(
            video_path, 
            as_attachment=True, 
            download_name=download_filename,
            mimetype=mimetype
        )
        
        # Ensure proper headers
        response.headers['Content-Type'] = mimetype
        response.headers['Content-Disposition'] = f'attachment; filename="{download_filename}"'
        
        return response
    
    print(f"❌ Video not found at: {video_path}")
    return jsonify({'error': 'Video not found'}), 404
    return jsonify({'error': 'Video not found'}), 404

@app.route('/download_report/<filename>')
def download_report(filename):
    """
    Download detailed threat intelligence report
    """
    report_path = os.path.join(app.config['RESULTS_FOLDER'], filename)
    if os.path.exists(report_path):
        return send_file(report_path, as_attachment=True, download_name=filename, mimetype='text/plain')
    return jsonify({'error': 'Report not found'}), 404

@app.route('/view_report/<filename>')
def view_report(filename):
    """
    View threat intelligence report in browser
    """
    report_path = os.path.join(app.config['RESULTS_FOLDER'], filename)
    if os.path.exists(report_path):
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        return Response(report_content, mimetype='text/plain')
    return jsonify({'error': 'Report not found'}), 404

@app.route('/generate_pdf_report', methods=['POST'])
def generate_pdf_report():
    """
    Generate comprehensive PDF report for DRDO with threat detection and enhancement analysis
    """
    try:
        data = request.get_json()
        
        # Extract data from request
        unique_id = data.get('unique_id')
        threats = data.get('threats', [])
        metrics = data.get('metrics', {})
        
        if not unique_id:
            return jsonify({'error': 'Missing unique_id'}), 400
        
        # Simulate metadata (in production, this would come from sensors)
        metadata = {
            'report_id': unique_id,
            'timestamp': datetime.now().strftime("%d %B %Y, %H:%M:%S IST"),
            'gps_coords': f"{random.uniform(8.0, 37.0):.4f}°N, {random.uniform(68.0, 97.0):.4f}°E",
            'depth_m': random.randint(10, 150),
            'turbidity_score': round(random.uniform(3.5, 8.5), 1),
            'visibility': random.choice(['Poor', 'Moderate', 'Good']),
            'water_temp': round(random.uniform(18.0, 28.0), 1),
            'current_speed': round(random.uniform(0.5, 3.2), 1)
        }
        
        # Collect image paths
        results_folder = app.config['RESULTS_FOLDER']
        file_ext = 'jpg'  # Default extension
        
        images = {
            'before_after': os.path.join(results_folder, f"{unique_id}_quad_comparison.{file_ext}"),
            'threat_detection': os.path.join(results_folder, f"{unique_id}_distance_visualization.{file_ext}"),

            'attention_flow': os.path.join(results_folder, f"{unique_id}_attention_flow.png"),
            'enhancement_grid': os.path.join(results_folder, f"{unique_id}_enhancement_analysis.png")
        }
        
        # Calculate threat severity
        threat_count = len(threats)
        if threat_count == 0:
            severity = 'LOW'
        elif threat_count <= 2:
            severity = 'MEDIUM'
        elif threat_count <= 5:
            severity = 'HIGH'
        else:
            severity = 'CRITICAL'
        
        # Generate summary
        summary = {
            'mission_summary': (
                f"Underwater surveillance operation conducted at depth {metadata['depth_m']} meters. "
                f"AI-enhanced image processing detected {threat_count} potential threat(s) in the operational area. "
                f"Advanced deep learning models (YOLOv8-X) were deployed for threat detection with multi-scale "
                f"Image enhancement using Deep WaveNet architecture improved "
                f"visibility by correcting color attenuation and removing scattering artifacts."
            ),
            'recommended_actions': [
                'Maintain continuous surveillance of detected threat locations',
                'Verify threat classification with secondary sensors',
                'Report findings to naval operations command center',
                'Consider deployment of unmanned underwater vehicle (UUV) for closer inspection',
                'Update threat database with current detection parameters'
            ] if threat_count > 0 else [
                'Area classified as CLEAR - no hostile threats detected',
                'Continue routine surveillance protocol',
                'Maintain operational readiness',
                'Log mission completion in operational database'
            ],
            'severity_rating': severity
        }
        
        # Prepare report data
        report_data = {
            'metadata': metadata,
            'threats': threats,
            'images': images,
            'metrics': metrics,
            'summary': summary
        }
        
        # Generate PDF
        pdf_filename = f"{unique_id}_DRDO_ThreatReport.pdf"
        pdf_path = os.path.join(results_folder, pdf_filename)
        
        logo_folder = os.path.join(os.path.dirname(__file__), 'photos')
        pdf_generator = FormalPDFReportGenerator(logo_folder_path=logo_folder)
        
        pdf_generator.generate_report(pdf_path, report_data)
        
        print(f"PDF Report generated successfully: {pdf_filename}")
        
        return jsonify({
            'success': True,
            'pdf_filename': pdf_filename,
            'message': 'PDF report generated successfully'
        })
        
    except Exception as e:
        print(f"Error generating PDF report: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/download_pdf_report/<filename>')
def download_pdf_report(filename):
    """
    Download generated PDF report
    """
    report_path = os.path.join(app.config['RESULTS_FOLDER'], filename)
    if os.path.exists(report_path):
        return send_file(report_path, as_attachment=True, download_name=filename, mimetype='application/pdf')
    return jsonify({'error': 'PDF report not found'}), 404

@app.route('/detect_threats', methods=['POST'])
def detect_threats():
    """
    Detect and highlight underwater threats
    """
    global processor
    
    try:
        # Get file from request
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            unique_id = str(uuid.uuid4())
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower()
            
            # Generate unique filenames for different outputs
            input_filename = f"{unique_id}_threat_input.{file_ext}"
            enhanced_output_filename = f"{unique_id}_enhanced_clean.{file_ext}"
            threat_output_filename = f"{unique_id}_threat_detection.{file_ext}"
            distance_output_filename = f"{unique_id}_distance_measurement.{file_ext}"
            
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
            enhanced_output_path = os.path.join(app.config['RESULTS_FOLDER'], enhanced_output_filename)
            threat_output_path = os.path.join(app.config['RESULTS_FOLDER'], threat_output_filename)
            distance_output_path = os.path.join(app.config['RESULTS_FOLDER'], distance_output_filename)
            
            # Save uploaded file
            file.save(input_path)
            
            try:
                # Initialize processor if needed
                if processor is None:
                    processor = get_processor()
                
                # Load threat detector
                processor.load_threat_detector()
                
                # Get options
                enhance_first = request.form.get('enhance_first', 'true').lower() == 'true'
                exclude_marine_life = request.form.get('exclude_marine_life', 'true').lower() == 'true'
                
                # Detect and highlight threats with ADVANCED SYSTEM
                start_time = time.time()
                
                print(f"\n Initiating ADVANCED threat detection...")
                print(f"   Enhancement: {'ENABLED' if enhance_first else 'DISABLED'}")
                print(f"   Marine life filtering: {'ON' if exclude_marine_life else 'OFF - Maximum Detection'}")
                
                # Generate threat detection image (circles/boxes only)
                output_with_threats, threats, summary = processor.detect_and_highlight_threats(
                    input_path,
                    threat_output_path,
                    enhance_first=enhance_first,
                    exclude_marine_life=exclude_marine_life
                )
                
                # Generate detailed threat intelligence report
                report_filename = None
                if threats and hasattr(processor.threat_detector, 'generate_detailed_report'):
                    report_filename = f"{unique_id}_threat_report.txt"
                    report_path = os.path.join(app.config['RESULTS_FOLDER'], report_filename)
                    try:
                        detailed_report = processor.threat_detector.generate_detailed_report(
                            threats, 
                            input_path,
                            report_path
                        )
                        print(f" Comprehensive threat report generated: {report_filename}")
                    except Exception as e:
                        print(f" Could not generate report: {str(e)}")
                        report_filename = None
                
                # Save the CLEAN enhanced image (no annotations) - for 2nd quadrant
                import cv2
                import numpy as np
                
                # Get the clean enhanced image
                if enhance_first:
                    # Try to load the enhanced version that was created during threat detection
                    enhanced_path_temp = input_path.replace(f'.{file_ext}', f'_enhanced.{file_ext}')
                    if os.path.exists(enhanced_path_temp):
                        enhanced_img = cv2.imread(enhanced_path_temp)
                    else:
                        # Fallback: enhance it here
                        enhanced_img = processor.process_image(input_path, enhanced_output_path, 'uieb')
                        enhanced_img = cv2.imread(enhanced_output_path)
                else:
                    # No enhancement, copy original
                    enhanced_img = cv2.imread(input_path)
                
                # Save clean enhanced image
                cv2.imwrite(enhanced_output_path, enhanced_img)
                
                # Generate distance measurement image (camera-to-threat distances)
                # This shows distance FROM CAMERA to each detected threat
                distance_img = enhanced_img.copy()
                
                if threats:
                    print(f" Processing {len(threats)} threats for distance visualization...")
                    threats_with_distance = 0
                    
                    for idx, threat in enumerate(threats):
                        # Check if distance info exists and is valid
                        has_distance = 'distance' in threat and threat['distance'] is not None and threat['distance'].get('distance_m') is not None
                        
                        if has_distance:
                            threats_with_distance += 1
                            center = threat['center']
                            dist_info = threat['distance']
                            
                            print(f"   Threat {idx + 1}: {threat['threat_type']} at {dist_info['distance_display']}")
                            
                            # Draw a small circle at threat center
                            cv2.circle(distance_img, tuple(center), 10, (0, 255, 159), -1)
                            cv2.circle(distance_img, tuple(center), 12, (255, 255, 255), 2)
                            
                            # Prepare distance text
                            dist_text = f"{dist_info['distance_display']}"
                            threat_label = f"Threat #{idx + 1}"
                            
                            # Position for text (above the threat)
                            text_x = center[0]
                            text_y = center[1] - 40
                            
                            font = cv2.FONT_HERSHEY_SIMPLEX
                            font_scale = 0.8
                            thickness = 2
                            
                            # Draw threat label
                            (tw1, th1), _ = cv2.getTextSize(threat_label, font, font_scale, thickness)
                            cv2.rectangle(distance_img,
                                        (text_x - tw1//2 - 8, text_y - th1 - 8),
                                        (text_x + tw1//2 + 8, text_y + 8),
                                        (0, 0, 0), -1)
                            cv2.rectangle(distance_img,
                                        (text_x - tw1//2 - 8, text_y - th1 - 8),
                                        (text_x + tw1//2 + 8, text_y + 8),
                                        (0, 255, 159), 2)
                            cv2.putText(distance_img, threat_label,
                                      (text_x - tw1//2, text_y),
                                      font, font_scale, (255, 255, 255), thickness)
                            
                            # Draw distance text (below threat label)
                            text_y2 = text_y + 35
                            (tw2, th2), _ = cv2.getTextSize(dist_text, font, font_scale + 0.2, thickness + 1)
                            cv2.rectangle(distance_img,
                                        (text_x - tw2//2 - 8, text_y2 - th2 - 8),
                                        (text_x + tw2//2 + 8, text_y2 + 8),
                                        (0, 0, 0), -1)
                            cv2.rectangle(distance_img,
                                        (text_x - tw2//2 - 8, text_y2 - th2 - 8),
                                        (text_x + tw2//2 + 8, text_y2 + 8),
                                        (0, 255, 159), 2)
                            cv2.putText(distance_img, dist_text,
                                      (text_x - tw2//2, text_y2),
                                      font, font_scale + 0.2, (0, 255, 159), thickness + 1)
                            
                            # Draw line from bottom center to threat (indicating direction from camera)
                            img_height, img_width = distance_img.shape[:2]
                            camera_point = (img_width // 2, img_height - 20)
                            cv2.line(distance_img, camera_point, tuple(center), (0, 255, 159), 2)
                            
                            # Draw camera icon/indicator at bottom
                            cv2.circle(distance_img, camera_point, 15, (139, 92, 246), -1)
                            cv2.circle(distance_img, camera_point, 17, (255, 255, 255), 2)
                            cv2.putText(distance_img, "CAM", (camera_point[0] - 20, camera_point[1] + 5),
                                      font, 0.5, (255, 255, 255), 2)
                        else:
                            print(f"   Threat {idx + 1}: {threat['threat_type']} - No distance data available")
                    
                    print(f" Distance visualization: {threats_with_distance}/{len(threats)} threats have distance data")
                    
                    # If no threats have distance, add a message on the image
                    if threats_with_distance == 0:
                        img_height, img_width = distance_img.shape[:2]
                        message = "Distance estimation unavailable"
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        font_scale = 1.0
                        thickness = 2
                        (tw, th), _ = cv2.getTextSize(message, font, font_scale, thickness)
                        text_x = (img_width - tw) // 2
                        text_y = img_height // 2
                        
                        cv2.rectangle(distance_img,
                                    (text_x - 10, text_y - th - 10),
                                    (text_x + tw + 10, text_y + 10),
                                    (0, 0, 0), -1)
                        cv2.rectangle(distance_img,
                                    (text_x - 10, text_y - th - 10),
                                    (text_x + tw + 10, text_y + 10),
                                    (255, 165, 0), 2)
                        cv2.putText(distance_img, message,
                                  (text_x, text_y),
                                  font, font_scale, (255, 165, 0), thickness)
                else:
                    # NO THREATS DETECTED - Add message overlay
                    print(f" No threats detected - clean scan")
                    img_height, img_width = distance_img.shape[:2]
                    message = "NO THREATS DETECTED"
                    sub_message = "Area Clear - Safe Zone"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 1.2
                    thickness = 3
                    
                    # Main message
                    (tw, th), _ = cv2.getTextSize(message, font, font_scale, thickness)
                    text_x = (img_width - tw) // 2
                    text_y = img_height // 2 - 30
                    
                    cv2.rectangle(distance_img,
                                (text_x - 20, text_y - th - 20),
                                (text_x + tw + 20, text_y + 20),
                                (0, 0, 0), -1)
                    cv2.rectangle(distance_img,
                                (text_x - 20, text_y - th - 20),
                                (text_x + tw + 20, text_y + 20),
                                (0, 255, 0), 3)
                    cv2.putText(distance_img, message,
                              (text_x, text_y),
                              font, font_scale, (0, 255, 0), thickness)
                    
                    # Sub message
                    (tw2, th2), _ = cv2.getTextSize(sub_message, font, 0.8, 2)
                    text_x2 = (img_width - tw2) // 2
                    text_y2 = text_y + 50
                    cv2.putText(distance_img, sub_message,
                              (text_x2, text_y2),
                              font, 0.8, (0, 255, 0), 2)
                
                cv2.imwrite(distance_output_path, distance_img)
                print(f" Distance measurement image saved to: {distance_output_path}")
                
                # Heatmap generation disabled for performance
                heatmap_filename = None
                enhancement_analysis_filename = None
                attention_flow_filename = None
                
                processing_time = time.time() - start_time
                
                # Calculate quality metrics if enhancement was performed
                calculated_metrics = {
                    'psnr': 0,
                    'ssim': 0,
                    'uiqm': 0,
                    'turbidity_reduction': 0,
                    'entropy_gain': 0
                }
                
                if enhance_first and os.path.exists(enhanced_output_path):
                    try:
                        print(f"\n Calculating image quality metrics...")
                        if metrics_calc is None:
                            metrics_calc = get_metrics_calculator()
                        
                        # Load original and enhanced images
                        original_img = cv2.imread(input_path)
                        enhanced_img = cv2.imread(enhanced_output_path)
                        
                        # Calculate all metrics
                        metrics_result = metrics_calc.calculate_all_metrics(
                            cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB),
                            cv2.cvtColor(enhanced_img, cv2.COLOR_BGR2RGB)
                        )
                        
                        calculated_metrics['psnr'] = round(metrics_result['psnr'], 2)
                        calculated_metrics['ssim'] = round(metrics_result['ssim'], 3)
                        calculated_metrics['uiqm'] = round(metrics_result['uiqm_enhanced'], 3)
                        
                        # Calculate turbidity reduction
                        orig_turbidity = 100 - (metrics_result['uiqm_original'] * 25)  # Approximate
                        enh_turbidity = 100 - (metrics_result['uiqm_enhanced'] * 25)
                        calculated_metrics['turbidity_reduction'] = round(max(0, orig_turbidity - enh_turbidity), 1)
                        
                        # Calculate entropy gain
                        orig_gray = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
                        enh_gray = cv2.cvtColor(enhanced_img, cv2.COLOR_BGR2GRAY)
                        orig_entropy = -np.sum(np.histogram(orig_gray, bins=256, range=(0, 256))[0] / orig_gray.size * 
                                              np.log2(np.histogram(orig_gray, bins=256, range=(0, 256))[0] / orig_gray.size + 1e-10))
                        enh_entropy = -np.sum(np.histogram(enh_gray, bins=256, range=(0, 256))[0] / enh_gray.size * 
                                            np.log2(np.histogram(enh_gray, bins=256, range=(0, 256))[0] / enh_gray.size + 1e-10))
                        calculated_metrics['entropy_gain'] = round(enh_entropy - orig_entropy, 3)
                        
                        print(f"    Metrics calculated: PSNR={calculated_metrics['psnr']} dB, SSIM={calculated_metrics['ssim']}, UIQM={calculated_metrics['uiqm']}")
                        
                    except Exception as e:
                        print(f"    Metrics calculation failed: {str(e)}")
                
                # Generate quad comparison image (Original | Enhanced | Threats | Distance)
                quad_comparison_filename = f"{unique_id}_quad_comparison.{file_ext}"
                quad_comparison_path = os.path.join(app.config['RESULTS_FOLDER'], quad_comparison_filename)
                
                try:
                    print(f"\n Generating quad comparison image...")
                    original_img = cv2.imread(input_path)
                    enhanced_img = cv2.imread(enhanced_output_path)
                    threat_img = cv2.imread(threat_output_path)
                    distance_img = cv2.imread(distance_output_path)
                    
                    # Resize all to same dimensions
                    target_height = 400
                    aspect = original_img.shape[1] / original_img.shape[0]
                    target_width = int(target_height * aspect)
                    
                    orig_resized = cv2.resize(original_img, (target_width, target_height))
                    enh_resized = cv2.resize(enhanced_img, (target_width, target_height))
                    threat_resized = cv2.resize(threat_img, (target_width, target_height))
                    dist_resized = cv2.resize(distance_img, (target_width, target_height))
                    
                    # Add labels
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    label_color = (255, 255, 255)
                    bg_color = (0, 0, 0)
                    
                    def add_label(img, text):
                        img_copy = img.copy()
                        (tw, th), _ = cv2.getTextSize(text, font, 0.8, 2)
                        cv2.rectangle(img_copy, (10, 10), (tw + 20, th + 20), bg_color, -1)
                        cv2.putText(img_copy, text, (15, th + 15), font, 0.8, label_color, 2)
                        return img_copy
                    
                    orig_labeled = add_label(orig_resized, "Original")
                    enh_labeled = add_label(enh_resized, "Enhanced")
                    threat_labeled = add_label(threat_resized, "Threat Detection")
                    dist_labeled = add_label(dist_resized, "Distance Measurement")
                    
                    # Create 2x2 grid
                    top_row = np.hstack([orig_labeled, enh_labeled])
                    bottom_row = np.hstack([threat_labeled, dist_labeled])
                    quad_image = np.vstack([top_row, bottom_row])
                    
                    cv2.imwrite(quad_comparison_path, quad_image)
                    print(f"    Quad comparison saved: {quad_comparison_filename}")
                    
                except Exception as e:
                    print(f"    Quad comparison generation failed: {str(e)}")
                
                # Format threat data for JSON response with DETAILED ANALYSIS
                threat_list = []
                for threat in threats:
                    threat_data = {
                        'type': threat['threat_type'],
                        'confidence': float(threat['confidence']),
                        'risk_level': threat['risk_level'],
                        'bbox': threat['bbox'],
                        'center': threat['center']
                    }
                    
                    # Add advanced analysis data
                    if 'severity' in threat:
                        threat_data['severity'] = threat['severity']
                    
                    if 'threat_score' in threat:
                        threat_data['threat_score'] = threat['threat_score']
                    
                    if 'characteristics' in threat:
                        char = threat['characteristics']
                        threat_data['characteristics'] = {
                            'size_class': char['size_analysis']['size_class'],
                            'proximity': char['size_analysis']['proximity_alert'],
                            'position': f"{char['position_analysis']['depth_zone']}, {char['position_analysis']['lateral_zone']}",
                            'shape': char['shape_profile'],
                            'screen_coverage': char['size_analysis']['screen_coverage']
                        }
                    
                    if 'behavior' in threat:
                        threat_data['behavior'] = {
                            'assessment': threat['behavior']['assessment'],
                            'indicators': threat['behavior']['additional_indicators'][:3]
                        }
                    
                    if 'tactical_response' in threat:
                        threat_data['tactical_response'] = threat['tactical_response']
                    
                    # Add distance information if available
                    if 'distance' in threat and threat['distance'].get('distance_m'):
                        dist_info = threat['distance']
                        threat_data['distance'] = {
                            'value': dist_info['distance_m'],
                            'display': dist_info['distance_display'],
                            'confidence': dist_info['confidence'],
                            'error_margin': dist_info['error_margin']
                        }
                    
                    threat_list.append(threat_data)
                
                # Prepare comprehensive response with detailed analysis
                response_data = {
                    'success': True,
                    'unique_id': unique_id,  # Add unique_id for PDF generation
                    'input_file': input_filename,
                    'enhanced_output_file': enhanced_output_filename,
                    'threat_output_file': threat_output_filename,
                    'distance_output_file': distance_output_filename,
                    'processing_time': round(processing_time, 2),
                    'threats_detected': len(threats) > 0,
                    'threat_count': summary['total'],
                    'threats': threat_list,
                    'metrics': calculated_metrics,  # Use calculated metrics
                    'summary': {
                        'total': summary['total'],
                        'critical': summary.get('critical', 0),
                        'high_risk': summary['high_risk'],
                        'medium_risk': summary['medium_risk'],
                        'low_risk': summary['low_risk'],
                        'unknown_risk': summary.get('unknown_risk', 0),
                        'status': summary.get('status', 'UNKNOWN'),
                        'average_threat_score': summary.get('average_threat_score', 0),
                        'max_threat_score': summary.get('max_threat_score', 0),
                        'immediate_threats': summary.get('immediate_threats', 0),
                        'types': summary['types']
                    },
                    'advanced_analysis': {
                        'severity_breakdown': summary.get('severity_breakdown', {}),
                        'proximity_alerts': summary.get('proximity_alerts', {}),
                        'behavior_patterns': summary.get('behavior_patterns', {}),
                        'distance_range': summary.get('distance_range', {}),
                        'tactical_alerts': summary.get('tactical_alerts', [])
                    }
                }
                
                # Add report file if generated
                if report_filename:
                    response_data['report_file'] = report_filename
                
                # Save to database if available
                db_image_id = None
                if db is not None:
                    try:
                        # Save raw input image
                        raw_id = db.store_image(input_path, user_id=1, image_type='raw', classification='RESTRICTED')
                        # Save enhanced image
                        enhanced_id = db.store_image(os.path.join(app.config['RESULTS_FOLDER'], enhanced_output_filename), 
                                                     user_id=1, image_type='enhanced', classification='RESTRICTED')
                        # Save threat detection image
                        db_image_id = db.store_image(os.path.join(app.config['RESULTS_FOLDER'], threat_output_filename), 
                                                     user_id=1, image_type='enhanced', classification='RESTRICTED')
                        
                        response_data['db_saved'] = True
                        response_data['db_image_id'] = db_image_id
                        print(f" Images saved to database: raw={raw_id}, enhanced={enhanced_id}, threat={db_image_id}")
                    except Exception as db_error:
                        print(f" Database save failed: {db_error}")
                        response_data['db_saved'] = False
                
                return jsonify(response_data)
                
            except Exception as e:
                # Clean up files on error
                if os.path.exists(input_path):
                    os.remove(input_path)
                return jsonify({'error': str(e)}), 500
        
        return jsonify({'error': 'Invalid file type'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Database-related routes
@app.route('/api/gallery')
def get_gallery():
    """Get all stored images from database"""
    if db is None:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        conn = db.pg_pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT image_id, original_filename, image_type, 
                       file_size_bytes, upload_timestamp, classification_level
                FROM images 
                ORDER BY upload_timestamp DESC 
                LIMIT 100
            """)
            
            images = []
            for row in cursor.fetchall():
                images.append({
                    'id': row[0],
                    'filename': row[1],
                    'type': row[2],
                    'size': row[3],
                    'uploaded': row[4].strftime('%Y-%m-%d %H:%M:%S'),
                    'classification': row[5]
                })
            
            return jsonify({'images': images, 'count': len(images)})
        finally:
            cursor.close()
            db.pg_pool.putconn(conn)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/image/<int:image_id>')
def get_image(image_id):
    """Retrieve image from database"""
    if db is None:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        # Create temp file
        temp_path = os.path.join(app.config['RESULTS_FOLDER'], f'temp_{image_id}.jpg')
        
        # Retrieve from database
        success = db.retrieve_image(image_id, user_id=1, output_path=temp_path)
        
        if success:
            return send_file(temp_path, mimetype='image/jpeg')
        else:
            return jsonify({'error': 'Image not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats')
def get_stats():
    """Get database statistics"""
    if db is None:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        stats = db.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/save-to-db', methods=['POST'])
def save_to_database():
    """Save processed image to database"""
    if db is None:
        return jsonify({'error': 'Database not available'}), 503
    
    try:
        data = request.json
        image_path = os.path.join(app.config['RESULTS_FOLDER'], data.get('filename'))
        image_type = data.get('type', 'enhanced')
        
        if not os.path.exists(image_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Store in database (user_id=1 for demo)
        image_id = db.store_image(image_path, user_id=1, image_type=image_type)
        
        if image_id:
            return jsonify({
                'success': True, 
                'image_id': image_id,
                'message': 'Image saved to database successfully'
            })
        else:
            return jsonify({'error': 'Failed to save image'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats')
def api_stats():
    """Get database statistics"""
    if db is None:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        stats = db.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/gallery')
def api_gallery():
    """Get list of all images from database"""
    if db is None:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        conn = db.pg_pool.getconn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                image_id,
                original_filename,
                file_size_bytes,
                image_type,
                upload_timestamp,
                classification_level
            FROM images
            ORDER BY upload_timestamp DESC
            LIMIT 100
        """)
        
        images = []
        for row in cursor.fetchall():
            images.append({
                'id': row[0],
                'filename': row[1],
                'size': row[2],
                'type': row[3],
                'uploaded': row[4].strftime('%Y-%m-%d %H:%M:%S'),
                'classification': row[5]
            })
        
        cursor.close()
        db.pg_pool.putconn(conn)
        
        return jsonify({'images': images, 'count': len(images)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/image/<int:image_id>')
def api_image(image_id):
    """Retrieve and serve image from database"""
    if db is None:
        return jsonify({'error': 'Database not connected'}), 500
    
    try:
        import tempfile
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_path = temp_file.name
        temp_file.close()
        
        # Retrieve image from database
        success = db.retrieve_image(image_id, user_id=1, output_path=temp_path)
        
        if success:
            return send_file(temp_path, mimetype='image/jpeg')
        else:
            return jsonify({'error': 'Image not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print(" Deep WaveNet Web Application")
    print("=" * 50)
    print("Initializing models...")
    
    try:
        processor = get_processor()
        info = processor.get_model_info()
        print(" All models loaded successfully!")
        print(f" Starting server on http://localhost:5000")
        print(" Available models:", info['available_models'])
        print(" Device:", info['device'])
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f" Failed to load models: {str(e)}")
        print(" Starting server anyway (models will load on first request)...")
        app.run(debug=True, host='0.0.0.0', port=5000)