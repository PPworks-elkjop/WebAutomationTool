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
        self.dialog.geometry("400x550")
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
        self.dialog.configure(bg="#F8F9FA")
        
        # Header with gradient-like design
        header = tk.Frame(self.dialog, bg="#3D6B9E", height=140)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # Logo and title container
        title_container = tk.Frame(header, bg="#3D6B9E")
        title_container.pack(expand=True, pady=(20, 0))
        
        # V logo
        logo_frame = tk.Frame(title_container, bg="white", width=50, height=50)
        logo_frame.pack(side=tk.LEFT, padx=(0, 15))
        logo_frame.pack_propagate(False)
        
        tk.Label(logo_frame, text="V", font=('Segoe UI', 28, 'bold'),
                bg="white", fg="#003D82").pack(expand=True)
        
        # VERA title
        tk.Label(title_container, text="VERA", font=('Segoe UI', 32, 'bold'),
                bg="#3D6B9E", fg="white").pack(anchor="w")
        
        tk.Label(header, text="Vusion Expert Robot Assistant", font=('Segoe UI', 11),
                bg="#3D6B9E", fg="#E0E0E0").pack()
        
        tk.Label(header, text="Support with a human touch", font=('Segoe UI', 9, 'italic'),
                bg="#3D6B9E", fg="#B0C4DE").pack(pady=(2, 0))
        
        # Content area
        content = tk.Frame(self.dialog, bg="#FFFFFF", padx=40, pady=30)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text="Please sign in to continue", font=('Segoe UI', 10),
                bg="#FFFFFF", fg="#6C757D").pack(pady=(0, 25))
        
        # Username field
        tk.Label(content, text="Username", font=('Segoe UI', 9, 'bold'),
                bg="#FFFFFF", fg="#495057", anchor="w").pack(fill=tk.X, pady=(0, 5))
        
        username_container = tk.Frame(content, bg="#F8F9FA", relief=tk.SOLID, borderwidth=1)
        username_container.pack(fill=tk.X, pady=(0, 15))
        
        self.username_entry = tk.Entry(username_container, font=('Segoe UI', 11),
                                       bg="#F8F9FA", fg="#212529", relief=tk.FLAT, bd=0)
        self.username_entry.pack(fill=tk.X, padx=12, pady=10)
        
        # Password field
        tk.Label(content, text="Password", font=('Segoe UI', 9, 'bold'),
                bg="#FFFFFF", fg="#495057", anchor="w").pack(fill=tk.X, pady=(0, 5))
        
        password_container = tk.Frame(content, bg="#F8F9FA", relief=tk.SOLID, borderwidth=1)
        password_container.pack(fill=tk.X, pady=(0, 10))
        
        self.password_entry = tk.Entry(password_container, show="●", font=('Segoe UI', 11),
                                       bg="#F8F9FA", fg="#212529", relief=tk.FLAT, bd=0)
        self.password_entry.pack(fill=tk.X, padx=12, pady=10)
        
        # Show password checkbox
        self.show_password_var = tk.BooleanVar(value=False)
        check_container = tk.Frame(content, bg="#FFFFFF")
        check_container.pack(anchor="w", pady=(0, 25))
        
        checkbox_frame = tk.Frame(check_container, bg="#FFFFFF", relief=tk.SOLID, borderwidth=1,
                                 width=16, height=16, cursor="hand2")
        checkbox_frame.pack(side=tk.LEFT, padx=(0, 8))
        checkbox_frame.pack_propagate(False)
        
        self.checkbox_label = tk.Label(checkbox_frame, text="", bg="#FFFFFF", fg="#3D6B9E",
                                       font=('Segoe UI', 10, 'bold'))
        self.checkbox_label.pack(expand=True)
        
        text_label = tk.Label(check_container, text="Show password", font=('Segoe UI', 9),
                             bg="#FFFFFF", fg="#495057", cursor="hand2")
        text_label.pack(side=tk.LEFT)
        
        def toggle_show_password():
            self.show_password_var.set(not self.show_password_var.get())
            self._toggle_password()
        
        checkbox_frame.bind("<Button-1>", lambda e: toggle_show_password())
        self.checkbox_label.bind("<Button-1>", lambda e: toggle_show_password())
        text_label.bind("<Button-1>", lambda e: toggle_show_password())
        
        # Buttons
        button_frame = tk.Frame(content, bg="#FFFFFF")
        button_frame.pack(fill=tk.X)
        
        tk.Button(button_frame, text="Login", command=self._on_login,
                 bg="#3D6B9E", fg="white", font=('Segoe UI', 11, 'bold'),
                 padx=30, pady=10, relief=tk.FLAT, cursor="hand2",
                 borderwidth=0).pack(side=tk.RIGHT, padx=(10, 0))
        
        tk.Button(button_frame, text="Cancel", command=self._on_cancel,
                 bg="#6C757D", fg="white", font=('Segoe UI', 11),
                 padx=25, pady=10, relief=tk.FLAT, cursor="hand2",
                 borderwidth=0).pack(side=tk.RIGHT)
    
    def _toggle_password(self):
        """Toggle password visibility."""
        if self.show_password_var.get():
            self.password_entry.config(show="")
            self.checkbox_label.config(text="✓", bg="#3D6B9E", fg="#FFFFFF")
            self.checkbox_label.master.config(bg="#3D6B9E")
        else:
            self.password_entry.config(show="●")
            self.checkbox_label.config(text="", bg="#FFFFFF")
            self.checkbox_label.master.config(bg="#FFFFFF")
    
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
