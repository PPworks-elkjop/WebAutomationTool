"""
ESL AP Helper v3 - Dashboard Version
Modern 4-panel dashboard interface

Requirements:
    python -m pip install selenium webdriver-manager
"""

import sys
import tkinter as tk
from tkinter import messagebox
import threading
from pathlib import Path

# Import database and authentication
from database_manager import DatabaseManager
from login_dialog import LoginDialog
from dashboard_main import DashboardMain
from splash_screen import show_splash_with_loading

APP_NAME = "VERA"
APP_TAGLINE = "Vusion support with a human touch"
APP_VERSION = "3.0"
APP_RELEASE_DATE = "2025-11-16"


class APHelperV3:
    """Main application controller for v3."""
    
    def __init__(self):
        self.root = None
        self.db = None
        self.current_user = None
        self.dashboard = None
    
    def start(self):
        """Start the application with splash screen."""
        # Show splash screen during initialization
        def on_splash_complete():
            self._show_login()
        
        show_splash_with_loading(on_splash_complete)
    
    def _show_login(self):
        """Show login window."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide main window initially
        
        # Initialize database
        try:
            self.db = DatabaseManager()
        except Exception as e:
            messagebox.showerror("Database Error", 
                               f"Failed to initialize database:\n{e}\n\n"
                               "The application will now exit.")
            sys.exit(1)
        
        # Show login dialog
        login_dialog = LoginDialog(self.root)
        result = login_dialog.show()
        
        if result:
            self.current_user = result['username']
            self._start_dashboard()
        else:
            # User canceled login
            sys.exit(0)
    
    def _start_dashboard(self):
        """Start the main dashboard."""
        # Destroy login window if it exists
        if self.root:
            self.root.withdraw()
        
        # Create new main window for dashboard
        dashboard_root = tk.Tk()
        dashboard_root.protocol("WM_DELETE_WINDOW", self._on_dashboard_close)
        
        # Create dashboard
        self.dashboard = DashboardMain(dashboard_root, self.current_user, self.db)
        
        # Start main loop
        dashboard_root.mainloop()
    
    def _on_dashboard_close(self):
        """Handle dashboard close event."""
        if messagebox.askokcancel("Exit", "Are you sure you want to exit AP Helper v3?"):
            # Log logout
            try:
                self.db.log_user_activity(
                    username=self.current_user,
                    activity_type='logout',
                    description='User logged out',
                    success=True
                )
            except:
                pass
            
            # Close database
            if self.db:
                self.db.close()
            
            # Exit application
            sys.exit(0)


def main():
    """Main entry point."""
    print(f"{APP_NAME} v{APP_VERSION} - {APP_TAGLINE}")
    print(f"Released: {APP_RELEASE_DATE}")
    print("-" * 60)
    print("Starting dashboard interface...")
    print()
    
    # Create and start application
    app = APHelperV3()
    app.start()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
