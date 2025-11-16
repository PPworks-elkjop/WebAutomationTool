"""
Main Dashboard Window for AP Helper v3
4-panel layout with resizable panes
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from database_manager import DatabaseManager
from dashboard_components import APPanel, ContextPanel, ActivityLogPanel, ContentPanel


class DashboardMain:
    """Main dashboard window with 4-panel layout."""
    
    def __init__(self, root, current_user, db):
        self.root = root
        self.current_user = current_user
        self.db = db
        
        # Window setup
        self.root.title("VERA - Vusion support with a human touch")
        self.root.geometry("1600x900")
        self.root.configure(bg="#F0F0F0")
        
        # Shared state
        self.active_ap = None  # Currently active AP in AP panel
        self.active_ap_tab_index = None
        
        # Style configuration for larger tabs
        style = ttk.Style()
        style.configure('Dashboard.TNotebook.Tab', font=('Segoe UI', 11), padding=[15, 8])
        
        # Create UI
        self._create_menu()
        self._create_top_banner()
        self._create_dashboard()
        
        # Log startup
        self.activity_log.log_message("Dashboard", "Application started", "info")
        
        # Load admin notification if exists
        self._load_admin_notification()
    
    def _create_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Search AP", command=self._search_ap)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_exit)
        
        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Batch Ping", command=self._open_batch_ping)
        tools_menu.add_command(label="Batch Browser Operations", command=self._open_batch_browser)
        tools_menu.add_command(label="Batch SSH Operations", command=self._open_batch_ssh)
        
        # Admin Menu
        admin_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Admin", menu=admin_menu)
        admin_menu.add_command(label="Add New AP", command=self._add_new_ap)
        admin_menu.add_separator()
        admin_menu.add_command(label="Post System Notification", command=self._post_notification)
        admin_menu.add_separator()
        admin_menu.add_command(label="Manage AP Credentials", command=self._open_credentials_manager)
        admin_menu.add_command(label="Manage Users", command=self._open_user_management)
        admin_menu.add_command(label="Change Password", command=self._change_password)
        admin_menu.add_separator()
        admin_menu.add_command(label="Admin Settings", command=self._open_admin_settings)
        admin_menu.add_command(label="Audit Log", command=self._open_audit_log)
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self._show_documentation)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_top_banner(self):
        """Create top banner with app name, logo, and admin notifications."""
        banner = tk.Frame(self.root, bg="#0066CC", height=80)
        banner.pack(fill=tk.X, side=tk.TOP)
        banner.pack_propagate(False)
        
        # Left side: Logo and app name
        left_frame = tk.Frame(banner, bg="#0066CC")
        left_frame.pack(side=tk.LEFT, padx=20, pady=15)
        
        # SVG-style logo placeholder (will use actual SVG/icon later)
        logo_frame = tk.Frame(left_frame, bg="white", width=50, height=50)
        logo_frame.pack(side=tk.LEFT, padx=(0, 15))
        logo_frame.pack_propagate(False)
        
        tk.Label(logo_frame, text="V", font=('Segoe UI', 24, 'bold'),
                bg="white", fg="#0066CC").pack(expand=True)
        
        # App name and tagline
        name_frame = tk.Frame(left_frame, bg="#0066CC")
        name_frame.pack(side=tk.LEFT)
        
        tk.Label(name_frame, text="VERA", font=('Segoe UI', 20, 'bold'),
                bg="#0066CC", fg="white").pack(anchor="w")
        
        tk.Label(name_frame, text="Vusion support with a human touch", 
                font=('Segoe UI', 9),
                bg="#0066CC", fg="#E0E0E0").pack(anchor="w")
        
        # Right side: User info
        right_frame = tk.Frame(banner, bg="#0066CC")
        right_frame.pack(side=tk.RIGHT, padx=20, pady=15)
        
        tk.Label(right_frame, text=f"Welcome, {self.current_user}", 
                font=('Segoe UI', 10),
                bg="#0066CC", fg="white").pack(anchor="e")
        
        # Admin notification area (will be shown when notification exists)
        self.notification_frame = tk.Frame(self.root, bg="#FFF3CD", bd=1, relief=tk.SOLID)
        # Pack will be done when notification is loaded
    
    def _create_dashboard(self):
        """Create 4-panel dashboard layout with resizable panes."""
        
        # Main container with vertical split (upper / lower)
        main_paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Upper pane with horizontal split (AP Panel / Context Panel)
        upper_paned = ttk.PanedWindow(main_paned, orient=tk.HORIZONTAL)
        main_paned.add(upper_paned, weight=3)
        
        # Lower pane with horizontal split (Activity Log / Content Panel)
        lower_paned = ttk.PanedWindow(main_paned, orient=tk.HORIZONTAL)
        main_paned.add(lower_paned, weight=2)
        
        # === UPPER LEFT: AP Panel ===
        ap_frame = ttk.Frame(upper_paned, relief=tk.RIDGE, borderwidth=1)
        upper_paned.add(ap_frame, weight=1)
        
        self.ap_panel = APPanel(
            ap_frame, 
            self.current_user, 
            self.db,
            on_ap_change=self._on_ap_changed,
            on_tab_change=self._on_ap_tab_changed,
            log_callback=self._log_activity
        )
        
        # === UPPER RIGHT: Context Panel ===
        context_frame = ttk.Frame(upper_paned, relief=tk.RIDGE, borderwidth=1)
        upper_paned.add(context_frame, weight=1)
        
        self.context_panel = ContextPanel(
            context_frame,
            self.db,
            on_selection=self._on_context_selection,
            log_callback=self._log_activity
        )
        
        # === LOWER LEFT: Activity Log Panel ===
        log_frame = ttk.Frame(lower_paned, relief=tk.RIDGE, borderwidth=1)
        lower_paned.add(log_frame, weight=1)
        
        self.activity_log = ActivityLogPanel(log_frame)
        
        # === LOWER RIGHT: Content Panel ===
        content_frame = ttk.Frame(lower_paned, relief=tk.RIDGE, borderwidth=1)
        lower_paned.add(content_frame, weight=1)
        
        self.content_panel = ContentPanel(
            content_frame,
            self.db,
            log_callback=self._log_activity
        )
    
    # === Event Handlers ===
    
    def _on_ap_changed(self, ap_id, ap_data):
        """Called when active AP changes in AP panel."""
        self.active_ap = ap_data
        self.activity_log.log_message("AP Panel", f"Switched to AP {ap_id}", "info")
        
        # Update context panel to show data for this AP
        self.context_panel.set_active_ap(ap_id, ap_data)
        
        # Update content panel
        self.content_panel.show_ap_overview(ap_data)
    
    def _on_ap_tab_changed(self, ap_id, tab_name):
        """Called when user switches sub-tabs within an AP (Overview, Notes, Browser, SSH, Actions)."""
        self.activity_log.log_message("AP Panel", f"Switched to {tab_name} tab for AP {ap_id}", "info")
        
        # Update content panel based on active tab
        if tab_name == "SSH Terminal":
            self.content_panel.show_ssh_terminal(ap_id)
        elif tab_name == "Browser":
            self.content_panel.show_browser_status(ap_id)
        elif tab_name == "Notes":
            self.content_panel.show_notes(ap_id)
        elif tab_name == "Overview":
            if self.active_ap:
                self.content_panel.show_ap_overview(self.active_ap)
        else:
            # Default to overview
            if self.active_ap:
                self.content_panel.show_ap_overview(self.active_ap)
    
    def _on_context_selection(self, item_type, item_data):
        """Called when user selects something in context panel (Jira ticket, Vusion item, etc.)."""
        self.activity_log.log_message("Context Panel", f"Selected {item_type}", "info")
        
        # Show details in content panel
        if item_type == "jira":
            self.content_panel.show_jira_details(item_data)
        elif item_type == "vusion":
            self.content_panel.show_vusion_details(item_data)
        elif item_type == "note":
            self.content_panel.show_note_details(item_data)
    
    def _log_activity(self, source, message, level="info"):
        """Central logging function called by all panels."""
        self.activity_log.log_message(source, message, level)
    
    # === Menu Actions ===
    
    def _search_ap(self):
        """Open AP search dialog."""
        from ap_support_ui import APSearchDialog
        
        def on_ap_selected(ap_data):
            # Add AP as new tab in AP panel
            self.ap_panel.add_ap_tab(ap_data)
        
        APSearchDialog(self.root, self.current_user, self.db, on_select_callback=on_ap_selected)
    
    def _open_batch_ping(self):
        """Open batch ping window (independent)."""
        try:
            from batch_ping import BatchPingWindow
            BatchPingWindow(tk.Toplevel(), self.current_user, self.db)
            self.activity_log.log_message("Tools", "Opened Batch Ping", "info")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Batch Ping: {e}")
    
    def _open_batch_browser(self):
        """Open batch browser operations window (independent)."""
        try:
            from batch_browser import BatchBrowserWindow
            BatchBrowserWindow(tk.Toplevel(), self.current_user, self.db)
            self.activity_log.log_message("Tools", "Opened Batch Browser", "info")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Batch Browser: {e}")
    
    def _open_batch_ssh(self):
        """Open batch SSH operations window (independent)."""
        try:
            from batch_ssh import BatchSSHWindow
            BatchSSHWindow(tk.Toplevel(), self.current_user, self.db)
            self.activity_log.log_message("Tools", "Opened Batch SSH", "info")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Batch SSH: {e}")
    
    def _open_credentials_manager(self):
        """Open credentials manager window (modern style)."""
        try:
            # TODO: Create credentials_manager_v3.py with modern style
            from credentials_manager import CredentialsManager
            CredentialsManager(tk.Toplevel(), self.current_user, self.db)
            self.activity_log.log_message("Admin", "Opened Credentials Manager", "info")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Credentials Manager: {e}")
    
    def _open_user_management(self):
        """Open user management window (modern style)."""
        try:
            # TODO: Create user_management_v3.py with modern style
            from user_management import UserManagement
            UserManagement(tk.Toplevel(), self.current_user, self.db)
            self.activity_log.log_message("Admin", "Opened User Management", "info")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open User Management: {e}")
    
    def _change_password(self):
        """Open change password dialog."""
        try:
            from change_password_dialog import ChangePasswordDialog
            ChangePasswordDialog(self.root, self.current_user, self.db)
            self.activity_log.log_message("Admin", "Changed password", "info")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Change Password: {e}")
    
    def _open_admin_settings(self):
        """Open admin settings window."""
        try:
            from admin_settings import AdminSettingsWindow
            AdminSettingsWindow(self.root, self.current_user, self.db)
            self.activity_log.log_message("Admin", "Opened Admin Settings", "info")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Admin Settings: {e}")
    
    def _open_audit_log(self):
        """Open audit log window."""
        try:
            from audit_log_viewer import AuditLogViewer
            AuditLogViewer(tk.Toplevel(), self.current_user, self.db)
            self.activity_log.log_message("Admin", "Opened Audit Log", "info")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Audit Log: {e}")
    
    def _show_documentation(self):
        """Show documentation."""
        messagebox.showinfo("Documentation", 
                           "Documentation will be available soon.\n\n"
                           "For now, use the application and explore the menus.",
                           parent=self.root)
    
    def _show_about(self):
        """Show about dialog."""
        try:
            from about_dialog import show_about_dialog
            show_about_dialog(self.root)
        except Exception as e:
            messagebox.showinfo("About", 
                               "AP Helper v3.0\n\n"
                               "Modern dashboard for AP management",
                               parent=self.root)
    
    def _on_exit(self):
        """Handle application exit."""
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?", parent=self.root):
            self.activity_log.log_message("Dashboard", "Application closed", "info")
            self.root.quit()
    
    # === Admin Notification System ===
    
    def _load_admin_notification(self):
        """Load and display admin notification if exists."""
        try:
            # Check for active notification in database
            # TODO: Add notification table to database
            # For now, check if notification file exists
            import os
            notification_file = os.path.join(os.path.dirname(__file__), 'admin_notification.json')
            
            if os.path.exists(notification_file):
                import json
                with open(notification_file, 'r', encoding='utf-8') as f:
                    notification = json.load(f)
                
                self._show_notification(
                    notification.get('title', 'System Notification'),
                    notification.get('message', ''),
                    notification.get('details', '')
                )
        except Exception as e:
            # Silently fail - notification is optional
            pass
    
    def _show_notification(self, title, message, details):
        """Display admin notification banner."""
        # Clear existing notification content
        for widget in self.notification_frame.winfo_children():
            widget.destroy()
        
        # Pack notification frame
        self.notification_frame.pack(fill=tk.X, after=self.root.winfo_children()[0])
        
        content = tk.Frame(self.notification_frame, bg="#FFF3CD", padx=20, pady=12)
        content.pack(fill=tk.X)
        
        # Icon (warning symbol)
        icon_label = tk.Label(content, text="⚠", font=('Segoe UI', 18),
                             bg="#FFF3CD", fg="#856404")
        icon_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Text content
        text_frame = tk.Frame(content, bg="#FFF3CD")
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(text_frame, text=title, font=('Segoe UI', 11, 'bold'),
                bg="#FFF3CD", fg="#856404").pack(anchor="w")
        
        tk.Label(text_frame, text=message, font=('Segoe UI', 9),
                bg="#FFF3CD", fg="#856404", wraplength=800).pack(anchor="w", pady=(2, 0))
        
        # Buttons
        button_frame = tk.Frame(content, bg="#FFF3CD")
        button_frame.pack(side=tk.RIGHT, padx=(10, 0))
        
        if details:
            tk.Button(button_frame, text="Read More", 
                     command=lambda: self._show_notification_details(title, details),
                     bg="#856404", fg="white", font=('Segoe UI', 9, 'bold'),
                     padx=15, pady=6, relief=tk.FLAT, cursor="hand2",
                     activebackground="#6d5103").pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="✕ Dismiss", 
                 command=self._dismiss_notification,
                 bg="#856404", fg="white", font=('Segoe UI', 9),
                 padx=15, pady=6, relief=tk.FLAT, cursor="hand2",
                 activebackground="#6d5103").pack(side=tk.LEFT)
    
    def _show_notification_details(self, title, details):
        """Show full notification details in a window."""
        detail_window = tk.Toplevel(self.root)
        detail_window.title(title)
        detail_window.geometry("700x500")
        detail_window.transient(self.root)
        
        # Center window
        detail_window.update_idletasks()
        x = (detail_window.winfo_screenwidth() // 2) - (700 // 2)
        y = (detail_window.winfo_screenheight() // 2) - (500 // 2)
        detail_window.geometry(f"700x500+{x}+{y}")
        
        # Header
        header = tk.Frame(detail_window, bg="#0066CC", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text=title, font=('Segoe UI', 14, 'bold'),
                bg="#0066CC", fg="white").pack(side=tk.LEFT, padx=20, pady=15)
        
        # Content
        content_frame = tk.Frame(detail_window, bg="#FFFFFF")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        detail_text = scrolledtext.ScrolledText(content_frame, font=('Segoe UI', 10),
                                               wrap=tk.WORD, bg="#FFFFFF", bd=0)
        detail_text.pack(fill=tk.BOTH, expand=True)
        detail_text.insert('1.0', details)
        detail_text.config(state='disabled')
        
        # Close button
        tk.Button(detail_window, text="Close", command=detail_window.destroy,
                 bg="#6C757D", fg="white", font=('Segoe UI', 10),
                 padx=20, pady=8, relief=tk.FLAT, cursor="hand2").pack(pady=(0, 20))
    
    def _dismiss_notification(self):
        """Dismiss the notification banner."""
        self.notification_frame.pack_forget()
        self.activity_log.log_message("Dashboard", "Dismissed admin notification", "info")
    
    def _post_notification(self):
        """Admin: Post a system notification."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Post System Notification")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.configure(bg="#FFFFFF")
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"600x500+{x}+{y}")
        
        content = tk.Frame(dialog, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text="Post System Notification", font=('Segoe UI', 14, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(0, 20))
        
        # Title
        tk.Label(content, text="Title:", font=('Segoe UI', 10),
                bg="#FFFFFF", fg="#495057").pack(anchor="w", pady=(0, 5))
        title_entry = tk.Entry(content, font=('Segoe UI', 10), bd=1, relief=tk.SOLID)
        title_entry.pack(fill=tk.X, pady=(0, 15))
        title_entry.focus()
        
        # Short message
        tk.Label(content, text="Short Message (shown in banner):", font=('Segoe UI', 10),
                bg="#FFFFFF", fg="#495057").pack(anchor="w", pady=(0, 5))
        message_entry = tk.Entry(content, font=('Segoe UI', 10), bd=1, relief=tk.SOLID)
        message_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Detailed message
        tk.Label(content, text="Detailed Message (shown when 'Read More' is clicked):", 
                font=('Segoe UI', 10),
                bg="#FFFFFF", fg="#495057").pack(anchor="w", pady=(0, 5))
        details_text = scrolledtext.ScrolledText(content, font=('Segoe UI', 10), 
                                                wrap=tk.WORD, height=10, bd=1, relief=tk.SOLID)
        details_text.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        def save_notification():
            title = title_entry.get().strip()
            message = message_entry.get().strip()
            details = details_text.get('1.0', tk.END).strip()
            
            if not title or not message:
                messagebox.showwarning("Missing Info", 
                                     "Please provide both title and short message",
                                     parent=dialog)
                return
            
            try:
                # Save notification to file
                import json
                import os
                notification_file = os.path.join(os.path.dirname(__file__), 'admin_notification.json')
                
                notification_data = {
                    'title': title,
                    'message': message,
                    'details': details,
                    'posted_by': self.current_user,
                    'posted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                with open(notification_file, 'w', encoding='utf-8') as f:
                    json.dump(notification_data, f, indent=2)
                
                messagebox.showinfo("Success", "Notification posted successfully!\n\n"
                                  "All users will see it when they log in.",
                                  parent=dialog)
                dialog.destroy()
                
                # Show notification immediately in current window
                self._show_notification(title, message, details)
                
                self.activity_log.log_message("Admin", f"Posted notification: {title}", "success")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to post notification: {e}", parent=dialog)
        
        def clear_notification():
            if messagebox.askyesno("Clear Notification", 
                                  "Remove active notification for all users?",
                                  parent=dialog):
                try:
                    import os
                    notification_file = os.path.join(os.path.dirname(__file__), 'admin_notification.json')
                    if os.path.exists(notification_file):
                        os.remove(notification_file)
                    
                    messagebox.showinfo("Success", "Notification cleared", parent=dialog)
                    dialog.destroy()
                    self._dismiss_notification()
                    self.activity_log.log_message("Admin", "Cleared system notification", "info")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to clear notification: {e}", parent=dialog)
        
        # Buttons
        button_frame = tk.Frame(content, bg="#FFFFFF")
        button_frame.pack(fill=tk.X)
        
        tk.Button(button_frame, text="Post Notification", command=save_notification,
                 bg="#28A745", fg="white", font=('Segoe UI', 10, 'bold'),
                 padx=20, pady=10, relief=tk.FLAT, cursor="hand2",
                 activebackground="#218838").pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(button_frame, text="Clear Active Notification", command=clear_notification,
                 bg="#DC3545", fg="white", font=('Segoe UI', 10),
                 padx=20, pady=10, relief=tk.FLAT, cursor="hand2",
                 activebackground="#C82333").pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                 bg="#6C757D", fg="white", font=('Segoe UI', 10),
                 padx=20, pady=10, relief=tk.FLAT, cursor="hand2",
                 activebackground="#5A6268").pack(side=tk.LEFT)
    
    def _add_new_ap(self):
        """Admin: Add a new AP to the database."""
        from ap_support_ui import APSearchDialog
        
        # Use the existing AP add dialog
        # TODO: Create a dedicated "Add New AP" form
        messagebox.showinfo("Add New AP", 
                           "AP registration functionality will be added here.\n\n"
                           "For now, use the database management tools.",
                           parent=self.root)


def main():
    """Main entry point for testing dashboard."""
    root = tk.Tk()
    db = DatabaseManager()
    
    # Test with a dummy user
    dashboard = DashboardMain(root, "test_user", db)
    
    root.mainloop()


if __name__ == '__main__':
    main()
