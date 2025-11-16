"""
AP Support System UI - Modern Redesign (Test Version)
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
            if existing_window.window.winfo_exists():
                existing_window.window.lift()
                existing_window.window.focus_force()
                return
            else:
                del APSupportWindowModern._open_windows[ap_id]
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"AP Support - {ap_id}")
        self.window.geometry("1000x700")
        
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
    
    # Placeholder methods
    def _check_connection(self):
        messagebox.showinfo("Check Connection", "Connection check not implemented in test version")
    
    def _connect_browser(self):
        messagebox.showinfo("Browser", "Browser connection not implemented in test version")
    
    def _open_browser(self):
        messagebox.showinfo("Browser", "Open browser not implemented in test version")
    
    def _run_browser_automation(self):
        messagebox.showinfo("Browser", "Browser automation not implemented in test version")
    
    def _open_ssh(self):
        messagebox.showinfo("SSH", "SSH terminal not implemented in test version")
    
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
        messagebox.showinfo("Open AP", "This feature requires the full application")
    
    def _open_write_note_dialog(self):
        messagebox.showinfo("Write Note", "Note writing not fully implemented in test version")
    
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
