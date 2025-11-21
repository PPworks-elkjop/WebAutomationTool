"""
User Manager GUI - Interface for managing users

Features:
- Admins: Can add/remove users, view all users
- Users: Can only change their own password
- Passwords only visible to the user they belong to
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from user_manager import UserManager

class UserManagerGUI:
    """GUI for managing users with role-based permissions."""
    
    def __init__(self, current_user: dict, parent=None):
        self.current_user = current_user
        self.user_manager = UserManager()
        self.is_admin = current_user['role'] == UserManager.ROLE_ADMIN
        
        # Create window
        if parent:
            self.root = tk.Toplevel(parent)
            self.root.transient(parent)
        else:
            self.root = tk.Tk()
        
        self.root.title(f"User Manager - {current_user['full_name']} ({current_user['role']})")
        self.root.geometry("900x600")
        
        self._build_ui()
        self._refresh_list()
    
    def _build_ui(self):
        """Build the user interface."""
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        bg_color = "#F5F5F5"
        frame_bg = "#FFFFFF"
        accent_color = "#28A745"
        
        self.root.configure(bg=bg_color)
        
        style.configure("Modern.TFrame", background=frame_bg)
        style.configure("Modern.TLabelframe", background=frame_bg)
        style.configure("Modern.TLabelframe.Label", background=frame_bg, foreground="#333333", font=("Segoe UI", 11, "bold"))
        style.configure("Modern.TLabel", background=frame_bg, foreground="#555555", font=("Segoe UI", 10))
        style.configure("Modern.TButton", background=accent_color, foreground="white", font=("Segoe UI", 10), padding=6)
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding=20, style="Modern.TFrame")
        main_frame.pack(fill="both", expand=True)
        
        # Toolbar
        toolbar = ttk.Frame(main_frame, style="Modern.TFrame")
        toolbar.pack(fill="x", pady=(0, 10))
        
        if self.is_admin:
            ttk.Button(toolbar, text="➕ Add User", command=self._add_user, style="Modern.TButton").pack(side="left", padx=(0, 5))
            ttk.Button(toolbar, text="🗑️ Delete User", command=self._delete_user, style="Modern.TButton").pack(side="left", padx=(0, 5))
        
        ttk.Button(toolbar, text="🔑 Change Password", command=self._change_password, style="Modern.TButton").pack(side="left", padx=(0, 5))
        ttk.Button(toolbar, text="🔄 Refresh", command=self._refresh_list, style="Modern.TButton").pack(side="left", padx=(0, 5))
        ttk.Button(toolbar, text="❌ Close", command=self.root.destroy, style="Modern.TButton").pack(side="right")
        
        # User list
        list_frame = ttk.LabelFrame(main_frame, text="Users", padding=10, style="Modern.TLabelframe")
        list_frame.pack(fill="both", expand=True)
        
        # Create Treeview with scrollbars
        tree_scroll_y = ttk.Scrollbar(list_frame)
        tree_scroll_y.pack(side="right", fill="y")
        
        tree_scroll_x = ttk.Scrollbar(list_frame, orient="horizontal")
        tree_scroll_x.pack(side="bottom", fill="x")
        
        columns = ("Full Name", "Username", "Role", "Created", "Last Modified")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings",
                                yscrollcommand=tree_scroll_y.set,
                                xscrollcommand=tree_scroll_x.set,
                                selectmode="browse")
        
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)
        
        # Configure columns
        self.tree.heading("Full Name", text="Full Name")
        self.tree.heading("Username", text="Username")
        self.tree.heading("Role", text="Role")
        self.tree.heading("Created", text="Created")
        self.tree.heading("Last Modified", text="Last Modified")
        
        self.tree.column("Full Name", width=200)
        self.tree.column("Username", width=150)
        self.tree.column("Role", width=100)
        self.tree.column("Created", width=180)
        self.tree.column("Last Modified", width=180)
        
        self.tree.pack(fill="both", expand=True)
        
        # Bind double-click
        self.tree.bind('<Double-Button-1>', lambda e: self._change_password())
    
    def _refresh_list(self):
        """Refresh the user list."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add users
        users = self.user_manager.get_all_users()
        for user in users:
            values = (
                user['full_name'],
                user['username'],
                user['role'],
                user.get('created_at', '')[:19] if user.get('created_at') else '',
                user.get('last_modified', '')[:19] if user.get('last_modified') else ''
            )
            self.tree.insert('', 'end', values=values, tags=(user['username'],))
    
    def _add_user(self):
        """Add a new user (Admin only)."""
        if not self.is_admin:
            messagebox.showerror("Access Denied", "Only administrators can add users")
            return
        
        dialog = UserDialog(self.root, "Add User", is_admin=True)
        result = dialog.show()
        
        if result:
            success, message = self.user_manager.add_user(
                result['full_name'],
                result['username'],
                result['password'],
                result['role']
            )
            
            if success:
                messagebox.showinfo("Success", message)
                self._refresh_list()
            else:
                messagebox.showerror("Error", message)
    
    def _delete_user(self):
        """Delete a user (Admin only)."""
        if not self.is_admin:
            messagebox.showerror("Access Denied", "Only administrators can delete users")
            return
        
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a user to delete")
            return
        
        item = self.tree.item(selected[0])
        username = item['values'][1]
        
        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete user '{username}'?"):
            success, message = self.user_manager.delete_user(username)
            
            if success:
                messagebox.showinfo("Success", message)
                self._refresh_list()
            else:
                messagebox.showerror("Error", message)
    
    def _change_password(self):
        """Change password."""
        selected = self.tree.selection()
        if not selected:
            # If no selection, change own password
            username = self.current_user['username']
        else:
            item = self.tree.item(selected[0])
            username = item['values'][1]
        
        # Check if user can change this password
        if not self.is_admin and username != self.current_user['username']:
            messagebox.showerror("Access Denied", "You can only change your own password")
            return
        
        # Get user info
        user = self.user_manager.find_by_username(username)
        if not user:
            messagebox.showerror("Error", "User not found")
            return
        
        # Show password dialog
        dialog = PasswordDialog(self.root, username, user['password'], 
                               can_see_current=True)  # Only own password visible
        result = dialog.show()
        
        if result:
            success, message = self.user_manager.update_user(username, password=result)
            
            if success:
                messagebox.showinfo("Success", message)
                self._refresh_list()
            else:
                messagebox.showerror("Error", message)


class UserDialog:
    """Dialog for adding/editing users."""
    
    def __init__(self, parent, title, user=None, is_admin=False):
        self.result = None
        self.is_admin = is_admin
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x350")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._build_ui(user)
    
    def _build_ui(self, user):
        """Build the dialog UI."""
        frame = ttk.Frame(self.dialog, padding=20)
        frame.pack(fill="both", expand=True)
        
        # Full Name
        ttk.Label(frame, text="Full Name:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.full_name_entry = ttk.Entry(frame, width=40, font=("Segoe UI", 10))
        self.full_name_entry.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        
        # Username
        ttk.Label(frame, text="Username:").grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.username_entry = ttk.Entry(frame, width=40, font=("Segoe UI", 10))
        self.username_entry.grid(row=3, column=0, sticky="ew", pady=(0, 15))
        
        # Password
        ttk.Label(frame, text="Password:").grid(row=4, column=0, sticky="w", pady=(0, 5))
        self.password_entry = ttk.Entry(frame, width=40, show="*", font=("Segoe UI", 10))
        self.password_entry.grid(row=5, column=0, sticky="ew", pady=(0, 15))
        
        # Show password checkbox
        self.show_password_var = tk.BooleanVar(value=False)
        show_pwd_check = ttk.Checkbutton(frame, text="Show password", 
                                         variable=self.show_password_var,
                                         command=lambda: self.password_entry.config(
                                             show="" if self.show_password_var.get() else "*"))
        show_pwd_check.grid(row=6, column=0, sticky="w", pady=(0, 15))
        
        # Role (only for admins)
        if self.is_admin:
            ttk.Label(frame, text="Role:").grid(row=7, column=0, sticky="w", pady=(0, 5))
            self.role_var = tk.StringVar(value=UserManager.ROLE_USER)
            role_frame = ttk.Frame(frame)
            role_frame.grid(row=8, column=0, sticky="w", pady=(0, 15))
            ttk.Radiobutton(role_frame, text="User", variable=self.role_var, 
                           value=UserManager.ROLE_USER).pack(side="left", padx=(0, 20))
            ttk.Radiobutton(role_frame, text="Admin", variable=self.role_var, 
                           value=UserManager.ROLE_ADMIN).pack(side="left")
        else:
            self.role_var = tk.StringVar(value=UserManager.ROLE_USER)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=9, column=0, sticky="e", pady=(10, 0))
        
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side="right", padx=(10, 0))
        ttk.Button(button_frame, text="Save", command=self._on_save).pack(side="right")
        
        # Populate if editing
        if user:
            self.full_name_entry.insert(0, user.get('full_name', ''))
            self.username_entry.insert(0, user.get('username', ''))
            self.password_entry.insert(0, user.get('password', ''))
            if 'role' in user:
                self.role_var.set(user['role'])
    
    def _on_save(self):
        """Handle save button."""
        full_name = self.full_name_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        role = self.role_var.get()
        
        if not full_name or not username or not password:
            messagebox.showerror("Validation Error", "All fields are required")
            return
        
        self.result = {
            'full_name': full_name,
            'username': username,
            'password': password,
            'role': role
        }
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Handle cancel button."""
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and return result."""
        self.dialog.wait_window()
        return self.result


class PasswordDialog:
    """Dialog for changing password."""
    
    def __init__(self, parent, username, current_password, can_see_current=True):
        self.result = None
        self.can_see_current = can_see_current
        self.current_password = current_password if can_see_current else "********"
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Change Password - {username}")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the dialog UI."""
        frame = ttk.Frame(self.dialog, padding=20)
        frame.pack(fill="both", expand=True)
        
        # Current Password (display only)
        ttk.Label(frame, text="Current Password:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        current_pwd_entry = ttk.Entry(frame, width=40, font=("Segoe UI", 10))
        current_pwd_entry.insert(0, self.current_password if self.can_see_current else "********")
        current_pwd_entry.config(state="readonly")
        current_pwd_entry.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        
        # New Password
        ttk.Label(frame, text="New Password:").grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.new_password_entry = ttk.Entry(frame, width=40, show="*", font=("Segoe UI", 10))
        self.new_password_entry.grid(row=3, column=0, sticky="ew", pady=(0, 15))
        
        # Confirm Password
        ttk.Label(frame, text="Confirm Password:").grid(row=4, column=0, sticky="w", pady=(0, 5))
        self.confirm_password_entry = ttk.Entry(frame, width=40, show="*", font=("Segoe UI", 10))
        self.confirm_password_entry.grid(row=5, column=0, sticky="ew", pady=(0, 15))
        
        # Show password checkbox
        self.show_password_var = tk.BooleanVar(value=False)
        show_pwd_check = ttk.Checkbutton(frame, text="Show passwords", 
                                         variable=self.show_password_var,
                                         command=self._toggle_password)
        show_pwd_check.grid(row=6, column=0, sticky="w", pady=(0, 15))
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=7, column=0, sticky="e", pady=(10, 0))
        
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side="right", padx=(10, 0))
        ttk.Button(button_frame, text="Change Password", command=self._on_save).pack(side="right")
    
    def _toggle_password(self):
        """Toggle password visibility."""
        show = "" if self.show_password_var.get() else "*"
        self.new_password_entry.config(show=show)
        self.confirm_password_entry.config(show=show)
    
    def _on_save(self):
        """Handle save button."""
        new_password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        if not new_password:
            messagebox.showerror("Validation Error", "Password cannot be empty")
            return
        
        if new_password != confirm_password:
            messagebox.showerror("Validation Error", "Passwords do not match")
            return
        
        self.result = new_password
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Handle cancel button."""
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and return result."""
        self.dialog.wait_window()
        return self.result


def main():
    """Test the user manager GUI."""
    # Simulate logged in user
    test_user = {
        'full_name': 'Elkjop Master',
        'username': 'MasterBlaster',
        'role': UserManager.ROLE_ADMIN
    }
    
    root = tk.Tk()
    root.withdraw()
    app = UserManagerGUI(test_user)
    root.mainloop()


if __name__ == "__main__":
    main()
