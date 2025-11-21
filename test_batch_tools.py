"""
Test script for batch operations tools
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_manager import DatabaseManager
from batch_ping import BatchPingWindow
from batch_browser import BatchBrowserWindow
from batch_ssh import BatchSSHWindow


def test_batch_tools():
    """Test all batch operation tools."""
    
    # Create root window
    root = tk.Tk()
    root.withdraw()
    
    # Initialize database
    print("Initializing database...")
    db = DatabaseManager()
    
    # Test user
    current_user = {
        'username': 'test_user',
        'full_name': 'Test User'
    }
    
    # Create test window with buttons to launch each tool
    test_window = tk.Toplevel()
    test_window.title("Batch Operations Test")
    test_window.geometry("400x300")
    
    header = ttk.Label(test_window, text="Batch Operations Test Suite", 
                      font=('Segoe UI', 14, 'bold'))
    header.pack(pady=20)
    
    info = ttk.Label(test_window, 
                    text="Click a button to test each batch operation tool.\n"
                         "These tools allow automation on multiple APs simultaneously.",
                    wraplength=350,
                    justify=tk.CENTER)
    info.pack(pady=10)
    
    button_frame = ttk.Frame(test_window)
    button_frame.pack(pady=20)
    
    def launch_ping():
        BatchPingWindow(test_window, current_user, db)
    
    def launch_browser():
        BatchBrowserWindow(test_window, current_user, db)
    
    def launch_ssh():
        BatchSSHWindow(test_window, current_user, db)
    
    ttk.Button(button_frame, text="Test Batch Ping", 
              command=launch_ping, width=25).pack(pady=5)
    
    ttk.Button(button_frame, text="Test Batch Browser", 
              command=launch_browser, width=25).pack(pady=5)
    
    ttk.Button(button_frame, text="Test Batch SSH", 
              command=launch_ssh, width=25).pack(pady=5)
    
    ttk.Separator(button_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
    
    ttk.Button(button_frame, text="Exit Test", 
              command=root.quit, width=25).pack(pady=5)
    
    print("\n" + "="*60)
    print("BATCH OPERATIONS TEST SUITE")
    print("="*60)
    print("\nFeatures implemented:")
    print("✓ Base framework with search and selection")
    print("✓ Multi-search capability (remembers previous selections)")
    print("✓ Parallel processing with progress tracking")
    print("✓ Activity logging with color-coded messages")
    print("✓ Batch Ping - Ping multiple APs simultaneously")
    print("✓ Batch Browser - Web automation on multiple APs")
    print("✓ Batch SSH - Execute SSH commands on multiple APs")
    print("\nKey Features:")
    print("• Search APs by any field (ID, hostname, IP, MAC, store)")
    print("• Mark APs across multiple searches")
    print("• Real-time progress tracking")
    print("• Per-AP status and results")
    print("• Detailed activity log")
    print("• Configurable parallelism")
    print("• Independent windows (non-blocking)")
    print("="*60 + "\n")
    
    root.mainloop()


if __name__ == '__main__':
    test_batch_tools()
