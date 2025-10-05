"""
Test script for Deep WaveNet web application
"""

import os
import sys
import shutil

def setup_webapp():
    """Set up the web application directories and test files"""
    
    # Get the current directory (webapp)
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create necessary directories
    directories = ['uploads', 'results', 'static']
    for directory in directories:
        dir_path = os.path.join(webapp_dir, directory)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"📁 Directory exists: {directory}")
    
    # Copy a sample test image
    base_dir = os.path.dirname(webapp_dir)
    sample_image_src = os.path.join(base_dir, 'uie_uieb', 'hazy_test', '807.png')
    sample_image_dst = os.path.join(webapp_dir, 'static', 'sample_underwater.png')
    
    if os.path.exists(sample_image_src):
        shutil.copy2(sample_image_src, sample_image_dst)
        print(f"✅ Copied sample image to static folder")
    else:
        print(f"❌ Sample image not found: {sample_image_src}")
    
    print("\n🎉 Web application setup complete!")
    print(f"📂 Web app directory: {webapp_dir}")
    print("🚀 Run 'python app.py' to start the server")

if __name__ == "__main__":
    setup_webapp()