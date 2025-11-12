"""
Login Dialog - Authentication dialog for VERA applications
"""

import tkinter as tk
from tkinter import ttk, messagebox
from user_manager_v2 import UserManager

class LoginDialog:
    """Login dialog for user authentication."""
    
    def __init__(self, parent=None):
        self.result = None
        self.user_manager = UserManager()
        
        # Always create as standalone Tk window for better visibility
        self.dialog = tk.Tk()
        
        self.dialog.title("VERA - Login")
        self.dialog.geometry("400x450")
        self.dialog.resizable(False, False)
        
        # Force window to front and make it visible
        self.dialog.lift()
        self.dialog.focus_force()
        self.dialog.attributes('-topmost', True)
        self.dialog.after(100, lambda: self.dialog.attributes('-topmost', False))
        
        # Center the window
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        self.dialog.grab_set()
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        self._build_ui()
        
        # Focus on username field
        self.username_entry.focus()
        
        # Bind Enter key to login
        self.dialog.bind('<Return>', lambda e: self._on_login())
    
    def _build_ui(self):
        """Build the login dialog UI."""
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        bg_color = "#F5F5F5"
        frame_bg = "#FFFFFF"
        accent_color = "#28A745"
        
        self.dialog.configure(bg=bg_color)
        
        style.configure("Login.TFrame", background=frame_bg)
        style.configure("Login.TLabel", background=frame_bg, foreground="#333333", font=("Segoe UI", 10))
        style.configure("Login.Title.TLabel", background=frame_bg, foreground="#333333", font=("Segoe UI", 16, "bold"))
        style.configure("Login.TEntry", fieldbackground="white", padding=8)
        style.configure("Login.TButton", background=accent_color, foreground="white", font=("Segoe UI", 10), padding=8)
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=30, style="Login.TFrame")
        main_frame.pack(fill="both", expand=True)
        
        # Title with robot-granny emoji
        title_label = ttk.Label(main_frame, text="👵🤖 VERA", style="Login.Title.TLabel")
        title_label.pack(pady=(0, 5))
        
        subtitle_label = ttk.Label(main_frame, text="Vusion support with a human touch", 
                                   style="Login.TLabel", font=("Segoe UI", 9, "italic"))
        subtitle_label.pack(pady=(0, 5))
        
        signin_label = ttk.Label(main_frame, text="Please sign in to continue", style="Login.TLabel")
        signin_label.pack(pady=(0, 30))
        
        # Username
        username_frame = ttk.Frame(main_frame, style="Login.TFrame")
        username_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(username_frame, text="Username:", style="Login.TLabel").pack(anchor="w", pady=(0, 5))
        self.username_entry = ttk.Entry(username_frame, font=("Segoe UI", 10), style="Login.TEntry")
        self.username_entry.pack(fill="x")
        self.username_entry.insert(0, "peterander")  # Pre-fill for testing
        
        # Password
        password_frame = ttk.Frame(main_frame, style="Login.TFrame")
        password_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(password_frame, text="Password:", style="Login.TLabel").pack(anchor="w", pady=(0, 5))
        self.password_entry = ttk.Entry(password_frame, show="*", font=("Segoe UI", 10), style="Login.TEntry")
        self.password_entry.pack(fill="x")
        self.password_entry.insert(0, "Test1234567890")  # Pre-fill for testing
        
        # Show password checkbox
        self.show_password_var = tk.BooleanVar(value=False)
        show_pwd_check = ttk.Checkbutton(password_frame, text="Show password", 
                                         variable=self.show_password_var,
                                         command=self._toggle_password)
        show_pwd_check.pack(anchor="w", pady=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame, style="Login.TFrame")
        button_frame.pack(fill="x", pady=(10, 0))
        
        login_btn = tk.Button(button_frame, text="Login", command=self._on_login, 
                             font=("Segoe UI", 10), bg="#28A745", fg="white",
                             relief="flat", padx=20, pady=8, cursor="hand2")
        login_btn.pack(side="right", padx=(10, 0))
        
        cancel_btn = tk.Button(button_frame, text="Cancel", command=self._on_cancel,
                              font=("Segoe UI", 10), bg="#6C757D", fg="white",
                              relief="flat", padx=20, pady=8, cursor="hand2")
        cancel_btn.pack(side="right")
    
    def _toggle_password(self):
        """Toggle password visibility."""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")
    
    def _on_login(self):
        """Handle login button click."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Login Failed", "Please enter both username and password")
            return
        
        # Authenticate
        user = self.user_manager.authenticate(username, password)
        if user:
            self.result = user
            self.dialog.quit()  # Exit mainloop but don't destroy
            self.dialog.withdraw()  # Hide the window
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.result = None
        self.dialog.quit()  # Exit mainloop but don't destroy
        self.dialog.withdraw()  # Hide the window
    
    def show(self):
        """Show the dialog and return the result."""
        self.dialog.mainloop()  # Run our own mainloop
        return self.result
    
    def cleanup(self):
        """Clean up login dialog widgets before reusing the root window."""
        # Destroy all children widgets to avoid geometry manager conflicts
        for widget in self.dialog.winfo_children():
            widget.destroy()
    
    def get_root(self):
        """Return the Tk root window for reuse."""
        return self.dialog


def main():
    """Test the login dialog."""
    result = LoginDialog().show()
    if result:
        print(f"Login successful!")
        print(f"  Name: {result['full_name']}")
        print(f"  Username: {result['username']}")
        print(f"  Role: {result['role']}")
    else:
        print("Login cancelled")


if __name__ == "__main__":
    main()
