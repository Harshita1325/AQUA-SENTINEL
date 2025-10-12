# 🌊 Underwater Image Restoration Web Application

A modern web interface for Deep WaveNet underwater image restoration, featuring AI-powered image enhancement and super-resolution capabilities.

![Web Application Preview](https://img.shields.io/badge/Status-Active-green) ![Python](https://img.shields.io/badge/Python-3.8+-blue) ![Flask](https://img.shields.io/badge/Flask-Web%20App-lightgrey) ![PyTorch](https://img.shields.io/badge/PyTorch-AI%20Models-orange)

## ✨ Features

- 🎨 **Beautiful Web Interface**: Modern, responsive design with drag-and-drop file upload
- 🤖 **4 AI Models**: UIEB Enhancement + 2X/3X/4X Super-Resolution
- ⚡ **Real-time Processing**: Live progress indicators and status updates
- 📸 **Image Preview**: Side-by-side comparison of original vs enhanced images
- 💾 **Download Results**: Direct download of processed images
- 🛡️ **Robust Error Handling**: Secure file handling and user feedback

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/Kunalrpawar/underwater.git
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

## 🎯 Usage

1. **Upload Image**: Drag & drop or click to select underwater image
2. **Choose Model**: Select enhancement or super-resolution (2X/3X/4X)
3. **Process**: Click "Process Image" and wait for AI magic
4. **Download**: Get your enhanced underwater image!

## 📁 Project Structure

```
underwater/
├── webapp/                    # 🌐 Web Application
│   ├── app.py                # Flask server
│   ├── model_processor.py    # AI model integration
│   ├── templates/            # HTML templates
│   └── static/               # CSS, JS, assets
├── uie_uieb/                 # 🎨 Enhancement Model
├── super-resolution/         # 🔍 Super-Resolution Models
│   ├── 2X/, 3X/, 4X/        # Different scale factors
├── utils/                    # 🛠️ Utility functions
└── DeepWaveNet_demo.ipynb    # 📓 Jupyter demo
```

## 🎨 Model Performance

| Model | PSNR | SSIM | Purpose |
|-------|------|------|---------|
| UIEB Enhancement | 21.57 | 0.80 | Color correction & clarity |
| 2X Super-Resolution | 25.71 | 0.77 | 2X upscaling |
| 3X Super-Resolution | 25.23 | 0.76 | 3X upscaling |
| 4X Super-Resolution | 25.08 | 0.74 | 4X upscaling |

## 🛠️ Technical Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **AI**: PyTorch + Deep WaveNet models
- **Processing**: OpenCV, PIL
- **Deployment**: Local development server

## 📸 Screenshots

The web application features:
- Modern gradient design
- Intuitive file upload interface
- Real-time processing feedback
- Side-by-side result comparison
- One-click download functionality

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is for **academic use only**. Commercial use is prohibited.

## 🙏 Acknowledgments

- Original [Deep WaveNet](https://github.com/pksvision/Deep-WaveNet-Underwater-Image-Restoration) by Sharma et al.
- UIEB, EUVP, and UFO-120 datasets
- Open source community

## 📞 Contact

**Kunal Ramesh Pawar**
- GitHub: [@Kunalrpawar](https://github.com/Kunalrpawar)
- Project: [underwater](https://github.com/Kunalrpawar/underwater)

---

**Transform your underwater images with AI! 🌊📸✨**