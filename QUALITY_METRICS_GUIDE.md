# 📊 Quality Metrics Dashboard - User Guide

## Overview
The Multi-Metric Quality Assessment Dashboard provides comprehensive analysis of underwater image enhancement quality using industry-standard metrics and visualizations.

## 🎯 Key Features

### 1. **Quality Metrics Calculated**

#### No-Reference Metrics (Always Calculated)
These metrics evaluate the enhanced image quality without needing a ground truth reference:

- **UIQM (Underwater Image Quality Measure)**: 0-4 scale
  - Combines colorfulness, sharpness, and contrast
  - Higher is better (typically 2.5-4 for good quality)
  - Best metric for underwater images

- **UCIQE (Underwater Color Image Quality Evaluation)**: 0-1 scale
  - Evaluates chroma, saturation, and luminance contrast
  - Higher is better (typically 0.5-0.7 for good quality)
  - Specifically designed for underwater color assessment

- **Sharpness**: Laplacian variance
  - Measures image clarity and edge definition
  - Higher values indicate sharper images
  - Typical range: 100-1000+

- **Contrast**: Standard deviation of intensity
  - Measures dynamic range of image
  - Higher values indicate better contrast
  - Typical range: 30-100

- **Colorfulness**: Color richness index
  - Measures color saturation and variety
  - Higher is better for underwater images
  - Typical range: 0.1-0.5

- **Overall Score**: 0-100 composite rating
  - Weighted combination of all metrics
  - 80+ = Excellent, 60-80 = Good, 40-60 = Fair, <40 = Poor

#### Reference-Based Metrics (Optional)
Only calculated when ground truth images are available:

- **PSNR (Peak Signal-to-Noise Ratio)**: Measured in dB
  - Higher is better (typically 20-50 dB)
  - 30+ dB indicates good reconstruction
  - Sensitive to pixel-level differences

- **SSIM (Structural Similarity Index)**: -1 to 1 scale
  - Higher is better (1 means identical)
  - 0.9+ indicates excellent structural preservation
  - Better correlates with human perception than PSNR

### 2. **Visual Analytics**

#### Histogram Analysis
- **Before/After Comparison**: Side-by-side RGB histograms
- **Color Distribution**: Shows pixel intensity distribution across channels
- **Enhancement Verification**: Visualizes color correction improvements

#### Color Statistics
- **Per-Channel Analysis**: Detailed statistics for R, G, B channels
  - Mean: Average intensity (0-255)
  - Standard Deviation: Color variance
  - Range: Min-Max values
- **Dominant Color Detection**: Identifies primary color channel

### 3. **Interactive Dashboard**

#### Real-Time Calculations
- Click "🔬 Calculate Metrics" after image processing
- Instant metric computation (typically < 1 second)
- No page reload required

#### Metric Cards
- Color-coded quality indicators
- Descriptive labels and units
- Tooltip explanations

#### Chart.js Visualizations
- Interactive line charts for histograms
- Hover for exact values
- Responsive design for all screen sizes

## 🚀 How to Use

### Step 1: Process an Image
1. Upload underwater image
2. Select enhancement model (UIEB recommended)
3. Click "🚀 Process Image"
4. Wait for processing to complete

### Step 2: Calculate Metrics
1. After processing, the Quality Dashboard appears
2. Click "🔬 Calculate Metrics" button
3. Wait 1-2 seconds for calculations
4. View comprehensive results

### Step 3: Analyze Results

#### Interpreting UIQM Scores
- **3.5-4.0**: Excellent quality - Clear, sharp, well-balanced
- **3.0-3.5**: Very Good - Minor improvements possible
- **2.5-3.0**: Good - Acceptable for most applications
- **2.0-2.5**: Fair - Needs improvement
- **< 2.0**: Poor - Significant enhancement needed

#### Interpreting Overall Score
- **90-100**: Outstanding enhancement
- **80-89**: Excellent results
- **70-79**: Very good quality
- **60-69**: Good quality
- **50-59**: Acceptable
- **< 50**: Needs improvement

#### Histogram Analysis
- **Original**: Often shows blue/green dominance (water color)
- **Enhanced**: Should show more balanced RGB distribution
- **Good Enhancement**: Wider histogram spread = better dynamic range

#### Color Statistics
- **Red Channel**: Should increase after enhancement (color correction)
- **Green Channel**: Moderate values indicate natural appearance
- **Blue Channel**: Should decrease (removing water blue cast)

## 🎨 Technical Implementation

### Backend Architecture
```
metrics_calculator.py
├── ImageQualityMetrics class
│   ├── calculate_all_metrics() - Main calculation function
│   ├── calculate_uiqm() - Underwater quality measure
│   ├── calculate_uciqe() - Color quality evaluation
│   ├── calculate_psnr() - Signal-to-noise ratio
│   ├── calculate_ssim() - Structural similarity
│   ├── calculate_sharpness() - Laplacian variance
│   ├── calculate_contrast() - Intensity std deviation
│   ├── calculate_colorfulness() - Color richness
│   ├── generate_histograms() - RGB histogram data
│   └── get_color_statistics() - Per-channel stats
```

### API Endpoints
```
POST /calculate_metrics
- Input: { "input_file": "xxx_input.png", "output_file": "xxx_output.png" }
- Output: { "metrics": {...}, "histograms": {...}, "color_stats": {...} }

POST /batch_metrics
- Input: { "file_pairs": [{"input": "...", "output": "..."}] }
- Output: { "results": [...], "average_metrics": {...} }
```

### Frontend Components
- **Chart.js**: Interactive histogram visualization
- **CSS Grid**: Responsive metric card layout
- **Fetch API**: Async metric calculations
- **Dynamic Updates**: Real-time metric display

## 📊 Metric Formulas

### UIQM (Underwater Image Quality Measure)
```
UIQM = (0.0282 × UICM) + (0.2953 × UISM) + (3.5753 × UIConM)

Where:
- UICM = Underwater Image Colorfulness Measure
- UISM = Underwater Image Sharpness Measure  
- UIConM = Underwater Image Contrast Measure
```

### UCIQE (Underwater Color Image Quality Evaluation)
```
UCIQE = c1×σ_chroma + c2×con_l + c3×μ_saturation

Where:
- σ_chroma = Standard deviation of chroma
- con_l = Contrast of luminance
- μ_saturation = Mean saturation
- c1=0.4680, c2=0.2745, c3=0.2576 (empirically determined)
```

### Sharpness (Laplacian Variance)
```
Sharpness = Var(Laplacian(Gray(Image)))
```

### Colorfulness
```
Colorfulness = √(σ²_rg + σ²_yb) + 0.3×√(μ²_rg + μ²_yb)

Where:
- rg = R - G
- yb = 0.5×(R + G) - B
```

## 🎯 Use Cases

### 1. **Quality Assurance**
- Verify enhancement effectiveness
- Compare different model results
- Validate processing pipeline

### 2. **Maritime Security**
- Assess image suitability for threat detection
- Ensure clarity for object identification
- Validate underwater surveillance quality

### 3. **Research & Development**
- Benchmark enhancement algorithms
- Quantify improvement metrics
- Generate quality reports

### 4. **Production Deployment**
- Automated quality checks
- Batch processing validation
- Performance monitoring

## 🔧 Troubleshooting

### Metrics Not Calculating
**Problem**: Click button but no results appear
**Solution**: 
- Check browser console for errors
- Verify Flask server is running
- Ensure image files exist in uploads/results folders

### Histogram Not Displaying
**Problem**: Charts section empty
**Solution**:
- Verify Chart.js CDN loaded (check network tab)
- Clear browser cache
- Check for JavaScript errors

### Low Quality Scores
**Problem**: Overall score < 50
**Solution**:
- Try different enhancement model (UIEB vs SR)
- Check input image quality
- Verify proper lighting conditions

### PSNR/SSIM Showing "N/A"
**Problem**: Reference metrics not calculated
**Solution**:
- This is expected - no ground truth available
- These metrics only work with reference images
- Focus on no-reference metrics (UIQM, UCIQE)

## 📈 Performance

- **Metric Calculation**: < 1 second per image pair
- **Histogram Generation**: < 500ms
- **Color Statistics**: < 100ms
- **Total Processing**: Typically 1-2 seconds

## 🎓 References

1. **UIQM**: Yang, M., & Sowmya, A. (2015). "An Underwater Color Image Quality Evaluation Metric"
2. **UCIQE**: Yang, M., et al. (2015). "Underwater Color Image Quality Evaluation"
3. **PSNR/SSIM**: Wang, Z., et al. (2004). "Image Quality Assessment: From Error Visibility to Structural Similarity"

## 🚀 Future Enhancements

- [ ] Export metrics to CSV/JSON
- [ ] Batch processing with progress bar
- [ ] Metric threshold alerts
- [ ] Historical comparison charts
- [ ] PDF report generation
- [ ] Real-time video metrics

## 📞 Support

For issues or questions:
- Check `README_WebApp.md` for setup instructions
- Review Flask logs for errors
- Inspect browser console for frontend issues

---

**Created for**: India's Maritime Security AI Hackathon  
**Version**: 1.0.0  
**Last Updated**: 2024