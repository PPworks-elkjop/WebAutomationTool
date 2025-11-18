"""
Build VERA executable using PyInstaller
Run this script to create a standalone executable
"""

import subprocess
import sys
import os
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller if not already installed."""
    try:
        import PyInstaller
        print("✓ PyInstaller is already installed")
        return True
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller installed successfully")
        return True

def build_executable():
    """Build the executable using PyInstaller."""
    
    # Get the user's home directory for database
    home_dir = Path.home()
    db_file = home_dir / ".vera_database.db"
    key_file = home_dir / ".vera_encryption_key"
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--name=VERA",
        "--onefile",  # Single executable file
        "--windowed",  # No console window
        "--icon=NONE",  # You can add an .ico file later
        "--add-data=dashboard_components;dashboard_components",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=selenium",
        "--hidden-import=webdriver_manager",
        "--hidden-import=cryptography",
        "--hidden-import=jira",
        "--hidden-import=atlassian",
        "--collect-all=selenium",
        "--collect-all=webdriver_manager",
    ]
    
    # Add database if it exists
    if db_file.exists():
        cmd.append(f"--add-data={db_file};.")
        print(f"✓ Including database: {db_file}")
    else:
        print(f"⚠ Database not found: {db_file}")
    
    # Add encryption key if it exists
    if key_file.exists():
        cmd.append(f"--add-data={key_file};.")
        print(f"✓ Including encryption key: {key_file}")
    else:
        print(f"⚠ Encryption key not found: {key_file}")
    
    # Main script
    cmd.append("dashboard_main.py")
    
    print("\nBuilding executable...")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        subprocess.check_call(cmd)
        print("\n" + "="*60)
        print("✓ Build completed successfully!")
        print("="*60)
        print("\nExecutable location:")
        print(f"  dist/VERA.exe")
        print("\nYou can now distribute the VERA.exe file.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("VERA Executable Builder")
    print("="*60)
    print()
    
    # Install PyInstaller if needed
    if not install_pyinstaller():
        print("Failed to install PyInstaller")
        sys.exit(1)
    
    # Build the executable
    if build_executable():
        print("\nBuild process completed!")
        sys.exit(0)
    else:
        print("\nBuild process failed!")
        sys.exit(1)
