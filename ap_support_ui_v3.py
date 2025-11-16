"""
AP Support System UI - Modern Redesign (Production Version)
Modernized design inspired by Admin Settings window with tabs layout
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from database_manager import DatabaseManager
from typing import Dict, List, Optional
import threading

try:
    from jira_search_ui import open_jira_search
    JIRA_AVAILABLE = True
except ImportError:
    JIRA_AVAILABLE = False

# Import necessary components from the original
try:
    from ssh_dialog import open_ssh_window
    SSH_AVAILABLE = True
except ImportError:
    SSH_AVAILABLE = False


class APSupportWindowModern:
    """Modern redesigned support window for a single AP with tabbed interface."""
    
    # Class variable to track open windows
    _open_windows = {}
    
    def __init__(self, parent, ap: Dict, current_user: str, db_manager: DatabaseManager, 
                 browser_helper=None):
        ap_id = ap['ap_id']
        
        # Check if window already exists for this AP
        if ap_id in APSupportWindowModern._open_windows:
            existing_window = APSupportWindowModern._open_windows[ap_id]
            if existing_window.window and existing_window.window.winfo_exists():
                existing_window.window.lift()
                existing_window.window.focus_force()
                return
            else:
                del APSupportWindowModern._open_windows[ap_id]
        
        # Create new window
        self.window = tk.Toplevel(parent)
        self.window.title(f"AP Support - {ap_id}")
        self.window.geometry("1000x700")
        
        # Initialize instance variables
        self.ap = ap
        self.ap_id = ap_id
        self.current_user = current_user
        self.db = db_manager
        self.browser_helper = browser_helper
        
        # Each window gets its own browser driver instance
        self.driver = None
        self.browser_connected = False
        
        # Register this window
        APSupportWindowModern._open_windows[ap_id] = self
        
        # Reload AP data from database
        latest_ap = self.db.get_access_point(ap_id)
        if latest_ap:
            self.ap = latest_ap
        
        # Log audit
        self.db.log_user_activity(
            username=current_user,
            activity_type='ap_support_open',
            description=f'Opened AP support window for {ap_id}',
            ap_id=ap_id,
            success=True
        )
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self._create_ui()
        self._load_data()
        
        # Start auto-refresh timer
        self._auto_refresh()
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.window.winfo_screenheight() // 2) - (700 // 2)
        self.window.geometry(f"1000x700+{x}+{y}")
    
    def _create_ui(self):
        """Create modern tabbed UI similar to Admin Settings."""
        # Modern styling
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colors
        bg_color = "#F0F0F0"
        tab_bg = "#FFFFFF"
        
        self.window.configure(bg=bg_color)
        
        # Configure tab styles
        style.configure("Modern.TNotebook", background=bg_color, borderwidth=0)
        style.configure("Modern.TNotebook.Tab", 
                       background="#E0E0E0",
                       foreground="#333333",
                       padding=[20, 10],
                       font=('Segoe UI', 10))
        style.map("Modern.TNotebook.Tab",
                 background=[("selected", "#FFFFFF")],
                 foreground=[("selected", "#0066CC")])
        
        # Main container
        main_frame = ttk.Frame(self.window, padding=0)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header with AP ID and status
        header = tk.Frame(main_frame, bg="#0066CC", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg="#0066CC")
        header_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(header_content, text=f"AP: {self.ap_id}", 
                font=('Segoe UI', 16, 'bold'), bg="#0066CC", fg="white").pack(side=tk.LEFT)
        
        # Status indicator
        status_frame = tk.Frame(header_content, bg="#0066CC")
        status_frame.pack(side=tk.RIGHT)
        
        tk.Label(status_frame, text="Status:", font=('Segoe UI', 10), 
                bg="#0066CC", fg="white").pack(side=tk.LEFT, padx=(0, 5))
        
        self.support_status_var = tk.StringVar(value=self.ap.get('support_status', 'active'))
        status_menu = ttk.Combobox(status_frame, textvariable=self.support_status_var,
                                   values=['active', 'monitoring', 'investigating', 'resolved'],
                                   state='readonly', width=12)
        status_menu.pack(side=tk.LEFT)
        status_menu.bind('<<ComboboxSelected>>', self._on_status_change)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame, style="Modern.TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Create tabs
        self._create_overview_tab()
        self._create_notes_tab()
        self._create_browser_tab()
        self._create_ssh_tab()
        self._create_actions_tab()
        
        # Footer with action buttons
        footer = tk.Frame(main_frame, bg=bg_color, height=60)
        footer.pack(fill=tk.X, padx=20, pady=10)
        footer.pack_propagate(False)
        
        button_container = tk.Frame(footer, bg=bg_color)
        button_container.pack(side=tk.RIGHT)
        
        if JIRA_AVAILABLE:
            tk.Button(button_container, text="🔍 Search Jira", command=self._open_jira_search,
                     bg="#0052CC", fg="white", font=('Segoe UI', 10), 
                     padx=15, pady=8, relief=tk.FLAT, cursor="hand2",
                     activebackground="#0747A6").pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_container, text="Open Another AP", command=self._open_another_ap,
                 bg="#007BFF", fg="white", font=('Segoe UI', 10), 
                 padx=15, pady=8, relief=tk.FLAT, cursor="hand2",
                 activebackground="#0056b3").pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_container, text="Close", command=self._on_close,
                 bg="#6C757D", fg="white", font=('Segoe UI', 10), 
                 padx=15, pady=8, relief=tk.FLAT, cursor="hand2",
                 activebackground="#5A6268").pack(side=tk.LEFT, padx=5)
    
    def _create_overview_tab(self):
        """Create Overview tab with AP information."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 Overview")
        
        # Scrollable frame
        canvas = tk.Canvas(tab, bg="#FFFFFF", highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Content frame
        content = tk.Frame(scrollable_frame, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        # AP Information Section
        self._create_section_header(content, "AP Information")
        info_frame = tk.Frame(content, bg="#F8F9FA", relief=tk.FLAT, bd=1)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        info_grid = tk.Frame(info_frame, bg="#F8F9FA", padx=20, pady=15)
        info_grid.pack(fill=tk.X)
        
        # Info fields
        info_fields = [
            ("AP ID", "ap_id"),
            ("Store ID", "store_id"),
            ("IP Address", "ip_address"),
            ("Type", "type"),
            ("Serial Number", "serial_number"),
            ("Software Version", "software_version"),
            ("Firmware Version", "firmware_version"),
            ("Hardware Revision", "hardware_revision"),
            ("MAC Address", "mac_address"),
            ("Uptime", "uptime"),
        ]
        
        self.info_entries = {}
        for idx, (label_text, field) in enumerate(info_fields):
            row = idx // 2
            col = (idx % 2) * 2
            
            tk.Label(info_grid, text=label_text + ":", font=('Segoe UI', 9, 'bold'),
                    bg="#F8F9FA", fg="#495057", anchor="w", width=18).grid(
                row=row, column=col, sticky="w", padx=(0, 10), pady=5)
            
            entry = tk.Entry(info_grid, font=('Segoe UI', 9), bg="#FFFFFF",
                           relief=tk.FLAT, bd=1, readonlybackground="#FFFFFF",
                           state="readonly", cursor="xterm")
            entry.grid(row=row, column=col+1, sticky="ew", padx=(0, 20), pady=5)
            self.info_entries[field] = entry
        
        info_grid.columnconfigure(1, weight=1)
        info_grid.columnconfigure(3, weight=1)
        
        # Connection Status Section
        self._create_section_header(content, "Connection Status")
        conn_frame = tk.Frame(content, bg="#F8F9FA", relief=tk.FLAT, bd=1)
        conn_frame.pack(fill=tk.X, pady=(0, 20))
        
        conn_content = tk.Frame(conn_frame, bg="#F8F9FA", padx=20, pady=15)
        conn_content.pack(fill=tk.X)
        
        tk.Button(conn_content, text="Check Connection", command=self._check_connection,
                 bg="#17A2B8", fg="white", font=('Segoe UI', 9, 'bold'),
                 padx=20, pady=8, relief=tk.FLAT, cursor="hand2",
                 activebackground="#138496").pack(side=tk.LEFT, padx=(0, 15))
        
        self.ping_result_label = tk.Label(conn_content, text="Click to test connection",
                                         font=('Segoe UI', 9), bg="#F8F9FA", fg="#6C757D")
        self.ping_result_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _create_notes_tab(self):
        """Create Notes tab for support notes."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📝 Notes")
        
        # Main container
        content = tk.Frame(tab, bg="#FFFFFF")
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header with Write Note button
        header = tk.Frame(content, bg="#FFFFFF")
        header.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(header, text="Support Notes", font=('Segoe UI', 14, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(side=tk.LEFT)
        
        tk.Button(header, text="✏️ Write Note", command=self._open_write_note_dialog,
                 bg="#28A745", fg="white", font=('Segoe UI', 9, 'bold'),
                 padx=15, pady=8, relief=tk.FLAT, cursor="hand2",
                 activebackground="#218838").pack(side=tk.RIGHT)
        
        # Notes list container
        notes_container = tk.Frame(content, bg="#FFFFFF")
        notes_container.pack(fill=tk.BOTH, expand=True)
        
        self.notes_canvas = tk.Canvas(notes_container, bg="#FFFFFF", highlightthickness=0)
        notes_scrollbar = ttk.Scrollbar(notes_container, orient="vertical", 
                                       command=self.notes_canvas.yview)
        self.notes_frame = tk.Frame(self.notes_canvas, bg="#FFFFFF")
        
        self.notes_frame.bind(
            "<Configure>",
            lambda e: self.notes_canvas.configure(scrollregion=self.notes_canvas.bbox("all"))
        )
        
        self.notes_canvas.create_window((0, 0), window=self.notes_frame, anchor="nw", width=900)
        self.notes_canvas.configure(yscrollcommand=notes_scrollbar.set)
        
        self.notes_canvas.pack(side="left", fill="both", expand=True)
        notes_scrollbar.pack(side="right", fill="y")
    
    def _create_browser_tab(self):
        """Create Browser tab for web automation."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🌐 Browser")
        
        content = tk.Frame(tab, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text="Browser Automation", font=('Segoe UI', 14, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(0, 15))
        
        # Connection status
        status_frame = tk.Frame(content, bg="#F8F9FA", relief=tk.FLAT, bd=1)
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        status_content = tk.Frame(status_frame, bg="#F8F9FA", padx=20, pady=15)
        status_content.pack(fill=tk.X)
        
        tk.Button(status_content, text="Connect Browser", command=self._connect_browser,
                 bg="#007BFF", fg="white", font=('Segoe UI', 9, 'bold'),
                 padx=20, pady=8, relief=tk.FLAT, cursor="hand2",
                 activebackground="#0056b3").pack(side=tk.LEFT, padx=(0, 15))
        
        self.browser_status_label = tk.Label(status_content, text="Not connected",
                                            font=('Segoe UI', 9), bg="#F8F9FA", fg="#6C757D")
        self.browser_status_label.pack(side=tk.LEFT)
        
        # Browser actions
        tk.Label(content, text="Quick Actions", font=('Segoe UI', 11, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(10, 10))
        
        actions_frame = tk.Frame(content, bg="#FFFFFF")
        actions_frame.pack(fill=tk.X)
        
        actions = [
            ("Open Web UI", self._open_browser),
            ("Run Automation", self._run_browser_automation),
        ]
        
        for action_text, command in actions:
            tk.Button(actions_frame, text=action_text, command=command,
                     bg="#17A2B8", fg="white", font=('Segoe UI', 9),
                     padx=15, pady=8, relief=tk.FLAT, cursor="hand2",
                     activebackground="#138496", width=20).pack(anchor="w", pady=5)
    
    def _create_ssh_tab(self):
        """Create SSH tab for terminal access."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🖥️ SSH Terminal")
        
        content = tk.Frame(tab, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text="SSH Terminal", font=('Segoe UI', 14, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(0, 15))
        
        tk.Button(content, text="Open SSH Terminal", command=self._open_ssh,
                 bg="#6F42C1", fg="white", font=('Segoe UI', 10, 'bold'),
                 padx=20, pady=10, relief=tk.FLAT, cursor="hand2",
                 activebackground="#5A32A3").pack(anchor="w", pady=5)
        
        tk.Label(content, text="Opens a new SSH terminal window for direct access to the AP.",
                font=('Segoe UI', 9), bg="#FFFFFF", fg="#6C757D").pack(anchor="w", pady=(5, 0))
    
    def _create_actions_tab(self):
        """Create Actions tab for common operations."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚡ Actions")
        
        # Scrollable frame
        canvas = tk.Canvas(tab, bg="#FFFFFF", highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        content = tk.Frame(scrollable_frame, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text="Quick Actions", font=('Segoe UI', 14, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(0, 15))
        
        # Action categories
        self._create_action_category(content, "Diagnostics", [
            ("Run Diagnostics", self._placeholder_action),
            ("Check Logs", self._placeholder_action),
            ("Network Test", self._placeholder_action),
        ])
        
        self._create_action_category(content, "Configuration", [
            ("Backup Config", self._placeholder_action),
            ("Restore Config", self._placeholder_action),
            ("Reset Settings", self._placeholder_action),
        ])
        
        self._create_action_category(content, "Maintenance", [
            ("Reboot AP", self._placeholder_action),
            ("Update Firmware", self._placeholder_action),
            ("Factory Reset", self._placeholder_action),
        ])
    
    def _create_section_header(self, parent, text):
        """Create a section header."""
        header_frame = tk.Frame(parent, bg="#FFFFFF")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_frame, text=text, font=('Segoe UI', 12, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(side=tk.LEFT)
        
        line = tk.Frame(header_frame, bg="#DEE2E6", height=2)
        line.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
    
    def _create_action_category(self, parent, category_name, actions):
        """Create an action category with buttons."""
        tk.Label(parent, text=category_name, font=('Segoe UI', 11, 'bold'),
                bg="#FFFFFF", fg="#495057").pack(anchor="w", pady=(10, 5))
        
        category_frame = tk.Frame(parent, bg="#F8F9FA", relief=tk.FLAT, bd=1)
        category_frame.pack(fill=tk.X, pady=(0, 15))
        
        buttons_frame = tk.Frame(category_frame, bg="#F8F9FA", padx=20, pady=15)
        buttons_frame.pack(fill=tk.X)
        
        for action_text, command in actions:
            tk.Button(buttons_frame, text=action_text, command=command,
                     bg="#FFFFFF", fg="#212529", font=('Segoe UI', 9),
                     padx=15, pady=8, relief=tk.FLAT, cursor="hand2",
                     activebackground="#E9ECEF", bd=1, width=25).pack(anchor="w", pady=3)
    
    def _load_data(self):
        """Load AP data into the UI."""
        # Populate info entries
        for field, entry in self.info_entries.items():
            value = self.ap.get(field, '')
            entry.config(state="normal")
            entry.delete(0, tk.END)
            if value:
                entry.insert(0, str(value))
            else:
                entry.insert(0, "-")
            entry.config(state="readonly")
        
        # Load support notes
        self._refresh_notes()
    
    def _refresh_notes(self):
        """Refresh support notes display."""
        # Clear existing notes
        for widget in self.notes_frame.winfo_children():
            widget.destroy()
        
        # Get notes from database
        notes = self.db.get_support_notes(self.ap_id)
        
        if not notes:
            tk.Label(self.notes_frame, text="No notes yet. Click 'Write Note' to add one.",
                    font=('Segoe UI', 10), bg="#FFFFFF", fg="#6C757D").pack(pady=20)
            return
        
        # Display notes
        for note in notes:
            self._create_note_card(note)
    
    def _create_note_card(self, note):
        """Create a note card widget."""
        card = tk.Frame(self.notes_frame, bg="#F8F9FA", relief=tk.FLAT, bd=1)
        card.pack(fill=tk.X, pady=(0, 10), padx=5)
        
        card_content = tk.Frame(card, bg="#F8F9FA", padx=15, pady=12)
        card_content.pack(fill=tk.X)
        
        # Header
        header = tk.Frame(card_content, bg="#F8F9FA")
        header.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(header, text=note['headline'], font=('Segoe UI', 11, 'bold'),
                bg="#F8F9FA", fg="#212529").pack(side=tk.LEFT)
        
        # Meta info
        meta = tk.Frame(header, bg="#F8F9FA")
        meta.pack(side=tk.RIGHT)
        
        tk.Label(meta, text=f"{note['user']} • {note['created_at'][:16]}",
                font=('Segoe UI', 8), bg="#F8F9FA", fg="#6C757D").pack()
        
        # Note text
        note_text = tk.Text(card_content, wrap=tk.WORD, height=3, font=('Segoe UI', 9),
                           bg="#FFFFFF", relief=tk.FLAT, bd=1, padx=10, pady=8)
        note_text.insert('1.0', note['note'])
        note_text.config(state='disabled')
        note_text.pack(fill=tk.X, pady=(0, 8))
        
        # Replies count
        replies = self.db.get_support_note_replies(note['id'])
        if replies:
            tk.Label(card_content, text=f"💬 {len(replies)} replies",
                    font=('Segoe UI', 8), bg="#F8F9FA", fg="#6C757D").pack(anchor="w")
    
    def _auto_refresh(self):
        """Auto-refresh data every 10 seconds."""
        if not self.window.winfo_exists():
            return
        
        updated_ap = self.db.get_access_point(self.ap_id)
        if updated_ap:
            self.ap = updated_ap
            for field, entry in self.info_entries.items():
                value = self.ap.get(field, '')
                entry.config(state="normal")
                entry.delete(0, tk.END)
                entry.insert(0, str(value) if value else "-")
                entry.config(state="readonly")
        
        self.window.after(10000, self._auto_refresh)
    
    # Connection methods
    def _check_connection(self):
        """Ping the AP IP address and display result."""
        ip_address = self.ap.get('ip_address', '')
        if not ip_address:
            self.ping_result_label.config(text="No IP address available", fg="#DC3545")
            return
        
        # Log audit
        self.db.log_user_activity(
            username=self.current_user,
            activity_type='ap_connection_check',
            description=f'Checking connection to {ip_address}',
            ap_id=self.ap_id,
            success=True
        )
        
        self.ping_result_label.config(text="Pinging...", fg="#6C757D")
        self.window.update_idletasks()
        
        def ping_thread():
            import subprocess
            import platform
            
            try:
                # Ping command differs by OS
                param = '-n' if platform.system().lower() == 'windows' else '-c'
                command = ['ping', param, '4', ip_address]
                
                result = subprocess.run(command, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    # Extract statistics from ping output
                    output_lines = result.stdout.split('\n')
                    avg_line = None
                    for line in output_lines:
                        if 'Average' in line or 'avg' in line:
                            avg_line = line.strip()
                            break
                    
                    if avg_line:
                        msg = f"✓ Connected - {avg_line}"
                    else:
                        msg = "✓ Connected (4/4 packets received)"
                    
                    self.window.after(0, lambda: self.ping_result_label.config(text=msg, fg="#28A745"))
                else:
                    self.window.after(0, lambda: self.ping_result_label.config(text="✗ Connection failed", fg="#DC3545"))
                    
            except subprocess.TimeoutExpired:
                self.window.after(0, lambda: self.ping_result_label.config(text="✗ Timeout", fg="#DC3545"))
            except Exception as e:
                error_msg = f"✗ Error: {str(e)}"
                self.window.after(0, lambda msg=error_msg: self.ping_result_label.config(text=msg, fg="#DC3545"))
        
        threading.Thread(target=ping_thread, daemon=True).start()
    
    def _log_activity(self, message):
        """Add message to activity log (no-op in modern UI - could add status bar later)."""
        import time
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    # ========== BROWSER METHODS ==========
    
    def _connect_browser(self):
        """Open AP in browser using BrowserManager."""
        ip = self.ap.get('ip_address', '')
        username = self.ap.get('username_webui', '')
        password = self.ap.get('password_webui', '')
        
        if not ip:
            self._log_activity("✗ Missing IP address")
            messagebox.showwarning("Missing Info", "IP address not available.", parent=self.window)
            return
        
        if not username or not password:
            self._log_activity("✗ Missing credentials")
            messagebox.showwarning("Missing Info", "Username or password not available.", parent=self.window)
            return
        
        self._log_activity(f"Opening browser for {ip}...")
        self.browser_status_label.config(text="Connecting...", fg="#FFA500")
        
        # Run browser connection in separate thread to avoid blocking UI
        thread = threading.Thread(target=self._connect_browser_thread, args=(ip, username, password), daemon=True)
        thread.start()
    
    def _connect_browser_thread(self, ip, username, password):
        """Browser connection thread - runs in background."""
        try:
            import time
            import base64
            
            # Initialize browser if not already open for this window
            if not self.driver:
                self._log_activity("Initializing Chrome driver...")
                try:
                    from selenium import webdriver
                    from selenium.webdriver.chrome.service import Service
                    from webdriver_manager.chrome import ChromeDriverManager
                    
                    options = webdriver.ChromeOptions()
                    options.add_argument('--ignore-certificate-errors')
                    options.add_argument('--ignore-ssl-errors')
                    options.add_experimental_option('excludeSwitches', ['enable-logging'])
                    options.add_argument('--start-minimized')
                    
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=options)
                    try:
                        self.driver.minimize_window()
                        self._log_activity("✓ Chrome driver initialized (minimized)")
                    except:
                        self._log_activity("✓ Chrome driver initialized")
                except Exception as e:
                    self._log_activity(f"Failed to initialize browser: {str(e)}")
                    self.window.after(0, lambda: messagebox.showerror("Error", f"Failed to initialize browser: {str(e)}", parent=self.window))
                    self.window.after(0, lambda: self.browser_status_label.config(text="Connection failed", fg="#DC3545"))
                    return
            
            # Login using CDP authentication
            try:
                self._log_activity(f"Setting up authentication for {ip}")
                self.driver.execute_cdp_cmd('Network.enable', {})
                auth_header = 'Basic ' + base64.b64encode(f'{username}:{password}'.encode()).decode()
                self.driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': {'Authorization': auth_header}})
                
                url = f"http://{ip}"
                self._log_activity(f"Navigating to {url}")
                self.driver.get(url)
                time.sleep(2)
                
                # Check for and handle Cato Networks warning
                self._handle_cato_warning()
                
                self._log_activity(f"✓ Successfully authenticated to {ip}")
                
                # Navigate to status.xml to fetch AP information
                try:
                    status_url = f"http://{ip}/service/status.xml"
                    self._log_activity(f"Fetching AP information from {status_url}")
                    self.driver.get(status_url)
                    time.sleep(3)
                    
                    page_source = self.driver.page_source
                    self._log_activity(f"✓ AP information retrieved")
                    
                    self._extract_and_save_status_data(page_source, ip)
                    
                except Exception as e:
                    self._log_activity(f"⚠ Could not fetch status info: {str(e)}")
                
                self._log_activity(f"✓ Browser opened for {self.ap_id}")
                self.window.after(0, lambda: self.browser_status_label.config(text="Connected", fg="#28A745"))
                self.browser_connected = True
                
            except Exception as e:
                self._log_activity(f"Authentication failed: {str(e)}")
                self.window.after(0, lambda: messagebox.showerror("Error", f"Authentication failed: {str(e)}", parent=self.window))
                self.window.after(0, lambda: self.browser_status_label.config(text="Connection failed", fg="#DC3545"))
                return
                
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self._log_activity(f"✗ Error: {str(e)}")
            self.window.after(0, lambda: messagebox.showerror("Browser Error", 
                               f"Failed to open browser: {str(e)}\n\nDetails:\n{error_detail}", 
                               parent=self.window))
            self.window.after(0, lambda: self.browser_status_label.config(text="Connection failed", fg="#DC3545"))
    
    def _handle_cato_warning(self):
        """Handle Cato Networks warning if present."""
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            import time
            
            time.sleep(1)
            
            page_source = self.driver.page_source.lower()
            has_warning = 'cato networks' in page_source or 'your connection is not private' in page_source
            has_ssl_error = 'ssl' in page_source or 'certificate' in page_source
            
            if has_warning or has_ssl_error:
                self._log_activity("🚨 Cato Networks warning detected, clicking PROCEED button...")
                
                try:
                    proceed_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.proceed.prompt"))
                    )
                    proceed_button.click()
                    self._log_activity("✓ Clicked PROCEED button")
                    time.sleep(2)
                    self.driver.refresh()
                    time.sleep(3)
                except:
                    pass
        except Exception as e:
            self._log_activity(f"⚠ Error handling Cato warning: {str(e)}")
    
    def _extract_and_save_status_data(self, page_source, ip):
        """Extract data from status.xml page source and save to database."""
        try:
            self._log_activity("Extracting AP information...")
            
            ap_id = self._extract_xml_value(page_source, "AP ID")
            transmitter = self._extract_xml_value(page_source, "Transmitter")
            store_id = self._extract_xml_value(page_source, "Store ID")
            ip_address = self._extract_xml_value(page_source, "IP Address") or ip
            
            serial_number = self._extract_xml_value(page_source, "Serial Number")
            software_version = self._extract_xml_value(page_source, "Software Version")
            firmware_version = self._extract_xml_value(page_source, "Firmware Version")
            hardware_revision = self._extract_xml_value(page_source, "Hardware Revision")
            build = self._extract_xml_value(page_source, "Build")
            configuration_mode = self._extract_xml_value(page_source, "Configuration mode")
            uptime = self._extract_xml_value(page_source, "Uptime")
            mac_address = self._extract_xml_value(page_source, "MAC Address")
            
            service_status = self._extract_status_field(page_source, "service")
            communication_daemon_status = self._extract_status_field(page_source, "daemon")
            
            connectivity_internet = self._extract_xml_value(page_source, "Internet")
            connectivity_provisioning = self._extract_xml_value(page_source, "Provisioning")
            connectivity_ntp_server = self._extract_xml_value(page_source, "NTP Server")
            connectivity_apc_address = self._extract_xml_value(page_source, "APC Address")
            
            extracted_count = sum(1 for v in [ap_id, transmitter, store_id, serial_number, software_version, 
                                              firmware_version, hardware_revision, build, uptime, mac_address,
                                              service_status, communication_daemon_status] if v)
            self._log_activity(f"Extracted {extracted_count} fields from status page")
            
            if not ap_id:
                self._log_activity("✗ Could not extract AP ID from status page")
                return False
            
            self._log_activity(f"✓ AP ID: {ap_id}, SW: {software_version}, Service: {service_status}")
            
            update_data = {
                "ip_address": ip_address,
                "store_id": store_id,
                "type": transmitter,
                "serial_number": serial_number,
                "software_version": software_version,
                "firmware_version": firmware_version,
                "hardware_revision": hardware_revision,
                "build": build,
                "configuration_mode": configuration_mode,
                "service_status": service_status,
                "uptime": uptime,
                "communication_daemon_status": communication_daemon_status,
                "mac_address": mac_address,
                "connectivity_internet": connectivity_internet,
                "connectivity_provisioning": connectivity_provisioning,
                "connectivity_ntp_server": connectivity_ntp_server,
                "connectivity_apc_address": connectivity_apc_address
            }
            
            success, msg = self.db.update_access_point(ap_id, update_data)
            if success:
                self._log_activity("✓ AP information saved to database")
                updated_ap = self.db.get_access_point(ap_id)
                if updated_ap:
                    self.ap = updated_ap
                    self._load_data()
                    self._log_activity("✓ UI refreshed with extracted data")
                    return True
                else:
                    self.ap.update(update_data)
                    return True
            else:
                self._log_activity(f"✗ Failed to update AP: {msg}")
                return False
                
        except Exception as e:
            self._log_activity(f"✗ Extraction error: {str(e)}")
            return False
    
    def _extract_xml_value(self, html_text, field_name):
        """Extract value from HTML table row."""
        import re
        pattern = f"<th>{field_name}:</th>\\s*<td>([^<]*)</td>"
        match = re.search(pattern, html_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_status_field(self, html_text, context):
        """Extract Status field based on context (service or daemon)."""
        import re
        
        if context == "service":
            pattern = r'<th>Status:</th>\s*<td[^>]*>([^<]*)</td>'
            match = re.search(pattern, html_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        elif context == "daemon":
            pattern = r'<th>Status:</th>\s*<td[^>]*>([^<]*)</td>'
            matches = re.findall(pattern, html_text, re.IGNORECASE)
            if len(matches) >= 2:
                return matches[1].strip()
        
        return None
    
    def _open_browser(self):
        """Navigate browser to main page."""
        if not self.browser_connected:
            messagebox.showwarning("Not Connected", "Please connect browser first.", parent=self.window)
            return
        
        ip = self.ap.get('ip_address', '')
        if ip and self.driver:
            url = f"http://{ip}"
            self.driver.get(url)
            self._log_activity(f"Navigated to {url}")
    
    def _run_browser_automation(self):
        """Run browser automation - navigate to status page."""
        if not self.browser_connected:
            messagebox.showwarning("Not Connected", "Please connect browser first.", parent=self.window)
            return
        
        ip = self.ap.get('ip_address', '')
        if not ip:
            return
        
        try:
            status_url = f"http://{ip}/service/status.xml"
            self._log_activity(f"Loading {status_url}")
            self.driver.get(status_url)
            
            import time
            time.sleep(3)
            
            page_source = self.driver.page_source
            success = self._extract_and_save_status_data(page_source, ip)
            
            if success:
                messagebox.showinfo("Success", "AP information extracted and saved successfully.", parent=self.window)
            else:
                messagebox.showwarning("Extraction Failed", "Could not extract AP information from status page.", parent=self.window)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run automation: {str(e)}", parent=self.window)
    
    def _work_with_provisioning(self):
        """Work with provisioning settings via web UI."""
        if not self.browser_connected or not self.driver:
            messagebox.showwarning("Not Connected", "Please connect browser first.", parent=self.window)
            return
        
        messagebox.showinfo("Provisioning", 
                           "Provisioning configuration requires the provisioning_dialog module.\n\n"
                           "Use the 'Open Web UI' button to navigate manually to provisioning settings.",
                           parent=self.window)
    
    def _work_with_ssh_webui(self):
        """Configure SSH settings via web UI."""
        if not self.browser_connected or not self.driver:
            messagebox.showwarning("Not Connected", "Please connect browser first.", parent=self.window)
            return
        
        # Simple implementation - navigate to SSH page
        ip = self.ap.get('ip_address', '')
        if not ip:
            return
        
        try:
            self._log_activity("Navigating to SSH configuration page...")
            ssh_url = f"http://{ip}/service/config/ssh.xml"
            self.driver.get(ssh_url)
            self._log_activity(f"✓ SSH configuration page loaded")
            messagebox.showinfo("SSH Config", 
                               "The SSH configuration page is now open.\n\n"
                               "You can enable/disable SSH and click Apply manually.",
                               parent=self.window)
        except Exception as e:
            self._log_activity(f"✗ Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to navigate: {str(e)}", parent=self.window)
    
    def _do_software_update(self):
        """Navigate to software update page."""
        if not self.browser_connected or not self.driver:
            messagebox.showwarning("Not Connected", "Please connect browser first.", parent=self.window)
            return
        
        ip = self.ap.get('ip_address', '')
        if not ip:
            self._log_activity("✗ Missing IP address")
            return
        
        self._log_activity("Navigating to software update page...")
        
        try:
            update_url = f"http://{ip}/admin/updateSoftware.xml"
            self._log_activity(f"Loading {update_url}")
            self.driver.get(update_url)
            
            import time
            time.sleep(2)
            
            self._log_activity("✓ Software update page loaded")
            messagebox.showinfo("Manual Upload Required", 
                              "The software update page is now open.\n\n"
                              "Please manually upload the software file through the browser.",
                              parent=self.window)
            
        except Exception as e:
            self._log_activity(f"✗ Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to navigate: {str(e)}", parent=self.window)
    
    def _show_log(self):
        """Navigate to system log page."""
        if not self.browser_connected or not self.driver:
            messagebox.showwarning("Not Connected", "Please connect browser first.", parent=self.window)
            return
        
        ip = self.ap.get('ip_address', '')
        if not ip:
            self._log_activity("✗ Missing IP address")
            return
        
        self._log_activity("Navigating to system log page...")
        
        try:
            log_url = f"http://{ip}/service/config/system/viewLog.xml"
            self._log_activity(f"Loading {log_url}")
            self.driver.get(log_url)
            
            import time
            time.sleep(2)
            
            self._log_activity("✓ System log page loaded")
            
        except Exception as e:
            self._log_activity(f"✗ Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to navigate: {str(e)}", parent=self.window)
    
    # ========== SSH METHODS ==========
    
    def _open_ssh(self):
        """Open SSH terminal window."""
        if not SSH_AVAILABLE:
            messagebox.showerror("Error", "SSH functionality not available")
            return
        
        ip = self.ap.get('ip_address', '')
        if not ip:
            messagebox.showwarning("No IP", "No IP address configured for this AP")
            return
        
        # Open SSH window
        try:
            open_ssh_window(self.window, ip, f"AP {self.ap_id}")
            self.db.log_user_activity(
                username=self.current_user,
                activity_type='ssh_open',
                description=f'Opened SSH terminal for {self.ap_id} ({ip})',
                ap_id=self.ap_id,
                success=True
            )
        except Exception as e:
            messagebox.showerror("SSH Error", f"Failed to open SSH terminal: {e}")
    
    def _placeholder_action(self):
        messagebox.showinfo("Action", "This action is not implemented in test version")
    
    def _on_status_change(self, event=None):
        new_status = self.support_status_var.get()
        self.db.update_support_status(self.ap_id, new_status)
        self.db.log_user_activity(
            username=self.current_user,
            activity_type='status_change',
            description=f'Changed support status to {new_status}',
            ap_id=self.ap_id,
            success=True
        )
    
    def _open_jira_search(self):
        if JIRA_AVAILABLE:
            open_jira_search(self.window, self.db, ap_id=self.ap_id)
    
    def _open_another_ap(self):
        """Open another AP in a new window."""
        from ap_support_ui import APSearchDialog
        
        def on_ap_selected(selected_ap):
            APSupportWindowModern(self.window, selected_ap, self.current_user, self.db, self.browser_helper)
        
        APSearchDialog(self.window, self.current_user, self.db, on_select_callback=on_ap_selected)
    
    def _open_write_note_dialog(self):
        """Open dialog to write a new note."""
        dialog = tk.Toplevel(self.window)
        dialog.title("Write Note")
        dialog.geometry("700x500")
        dialog.configure(bg="#FFFFFF")
        dialog.transient(self.window)
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"700x500+{x}+{y}")
        
        content = tk.Frame(dialog, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text="Write Support Note", font=('Segoe UI', 14, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(0, 15))
        
        tk.Label(content, text="Headline:", font=('Segoe UI', 10),
                bg="#FFFFFF", fg="#495057").pack(anchor="w", pady=(0, 5))
        headline_entry = tk.Entry(content, font=('Segoe UI', 10), bd=1, relief=tk.SOLID)
        headline_entry.pack(fill=tk.X, pady=(0, 15))
        headline_entry.focus()
        
        tk.Label(content, text="Note:", font=('Segoe UI', 10),
                bg="#FFFFFF", fg="#495057").pack(anchor="w", pady=(0, 5))
        note_text = scrolledtext.ScrolledText(content, font=('Segoe UI', 10), wrap=tk.WORD,
                                             bd=1, relief=tk.SOLID)
        note_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        def save_note():
            headline = headline_entry.get().strip()
            note = note_text.get('1.0', tk.END).strip()
            
            if not headline or not note:
                messagebox.showwarning("Missing Info", "Please provide both headline and note")
                return
            
            try:
                self.db.add_support_note(self.ap_id, self.current_user, headline, note)
                self.db.log_user_activity(
                    username=self.current_user,
                    activity_type='note_add',
                    description=f'Added note: {headline}',
                    ap_id=self.ap_id,
                    success=True
                )
                messagebox.showinfo("Success", "Note saved successfully")
                dialog.destroy()
                self._refresh_notes()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save note: {e}")
        
        button_frame = tk.Frame(content, bg="#FFFFFF")
        button_frame.pack(fill=tk.X)
        
        tk.Button(button_frame, text="Save Note", command=save_note,
                 bg="#28A745", fg="white", font=('Segoe UI', 10, 'bold'),
                 padx=20, pady=10, relief=tk.FLAT, cursor="hand2",
                 activebackground="#218838").pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                 bg="#6C757D", fg="white", font=('Segoe UI', 10),
                 padx=20, pady=10, relief=tk.FLAT, cursor="hand2",
                 activebackground="#5A6268").pack(side=tk.LEFT)
    
    def _on_close(self):
        """Handle window close."""
        if self.ap_id in APSupportWindowModern._open_windows:
            del APSupportWindowModern._open_windows[self.ap_id]
        
        self.db.log_user_activity(
            username=self.current_user,
            activity_type='ap_support_close',
            description=f'Closed AP support window for {self.ap_id}',
            ap_id=self.ap_id,
            success=True
        )
        
        self.window.destroy()


# Test window launcher
def test_modern_window():
    """Test the modern AP support window."""
    root = tk.Tk()
    root.withdraw()
    
    # Use the same database as the main app (default location)
    db = DatabaseManager()
    
    # Get all APs from real database
    aps = db.search_access_points("")
    
    if not aps:
        messagebox.showerror("Error", "No APs found in database.\n\nPlease add APs using the main application first.")
        root.destroy()
        return
    
    # Create selection dialog
    root.deiconify()
    root.title("Select AP for Testing")
    root.geometry("500x400")
    
    frame = tk.Frame(root, padx=20, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    tk.Label(frame, text="Select an AP to test the modern UI:",
            font=('Segoe UI', 11, 'bold')).pack(pady=(0, 10))
    
    # Listbox with APs
    listbox_frame = tk.Frame(frame)
    listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    scrollbar = tk.Scrollbar(listbox_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set,
                        font=('Segoe UI', 9))
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=listbox.yview)
    
    # Populate listbox
    for ap in aps:
        status = ap.get('current_status', 'N/A')
        listbox.insert(tk.END, f"{ap['ap_id']} - Store: {ap.get('store_id', 'N/A')} - Status: {status}")
    
    # Select first item
    if aps:
        listbox.selection_set(0)
    
    def open_selected():
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an AP")
            return
        
        selected_ap = aps[selection[0]]
        root.withdraw()
        APSupportWindowModern(root, selected_ap, "test_user", db)
    
    # Buttons
    button_frame = tk.Frame(frame)
    button_frame.pack(fill=tk.X)
    
    tk.Button(button_frame, text="Open Modern UI", command=open_selected,
             bg="#007BFF", fg="white", font=('Segoe UI', 10, 'bold'),
             padx=20, pady=8, relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=(0, 5))
    
    tk.Button(button_frame, text="Cancel", command=root.destroy,
             bg="#6C757D", fg="white", font=('Segoe UI', 10),
             padx=20, pady=8, relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT)
    
    # Bind double-click
    listbox.bind('<Double-Button-1>', lambda e: open_selected())
    
    root.mainloop()


if __name__ == '__main__':
    test_modern_window()
