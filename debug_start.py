"""Debug version of ESL AP Helper startup"""
import sys
import traceback

print("Starting ESL AP Helper...")

try:
    print("1. Importing tkinter...")
    import tkinter as tk
    from tkinter import messagebox
    print("   OK")
    
    print("2. Importing login_dialog...")
    from login_dialog import LoginDialog
    print("   OK")
    
    print("3. Showing login dialog...")
    login = LoginDialog()
    current_user = login.show()
    print(f"   Login result: {current_user}")
    
    if not current_user:
        print("   User cancelled login")
        sys.exit(0)
    
    print(f"4. User logged in: {current_user['username']}")
    
    print("5. Importing App class...")
    # Import main app components
    sys.path.insert(0, r'C:\Users\PeterAndersson\GitHubVSCode\WebAutomationTool')
    from esl_ap_helper_v2 import App
    print("   OK")
    
    print("6. Creating main window...")
    root = tk.Tk()
    print("   OK")
    
    print("7. Creating App...")
    app = App(root, current_user)
    print("   OK")
    
    print("8. Starting mainloop...")
    root.mainloop()
    print("   App closed")
    
except Exception as e:
    print(f"\nERROR: {e}")
    traceback.print_exc()
    input("\nPress Enter to close...")
