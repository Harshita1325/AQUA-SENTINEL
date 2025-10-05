# 🌊 Deep WaveNet Web Application

A modern web interface for Deep WaveNet underwater image restoration, featuring AI-powered image enhancement and super-resolution capabilities.

## 🚀 Features

- **🎨 Beautiful Web Interface**: Modern, responsive design with drag-and-drop file upload
- **🤖 4 AI Models**: 
  - UIEB Enhancement (underwater image enhancement)
  - 2X/3X/4X Super-Resolution (image upscaling)
- **⚡ Real-time Processing**: Live progress indicators and status updates
- **📸 Image Preview**: Side-by-side comparison of original vs enhanced images
- **💾 Download Results**: Direct download of processed images
- **🛡️ Robust Error Handling**: Secure file handling and user feedback

## 🛠️ Installation

### Prerequisites
- Python 3.8+ (tested with Python 3.12.5)
- PyTorch
- OpenCV
- Flask

### Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/pksvision/Deep-WaveNet-Underwater-Image-Restoration.git
   cd Deep-WaveNet-Underwater-Image-Restoration
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv deepwave_env
   ```

3. **Activate virtual environment**:
   - Windows: `.\deepwave_env\Scripts\Activate.ps1`
   - Linux/Mac: `source deepwave_env/bin/activate`

4. **Install dependencies**:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   pip install opencv-python scipy matplotlib tqdm scikit-image Flask
   ```

5. **Set up web application**:
   ```bash
   cd webapp
   python setup.py
   ```

## 🎯 Usage

### Web Application

1. **Start the server**:
   ```bash
   cd webapp
   python app.py
   ```

2. **Open your browser**:
   Navigate to `http://localhost:5000`

3. **Upload and process**:
   - Choose an underwater image
   - Select processing model (Enhancement or Super-Resolution)
   - Click "Process Image"
   - Download enhanced result

### Command Line Interface

#### UIEB Enhancement
```bash
cd uie_uieb
python test.py
```

#### Super-Resolution
```bash
cd super-resolution/4X  # or 2X, 3X
python test.py
```

## 📁 Project Structure

```
DeepWater/
├── webapp/                    # Web application
│   ├── app.py                # Main Flask application
│   ├── model_processor.py    # AI model integration
│   ├── templates/            # HTML templates
│   ├── static/               # CSS, JS, images
│   ├── uploads/              # Temporary uploads
│   └── results/              # Processed outputs
├── uie_uieb/                 # UIEB enhancement model
├── super-resolution/         # Super-resolution models
│   ├── 2X/                   # 2X upscaling
│   ├── 3X/                   # 3X upscaling
│   └── 4X/                   # 4X upscaling
├── utils/                    # Utility functions
└── DeepWaveNet_demo.ipynb    # Jupyter demo
```

## 🎨 Model Information

### UIEB Enhancement
- **Purpose**: Underwater image color correction and clarity enhancement
- **Dataset**: UIEB (Underwater Image Enhancement Benchmark)
- **Expected Results**: PSNR: 21.57, SSIM: 0.80

### Super-Resolution
- **2X Model**: PSNR: 25.71, SSIM: 0.77
- **3X Model**: PSNR: 25.23, SSIM: 0.76  
- **4X Model**: PSNR: 25.08, SSIM: 0.74

## 🌐 Web Interface Screenshots

The web application features:
- Gradient background design
- Intuitive file upload with preview
- Model selection interface
- Real-time processing feedback
- Side-by-side result comparison
- Download functionality

## 🔧 Technical Details

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **AI Framework**: PyTorch
- **Image Processing**: OpenCV, PIL
- **File Handling**: Secure upload/download with validation
- **Device Support**: CPU processing (GPU support available)

## 📊 Performance

- **Processing Time**: ~5 seconds per image (CPU)
- **Supported Formats**: PNG, JPG, JPEG, BMP, TIFF
- **Max File Size**: 16MB
- **Concurrent Processing**: Single-threaded (can be extended)

## 🐛 Troubleshooting

### Common Issues

1. **Model Loading Errors**:
   - Ensure all model files (.pt) are present in respective directories
   - Check PyTorch version compatibility

2. **Web Server Issues**:
   - Verify Flask installation: `pip install Flask`
   - Check port availability (default: 5000)

3. **Image Processing Errors**:
   - Verify image format is supported
   - Check file size limits
   - Ensure sufficient memory

## 📄 License

This project is for academic use only. Commercial use is prohibited.

## 🙏 Acknowledgments

- Original Deep WaveNet paper by Sharma et al.
- UIEB, EUVP, and UFO-120 datasets
- FUnIE-GAN for evaluation metrics
- Open source community for tools and libraries

## 📧 Contact

For questions or issues:
- Open an issue on GitHub
- Contact: kumar176101005@iitg.ac.in

---

**Happy underwater image restoration! 🌊📸**