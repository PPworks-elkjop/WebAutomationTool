"""
Main Dashboard Window for AP Helper v3
4-panel layout with resizable panes
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
import json
import os
from database_manager import DatabaseManager
from dashboard_components import APPanel, ContextPanel, ActivityLogPanel, ContentPanel
from custom_notebook import CustomNotebook


class DashboardMain:
    """Main dashboard window with 4-panel layout."""
    
    def __init__(self, root, current_user, db):
        self.root = root
        self.current_user = current_user
        self.db = db
        
        # Get username string from current_user (dict or string)
        self.username = current_user.get('username') if isinstance(current_user, dict) else current_user
        
        # Window setup
        self.root.title("VERA - Vusion support with a human touch")
        self.root.configure(bg="#F0F0F0")
        
        # Load saved window geometry
        self._load_window_geometry()
        
        # Shared state
        self.active_ap = None  # Currently active AP in AP panel
        self.active_ap_tab_index = None
        self.active_dropdown = None  # Track active menu dropdown
        
        # Style configuration for larger tabs - must be done before creating widgets
        style = ttk.Style()
        style.theme_use('default')  # Use default theme for better control
        # Configure all notebook tabs globally with 15pt font
        style.configure('TNotebook.Tab', 
                       font=('Segoe UI', 15, 'normal'), 
                       padding=[20, 14],
                       background="#E9ECEF",
                       foreground="#212529")
        style.map('TNotebook.Tab',
                 background=[('selected', '#FFFFFF')],
                 foreground=[('selected', '#212529')],
                 expand=[('selected', [1, 1, 1, 0])])
        
        # Create UI
        self._create_menu()
        self._create_top_banner()
        self._create_layout()
        
        # Log startup
        self.activity_log.log_message("Dashboard", "Application started", "info")
        
        # Load admin notification if exists
        self._load_admin_notification()
        
        # Save window state on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Load saved pane positions
        self.root.after(100, self._load_pane_positions)
        
        # Start auto-refresh timer (check for credential updates every minute)
        self.root.after(60000, self._auto_refresh_credentials)
    
    def _create_menu(self):
        """Create custom menu bar with buttons (modern styling with full control)."""
        # Custom menu bar frame
        menubar_frame = tk.Frame(self.root, bg="#FFFFFF", height=45, relief=tk.FLAT)
        menubar_frame.pack(fill=tk.X, side=tk.TOP)
        menubar_frame.pack_propagate(False)
        
        # Store active dropdown reference
        self.active_dropdown = None
        
        # File Menu
        self._create_menu_button(menubar_frame, "File", [
            ("Exit", self._on_exit)
        ])
        
        # Tools Menu
        self._create_menu_button(menubar_frame, "Tools", [
            ("Batch Ping", self._open_batch_ping),
            ("Batch Browser Operations", self._open_batch_browser),
            ("Batch SSH Operations", self._open_batch_ssh)
        ])
        
        # Admin Menu - different items based on user role
        is_admin = self.db.is_admin(self.username)
        if is_admin:
            # Admin users see all options
            self._create_menu_button(menubar_frame, "Admin", [
                ("Post System Notification", self._post_notification),
                None,
                ("Manage AP Credentials", self._open_credentials_manager),
                ("Manage Vusion API Keys", self._open_vusion_config),
                ("Manage Users", self._open_user_management),
                ("Change Password", self._change_password),
                None,
                ("Admin Settings", self._open_admin_settings),
                ("Audit Log", self._open_audit_log)
            ])
        else:
            # Regular users only see limited options
            self._create_menu_button(menubar_frame, "User", [
                ("Manage AP Credentials", self._open_credentials_manager),
                ("Change Password", self._change_password)
            ])
        
        # Help Menu
        self._create_menu_button(menubar_frame, "Help", [
            ("Documentation", self._show_documentation),
            ("About", self._show_about)
        ])
    
    def _create_menu_button(self, parent, label, items):
        """Create a custom menu button with dropdown."""
        btn = tk.Button(parent, text=label, font=('Segoe UI', 11), 
                       bg="#FFFFFF", fg="#212529", relief=tk.FLAT,
                       activebackground="#E9ECEF", activeforeground="#212529",
                       padx=15, pady=8, cursor="hand2", bd=0)
        btn.pack(side=tk.LEFT)
        
        # Add hover effects
        def on_enter(e):
            btn.config(bg="#E9ECEF")
        
        def on_leave(e):
            btn.config(bg="#FFFFFF")
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        def show_dropdown(event=None):
            # Close any existing dropdown
            if self.active_dropdown:
                try:
                    self.active_dropdown.destroy()
                except:
                    pass
            
            # Create dropdown menu
            dropdown = tk.Toplevel(self.root)
            dropdown.overrideredirect(True)  # Remove window decorations
            dropdown.configure(bg="#FFFFFF")
            
            # Position below button
            x = btn.winfo_rootx()
            y = btn.winfo_rooty() + btn.winfo_height()
            dropdown.geometry(f"+{x}+{y}")
            
            # Add menu items
            for item in items:
                if item is None:
                    # Separator
                    sep = tk.Frame(dropdown, bg="#E0E0E0", height=1)
                    sep.pack(fill=tk.X, padx=5, pady=2)
                else:
                    item_label, item_command = item
                    item_btn = tk.Button(dropdown, text=item_label, font=('Segoe UI', 10),
                                        bg="#FFFFFF", fg="#212529", relief=tk.FLAT,
                                        activebackground="#E9ECEF", activeforeground="#212529",
                                        anchor="w", padx=20, pady=8, cursor="hand2", bd=0)
                    item_btn.pack(fill=tk.X)
                    
                    # Add hover effects to menu items
                    def on_item_enter(e, btn=item_btn):
                        btn.config(bg="#E9ECEF")
                    
                    def on_item_leave(e, btn=item_btn):
                        btn.config(bg="#FFFFFF")
                    
                    item_btn.bind("<Enter>", on_item_enter)
                    item_btn.bind("<Leave>", on_item_leave)
                    
                    def on_click(cmd=item_command):
                        dropdown.destroy()
                        self.active_dropdown = None
                        cmd()
                    
                    item_btn.config(command=on_click)
            
            # Add border
            dropdown.configure(relief=tk.SOLID, bd=1, highlightthickness=1, highlightbackground="#CED4DA")
            
            self.active_dropdown = dropdown
            
            # Close dropdown on click outside
            def close_dropdown(event):
                if self.active_dropdown:
                    try:
                        self.active_dropdown.destroy()
                    except:
                        pass
                    self.active_dropdown = None
            
            dropdown.bind("<FocusOut>", close_dropdown)
            dropdown.focus_set()
        
        btn.config(command=show_dropdown)
    
    def _create_top_banner(self):
        """Create top banner with app name, logo, and admin notifications."""
        banner = tk.Frame(self.root, bg="#3D6B9E", height=100)
        banner.pack(fill=tk.X, side=tk.TOP)
        banner.pack_propagate(False)
        
        # Left side: Logo and app name
        left_frame = tk.Frame(banner, bg="#3D6B9E")
        left_frame.pack(side=tk.LEFT, padx=20, pady=20)
        
        # SVG-style logo placeholder (will use actual SVG/icon later)
        logo_frame = tk.Frame(left_frame, bg="white", width=50, height=50)
        logo_frame.pack(side=tk.LEFT, padx=(0, 15))
        logo_frame.pack_propagate(False)
        
        tk.Label(logo_frame, text="V", font=('Segoe UI', 24, 'bold'),
                bg="white", fg="#3D6B9E").pack(expand=True)
        
        # App name and tagline
        name_frame = tk.Frame(left_frame, bg="#3D6B9E")
        name_frame.pack(side=tk.LEFT)
        
        tk.Label(name_frame, text="VERA", font=('Segoe UI', 20, 'bold'),
                bg="#3D6B9E", fg="white").pack(anchor="w")
        
        tk.Label(name_frame, text="Vusion support with a human touch", 
                font=('Segoe UI', 9),
                bg="#3D6B9E", fg="#D0D0D0").pack(anchor="w")
        
        # Right side: User info
        right_frame = tk.Frame(banner, bg="#3D6B9E")
        right_frame.pack(side=tk.RIGHT, padx=20, pady=20)
        
        # Show full name from user data (handle both dict and string)
        if isinstance(self.current_user, dict):
            user_display = self.current_user.get('full_name', self.current_user.get('username', 'User'))
        else:
            user_display = self.current_user
        
        tk.Label(right_frame, text=f"Welcome, {user_display}", 
                font=('Segoe UI', 10),
                bg="#3D6B9E", fg="white").pack(anchor="e")
        
        # Admin notification area (will be shown when notification exists)
        self.notification_frame = tk.Frame(self.root, bg="#FFF3CD", bd=1, relief=tk.SOLID)
        # Pack will be done when notification is loaded
    
    def _create_layout(self):
        """Create 4-panel dashboard layout with resizable panes."""
        
        # Configure style for visible sash handles
        style = ttk.Style()
        style.configure('Sash.TPanedwindow', sashwidth=8, sashrelief=tk.RAISED, background='#D0D0D0')
        
        # Main container with vertical split (upper / lower)
        self.main_paned = tk.PanedWindow(self.root, orient=tk.VERTICAL, 
                                         sashwidth=8, sashrelief=tk.RAISED, 
                                         bg='#D0D0D0', bd=0)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Upper pane with horizontal split (AP Panel / Context Panel)
        self.upper_paned = tk.PanedWindow(self.main_paned, orient=tk.HORIZONTAL,
                                          sashwidth=8, sashrelief=tk.RAISED,
                                          bg='#D0D0D0', bd=0)
        self.main_paned.add(self.upper_paned, minsize=200)
        
        # Lower pane with horizontal split (Activity Log / Content Panel)
        self.lower_paned = tk.PanedWindow(self.main_paned, orient=tk.HORIZONTAL,
                                          sashwidth=8, sashrelief=tk.RAISED,
                                          bg='#D0D0D0', bd=0)
        self.main_paned.add(self.lower_paned, minsize=150)
        
        # Create panels (Content Panel first so AP Panel can reference it)
        
        # === UPPER LEFT: AP Panel ===
        ap_frame = ttk.Frame(self.upper_paned, relief=tk.RIDGE, borderwidth=1)
        self.upper_paned.add(ap_frame, minsize=400)
        
        # Content Panel (temporary, will be properly initialized below)
        content_frame = ttk.Frame(self.lower_paned, relief=tk.RIDGE, borderwidth=1)
        
        self.content_panel = ContentPanel(
            content_frame,
            self.db,
            current_user=self.current_user,
            log_callback=self._log_activity,
            refresh_callback=None  # Will set after context panel is created
        )
        
        self.ap_panel = APPanel(
            ap_frame, 
            self.current_user, 
            self.db,
            on_ap_change=self._on_ap_changed,
            on_tab_change=self._on_ap_tab_changed,
            log_callback=self._log_activity,
            content_panel=self.content_panel
        )
        
        # Set ap_panel reference in content_panel for browser operations
        self.content_panel.ap_panel = self.ap_panel
        
        # === UPPER RIGHT: Context Panel ===
        context_frame = ttk.Frame(self.upper_paned, relief=tk.RIDGE, borderwidth=1)
        self.upper_paned.add(context_frame, minsize=400)
        
        self.context_panel = ContextPanel(
            context_frame,
            self.db,
            current_user=self.current_user,
            on_selection=self._on_context_selection,
            log_callback=self._log_activity
        )
        
        # Set refresh callback now that context panel exists
        self.content_panel.refresh_callback = lambda: self.context_panel._load_notes()
        
        # === LOWER LEFT: Activity Log ===
        log_frame = ttk.Frame(self.lower_paned, relief=tk.RIDGE, borderwidth=1)
        self.lower_paned.add(log_frame, minsize=300)
        
        self.activity_log = ActivityLogPanel(log_frame)
        
        # === LOWER RIGHT: Content Panel ===
        self.lower_paned.add(content_frame, minsize=400)
    
    # === Event Handlers ===
    
    def _on_ap_changed(self, ap_id, ap_data):
        """Called when active AP changes in AP panel."""
        self.active_ap = ap_data
        self.activity_log.log_message("AP Panel", f"Switched to AP {ap_id}", "info")
        
        # Update context panel to show data for this AP
        self.context_panel.set_active_ap(ap_id, ap_data)
        
        # Update content panel - always update AP Support Details
        self.content_panel.show_ap_overview(ap_data)
        
        # Clear Context Details tab to show placeholder (user needs to select item again)
        self.content_panel._show_placeholder_in_frame(self.content_panel.context_details_frame)
    
    def _on_ap_tab_changed(self, ap_id, tab_name):
        """Called when user switches sub-tabs within an AP (Overview, Notes, Browser, SSH, Actions)."""
        self.activity_log.log_message("AP Panel", f"Switched to {tab_name} tab for AP {ap_id}", "info")
        
        # Get AP data for this AP
        ap_data = self.db.get_access_point(ap_id)
        if not ap_data:
            self.activity_log.log_message("Dashboard", f"Could not find AP data for {ap_id}", "error")
            return
        
        # Update content panel based on active tab
        if tab_name == "SSH Terminal":
            # Check if SSH terminal is already active for this AP
            if hasattr(self.content_panel, 'current_ssh_sessions') and ap_id in self.content_panel.current_ssh_sessions:
                session = self.content_panel.current_ssh_sessions[ap_id]
                if session.get('connected') and 'content_frame' in session:
                    # Restore existing session frame
                    self.activity_log.log_message("SSH", f"Restoring active SSH session for AP {ap_id}", "info")
                    self.content_panel.restore_ssh_terminal(ap_id)
                    return
            # No existing session, create new one
            self.content_panel.show_ssh_terminal(ap_data)
        elif tab_name == "Browser":
            self.content_panel.show_browser_status(ap_id, ap_data)
        elif tab_name == "Notes":
            self.content_panel.show_notes(ap_id)
        elif tab_name == "Overview":
            self.content_panel.show_ap_overview(ap_data)
        else:
            # Default to overview
            self.content_panel.show_ap_overview(ap_data)
    
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
        elif item_type == "add_note":
            self.content_panel.show_add_note_form(item_data["ap_id"], item_data.get("ap_data"))
    
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
            from credential_manager_modern import ModernCredentialManager
            ModernCredentialManager(current_user=self.current_user, parent=self.root, db_manager=self.db)
            self.activity_log.log_message("Admin", "Opened Credentials Manager", "info")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Credentials Manager: {e}")
    
    def _open_vusion_config(self):
        """Open Vusion API configuration dialog."""
        if not self.db.is_admin(self.username):
            messagebox.showerror("Access Denied", "This feature is only available to administrators.")
            return
        try:
            from vusion_config_dialog import VusionAPIConfigDialog
            dialog = VusionAPIConfigDialog(self.root)
            dialog.show()
            self.activity_log.log_message("Admin", "Opened Vusion API Configuration", "info")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Vusion API configuration:\n{str(e)}")
    
    def _open_user_management(self):
        """Open user management window."""
        if not self.db.is_admin(self.username):
            messagebox.showerror("Access Denied", "This feature is only available to administrators.")
            return
        try:
            from user_manager_modern import ModernUserManager
            ModernUserManager(self.current_user, self.root, self.db)
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
        if not self.db.is_admin(self.username):
            messagebox.showerror("Access Denied", "This feature is only available to administrators.")
            return
        try:
            from admin_settings import AdminSettingsDialog
            AdminSettingsDialog(self.root, self.current_user, self.db)
            self.activity_log.log_message("Admin", "Opened Admin Settings", "info")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Admin Settings: {e}")
    
    def _open_audit_log(self):
        """Open audit log window."""
        if not self.db.is_admin(self.username):
            messagebox.showerror("Access Denied", "This feature is only available to administrators.")
            return
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
            self._save_window_state()
            self.root.quit()
            self.root.destroy()
    
    def _on_closing(self):
        """Handle window close event."""
        # Check if browser is running
        if hasattr(self, 'content_panel') and self.content_panel.is_browser_running():
            from tkinter import messagebox
            if not messagebox.askyesno("Browser Running", 
                                       "Browser is still running. Are you sure you want to close?\n\n"
                                       "This will close all browser connections.",
                                       parent=self.root):
                return
            
            # Stop the browser
            try:
                self.content_panel.stop_browser()
            except:
                pass
        
        # Force update before saving to ensure pane positions are current
        self.root.update_idletasks()
        self._save_window_state()
        self.root.quit()
        self.root.destroy()
    
    def _get_config_file(self):
        """Get path to configuration file."""
        return os.path.join(os.path.dirname(__file__), 'dashboard_config.json')
    
    def _load_window_geometry(self):
        """Load saved window size and position."""
        try:
            config_file = self._get_config_file()
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    geometry = config.get('window_geometry', '1600x900')
                    print(f"Loading window geometry: {geometry}")
                    self.root.geometry(geometry)
            else:
                print("No saved geometry found, using default 1600x900")
                self.root.geometry("1600x900")
        except Exception as e:
            print(f"Error loading window geometry: {e}")
            self.root.geometry("1600x900")
    
    def _load_pane_positions(self):
        """Load saved pane sash positions."""
        try:
            config_file = self._get_config_file()
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    
                    # Restore main paned window position (vertical split)
                    # Default to 450 if not set or too small
                    main_pos = config.get('main_pane_pos', 450)
                    if main_pos < 300:  # Increased minimum from 200 to 300
                        main_pos = 450
                    self.main_paned.sash_place(0, 0, main_pos)
                    print(f"Main pane position set to: {main_pos}")
                    
                    # Restore upper paned window position (horizontal split)
                    # Default to 600 if not set or too small
                    upper_pos = config.get('upper_pane_pos', 600)
                    if upper_pos < 250:  # Minimum 250px to prevent too small
                        upper_pos = 400
                    self.upper_paned.sash_place(0, upper_pos, 0)
                    print(f"Upper pane position set to: {upper_pos}")
                    
                    # Restore lower paned window position (horizontal split)
                    # Default to 600 if not set or too small
                    lower_pos = config.get('lower_pane_pos', 600)
                    if lower_pos < 250:  # Minimum 250px to prevent too small
                        lower_pos = 400
                    self.lower_paned.sash_place(0, lower_pos, 0)
                    print(f"Lower pane position set to: {lower_pos}")
            else:
                # Set default positions if no config exists
                print("No config found, using defaults")
                self.root.update_idletasks()
                window_height = self.root.winfo_height()
                window_width = self.root.winfo_width()
                self.main_paned.sash_place(0, 0, max(450, int(window_height * 0.5)))
                self.upper_paned.sash_place(0, max(600, int(window_width * 0.45)), 0)
                self.lower_paned.sash_place(0, max(600, int(window_width * 0.45)), 0)
        except Exception as e:
            print(f"Error loading pane positions: {e}")
            # Set defaults on error
            self.root.update_idletasks()
            window_height = self.root.winfo_height()
            window_width = self.root.winfo_width()
            self.main_paned.sash_place(0, 0, max(450, int(window_height * 0.5)))
            self.upper_paned.sash_place(0, max(600, int(window_width * 0.45)), 0)
            self.lower_paned.sash_place(0, max(600, int(window_width * 0.45)), 0)
    
    def _save_window_state(self):
        """Save window size, position, and pane positions."""
        try:
            # Ensure all pending updates are processed
            self.root.update_idletasks()
            
            config = {
                'window_geometry': self.root.geometry()
            }
            
            # Only save pane positions if they exist and are valid
            if hasattr(self, 'main_paned'):
                main_pos = self.main_paned.sash_coord(0)[1]
                # Don't save if position is too small
                if main_pos >= 300:
                    config['main_pane_pos'] = main_pos
                else:
                    config['main_pane_pos'] = 450
                print(f"Saving main pane: {config['main_pane_pos']}")
                
            if hasattr(self, 'upper_paned'):
                upper_pos = self.upper_paned.sash_coord(0)[0]
                # Don't save if position is too small (minimum 250px)
                if upper_pos >= 250:
                    config['upper_pane_pos'] = upper_pos
                else:
                    config['upper_pane_pos'] = 400
                print(f"Saving upper pane: {config['upper_pane_pos']}")
                
            if hasattr(self, 'lower_paned'):
                lower_pos = self.lower_paned.sash_coord(0)[0]
                # Don't save if position is too small (minimum 250px)
                if lower_pos >= 250:
                    config['lower_pane_pos'] = lower_pos
                else:
                    config['lower_pane_pos'] = 400
                print(f"Saving lower pane: {config['lower_pane_pos']}")
            
            config_file = self._get_config_file()
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"Window state saved: {config['window_geometry']}")
        except Exception as e:
            print(f"Error saving window state: {e}")
    
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
        detail_window.geometry("700x650")
        detail_window.transient(self.root)
        
        # Center window
        detail_window.update_idletasks()
        x = (detail_window.winfo_screenwidth() // 2) - (700 // 2)
        y = (detail_window.winfo_screenheight() // 2) - (650 // 2)
        detail_window.geometry(f"700x650+{x}+{y}")
        
        # Header
        header = tk.Frame(detail_window, bg="#3D6B9E", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text=title, font=('Segoe UI', 14, 'bold'),
                bg="#3D6B9E", fg="white").pack(side=tk.LEFT, padx=20, pady=15)
        
        # Content
        content_frame = tk.Frame(detail_window, bg="#FFFFFF")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Text widget with scrollbar
        text_container = tk.Frame(content_frame, bg="#FFFFFF", relief=tk.SOLID, bd=1)
        text_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(text_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        detail_text = tk.Text(text_container, font=('Segoe UI', 10),
                             wrap=tk.WORD, bg="#FFFFFF", bd=0, padx=10, pady=10,
                             yscrollcommand=scrollbar.set)
        detail_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=detail_text.yview)
        
        # Configure tags for links
        detail_text.tag_configure("link", foreground="#0066CC", underline=True)
        detail_text.tag_bind("link", "<Enter>", lambda e: detail_text.config(cursor="hand2"))
        detail_text.tag_bind("link", "<Leave>", lambda e: detail_text.config(cursor=""))
        
        # Parse and insert text with clickable links
        import re
        url_pattern = r'(https?://[^\s]+)'
        
        last_pos = 0
        for match in re.finditer(url_pattern, details):
            # Insert text before the URL
            if match.start() > last_pos:
                detail_text.insert(tk.END, details[last_pos:match.start()])
            
            # Insert the URL as a clickable link
            url = match.group(0)
            start_index = detail_text.index(tk.END + "-1c")
            detail_text.insert(tk.END, url)
            end_index = detail_text.index(tk.END + "-1c")
            detail_text.tag_add("link", start_index, end_index)
            
            # Bind click event to open URL in Edge
            detail_text.tag_bind("link", "<Button-1>", 
                               lambda e, link=url: self._open_url_in_edge(link))
            
            last_pos = match.end()
        
        # Insert remaining text after last URL
        if last_pos < len(details):
            detail_text.insert(tk.END, details[last_pos:])
        
        detail_text.config(state='disabled')
        
        # Close button
        tk.Button(detail_window, text="Close", command=detail_window.destroy,
                 bg="#6C757D", fg="white", font=('Segoe UI', 10),
                 padx=20, pady=8, relief=tk.FLAT, cursor="hand2").pack(pady=(0, 20))
    
    def _open_url_in_edge(self, url):
        """Open URL in Microsoft Edge browser."""
        import subprocess
        try:
            subprocess.Popen(['msedge', url])
        except Exception as e:
            # Fallback to default browser if Edge is not available
            import webbrowser
            webbrowser.open(url)
    
    def _dismiss_notification(self):
        """Dismiss the notification banner."""
        self.notification_frame.pack_forget()
        self.activity_log.log_message("Dashboard", "Dismissed admin notification", "info")
    
    def _post_notification(self):
        """Admin: Post a system notification."""
        if not self.db.is_admin(self.username):
            messagebox.showerror("Access Denied", "This feature is only available to administrators.")
            return
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
        
        # Load existing notification if present
        import json
        import os
        notification_file = os.path.join(os.path.dirname(__file__), 'admin_notification.json')
        existing_notification = None
        
        if os.path.exists(notification_file):
            try:
                with open(notification_file, 'r', encoding='utf-8') as f:
                    existing_notification = json.load(f)
            except:
                pass
        
        # Title
        tk.Label(content, text="Title:", font=('Segoe UI', 10),
                bg="#FFFFFF", fg="#495057").pack(anchor="w", pady=(0, 5))
        title_entry = tk.Entry(content, font=('Segoe UI', 10), bd=1, relief=tk.SOLID)
        title_entry.pack(fill=tk.X, pady=(0, 15))
        if existing_notification:
            title_entry.insert(0, existing_notification.get('title', ''))
        title_entry.focus()
        
        # Short message
        tk.Label(content, text="Short Message (shown in banner):", font=('Segoe UI', 10),
                bg="#FFFFFF", fg="#495057").pack(anchor="w", pady=(0, 5))
        message_entry = tk.Entry(content, font=('Segoe UI', 10), bd=1, relief=tk.SOLID)
        message_entry.pack(fill=tk.X, pady=(0, 15))
        if existing_notification:
            message_entry.insert(0, existing_notification.get('message', ''))
        
        # Detailed message
        tk.Label(content, text="Detailed Message (shown when 'Read More' is clicked):", 
                font=('Segoe UI', 10),
                bg="#FFFFFF", fg="#495057").pack(anchor="w", pady=(0, 5))
        details_text = scrolledtext.ScrolledText(content, font=('Segoe UI', 10), 
                                                wrap=tk.WORD, height=10, bd=1, relief=tk.SOLID)
        details_text.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        if existing_notification:
            details_text.insert('1.0', existing_notification.get('details', ''))
        
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
    
    def _auto_refresh_credentials(self):
        """Auto-refresh AP data from database every minute."""
        try:
            # Check if window still exists
            if not self.root.winfo_exists():
                return
            
            # Refresh currently active AP data
            if self.active_ap and 'ap_id' in self.active_ap:
                ap_id = self.active_ap['ap_id']
                
                # Reload AP from database
                from credential_manager_v2 import CredentialManager
                creds_manager = CredentialManager()
                updated_ap = creds_manager.find_by_ap_id(ap_id)
                
                if updated_ap:
                    # Update active AP data
                    self.active_ap = updated_ap
                    
                    # Update context panel with fresh AP data only (no Jira refresh)
                    if hasattr(self, 'context_panel'):
                        # Update the AP data but don't trigger Jira reload
                        self.context_panel.active_ap_data = updated_ap
                        # Only refresh notes (fast operation)
                        self.context_panel._load_notes()
                    
                    # Update content panel if showing overview
                    if hasattr(self, 'content_panel'):
                        # Only update if we're on overview (not browser/ssh/notes)
                        # This prevents interrupting active sessions
                        pass  # Content panel will refresh on next view change
            
        except Exception as e:
            # Silently log error without disrupting UI
            if hasattr(self, 'activity_log'):
                self.activity_log.log_message("System", f"Auto-refresh error: {str(e)}", "warning")
        
        # Schedule next refresh in 60 seconds
        self.root.after(60000, self._auto_refresh_credentials)


def main():
    """Main entry point for dashboard."""
    from splash_screen import SplashScreen
    from login_dialog import LoginDialog
    
    # Show splash screen
    splash = SplashScreen()
    splash.update_progress(10, "Loading configuration...")
    
    # Show login dialog
    splash.update_progress(30, "Waiting for authentication...")
    login = LoginDialog()
    user = login.show()
    
    if not user:
        # User cancelled login
        splash.close()
        return
    
    splash.update_progress(50, "Initializing database...")
    db = DatabaseManager()
    
    splash.update_progress(70, "Loading user interface...")
    root = tk.Tk()
    root.withdraw()  # Hide main window during setup
    
    splash.update_progress(90, "Setting up dashboard...")
    dashboard = DashboardMain(root, user, db)
    
    splash.update_progress(100, "Starting application...")
    
    # Close splash and show main window
    import time
    time.sleep(0.2)
    splash.close()
    root.deiconify()  # Show main window
    
    root.mainloop()


if __name__ == '__main__':
    main()
