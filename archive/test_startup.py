import sys
import os
from datetime import datetime

log_file = "startup_log.txt"

def log(msg):
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now()}] {msg}\n")
    print(msg)

try:
    log("=" * 50)
    log("ESL AP Helper Startup Diagnostic")
    log(f"Python: {sys.version}")
    log(f"Working dir: {os.getcwd()}")
    
    log("\n1. Testing tkinter...")
    import tkinter as tk
    log("   ✓ tkinter imported")
    
    log("\n2. Testing user_manager...")
    from user_manager import UserManager
    um = UserManager()
    log(f"   ✓ UserManager loaded ({um.count()} users)")
    
    log("\n3. Testing login_dialog...")
    from login_dialog import LoginDialog
    log("   ✓ LoginDialog imported")
    
    log("\n4. Creating root window...")
    root = tk.Tk()
    root.withdraw()
    log("   ✓ Root window created")
    
    log("\n5. Showing login dialog...")
    login = LoginDialog(root)
    log("   ✓ Login dialog created")
    
    result = login.show()
    
    if result:
        log(f"\n✓ Login successful: {result['username']}")
    else:
        log("\n✗ Login cancelled")
    
    root.destroy()
    log("\nTest completed successfully")
    
except Exception as e:
    log(f"\n✗ ERROR: {e}")
    import traceback
    log(traceback.format_exc())

print(f"\nCheck {log_file} for details")
