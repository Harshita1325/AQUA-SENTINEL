#  Underwater Image Restoration Web Application

A modern web interface for Deep WaveNet underwater image restoration, featuring AI-powered image enhancement and super-resolution capabilities.

##  Features

- **Beautiful Web Interface**: Modern, responsive design with drag-and-drop file upload
-  **4 AI Models**: UIEB Enhancement + 2X/3X/4X Super-Resolution
-  **Real-time Processing**: Live progress indicators and status updates
-  **Image Preview**: Side-by-side comparison of original vs enhanced images
-  **Download Results**: Direct download of processed images
-  **Robust Error Handling**: Secure file handling and user feedback

##  Quick Start

### 1. Clone & Setup
```bash
git clone username 
cd underwater
python -m venv deepwave_env
```

### 2. Activate Environment
```bash
# Windows
.\deepwave_env\Scripts\Activate.ps1

# Linux/Mac
source deepwave_env/bin/activate
```

### 3. Install Dependencies
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install opencv-python scipy matplotlib tqdm scikit-image Flask
```

### 4. Run Web Application
```bash
cd webapp
python setup.py
python app.py
```

### 5. Open Browser
Navigate to: **http://localhost:5000**

##  Usage

1. **Upload Image**: Drag & drop or click to select underwater image
2. **Choose Model**: Select enhancement or super-resolution (2X/3X/4X)
3. **Process**: Click "Process Image" and wait for AI magic
4. **Download**: Get your enhanced underwater image!


```

## Model Performance mmm

| Model | PSNR | SSIM | Purpose |
|-------|------|------|---------|
| UIEB Enhancement | 21.57 | 0.80 | Color correction & clarity |
| 2X Super-Resolution | 25.71 | 0.77 | 2X upscaling |
| 3X Super-Resolution | 25.23 | 0.76 | 3X upscaling |
| 4X Super-Resolution | 25.08 | 0.74 | 4X upscaling |

##  Technical Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **AI**: PyTorch + Deep WaveNet models
- **Processing**: OpenCV, PIL
- **Deployment**: Local development server

##  Screenshots

The web application features:
- Modern gradient design
- Intuitive file upload interface
- Real-time processing feedback
- Side-by-side result comparison
- One-click download functionality

##  Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

##  License

This project is for **academic use only**. Commercial use is prohibited.
**Transform your underwater images with AI!
