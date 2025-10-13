import os
import uuid
import time
import cv2
from flask import Flask, request, render_template, send_file, jsonify, Response
from werkzeug.utils import secure_filename
from model_processor import get_processor
from metrics_calculator import get_metrics_calculator
from video_processor import get_video_processor
import json
from threading import Thread

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
app.config['VIDEO_FOLDER'] = 'videos'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size for videos

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv'}

# Global processor and metrics calculator
processor = None
metrics_calc = None
video_processor = None
video_progress = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

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
                    'postprocessing_log': enhancement_results['postprocessing_log']
                })
                
            elif adaptive_mode != 'off':
                # Use adaptive enhancement
                start_time = time.time()
                result_path, detected_env = processor.apply_adaptive_enhancement(
                    input_path, output_path, adaptive_mode
                )
                processing_time = time.time() - start_time
                
                return jsonify({
                    'success': True,
                    'input_file': input_filename,
                    'output_file': output_filename,
                    'processing_time': round(processing_time, 2),
                    'model_used': model_type,
                    'adaptive_mode': True,
                    'detected_environment': detected_env.upper()
                })
            else:
                # Standard processing
                start_time = time.time()
                processor.process_image(input_path, output_path, model_type)
                processing_time = time.time() - start_time
                
                return jsonify({
                    'success': True,
                    'input_file': input_filename,
                    'output_file': output_filename,
                    'processing_time': round(processing_time, 2),
                    'model_used': model_type,
                    'adaptive_mode': False
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
            'eta': 0
        }
        
        # Process video in background thread
        def process_video_async():
            try:
                video_progress[unique_id]['status'] = 'processing'
                
                # Initialize video processor
                if video_processor is None or video_processor.model_type != model_type:
                    proc = get_video_processor(model_type)
                else:
                    proc = video_processor
                
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
    Serve video files
    """
    video_path = os.path.join(app.config['VIDEO_FOLDER'], filename)
    if os.path.exists(video_path):
        return send_file(video_path, mimetype='video/mp4')
    return jsonify({'error': 'Video not found'}), 404

@app.route('/download_video/<filename>')
def download_video(filename):
    """
    Download enhanced video
    """
    video_path = os.path.join(app.config['VIDEO_FOLDER'], filename)
    if os.path.exists(video_path):
        return send_file(video_path, as_attachment=True, download_name=f"enhanced_{filename}")
    return jsonify({'error': 'Video not found'}), 404

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
                
                # Detect and highlight threats
                start_time = time.time()
                
                # Generate threat detection image (circles/boxes only)
                output_with_threats, threats, summary = processor.detect_and_highlight_threats(
                    input_path,
                    threat_output_path,
                    enhance_first=enhance_first,
                    exclude_marine_life=exclude_marine_life
                )
                
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
                    print(f"🔍 Processing {len(threats)} threats for distance visualization...")
                    threats_with_distance = 0
                    
                    for idx, threat in enumerate(threats):
                        # Check if distance info exists and is valid
                        has_distance = 'distance' in threat and threat['distance'] is not None and threat['distance'].get('distance_m') is not None
                        
                        if has_distance:
                            threats_with_distance += 1
                            center = threat['center']
                            dist_info = threat['distance']
                            
                            print(f"  ✅ Threat {idx + 1}: {threat['threat_type']} at {dist_info['distance_display']}")
                            
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
                            print(f"  ⚠️ Threat {idx + 1}: {threat['threat_type']} - No distance data available")
                    
                    print(f"📊 Distance visualization: {threats_with_distance}/{len(threats)} threats have distance data")
                    
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
                    print(f"⚠️ No threats detected for distance visualization")
                
                cv2.imwrite(distance_output_path, distance_img)
                print(f"💾 Distance measurement image saved to: {distance_output_path}")
                
                processing_time = time.time() - start_time
                
                # Format threat data for JSON response
                threat_list = []
                for threat in threats:
                    threat_data = {
                        'type': threat['threat_type'],
                        'confidence': float(threat['confidence']),
                        'risk_level': threat['risk_level'],
                        'bbox': threat['bbox'],
                        'center': threat['center']
                    }
                    
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
                
                return jsonify({
                    'success': True,
                    'input_file': input_filename,
                    'enhanced_output_file': enhanced_output_filename,
                    'threat_output_file': threat_output_filename,
                    'distance_output_file': distance_output_filename,
                    'processing_time': round(processing_time, 2),
                    'threats_detected': len(threats) > 0,
                    'threat_count': summary['total'],
                    'threats': threat_list,
                    'summary': {
                        'total': summary['total'],
                        'high_risk': summary['high_risk'],
                        'medium_risk': summary['medium_risk'],
                        'low_risk': summary['low_risk'],
                        'types': summary['types']
                    }
                })
                
            except Exception as e:
                # Clean up files on error
                if os.path.exists(input_path):
                    os.remove(input_path)
                return jsonify({'error': str(e)}), 500
        
        return jsonify({'error': 'Invalid file type'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🌊 Deep WaveNet Web Application")
    print("=" * 50)
    print("Initializing models...")
    
    try:
        processor = get_processor()
        info = processor.get_model_info()
        print("✅ All models loaded successfully!")
        print(f"🚀 Starting server on http://localhost:5000")
        print("📁 Available models:", info['available_models'])
        print("💻 Device:", info['device'])
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"❌ Failed to load models: {str(e)}")
        print("🔧 Starting server anyway (models will load on first request)...")
        app.run(debug=True, host='0.0.0.0', port=5000)