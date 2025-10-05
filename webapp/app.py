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
            
            # Process image
            start_time = time.time()
            processor.process_image(input_path, output_path, model_type)
            processing_time = time.time() - start_time
            
            return jsonify({
                'success': True,
                'input_file': input_filename,
                'output_file': output_filename,
                'processing_time': round(processing_time, 2),
                'model_used': model_type
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