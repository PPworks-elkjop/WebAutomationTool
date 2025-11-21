"""
Modern User Manager - Enhanced UI matching credential manager style
"""

import tkinter as tk
from tkinter import ttk, messagebox
from user_manager_v2 import UserManager
from datetime import datetime


class ModernUserManager:
    """Modern user manager with enhanced UI and audit logging."""
    
    def __init__(self, current_user, parent=None, db_manager=None):
        """Initialize the modern user manager."""
        self.current_user = current_user
        self.db_manager = db_manager if db_manager else None
        
        print(f"DEBUG: ModernUserManager init - db_manager type: {type(db_manager)}, is None: {db_manager is None}")
        
        # If db_manager is provided, use it; otherwise create new UserManager
        if db_manager:
            print("DEBUG: Creating UserManagerWrapper")
            # Create a wrapper that mimics UserManager interface
            class UserManagerWrapper:
                def __init__(self, db):
                    self.db = db
                
                def get_all_users(self):
                    return self.db.get_all_users()
                
                def get_user(self, username):
                    return self.db.get_user(username)
                
                def find_by_username(self, username):
                    return self.db.get_user(username)
                
                def add_user(self, username, full_name, password, role, created_by):
                    return self.db.add_user(username, full_name, password, role, created_by)
                
                def update_user(self, username, **kwargs):
                    return self.db.update_user(username, **kwargs)
                
                def delete_user(self, username, deleted_by):
                    return self.db.delete_user(username, deleted_by)
                
                def count(self):
                    return len(self.db.get_all_users())
                
                def get_user_audit_log(self, target_username=None, actor_username=None, limit=100):
                    return self.db.get_user_audit_log(target_username, actor_username, limit)
            
            self.user_manager = UserManagerWrapper(db_manager)
            print(f"DEBUG: user_manager created, type: {type(self.user_manager)}, has db: {hasattr(self.user_manager, 'db')}")
        else:
            print("DEBUG: Creating new UserManager()")
            self.user_manager = UserManager()
            print(f"DEBUG: user_manager created, type: {type(self.user_manager)}")
        
        if parent:
            self.root = tk.Toplevel(parent)
            self.root.transient(parent)
        else:
            self.root = tk.Tk()
        
        # Set title with user context
        self.root.title(f"User Manager - {current_user['full_name']} ({current_user['role']})")
        self.root.geometry("1200x700")
        self.root.configure(bg="#F5F5F5")
        
        # Check permissions
        self.is_admin = (current_user.get('role', '').lower() == 'admin')
        
        self.selected_user = None
        self.sort_reverse = {}
        
        self._build_ui()
        self._refresh_list()
        self._center_window()
    
    def _center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _build_ui(self):
        """Build the modern UI."""
        # Header
        header_frame = tk.Frame(self.root, bg="#2C3E50", height=70)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="👥 User Manager",
            font=("Segoe UI", 18, "bold"),
            bg="#2C3E50",
            fg="white"
        ).pack(side="left", padx=20, pady=15)
        
        # Stats in header
        self.stats_label = tk.Label(
            header_frame,
            text="Loading...",
            font=("Segoe UI", 11),
            bg="#2C3E50",
            fg="#BDC3C7"
        )
        self.stats_label.pack(side="right", padx=20)
        
        # Main content area
        content_frame = tk.Frame(self.root, bg="#F5F5F5")
        content_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Toolbar
        self._build_toolbar(content_frame)
        
        # Search frame
        self._build_search_frame(content_frame)
        
        # User list
        self._build_user_list(content_frame)
        
        # Status bar
        self._build_status_bar()
    
    def _build_toolbar(self, parent):
        """Build the toolbar with action buttons."""
        toolbar = tk.Frame(parent, bg="#F5F5F5")
        toolbar.pack(fill="x", pady=(0, 10))
        
        # Left side buttons
        left_frame = tk.Frame(toolbar, bg="#F5F5F5")
        left_frame.pack(side="left")
        
        if self.is_admin:
            self._create_button(left_frame, "➕ Add User", "#28A745", self._add_user).pack(side="left", padx=(0, 5))
            self._create_button(left_frame, "✏️ Edit User", "#17A2B8", self._edit_user).pack(side="left", padx=(0, 5))
            self._create_button(left_frame, "🗑️ Delete User", "#DC3545", self._delete_user).pack(side="left", padx=(0, 5))
        
        self._create_button(left_frame, "🔑 Change Password", "#FFC107", self._change_password).pack(side="left", padx=(0, 5))
        
        if self.is_admin:
            tk.Frame(left_frame, bg="#DEE2E6", width=2, height=30).pack(side="left", padx=10)
            self._create_button(left_frame, "📋 Audit Log", "#6C757D", self._view_audit_log).pack(side="left", padx=(0, 5))
        
        # Right side buttons
        right_frame = tk.Frame(toolbar, bg="#F5F5F5")
        right_frame.pack(side="right")
        
        self._create_button(right_frame, "🔄 Refresh", "#6C757D", self._refresh_list).pack(side="left", padx=(0, 5))
        self._create_button(right_frame, "❌ Close", "#6C757D", self.root.destroy).pack(side="left")
    
    def _create_button(self, parent, text, color, command):
        """Create a modern styled button."""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=8,
            bd=0
        )
        
        # Hover effects
        def on_enter(e):
            btn.config(relief="raised")
        def on_leave(e):
            btn.config(relief="flat")
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    def _build_search_frame(self, parent):
        """Build the search frame."""
        search_frame = tk.Frame(parent, bg="white", relief="solid", bd=1)
        search_frame.pack(fill="x", pady=(0, 10))
        
        inner_frame = tk.Frame(search_frame, bg="white")
        inner_frame.pack(fill="x", padx=15, pady=12)
        
        tk.Label(
            inner_frame,
            text="🔎 Search:",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg="#2C3E50"
        ).pack(side="left", padx=(0, 10))
        
        self.search_entry = tk.Entry(
            inner_frame,
            font=("Segoe UI", 11),
            bg="#F8F9FA",
            fg="#495057",
            relief="solid",
            bd=1,
            width=50
        )
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=6)
        
        # Bind search events
        self.search_entry.bind('<KeyRelease>', lambda e: self._on_search_delayed())
        self.search_entry.bind('<Return>', lambda e: self._on_search())
        
        # Search button
        search_btn = tk.Button(
            inner_frame,
            text="🔍",
            command=self._on_search,
            bg="#007BFF",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=10,
            bd=0
        )
        search_btn.pack(side="left", padx=(5, 0))
        
        # Clear button
        def clear_search():
            self.search_entry.delete(0, tk.END)
            self._on_search()
        
        clear_btn = tk.Button(
            inner_frame,
            text="✖",
            command=clear_search,
            bg="#E9ECEF",
            fg="#6C757D",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=10,
            bd=0
        )
        clear_btn.pack(side="left", padx=(5, 0))
        
        self.search_timer = None
    
    def _on_search_delayed(self):
        """Debounced search."""
        if self.search_timer:
            self.root.after_cancel(self.search_timer)
        self.search_timer = self.root.after(300, self._on_search)
    
    def _on_search(self):
        """Handle search."""
        query = self.search_entry.get().strip().lower()
        
        if query:
            users = self.user_manager.get_all_users()
            filtered = [u for u in users if 
                       query in u.get('username', '').lower() or
                       query in u.get('full_name', '').lower() or
                       query in u.get('email', '').lower() or
                       query in u.get('role', '').lower()]
            self._refresh_list(filtered)
            self.status_label.config(text=f"Search: '{query}' - Found {len(filtered)} users")
        else:
            self._refresh_list()
            self.status_label.config(text="Ready")
    
    def _build_user_list(self, parent):
        """Build the user list treeview."""
        list_frame = tk.Frame(parent, bg="white", relief="solid", bd=1)
        list_frame.pack(fill="both", expand=True)
        
        # Scrollbars
        vsb = ttk.Scrollbar(list_frame, orient="vertical")
        vsb.pack(side="right", fill="y")
        
        hsb = ttk.Scrollbar(list_frame, orient="horizontal")
        hsb.pack(side="bottom", fill="x")
        
        # Treeview
        columns = ("Full Name", "Username", "Email", "Role", "Created By", "Last Login")
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            selectmode="browse"
        )
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configure columns
        self.tree.heading("Full Name", text="Full Name", command=lambda: self._sort_by_column("Full Name"))
        self.tree.heading("Username", text="Username", command=lambda: self._sort_by_column("Username"))
        self.tree.heading("Email", text="Email", command=lambda: self._sort_by_column("Email"))
        self.tree.heading("Role", text="Role", command=lambda: self._sort_by_column("Role"))
        self.tree.heading("Created By", text="Created By", command=lambda: self._sort_by_column("Created By"))
        self.tree.heading("Last Login", text="Last Login", command=lambda: self._sort_by_column("Last Login"))
        
        self.tree.column("Full Name", width=180)
        self.tree.column("Username", width=150)
        self.tree.column("Email", width=200)
        self.tree.column("Role", width=100)
        self.tree.column("Created By", width=150)
        self.tree.column("Last Login", width=180)
        
        self.tree.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Bind events
        self.tree.bind('<<TreeviewSelect>>', lambda e: self._on_select())
        self.tree.bind('<Double-Button-1>', lambda e: self._edit_user() if self.is_admin else self._change_password())
        
        # Configure row colors
        self.tree.tag_configure('admin', background='#FFF3CD')
        self.tree.tag_configure('user', background='#FFFFFF')
        
        # Result count label
        result_frame = tk.Frame(list_frame, bg="white")
        result_frame.pack(fill="x", padx=10, pady=5)
        
        self.result_label = tk.Label(
            result_frame,
            text="",
            font=("Segoe UI", 9),
            bg="white",
            fg="#6C757D"
        )
        self.result_label.pack(side="left")
    
    def _build_status_bar(self):
        """Build the status bar."""
        status_frame = tk.Frame(self.root, bg="#E9ECEF", height=30)
        status_frame.pack(fill="x", side="bottom")
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready",
            font=("Segoe UI", 9),
            bg="#E9ECEF",
            fg="#495057",
            anchor="w"
        )
        self.status_label.pack(side="left", padx=10, fill="x", expand=True)
    
    def _refresh_list(self, users=None):
        """Refresh the user list."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get users
        if users is None:
            users = self.user_manager.get_all_users()
        
        # Populate tree
        for user in users:
            last_login = user.get('last_login', '')
            if last_login:
                last_login = last_login[:19] if len(last_login) > 19 else last_login
            else:
                last_login = 'Never'
            
            values = (
                user.get('full_name', ''),
                user.get('username', ''),
                user.get('email', ''),
                user.get('role', ''),
                user.get('created_by', 'N/A'),
                last_login
            )
            
            tag = 'admin' if user.get('role', '').lower() == 'admin' else 'user'
            self.tree.insert('', 'end', values=values, tags=(user.get('username', ''), tag))
        
        # Update stats
        total = len(users)
        admin_count = sum(1 for u in users if u.get('role', '').lower() == 'admin')
        user_count = total - admin_count
        
        self.stats_label.config(text=f"Total: {total} users ({admin_count} admins, {user_count} users)")
        self.result_label.config(text=f"Showing {len(users)} users")
        self.status_label.config(text=f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    
    def _sort_by_column(self, col):
        """Sort treeview by column."""
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children('')]
        
        reverse = self.sort_reverse.get(col, False)
        self.sort_reverse[col] = not reverse
        
        items.sort(reverse=reverse)
        
        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)
    
    def _on_select(self):
        """Handle user selection."""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            if values and len(values) >= 2:
                username = str(values[1]).strip()
                self.selected_user = self.user_manager.find_by_username(username)
    
    def _add_user(self):
        """Add a new user."""
        if not self.is_admin:
            messagebox.showerror("Access Denied", "Only administrators can add users")
            return
        
        dialog = UserDialog(self.root, "Add New User", None, is_admin=True)
        if dialog.result:
            success, message = self.user_manager.add_user(
                dialog.result['username'],
                dialog.result['full_name'],
                dialog.result['password'],
                dialog.result['role'],
                created_by=self.current_user['username']
            )
            
            if success:
                messagebox.showinfo("Success", message, parent=self.root)
                self._refresh_list()
            else:
                messagebox.showerror("Error", message, parent=self.root)
    
    def _edit_user(self):
        """Edit selected user."""
        if not self.is_admin:
            messagebox.showerror("Access Denied", "Only administrators can edit users")
            return
        
        if not self.selected_user:
            messagebox.showwarning("No Selection", "Please select a user to edit", parent=self.root)
            return
        
        dialog = UserDialog(self.root, f"Edit User - {self.selected_user['username']}", 
                          self.selected_user, is_admin=True)
        if dialog.result:
            username = self.selected_user['username']
            
            # Build update parameters
            update_params = {
                'full_name': dialog.result.get('full_name'),
                'role': dialog.result.get('role'),
                'updated_by': self.current_user['username']
            }
            
            # Only include password if it was provided
            if 'password' in dialog.result and dialog.result['password']:
                update_params['password'] = dialog.result['password']
            
            success, message = self.user_manager.update_user(username, **update_params)
            
            if success:
                messagebox.showinfo("Success", message, parent=self.root)
                self._refresh_list()
            else:
                messagebox.showerror("Error", message, parent=self.root)
    
    def _delete_user(self):
        """Delete selected user."""
        if not self.is_admin:
            messagebox.showerror("Access Denied", "Only administrators can delete users")
            return
        
        if not self.selected_user:
            messagebox.showwarning("No Selection", "Please select a user to delete", parent=self.root)
            return
        
        username = self.selected_user['username']
        
        if username.lower() == self.current_user['username'].lower():
            messagebox.showerror("Error", "You cannot delete your own account", parent=self.root)
            return
        
        if messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete user '{username}'?\n\n"
                              "This action cannot be undone.",
                              parent=self.root):
            success, message = self.user_manager.delete_user(username, 
                                                            deleted_by=self.current_user['username'])
            
            if success:
                messagebox.showinfo("Success", message, parent=self.root)
                self._refresh_list()
                self.selected_user = None
            else:
                messagebox.showerror("Error", message, parent=self.root)
    
    def _change_password(self):
        """Change password."""
        if not self.selected_user:
            username = self.current_user['username']
        else:
            username = self.selected_user['username']
        
        # Check permissions
        if not self.is_admin and username.lower() != self.current_user['username'].lower():
            messagebox.showerror("Access Denied",
                               "You can only change your own password.\n"
                               "Ask an administrator to change other users' passwords.",
                               parent=self.root)
            return
        
        dialog = PasswordDialog(self.root, username)
        if dialog.result:
            success, message = self.user_manager.update_user(
                username,
                password=dialog.result,
                updated_by=self.current_user['username']
            )
            
            if success:
                messagebox.showinfo("Success", message, parent=self.root)
            else:
                messagebox.showerror("Error", message, parent=self.root)
    
    def _view_audit_log(self):
        """View audit log."""
        if not self.is_admin:
            messagebox.showerror("Access Denied", "Only administrators can view audit logs")
            return
        
        AuditLogViewer(self.root, self.user_manager)


class UserDialog:
    """Dialog for adding/editing users."""
    
    def __init__(self, parent, title, user=None, is_admin=False):
        self.result = None
        self.user = user
        self.is_admin = is_admin
        self.is_edit = user is not None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x650")
        self.dialog.configure(bg="#F5F5F5")
        self.dialog.transient(parent)
        
        self._build_dialog()
        self._center_dialog(parent)
        
        # Try to grab, but don't fail if it doesn't work
        self.dialog.update_idletasks()
        try:
            self.dialog.grab_set()
        except tk.TclError:
            pass
    
    def _center_dialog(self, parent):
        """Center dialog on parent."""
        try:
            self.dialog.update_idletasks()
            x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
            y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
            self.dialog.geometry(f"+{x}+{y}")
        except (tk.TclError, AttributeError):
            # If centering fails, try to center on screen
            try:
                self.dialog.update_idletasks()
                screen_width = self.dialog.winfo_screenwidth()
                screen_height = self.dialog.winfo_screenheight()
                x = (screen_width // 2) - (self.dialog.winfo_width() // 2)
                y = (screen_height // 2) - (self.dialog.winfo_height() // 2)
                self.dialog.geometry(f"+{x}+{y}")
            except (tk.TclError, AttributeError):
                # If all else fails, use default position
                pass
    
    def _build_dialog(self):
        """Build the dialog UI."""
        # Header
        header = tk.Frame(self.dialog, bg="#17A2B8", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        header_inner = tk.Frame(header, bg="#17A2B8")
        header_inner.pack(fill="both", expand=True, padx=20, pady=15)
        
        tk.Label(
            header_inner,
            text="👤 User Information",
            font=("Segoe UI", 14, "bold"),
            bg="#17A2B8",
            fg="white"
        ).pack(side="left")
        
        # Show username in header if editing
        if self.is_edit:
            tk.Label(
                header_inner,
                text=f"  •  {self.user.get('username', '')}",
                font=("Segoe UI", 12),
                bg="#17A2B8",
                fg="white"
            ).pack(side="left")
        
        # Content
        content = tk.Frame(self.dialog, bg="#F5F5F5")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        row = 0
        
        # Username (editable when creating, read-only when editing)
        tk.Label(content, text="Username:", font=("Segoe UI", 10, "bold"),
                bg="#F5F5F5", fg="#495057").grid(row=row, column=0, sticky="w", pady=(0, 5))
        row += 1
        self.username_entry = tk.Entry(content, font=("Segoe UI", 11), bd=1, relief="solid",
                                      bg="#FFFFFF" if not self.is_edit else "#E9ECEF", 
                                      fg="#212529")
        self.username_entry.grid(row=row, column=0, sticky="ew", ipady=6, pady=(0, 15))
        if self.is_edit:
            self.username_entry.insert(0, self.user.get('username', ''))
            self.username_entry.config(state='readonly')
        row += 1
        
        # Full Name
        tk.Label(content, text="Full Name:", font=("Segoe UI", 10, "bold"),
                bg="#F5F5F5", fg="#495057").grid(row=row, column=0, sticky="w", pady=(0, 5))
        row += 1
        self.full_name_entry = tk.Entry(content, font=("Segoe UI", 11), bd=1, relief="solid",
                                        bg="#FFFFFF", fg="#212529")
        self.full_name_entry.grid(row=row, column=0, sticky="ew", ipady=6, pady=(0, 15))
        row += 1
        
        # Email
        tk.Label(content, text="Email:", font=("Segoe UI", 10, "bold"),
                bg="#F5F5F5", fg="#495057").grid(row=row, column=0, sticky="w", pady=(0, 5))
        row += 1
        self.email_entry = tk.Entry(content, font=("Segoe UI", 11), bd=1, relief="solid",
                                    bg="#FFFFFF", fg="#212529")
        self.email_entry.grid(row=row, column=0, sticky="ew", ipady=6, pady=(0, 15))
        row += 1
        
        # Password - Show for both new and edit if admin
        if self.is_admin:
            password_label_text = "Password:" if not self.is_edit else "New Password (leave blank to keep current):"
            tk.Label(content, text=password_label_text, font=("Segoe UI", 10, "bold"),
                    bg="#F5F5F5", fg="#495057").grid(row=row, column=0, sticky="w", pady=(0, 5))
            row += 1
            self.password_entry = tk.Entry(content, font=("Segoe UI", 11), show="●", bd=1, relief="solid",
                                          bg="#FFFFFF", fg="#212529")
            self.password_entry.grid(row=row, column=0, sticky="ew", ipady=6, pady=(0, 10))
            row += 1
            
            # Show password checkbox with custom style
            self.show_password_var = tk.BooleanVar(value=False)
            show_pwd_frame = tk.Frame(content, bg="#F5F5F5")
            show_pwd_frame.grid(row=row, column=0, sticky="w", pady=(0, 15))
            
            show_pwd_btn = tk.Button(
                show_pwd_frame,
                text="👁 Show password" if not self.show_password_var.get() else "🔒 Hide password",
                command=self._toggle_password,
                bg="#E9ECEF",
                fg="#495057",
                font=("Segoe UI", 9),
                relief="flat",
                cursor="hand2",
                padx=10,
                pady=4,
                bd=0
            )
            show_pwd_btn.pack(side="left")
            self.show_pwd_btn = show_pwd_btn
            row += 1
        
        # Role - Show for admin users
        if self.is_admin:
            tk.Label(content, text="Role:", font=("Segoe UI", 10, "bold"),
                    bg="#F5F5F5", fg="#495057").grid(row=row, column=0, sticky="w", pady=(0, 5))
            row += 1
            self.role_var = tk.StringVar(value=UserManager.ROLE_USER)
            role_frame = tk.Frame(content, bg="#F5F5F5")
            role_frame.grid(row=row, column=0, sticky="w", pady=(0, 15))
            
            # Custom styled radio buttons
            user_btn = tk.Button(
                role_frame,
                text="👤 User",
                command=lambda: self._set_role(UserManager.ROLE_USER),
                bg="#007BFF",
                fg="white",
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                cursor="hand2",
                padx=20,
                pady=8,
                bd=0
            )
            user_btn.pack(side="left", padx=(0, 10))
            self.user_role_btn = user_btn
            
            admin_btn = tk.Button(
                role_frame,
                text="👑 Admin",
                command=lambda: self._set_role(UserManager.ROLE_ADMIN),
                bg="#E9ECEF",
                fg="#495057",
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                cursor="hand2",
                padx=20,
                pady=8,
                bd=0
            )
            admin_btn.pack(side="left")
            self.admin_role_btn = admin_btn
            row += 1
        else:
            self.role_var = tk.StringVar(value=UserManager.ROLE_USER)
        
        # Active status - Show for edit if admin
        if self.is_edit and self.is_admin:
            self.active_var = tk.BooleanVar(value=True)
            active_frame = tk.Frame(content, bg="#F5F5F5")
            active_frame.grid(row=row, column=0, sticky="w", pady=(0, 15))
            
            self.active_btn = tk.Button(
                active_frame,
                text="✓ Active (user can log in)",
                command=self._toggle_active,
                bg="#28A745",
                fg="white",
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                cursor="hand2",
                padx=15,
                pady=8,
                bd=0
            )
            self.active_btn.pack(side="left")
            row += 1
        else:
            self.active_var = tk.BooleanVar(value=True)
        
        content.grid_columnconfigure(0, weight=1)
        
        # Buttons
        button_frame = tk.Frame(self.dialog, bg="#F5F5F5")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            bg="#6C757D",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8
        )
        cancel_btn.pack(side="right", padx=(10, 0))
        
        save_btn = tk.Button(
            button_frame,
            text="Save" if self.is_edit else "Create User",
            command=self._on_save,
            bg="#28A745",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8
        )
        save_btn.pack(side="right")
        
        # Populate if editing
        if self.user:
            self.full_name_entry.insert(0, self.user.get('full_name') or '')
            self.email_entry.insert(0, self.user.get('email') or '')
            if 'role' in self.user:
                self.role_var.set(self.user['role'])
                self._set_role(self.user['role'])  # Update button colors
            if 'is_active' in self.user:
                self.active_var.set(self.user['is_active'])
                if not self.user['is_active']:
                    self._toggle_active()  # Update button color
        
        self.dialog.wait_window()
    
    def _toggle_password(self):
        """Toggle password visibility."""
        if hasattr(self, 'password_entry'):
            self.show_password_var.set(not self.show_password_var.get())
            self.password_entry.config(show="" if self.show_password_var.get() else "●")
            if hasattr(self, 'show_pwd_btn'):
                self.show_pwd_btn.config(
                    text="🔒 Hide password" if self.show_password_var.get() else "👁 Show password"
                )
    
    def _set_role(self, role):
        """Set role and update button colors."""
        self.role_var.set(role)
        if role == UserManager.ROLE_USER:
            self.user_role_btn.config(bg="#007BFF", fg="white")
            self.admin_role_btn.config(bg="#E9ECEF", fg="#495057")
        else:
            self.user_role_btn.config(bg="#E9ECEF", fg="#495057")
            self.admin_role_btn.config(bg="#FFC107", fg="#212529")
    
    def _toggle_active(self):
        """Toggle active status."""
        self.active_var.set(not self.active_var.get())
        if self.active_var.get():
            self.active_btn.config(
                text="✓ Active (user can log in)",
                bg="#28A745",
                fg="white"
            )
        else:
            self.active_btn.config(
                text="✗ Inactive (user cannot log in)",
                bg="#DC3545",
                fg="white"
            )
    
    def _on_save(self):
        """Handle save button."""
        full_name = self.full_name_entry.get().strip()
        email = self.email_entry.get().strip()
        role = self.role_var.get()
        is_active = self.active_var.get()
        
        if not self.is_edit:
            username = self.username_entry.get().strip()
            if not full_name or not username:
                messagebox.showerror("Validation Error", "Full name and username are required",
                                   parent=self.dialog)
                return
        else:
            username = self.user['username']
            if not full_name:
                messagebox.showerror("Validation Error", "Full name is required",
                                   parent=self.dialog)
                return
        
        # Handle password
        password = None
        if hasattr(self, 'password_entry'):
            password = self.password_entry.get()
            
            if not self.is_edit:
                # New user - password required
                if not password:
                    messagebox.showerror("Validation Error", "Password is required",
                                       parent=self.dialog)
                    return
                if len(password) < 8:
                    messagebox.showerror("Validation Error", "Password must be at least 8 characters long",
                                       parent=self.dialog)
                    return
            else:
                # Edit user - password optional, but if provided must be valid
                if password and len(password) < 8:
                    messagebox.showerror("Validation Error", "Password must be at least 8 characters long",
                                       parent=self.dialog)
                    return
                # Empty password on edit means don't change it
                if not password:
                    password = None
        
        self.result = {
            'full_name': full_name,
            'username': username,
            'email': email,
            'role': role,
            'is_active': is_active
        }
        
        if password:
            self.result['password'] = password
        
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Handle cancel button."""
        self.result = None
        self.dialog.destroy()


class PasswordDialog:
    """Dialog for changing password."""
    
    def __init__(self, parent, username):
        self.result = None
        self.username = username
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Change Password - {username}")
        self.dialog.geometry("500x350")
        self.dialog.configure(bg="#F5F5F5")
        self.dialog.transient(parent)
        
        self._build_dialog()
        self._center_dialog(parent)
        
        # Try to grab, but don't fail if it doesn't work
        self.dialog.update_idletasks()
        try:
            self.dialog.grab_set()
        except tk.TclError:
            pass
    
    def _center_dialog(self, parent):
        """Center dialog on parent."""
        try:
            self.dialog.update_idletasks()
            x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
            y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
            self.dialog.geometry(f"+{x}+{y}")
        except (tk.TclError, AttributeError):
            # If centering fails, try to center on screen
            try:
                self.dialog.update_idletasks()
                screen_width = self.dialog.winfo_screenwidth()
                screen_height = self.dialog.winfo_screenheight()
                x = (screen_width // 2) - (self.dialog.winfo_width() // 2)
                y = (screen_height // 2) - (self.dialog.winfo_height() // 2)
                self.dialog.geometry(f"+{x}+{y}")
            except (tk.TclError, AttributeError):
                # If all else fails, use default position
                pass
    
    def _build_dialog(self):
        """Build the dialog UI."""
        # Header
        header = tk.Frame(self.dialog, bg="#FFC107", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="🔑 Change Password",
            font=("Segoe UI", 14, "bold"),
            bg="#FFC107",
            fg="#212529"
        ).pack(side="left", padx=20, pady=15)
        
        # Content
        content = tk.Frame(self.dialog, bg="#F5F5F5")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Info
        tk.Label(
            content,
            text=f"Setting new password for: {self.username}",
            font=("Segoe UI", 11, "bold"),
            bg="#F5F5F5",
            fg="#495057"
        ).grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        # New Password
        tk.Label(content, text="New Password:", font=("Segoe UI", 10, "bold"),
                bg="#F5F5F5", fg="#495057").grid(row=1, column=0, sticky="w", pady=(0, 5))
        self.new_password_entry = tk.Entry(content, font=("Segoe UI", 10), show="●", bd=1, relief="solid")
        self.new_password_entry.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        
        # Confirm Password
        tk.Label(content, text="Confirm Password:", font=("Segoe UI", 10, "bold"),
                bg="#F5F5F5", fg="#495057").grid(row=3, column=0, sticky="w", pady=(0, 5))
        self.confirm_password_entry = tk.Entry(content, font=("Segoe UI", 10), show="●", bd=1, relief="solid")
        self.confirm_password_entry.grid(row=4, column=0, sticky="ew", pady=(0, 15))
        
        # Show password checkbox
        self.show_password_var = tk.BooleanVar(value=False)
        show_pwd_check = tk.Checkbutton(
            content,
            text="Show passwords",
            variable=self.show_password_var,
            command=self._toggle_password,
            bg="#F5F5F5",
            font=("Segoe UI", 9)
        )
        show_pwd_check.grid(row=5, column=0, sticky="w", pady=(0, 15))
        
        content.grid_columnconfigure(0, weight=1)
        
        # Buttons
        button_frame = tk.Frame(self.dialog, bg="#F5F5F5")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            bg="#6C757D",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8
        )
        cancel_btn.pack(side="right", padx=(10, 0))
        
        save_btn = tk.Button(
            button_frame,
            text="Change Password",
            command=self._on_save,
            bg="#FFC107",
            fg="#212529",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8
        )
        save_btn.pack(side="right")
        
        self.dialog.wait_window()
    
    def _toggle_password(self):
        """Toggle password visibility."""
        show = "" if self.show_password_var.get() else "●"
        self.new_password_entry.config(show=show)
        self.confirm_password_entry.config(show=show)
    
    def _on_save(self):
        """Handle save button."""
        new_password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        if not new_password:
            messagebox.showerror("Validation Error", "Password cannot be empty",
                               parent=self.dialog)
            return
        
        if len(new_password) < 8:
            messagebox.showerror("Validation Error", "Password must be at least 8 characters long",
                               parent=self.dialog)
            return
        
        if new_password != confirm_password:
            messagebox.showerror("Validation Error", "Passwords do not match",
                               parent=self.dialog)
            return
        
        self.result = new_password
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Handle cancel button."""
        self.result = None
        self.dialog.destroy()


class AuditLogViewer:
    """Viewer for audit logs and user activity tracking."""
    
    def __init__(self, parent, user_manager):
        self.user_manager = user_manager
        
        self.window = tk.Toplevel(parent)
        self.window.title("User Audit Log & Activity Tracking")
        self.window.geometry("1200x700")
        self.window.configure(bg="#F5F5F5")
        self.window.transient(parent)
        
        self._build_ui()
        self._refresh_log()
    
    def _build_ui(self):
        """Build the audit log viewer UI with tabs."""
        # Header
        header = tk.Frame(self.window, bg="#2C3E50", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="📋 User Audit Log & Activity Tracking",
            font=("Segoe UI", 16, "bold"),
            bg="#2C3E50",
            fg="white"
        ).pack(side="left", padx=20, pady=15)
        
        # Content with tabs
        content = tk.Frame(self.window, bg="#F5F5F5")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(content)
        self.notebook.pack(fill="both", expand=True)
        
        # Audit Log tab
        self.audit_tab = tk.Frame(self.notebook, bg="#F5F5F5")
        self.notebook.add(self.audit_tab, text="Audit Log")
        
        # Activity Tracking tab
        self.activity_tab = tk.Frame(self.notebook, bg="#F5F5F5")
        self.notebook.add(self.activity_tab, text="Activity Tracking")
        
        # Build individual tab contents
        self._build_audit_tab()
        self._build_activity_tab()
    
    def _build_audit_tab(self):
        """Build the audit log tab content."""
        content = self.audit_tab
        
        # Toolbar
        toolbar = tk.Frame(content, bg="#F5F5F5")
        toolbar.pack(fill="x", pady=(10, 10))
        
        tk.Label(toolbar, text="Filter by user:", font=("Segoe UI", 10),
                bg="#F5F5F5", fg="#495057").pack(side="left", padx=(0, 5))
        self.audit_filter_var = tk.StringVar()
        filter_entry = tk.Entry(toolbar, textvariable=self.audit_filter_var, width=20,
                               font=("Segoe UI", 10), bd=1, relief="solid")
        filter_entry.pack(side="left", padx=(0, 5))
        
        filter_btn = tk.Button(
            toolbar,
            text="Filter",
            command=self._refresh_audit_log,
            bg="#007BFF",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5
        )
        filter_btn.pack(side="left", padx=(0, 5))
        
        clear_btn = tk.Button(
            toolbar,
            text="Clear",
            command=lambda: [self.audit_filter_var.set(''), self._refresh_audit_log()],
            bg="#6C757D",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5
        )
        clear_btn.pack(side="left", padx=(0, 5))
        
        refresh_btn = tk.Button(
            toolbar,
            text="🔄 Refresh",
            command=self._refresh_audit_log,
            bg="#6C757D",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5
        )
        refresh_btn.pack(side="left")
        
        # Audit log tree
        list_frame = tk.Frame(content, bg="white", relief="solid", bd=1)
        list_frame.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        columns = ("Timestamp", "Actor", "Action", "Target", "Details")
        self.audit_tree = ttk.Treeview(list_frame, columns=columns, show="headings",
                                yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.audit_tree.yview)
        
        for col in columns:
            self.audit_tree.heading(col, text=col)
        
        self.audit_tree.column("Timestamp", width=180)
        self.audit_tree.column("Actor", width=120)
        self.audit_tree.column("Action", width=150)
        self.audit_tree.column("Target", width=120)
        self.audit_tree.column("Details", width=500)
        
        self.audit_tree.pack(fill="both", expand=True, padx=2, pady=2)
    
    def _build_activity_tab(self):
        """Build the activity tracking tab content."""
        content = self.activity_tab
        
        # Toolbar
        toolbar = tk.Frame(content, bg="#F5F5F5")
        toolbar.pack(fill="x", pady=(10, 10))
        
        tk.Label(toolbar, text="Filter by user:", font=("Segoe UI", 10),
                bg="#F5F5F5", fg="#495057").pack(side="left", padx=(0, 5))
        self.activity_user_filter = tk.StringVar()
        user_entry = tk.Entry(toolbar, textvariable=self.activity_user_filter, width=20,
                             font=("Segoe UI", 10), bd=1, relief="solid")
        user_entry.pack(side="left", padx=(0, 5))
        
        tk.Label(toolbar, text="Activity type:", font=("Segoe UI", 10),
                bg="#F5F5F5", fg="#495057").pack(side="left", padx=(10, 5))
        self.activity_type_filter = tk.StringVar()
        type_combo = ttk.Combobox(toolbar, textvariable=self.activity_type_filter, width=18,
                                 font=("Segoe UI", 10), state="readonly")
        type_combo['values'] = ("All", "login", "logout", "ap_connect", "provision", "config_change", "view_credentials")
        type_combo.current(0)
        type_combo.pack(side="left", padx=(0, 5))
        
        filter_btn = tk.Button(
            toolbar,
            text="Filter",
            command=self._refresh_activity_log,
            bg="#007BFF",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5
        )
        filter_btn.pack(side="left", padx=(5, 5))
        
        clear_btn = tk.Button(
            toolbar,
            text="Clear",
            command=lambda: [self.activity_user_filter.set(''), self.activity_type_filter.set('All'), self._refresh_activity_log()],
            bg="#6C757D",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5
        )
        clear_btn.pack(side="left", padx=(0, 5))
        
        refresh_btn = tk.Button(
            toolbar,
            text="🔄 Refresh",
            command=self._refresh_activity_log,
            bg="#6C757D",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5
        )
        refresh_btn.pack(side="left")
        
        # Activity log tree
        list_frame = tk.Frame(content, bg="white", relief="solid", bd=1)
        list_frame.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        columns = ("Timestamp", "Username", "Activity Type", "Description", "AP ID", "Success", "Details")
        self.activity_tree = ttk.Treeview(list_frame, columns=columns, show="headings",
                                         yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.activity_tree.yview)
        
        for col in columns:
            self.activity_tree.heading(col, text=col)
        
        self.activity_tree.column("Timestamp", width=180)
        self.activity_tree.column("Username", width=120)
        self.activity_tree.column("Activity Type", width=130)
        self.activity_tree.column("Description", width=250)
        self.activity_tree.column("AP ID", width=100)
        self.activity_tree.column("Success", width=70)
        self.activity_tree.column("Details", width=200)
        
        self.activity_tree.pack(fill="both", expand=True, padx=2, pady=2)
    
    def _refresh_log(self):
        """Refresh both audit log and activity log."""
        self._refresh_audit_log()
        self._refresh_activity_log()
    
    def _refresh_audit_log(self):
        """Refresh the audit log tab."""
        # Clear existing items
        for item in self.audit_tree.get_children():
            self.audit_tree.delete(item)
        
        # Get filtered logs
        target = self.audit_filter_var.get().strip() or None
        logs = self.user_manager.get_user_audit_log(target_username=target, limit=500)
        
        # Add logs
        for log in logs:
            values = (
                log.get('timestamp', '')[:19],
                log.get('actor_username', ''),
                log.get('action', ''),
                log.get('target_username', ''),
                log.get('details', '')
            )
            self.audit_tree.insert('', 'end', values=values)
    
    def _refresh_activity_log(self):
        """Refresh the activity tracking tab."""
        # Clear existing items
        for item in self.activity_tree.get_children():
            self.activity_tree.delete(item)
        
        # Get filter values
        username = self.activity_user_filter.get().strip() or None
        activity_type = self.activity_type_filter.get()
        if activity_type == "All":
            activity_type = None
        
        # Get filtered activity logs
        try:
            logs = self.user_manager.db.get_user_activity_log(
                username=username,
                activity_type=activity_type,
                limit=500
            )
        except AttributeError as e:
            messagebox.showerror("Error", f"Failed to get activity log: {str(e)}\nuser_manager type: {type(self.user_manager)}\nhas db attr: {hasattr(self.user_manager, 'db')}")
            return
        
        # Add logs
        for log in logs:
            success_text = "✓" if log.get('success', True) else "✗"
            values = (
                log.get('timestamp', '')[:19],
                log.get('username', ''),
                log.get('activity_type', ''),
                log.get('description', ''),
                log.get('ap_id', '') or '',
                success_text,
                log.get('details', '') or ''
            )
            self.activity_tree.insert('', 'end', values=values)


def open_user_manager(current_user, parent=None, db_manager=None):
    """Open the modern user manager."""
    return ModernUserManager(current_user, parent, db_manager)


if __name__ == "__main__":
    # Test standalone
    test_user = {
        'full_name': 'Test Admin',
        'username': 'admin',
        'role': 'Admin'
    }
    app = ModernUserManager(test_user)
    app.root.mainloop()
