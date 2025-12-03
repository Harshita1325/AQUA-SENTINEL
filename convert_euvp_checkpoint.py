"""
Convert old EUVP checkpoint to new architecture or copy to uw_video_processing for use
"""

import torch
import os
import shutil

def check_checkpoint():
    """Check what's in the EUVP checkpoint"""
    checkpoint_path = 'uie_euvp/ckpts/netG_17.pt'
    
    if not os.path.exists(checkpoint_path):
        print(f"❌ Checkpoint not found: {checkpoint_path}")
        return
    
    print(f"📦 Loading checkpoint: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=False)
    
    print("\n📊 Checkpoint contents:")
    print(f"   Keys: {list(checkpoint.keys())}")
    
    if 'epoch' in checkpoint:
        print(f"   Epoch: {checkpoint['epoch']}")
    
    if 'total_loss' in checkpoint:
        print(f"   Total loss: {checkpoint['total_loss']:.6f}")
    
    if 'model_state_dict' in checkpoint:
        state_dict = checkpoint['model_state_dict']
        print(f"   Model parameters: {len(state_dict)} layers")
        print(f"\n   First 10 layer names:")
        for i, key in enumerate(list(state_dict.keys())[:10]):
            shape = state_dict[key].shape
            print(f"      {key}: {shape}")
    
    # Calculate checkpoint size
    size_mb = os.path.getsize(checkpoint_path) / (1024 * 1024)
    print(f"\n   File size: {size_mb:.2f} MB")
    
    return checkpoint


def copy_to_video_processing():
    """Copy EUVP checkpoint to uw_video_processing for immediate use"""
    src = 'uie_euvp/ckpts/netG_17.pt'
    dst = 'uw_video_processing/ckpts/UIEB_EUVP.pth'
    
    if not os.path.exists(src):
        print(f"❌ Source not found: {src}")
        return False
    
    print(f"\n📋 Copying EUVP checkpoint for use...")
    print(f"   From: {src}")
    print(f"   To: {dst}")
    
    # Create destination directory if needed
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    
    # Copy the file
    shutil.copy2(src, dst)
    
    size_mb = os.path.getsize(dst) / (1024 * 1024)
    print(f"✅ Copied successfully! ({size_mb:.2f} MB)")
    print(f"\n🎯 Now you can use 'euvp' model in your webapp!")
    
    return True


def rename_old_checkpoint():
    """Rename old checkpoint so training starts fresh"""
    old_path = 'uie_euvp/ckpts/netG_17.pt'
    new_path = 'uie_euvp/ckpts/netG_17_old_architecture.pt'
    
    if not os.path.exists(old_path):
        print(f"❌ Checkpoint not found: {old_path}")
        return False
    
    print(f"\n📦 Renaming old checkpoint for backup...")
    print(f"   {old_path} → {new_path}")
    
    shutil.move(old_path, new_path)
    print(f"✅ Renamed! Now training will start fresh with new architecture")
    
    return True


if __name__ == "__main__":
    print("="*70)
    print("🔧 EUVP CHECKPOINT UTILITY")
    print("="*70)
    print()
    
    # Check checkpoint
    checkpoint = check_checkpoint()
    
    if checkpoint:
        print("\n" + "="*70)
        print("📌 OPTIONS:")
        print("="*70)
        print()
        print("1. COPY checkpoint to uw_video_processing (use EUVP model NOW)")
        print("   → Your webapp will be able to use the EUVP model immediately")
        print("   → Model trained for 17 epochs on EUVP dataset")
        print()
        print("2. RENAME checkpoint and start FRESH training")
        print("   → Train from scratch with new architecture")
        print("   → Old checkpoint saved as backup")
        print()
        
        choice = input("Choose option (1 or 2): ").strip()
        
        if choice == "1":
            print("\n🚀 Option 1: Copy for immediate use")
            copy_to_video_processing()
            
            print("\n" + "="*70)
            print("✅ DONE! Next steps:")
            print("="*70)
            print("1. Go to webapp interface")
            print("2. Select 'EUVP' model when processing images/videos")
            print("3. Your EUVP model (17 epochs) is now ready!")
            print()
            
        elif choice == "2":
            print("\n🔄 Option 2: Start fresh training")
            rename_old_checkpoint()
            
            print("\n" + "="*70)
            print("✅ DONE! Next steps:")
            print("="*70)
            print("cd uie_euvp")
            print("python train.py --end_epoch 50 --batch_size 4")
            print()
            print("Training will start from epoch 1 with new architecture")
            print()
        else:
            print("❌ Invalid choice")
    else:
        print("\n❌ Could not load checkpoint")
