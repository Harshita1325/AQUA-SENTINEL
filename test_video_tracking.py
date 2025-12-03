"""
Quick test script for video processing with threat tracking
"""

import os
import sys

# Add webapp to path
sys.path.append('webapp')

from webapp.video_processor_v2 import VideoProcessorV2

def test_video_processing():
    """Test the video processor with tracking"""
    
    print("=" * 60)
    print("🧪 Testing Video Processor V2 with OpenCV Tracking")
    print("=" * 60)
    
    # Find a test video
    video_dir = "webapp/uploads"
    if not os.path.exists(video_dir):
        os.makedirs(video_dir)
        print(f"📁 Created uploads directory: {video_dir}")
    
    # Look for any video file
    video_files = []
    if os.path.exists(video_dir):
        video_files = [f for f in os.listdir(video_dir) if f.endswith(('.mp4', '.avi', '.mov'))]
    
    if not video_files:
        print("❌ No video files found in uploads directory")
        print("   Please upload a video through the web interface first")
        return
    
    # Use the first video found
    input_video = os.path.join(video_dir, video_files[0])
    print(f"\n📹 Input video: {input_video}")
    
    # Output path
    output_dir = "webapp/results"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_video = os.path.join(output_dir, f"tracked_{video_files[0]}")
    print(f"💾 Output video: {output_video}")
    
    # Initialize processor with threat detection ENABLED
    print("\n🚀 Initializing processor...")
    processor = VideoProcessorV2(
        model_type='uieb', 
        enable_threat_detection=True  # ENABLE TRACKING
    )
    
    # Process video
    print("\n▶️  Starting video processing...")
    print("   This will:")
    print("   1. Enhance underwater video quality")
    print("   2. Detect threats using YOLO")
    print("   3. Track threats with OpenCV trackers")
    print("   4. Draw bounding boxes that follow threats")
    print()
    
    stats = processor.process_video(
        input_path=input_video,
        output_path=output_video,
        create_comparison=True  # Side-by-side comparison
    )
    
    # Print results
    print("\n" + "=" * 60)
    print("📊 PROCESSING RESULTS")
    print("=" * 60)
    
    if stats.get('success'):
        print(f"✅ SUCCESS!")
        print(f"   Total frames: {stats['total_frames']}")
        print(f"   Processing time: {stats['processing_time']:.2f} seconds")
        print(f"   Average FPS: {stats['average_fps']:.2f}")
        print(f"   Resolution: {stats['resolution']}")
        print(f"   Threats detected: {'YES' if stats.get('threats_detected') else 'NO'}")
        print(f"\n📹 Output saved to: {output_video}")
        print(f"   Open this video to see the bounding boxes!")
    else:
        print(f"❌ FAILED: {stats.get('error', 'Unknown error')}")
    
    print("=" * 60)


if __name__ == "__main__":
    test_video_processing()
