"""
Simple build script for VERA executable
Creates a standalone .exe without bundling database/encryption key
"""

import subprocess
import sys
from pathlib import Path

def build_exe():
    """Build VERA executable using PyInstaller"""
    
    print("Building VERA.exe...")
    print("=" * 60)
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=VERA",
        "--onefile",
        "--windowed",
        "--add-data=dashboard_components;dashboard_components",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=selenium.webdriver.chrome.service",
        "--hidden-import=webdriver_manager.chrome",
        "--collect-all=selenium",
        "--collect-all=webdriver_manager",
        "--clean",
        "dashboard_main.py"
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("\n" + "=" * 60)
        print("✓ Build successful!")
        print(f"Executable location: dist\\VERA.exe")
        print("\nNote: Database and encryption key NOT included.")
        print("      Users must run the app once to initialize their own database.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        return False

if __name__ == "__main__":
    success = build_exe()
    sys.exit(0 if success else 1)
