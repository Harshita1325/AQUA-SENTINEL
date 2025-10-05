# 🌊 Running the DeepWater Web Application with Metrics Display

## ✨ New Features
The UI now automatically displays **ALL quality metrics** for the enhanced output image:

### Metrics Displayed:
1. **Overall Quality Score** (0-100) - Combined quality indicator
2. **UIQM** - Underwater Image Quality Measure
3. **UCIQE** - Underwater Color Image Quality Evaluation
4. **Sharpness** - Edge definition and detail
5. **Contrast** - Dynamic range
6. **Colorfulness** - Color vibrancy
7. **SSIM** - Structural Similarity (if applicable)
8. **PSNR** - Peak Signal-to-Noise Ratio in dB (if applicable)

Each metric is displayed with:
- 🎯 Numeric value
- 📊 Visual progress bar
- 🎨 Color-coded quality indicator (Poor/Average/Good/Excellent)
- 📝 Description

---

## 🚀 How to Run

### Step 1: Activate Virtual Environment
```powershell
cd "c:\Users\Kunal Ramesh Pawar\OneDrive\Desktop\Kunal-Project\water-image\DeepWater"
.\deepwave_env\Scripts\Activate.ps1
```

### Step 2: Navigate to WebApp Directory
```powershell
cd webapp
```

### Step 3: Start the Flask Server
```powershell
python app.py
```

### Step 4: Open Browser
Navigate to: **http://localhost:5000**

---

## 📋 Usage Instructions

1. **Upload Image**: Click "Choose Image File" and select an underwater image
2. **Select Model**: Choose from:
   - Enhancement (UIEB Model)
   - 2X Super-Resolution
   - 3X Super-Resolution
   - 4X Super-Resolution
3. **Process**: Click "Process Image" button
4. **View Results**: 
   - See original vs enhanced images side-by-side
   - **NEW**: Scroll down to see all quality metrics automatically calculated
5. **Download**: Click "Download Enhanced Image" to save the result

---

## 🎨 Metrics Display Features

### Overall Score Card
- Large animated card showing overall quality (0-100)
- Visual progress bar with gradient colors
- Pulsing star icon

### Individual Metric Cards
- Grid layout with 7 metric cards
- Each card shows:
  - Icon representation
  - Metric name
  - Numeric value
  - Description
  - Animated progress bar
  - Color-coded quality level

### Quality Indicators
- 🟢 **Excellent** (Green) - Top tier quality
- 🔵 **Good** (Blue) - High quality
- 🟡 **Average** (Yellow) - Moderate quality
- 🔴 **Poor** (Red) - Needs improvement

---

## 🛠️ Technical Details

### Backend API
- `/upload` - Process the image
- `/calculate_metrics` - Calculate quality metrics (automatically called)
- Results displayed in real-time with smooth animations

### Metrics Calculation
- **UIQM**: Combines colorfulness, sharpness, and contrast (0-4 scale)
- **UCIQE**: Based on chroma, saturation, and contrast (0-0.7 scale)
- **Sharpness**: Laplacian variance (higher is better)
- **Contrast**: Standard deviation of intensity (0-100)
- **Colorfulness**: RGB opponent color space analysis
- **Overall Score**: Weighted combination of all metrics

---

## 📝 Notes

- Metrics are calculated automatically after image processing
- Loading spinner shown during metric calculation
- SSIM and PSNR show "N/A" when ground truth not available (normal for underwater enhancement)
- All animations are smooth with CSS transitions
- Responsive design works on all screen sizes

---

## 🐛 Troubleshooting

**Metrics not showing?**
- Check browser console for errors (F12)
- Ensure `/calculate_metrics` endpoint is responding
- Verify images were successfully processed

**Slow calculation?**
- Large images take longer to process
- Metrics calculation is optimized but comprehensive

**Values seem wrong?**
- Underwater images have different quality ranges
- UIQM and UCIQE are specifically designed for underwater images
- Reference-based metrics (SSIM/PSNR) only work with ground truth

---

## 🎯 Example Quality Ranges

### Good Enhancement:
- UIQM: 2.5 - 4.0
- UCIQE: 0.5 - 0.7
- Sharpness: >500
- Contrast: >40
- Overall Score: >75

### Moderate Enhancement:
- UIQM: 1.5 - 2.5
- UCIQE: 0.3 - 0.5
- Sharpness: 200-500
- Contrast: 25-40
- Overall Score: 50-75

---

Enjoy the enhanced metrics visualization! 🌊✨
