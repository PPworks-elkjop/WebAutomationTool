"""
Change Password Dialog - Standalone dialog for changing user password
"""

import tkinter as tk
from tkinter import messagebox


class ChangePasswordDialog:
    """Dialog for changing current user's password."""
    
    def __init__(self, parent, current_user, db_manager):
        """
        Initialize change password dialog.
        
        Args:
            parent: Parent window
            current_user: Current user dict with username
            db_manager: DatabaseManager instance
        """
        self.parent = parent
        self.current_user = current_user
        self.db = db_manager
        self.username = current_user.get('username') if isinstance(current_user, dict) else current_user
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Change Password")
        self.dialog.geometry("500x550")
        self.dialog.configure(bg="#F5F5F5")
        self.dialog.transient(parent)
        self.dialog.resizable(False, False)
        
        self._build_dialog()
        self._center_dialog()
        
        # Grab focus
        self.dialog.update_idletasks()
        try:
            self.dialog.grab_set()
        except tk.TclError:
            pass
        
        self.dialog.focus_force()
    
    def _center_dialog(self):
        """Center dialog on parent or screen."""
        try:
            self.dialog.update_idletasks()
            x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
            y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
            self.dialog.geometry(f"+{x}+{y}")
        except (tk.TclError, AttributeError):
            # Center on screen
            try:
                self.dialog.update_idletasks()
                screen_width = self.dialog.winfo_screenwidth()
                screen_height = self.dialog.winfo_screenheight()
                x = (screen_width // 2) - (self.dialog.winfo_width() // 2)
                y = (screen_height // 2) - (self.dialog.winfo_height() // 2)
                self.dialog.geometry(f"+{x}+{y}")
            except (tk.TclError, AttributeError):
                pass
    
    def _build_dialog(self):
        """Build the dialog UI."""
        # Header
        header = tk.Frame(self.dialog, bg="#FFC107", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg="#FFC107")
        header_content.pack(expand=True)
        
        tk.Label(
            header_content,
            text="🔑 Change Password",
            font=("Segoe UI", 16, "bold"),
            bg="#FFC107",
            fg="#212529"
        ).pack()
        
        tk.Label(
            header_content,
            text=f"User: {self.username}",
            font=("Segoe UI", 10),
            bg="#FFC107",
            fg="#495057"
        ).pack(pady=(5, 0))
        
        # Content area
        content = tk.Frame(self.dialog, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill="both", expand=True)
        
        # Current Password (for verification)
        tk.Label(
            content,
            text="Current Password",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#495057"
        ).pack(anchor="w", pady=(0, 5))
        
        current_pwd_frame = tk.Frame(content, bg="#F8F9FA", relief=tk.SOLID, bd=1)
        current_pwd_frame.pack(fill="x", pady=(0, 15))
        
        self.current_password_entry = tk.Entry(
            current_pwd_frame,
            font=("Segoe UI", 11),
            show="●",
            bg="#F8F9FA",
            fg="#212529",
            relief=tk.FLAT,
            bd=0
        )
        self.current_password_entry.pack(fill="x", padx=10, pady=10)
        
        # New Password
        tk.Label(
            content,
            text="New Password",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#495057"
        ).pack(anchor="w", pady=(0, 5))
        
        new_pwd_frame = tk.Frame(content, bg="#F8F9FA", relief=tk.SOLID, bd=1)
        new_pwd_frame.pack(fill="x", pady=(0, 15))
        
        self.new_password_entry = tk.Entry(
            new_pwd_frame,
            font=("Segoe UI", 11),
            show="●",
            bg="#F8F9FA",
            fg="#212529",
            relief=tk.FLAT,
            bd=0
        )
        self.new_password_entry.pack(fill="x", padx=10, pady=10)
        
        # Confirm New Password
        tk.Label(
            content,
            text="Confirm New Password",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#495057"
        ).pack(anchor="w", pady=(0, 5))
        
        confirm_pwd_frame = tk.Frame(content, bg="#F8F9FA", relief=tk.SOLID, bd=1)
        confirm_pwd_frame.pack(fill="x", pady=(0, 10))
        
        self.confirm_password_entry = tk.Entry(
            confirm_pwd_frame,
            font=("Segoe UI", 11),
            show="●",
            bg="#F8F9FA",
            fg="#212529",
            relief=tk.FLAT,
            bd=0
        )
        self.confirm_password_entry.pack(fill="x", padx=10, pady=10)
        
        # Show passwords checkbox
        self.show_password_var = tk.BooleanVar(value=False)
        
        checkbox_frame = tk.Frame(content, bg="#FFFFFF")
        checkbox_frame.pack(anchor="w", pady=(0, 20))
        
        checkbox_box = tk.Frame(
            checkbox_frame,
            bg="#FFFFFF",
            relief=tk.SOLID,
            bd=1,
            width=16,
            height=16,
            cursor="hand2"
        )
        checkbox_box.pack(side=tk.LEFT, padx=(0, 8))
        checkbox_box.pack_propagate(False)
        
        self.checkbox_label = tk.Label(
            checkbox_box,
            text="",
            bg="#FFFFFF",
            fg="#FFC107",
            font=("Segoe UI", 10, "bold")
        )
        self.checkbox_label.pack(expand=True)
        
        text_label = tk.Label(
            checkbox_frame,
            text="Show passwords",
            font=("Segoe UI", 9),
            bg="#FFFFFF",
            fg="#495057",
            cursor="hand2"
        )
        text_label.pack(side=tk.LEFT)
        
        def toggle_show():
            self.show_password_var.set(not self.show_password_var.get())
            self._toggle_password()
        
        checkbox_box.bind("<Button-1>", lambda e: toggle_show())
        self.checkbox_label.bind("<Button-1>", lambda e: toggle_show())
        text_label.bind("<Button-1>", lambda e: toggle_show())
        
        # Password requirements
        requirements = tk.Label(
            content,
            text="Password must be at least 8 characters long",
            font=("Segoe UI", 9, "italic"),
            bg="#FFFFFF",
            fg="#6C757D"
        )
        requirements.pack(anchor="w", pady=(0, 20))
        
        # Buttons
        button_frame = tk.Frame(content, bg="#FFFFFF")
        button_frame.pack(fill="x")
        
        tk.Button(
            button_frame,
            text="Change Password",
            command=self._on_change,
            bg="#FFC107",
            fg="#212529",
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=25,
            pady=10,
            bd=0
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        tk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            bg="#6C757D",
            fg="white",
            font=("Segoe UI", 11),
            relief=tk.FLAT,
            cursor="hand2",
            padx=25,
            pady=10,
            bd=0
        ).pack(side=tk.RIGHT)
        
        # Bind Enter key
        self.dialog.bind("<Return>", lambda e: self._on_change())
        self.dialog.bind("<Escape>", lambda e: self._on_cancel())
        
        # Focus on current password
        self.current_password_entry.focus()
    
    def _toggle_password(self):
        """Toggle password visibility."""
        if self.show_password_var.get():
            self.current_password_entry.config(show="")
            self.new_password_entry.config(show="")
            self.confirm_password_entry.config(show="")
            self.checkbox_label.config(text="✓", bg="#FFC107", fg="white")
            self.checkbox_label.master.config(bg="#FFC107")
        else:
            self.current_password_entry.config(show="●")
            self.new_password_entry.config(show="●")
            self.confirm_password_entry.config(show="●")
            self.checkbox_label.config(text="", bg="#FFFFFF")
            self.checkbox_label.master.config(bg="#FFFFFF")
    
    def _on_change(self):
        """Handle change password button."""
        current_pwd = self.current_password_entry.get()
        new_pwd = self.new_password_entry.get()
        confirm_pwd = self.confirm_password_entry.get()
        
        # Validate inputs
        if not current_pwd:
            messagebox.showerror(
                "Validation Error",
                "Please enter your current password",
                parent=self.dialog
            )
            self.current_password_entry.focus()
            return
        
        if not new_pwd:
            messagebox.showerror(
                "Validation Error",
                "Please enter a new password",
                parent=self.dialog
            )
            self.new_password_entry.focus()
            return
        
        if len(new_pwd) < 8:
            messagebox.showerror(
                "Validation Error",
                "Password must be at least 8 characters long",
                parent=self.dialog
            )
            self.new_password_entry.focus()
            return
        
        if new_pwd != confirm_pwd:
            messagebox.showerror(
                "Validation Error",
                "New passwords do not match",
                parent=self.dialog
            )
            self.confirm_password_entry.focus()
            return
        
        if current_pwd == new_pwd:
            messagebox.showwarning(
                "Validation Warning",
                "New password must be different from current password",
                parent=self.dialog
            )
            self.new_password_entry.focus()
            return
        
        # Verify current password
        user = self.db.authenticate_user(self.username, current_pwd)
        if not user:
            messagebox.showerror(
                "Authentication Failed",
                "Current password is incorrect",
                parent=self.dialog
            )
            self.current_password_entry.delete(0, tk.END)
            self.current_password_entry.focus()
            return
        
        # Change password
        success, message = self.db.update_user(
            self.username,
            password=new_pwd,
            updated_by=self.username
        )
        
        if success:
            messagebox.showinfo(
                "Success",
                "Password changed successfully!\n\n"
                "Your password has been updated with secure bcrypt hashing.",
                parent=self.dialog
            )
            self.dialog.destroy()
        else:
            messagebox.showerror(
                "Error",
                f"Failed to change password:\n{message}",
                parent=self.dialog
            )
    
    def _on_cancel(self):
        """Handle cancel button."""
        self.dialog.destroy()


def main():
    """Test the change password dialog."""
    root = tk.Tk()
    root.withdraw()
    
    from database_manager import DatabaseManager
    db = DatabaseManager()
    
    # Test with a user
    current_user = {'username': 'peterander'}
    
    ChangePasswordDialog(root, current_user, db)
    root.mainloop()


if __name__ == "__main__":
    main()
