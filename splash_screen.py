"""
Splash Screen for AP Helper v3
Shows during application startup with progress bar
"""

import tkinter as tk
from tkinter import ttk
import time


class SplashScreen:
    """Splash screen with progress bar."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("")
        self.root.overrideredirect(True)  # Remove window decorations
        
        # Window size
        width = 500
        height = 300
        
        # Center on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.configure(bg="#0066CC")
        
        self._create_ui()
    
    def _create_ui(self):
        """Create splash screen UI."""
        # Main container
        container = tk.Frame(self.root, bg="#FFFFFF", bd=5, relief=tk.FLAT)
        container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Header with gradient effect (simulated with color)
        header = tk.Frame(container, bg="#0066CC", height=100)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # Logo and title container
        title_container = tk.Frame(header, bg="#0066CC")
        title_container.pack(pady=(15, 2))
        
        # V logo
        logo_frame = tk.Frame(title_container, bg="white", width=45, height=45)
        logo_frame.pack(side=tk.LEFT, padx=(0, 12))
        logo_frame.pack_propagate(False)
        
        tk.Label(logo_frame, text="V", font=('Segoe UI', 26, 'bold'),
                bg="white", fg="#003D82").pack(expand=True)
        
        # App name with VERA branding
        tk.Label(title_container, text="VERA", font=('Segoe UI', 32, 'bold'),
                bg="#0066CC", fg="white").pack(anchor="w")
        
        tk.Label(header, text="Vusion Expert Robot Assistant", font=('Segoe UI', 11),
                bg="#0066CC", fg="#E0E0E0").pack(pady=(0, 2))
        
        tk.Label(header, text="Version 3.0", font=('Segoe UI', 10),
                bg="#0066CC", fg="#B0C4DE").pack()
        
        # Content area
        content = tk.Frame(container, bg="#FFFFFF", padx=40, pady=30)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Status label
        self.status_label = tk.Label(content, text="Initializing...",
                                     font=('Segoe UI', 11),
                                     bg="#FFFFFF", fg="#495057")
        self.status_label.pack(pady=(0, 20))
        
        # Progress bar
        self.progress = ttk.Progressbar(content, mode='determinate',
                                       length=400)
        self.progress.pack(pady=(0, 10))
        
        # Progress percentage
        self.progress_label = tk.Label(content, text="0%",
                                       font=('Segoe UI', 9),
                                       bg="#FFFFFF", fg="#6C757D")
        self.progress_label.pack()
        
        # Footer
        footer = tk.Frame(container, bg="#F8F9FA", height=40)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        tk.Label(footer, text="© 2025 Elkjøp - Loading application...",
                font=('Segoe UI', 8), bg="#F8F9FA", fg="#6C757D").pack(expand=True)
    
    def update_progress(self, percent, message):
        """Update progress bar and message.
        
        Args:
            percent: Progress percentage (0-100)
            message: Status message to display
        """
        self.progress['value'] = percent
        self.progress_label.config(text=f"{percent}%")
        self.status_label.config(text=message)
        self.root.update_idletasks()
        self.root.update()
    
    def close(self):
        """Close splash screen."""
        self.root.destroy()
    
    def show(self):
        """Show splash screen (for testing)."""
        self.root.mainloop()


def show_splash_with_loading(on_complete=None):
    """Show splash screen with simulated loading progress.
    
    Args:
        on_complete: Callback function to call when loading is complete
    """
    splash = SplashScreen()
    
    # Simulate loading steps
    loading_steps = [
        (10, "Loading configuration..."),
        (20, "Connecting to database..."),
        (35, "Initializing modules..."),
        (50, "Loading user interface..."),
        (65, "Setting up components..."),
        (80, "Finalizing setup..."),
        (95, "Almost ready..."),
        (100, "Starting application...")
    ]
    
    for percent, message in loading_steps:
        splash.update_progress(percent, message)
        time.sleep(0.3)  # Simulate work
    
    splash.close()
    
    if on_complete:
        on_complete()


# Test splash screen
if __name__ == '__main__':
    def on_done():
        print("Splash screen closed, starting main app...")
    
    show_splash_with_loading(on_done)
