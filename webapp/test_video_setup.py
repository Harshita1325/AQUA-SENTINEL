"""
Quick Test Script for Video Enhancement Feature
Run this to test the video processing functionality
"""

import os
import sys

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required = {
        'flask': 'Flask',
        'cv2': 'opencv-python',
        'torch': 'pytorch',
        'numpy': 'numpy'
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    
    print("✅ All dependencies installed!\n")
    return True

def check_model_files():
    """Check if model checkpoint files exist"""
    print("🔍 Checking model files...")
    
    model_paths = [
        '../uie_uieb/ckpts/netG_295.pt',
        '../uie_euvp/ckpts/netG_295.pt',
        '../uw_video_processing/ckpts/netG_295.pt'
    ]
    
    found = False
    for path in model_paths:
        if os.path.exists(path):
            print(f"  ✅ Found model: {path}")
            found = True
        else:
            print(f"  ⚠️  Missing: {path}")
    
    if not found:
        print("\n⚠️  No model files found!")
        print("Please download model checkpoints")
        return False
    
    print("✅ Model files available!\n")
    return True

def check_test_video():
    """Check if test video exists"""
    print("🔍 Checking test video...")
    
    test_video = '../uw_video_processing/degraded_video.mp4'
    
    if os.path.exists(test_video):
        print(f"  ✅ Test video found: {test_video}")
        return True
    else:
        print(f"  ⚠️  No test video found")
        print(f"  You can use any underwater video for testing")
        return False

def check_folders():
    """Check/create necessary folders"""
    print("🔍 Checking folders...")
    
    folders = ['uploads', 'results', 'videos']
    
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"  ✅ Created: {folder}/")
        else:
            print(f"  ✅ Exists: {folder}/")
    
    print("✅ All folders ready!\n")
    return True

def run_webapp():
    """Instructions to run the webapp"""
    print("=" * 60)
    print("🚀 READY TO START!")
    print("=" * 60)
    print("\n📋 To start the web application:\n")
    print("1. Make sure you're in the webapp directory:")
    print("   cd webapp")
    print("\n2. Activate virtual environment:")
    print("   ..\\deepwave_env\\Scripts\\Activate.ps1")
    print("\n3. Run the Flask app:")
    print("   python app.py")
    print("\n4. Open browser:")
    print("   http://localhost:5000")
    print("\n5. Click '🎬 Video Enhancement' tab")
    print("\n6. Upload a video and watch the magic! ✨")
    print("\n" + "=" * 60)
    print("💡 TIP: Use a short video (<30 seconds) for quick testing")
    print("=" * 60)

def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("🌊 DeepWater Video Enhancement - System Check")
    print("=" * 60 + "\n")
    
    # Change to webapp directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Run checks
    deps_ok = check_dependencies()
    models_ok = check_model_files()
    video_ok = check_test_video()
    folders_ok = check_folders()
    
    # Summary
    print("=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Dependencies: {'✅' if deps_ok else '❌'}")
    print(f"Model Files:  {'✅' if models_ok else '⚠️'}")
    print(f"Test Video:   {'✅' if video_ok else '⚠️'}")
    print(f"Folders:      {'✅' if folders_ok else '❌'}")
    print("=" * 60 + "\n")
    
    if deps_ok and folders_ok:
        if not models_ok:
            print("⚠️  Model files missing, but you can still test the UI")
        run_webapp()
    else:
        print("❌ Please fix the issues above before running")

if __name__ == '__main__':
    main()
