"""
Helper script to switch between original and metrics dashboard UI
"""

import os
import shutil
from pathlib import Path

def switch_to_metrics_ui():
    """Switch to the new metrics dashboard UI"""
    base_path = Path(__file__).parent.parent / "webapp" / "templates"
    
    index_path = base_path / "index.html"
    metrics_path = base_path / "index_metrics.html"
    backup_path = base_path / "index_original.html"
    
    print("=" * 60)
    print("🔄 Switching to Metrics Dashboard UI")
    print("=" * 60)
    
    # Check if files exist
    if not metrics_path.exists():
        print("❌ Error: index_metrics.html not found!")
        return False
    
    # Backup original if not already backed up
    if index_path.exists() and not backup_path.exists():
        print(f"📦 Backing up original index.html...")
        shutil.copy2(index_path, backup_path)
        print(f"✅ Backup created: {backup_path.name}")
    
    # Copy metrics UI to index.html
    print(f"📝 Copying metrics dashboard to index.html...")
    shutil.copy2(metrics_path, index_path)
    print(f"✅ Metrics dashboard is now active!")
    
    print()
    print("=" * 60)
    print("✅ UI Switch Complete!")
    print("=" * 60)
    print()
    print("📝 What happened:")
    print(f"  • Original UI backed up as: {backup_path.name}")
    print(f"  • Metrics dashboard now active as: index.html")
    print()
    print("🚀 Next steps:")
    print("  1. Start Flask server: python webapp/app.py")
    print("  2. Open http://localhost:5000")
    print("  3. Enjoy the new metrics dashboard!")
    print()
    print("🔙 To restore original UI, run:")
    print("     python tests/restore_original_ui.py")
    print()
    
    return True

def restore_original_ui():
    """Restore the original UI"""
    base_path = Path(__file__).parent.parent / "webapp" / "templates"
    
    index_path = base_path / "index.html"
    backup_path = base_path / "index_original.html"
    
    print("=" * 60)
    print("🔄 Restoring Original UI")
    print("=" * 60)
    
    if not backup_path.exists():
        print("❌ Error: No backup found (index_original.html)")
        print("The metrics dashboard is the current UI.")
        return False
    
    print(f"📝 Restoring from backup...")
    shutil.copy2(backup_path, index_path)
    print(f"✅ Original UI restored!")
    
    print()
    print("=" * 60)
    print("✅ Restore Complete!")
    print("=" * 60)
    print()
    print("🚀 Restart Flask server to see changes")
    print()
    
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_original_ui()
    else:
        switch_to_metrics_ui()
