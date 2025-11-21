"""Test script to diagnose login issues"""
import sys
print("Python version:", sys.version)
print("Starting test...")

try:
    print("1. Importing tkinter...")
    import tkinter as tk
    print("   OK")
    
    print("2. Importing user_manager...")
    from user_manager import UserManager
    print("   OK")
    
    print("3. Creating UserManager...")
    um = UserManager()
    print(f"   OK - {um.count()} users found")
    
    print("4. Importing login_dialog...")
    from login_dialog import LoginDialog
    print("   OK")
    
    print("5. Creating test window...")
    root = tk.Tk()
    root.withdraw()
    print("   OK")
    
    print("6. Creating login dialog...")
    login = LoginDialog(root)
    print("   OK")
    
    print("7. Showing login dialog...")
    result = login.show()
    
    if result:
        print(f"\n✓ Login successful!")
        print(f"  User: {result['full_name']}")
        print(f"  Username: {result['username']}")
        print(f"  Role: {result['role']}")
    else:
        print("\n✗ Login cancelled")
    
    root.destroy()
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\nTest complete")
