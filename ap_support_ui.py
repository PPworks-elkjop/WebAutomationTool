"""
AP Support System UI
Provides comprehensive support interface for managing ESL Access Points
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from database_manager import DatabaseManager
from typing import Dict, List, Optional


class APSearchDialog:
    """Dialog for searching and selecting APs for support."""
    
    def __init__(self, parent, current_user: str, db_manager: DatabaseManager):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("AP Support - Search")
        self.dialog.geometry("1000x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.current_user = current_user
        self.db = db_manager
        self.selected_ap = None
        
        self._create_ui()
        self._perform_search()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"1000x600+{x}+{y}")
    
    def _create_ui(self):
        """Create the search UI."""
        # Search criteria frame
        search_frame = tk.LabelFrame(self.dialog, text="Search Criteria", padx=10, pady=10)
        search_frame.pack(fill="x", padx=10, pady=10)
        
        # Row 1: AP ID / IP Address
        row1 = tk.Frame(search_frame)
        row1.pack(fill="x", pady=5)
        
        tk.Label(row1, text="AP ID / IP Address:", width=15, anchor="w").pack(side="left")
        self.search_var = tk.StringVar()
        tk.Entry(row1, textvariable=self.search_var, width=30).pack(side="left", padx=5)
        
        # Row 2: Store ID
        row2 = tk.Frame(search_frame)
        row2.pack(fill="x", pady=5)
        
        tk.Label(row2, text="Store ID:", width=15, anchor="w").pack(side="left")
        self.store_var = tk.StringVar()
        tk.Entry(row2, textvariable=self.store_var, width=30).pack(side="left", padx=5)
        
        # Row 3: Support Status
        row3 = tk.Frame(search_frame)
        row3.pack(fill="x", pady=5)
        
        tk.Label(row3, text="Support Status:", width=15, anchor="w").pack(side="left")
        self.status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(row3, textvariable=self.status_var, width=27, state="readonly")
        status_combo['values'] = ("All", "active", "in_progress", "pending", "resolved", "closed")
        status_combo.pack(side="left", padx=5)
        
        # Row 4: Jira Tickets
        row4 = tk.Frame(search_frame)
        row4.pack(fill="x", pady=5)
        
        tk.Label(row4, text="Jira Tickets:", width=15, anchor="w").pack(side="left")
        self.tickets_var = tk.StringVar(value="All")
        tickets_combo = ttk.Combobox(row4, textvariable=self.tickets_var, width=27, state="readonly")
        tickets_combo['values'] = ("All", "With Open Tickets", "Without Open Tickets")
        tickets_combo.pack(side="left", padx=5)
        
        # Search button
        tk.Button(row4, text="Search", command=self._perform_search, bg="#007BFF", fg="white", 
                 cursor="hand2", padx=20).pack(side="left", padx=10)
        
        # Results frame
        results_frame = tk.LabelFrame(self.dialog, text="Search Results", padx=10, pady=10)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Treeview for results
        tree_frame = tk.Frame(results_frame)
        tree_frame.pack(fill="both", expand=True)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("ap_id", "store_id", "ip_address", "type", "status", "support_status", "tickets"),
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configure columns
        self.tree.heading("ap_id", text="AP ID")
        self.tree.heading("store_id", text="Store ID")
        self.tree.heading("ip_address", text="IP Address")
        self.tree.heading("type", text="Type")
        self.tree.heading("status", text="Status")
        self.tree.heading("support_status", text="Support Status")
        self.tree.heading("tickets", text="Open Tickets")
        
        self.tree.column("ap_id", width=120, anchor="w")
        self.tree.column("store_id", width=100, anchor="center")
        self.tree.column("ip_address", width=120, anchor="center")
        self.tree.column("type", width=100, anchor="w")
        self.tree.column("status", width=80, anchor="center")
        self.tree.column("support_status", width=120, anchor="center")
        self.tree.column("tickets", width=100, anchor="center")
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Double-click to open
        self.tree.bind("<Double-1>", self._on_double_click)
        
        # Buttons frame
        btn_frame = tk.Frame(self.dialog)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(btn_frame, text="Open Selected", command=self._on_open, bg="#28A745", fg="white",
                 cursor="hand2", padx=20, pady=5).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", command=self.dialog.destroy, bg="#6C757D", fg="white",
                 cursor="hand2", padx=20, pady=5).pack(side="right", padx=5)
        
        # Result count label
        self.count_label = tk.Label(btn_frame, text="0 APs found", fg="#666666")
        self.count_label.pack(side="left", padx=20)
    
    def _perform_search(self):
        """Perform AP search based on criteria."""
        # Clear existing results
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get search parameters
        search_term = self.search_var.get().strip() or None
        store_id = self.store_var.get().strip() or None
        support_status = None if self.status_var.get() == "All" else self.status_var.get()
        
        has_open_tickets = None
        if self.tickets_var.get() == "With Open Tickets":
            has_open_tickets = True
        elif self.tickets_var.get() == "Without Open Tickets":
            has_open_tickets = False
        
        # Perform search
        aps = self.db.search_aps_for_support(
            search_term=search_term,
            store_id=store_id,
            support_status=support_status,
            has_open_tickets=has_open_tickets
        )
        
        # Populate results
        for ap in aps:
            # Count open tickets
            open_tickets = self._count_open_tickets(ap['ap_id'])
            
            self.tree.insert("", "end", values=(
                ap.get('ap_id', ''),
                ap.get('store_id', ''),
                ap.get('ip_address', ''),
                ap.get('type', ''),
                ap.get('status', 'unknown'),
                ap.get('support_status', 'active'),
                str(open_tickets) if open_tickets > 0 else '-'
            ), tags=(ap['ap_id'],))
        
        self.count_label.config(text=f"{len(aps)} AP(s) found")
    
    def _count_open_tickets(self, ap_id: str) -> int:
        """Count open Jira tickets for an AP."""
        try:
            # Get tickets from database
            tickets = self.db.get_tickets_for_ap(ap_id)
            return sum(1 for t in tickets if t.get('status') not in ('Closed', 'Resolved', 'Done'))
        except:
            return 0
    
    def _on_double_click(self, event):
        """Handle double-click on tree item."""
        self._on_open()
    
    def _on_open(self):
        """Open the selected AP in support window."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an AP to open.", parent=self.dialog)
            return
        
        item = selection[0]
        ap_id = self.tree.item(item, "tags")[0]
        
        # Get full AP data
        ap = self.db.get_access_point(ap_id)
        if ap:
            self.selected_ap = ap
            self.dialog.destroy()
        else:
            messagebox.showerror("Error", "Failed to load AP data.", parent=self.dialog)
    
    def get_selected_ap(self) -> Optional[Dict]:
        """Get the selected AP (call after dialog closes)."""
        return self.selected_ap


class APSupportWindow:
    """Support window for a single AP."""
    
    # Class variable to track open windows
    _open_windows = {}
    
    def __init__(self, parent, ap: Dict, current_user: str, db_manager: DatabaseManager, 
                 browser_helper=None):
        ap_id = ap['ap_id']
        
        # Check if window already exists for this AP
        if ap_id in APSupportWindow._open_windows:
            existing_window = APSupportWindow._open_windows[ap_id]
            if existing_window.window.winfo_exists():
                existing_window.window.lift()
                existing_window.window.focus_force()
                return
            else:
                # Window was closed, remove from dict
                del APSupportWindow._open_windows[ap_id]
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"AP Support - {ap_id}")
        self.window.geometry("900x700")
        
        self.ap = ap
        self.ap_id = ap_id
        self.current_user = current_user
        self.db = db_manager
        self.browser_helper = browser_helper
        
        # Register this window
        APSupportWindow._open_windows[ap_id] = self
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self._create_ui()
        self._load_data()
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.window.winfo_screenheight() // 2) - (700 // 2)
        self.window.geometry(f"900x700+{x}+{y}")
    
    def _create_ui(self):
        """Create the support window UI with modern layout matching main window."""
        # Configure modern style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Modern color scheme (matching main window)
        bg_color = "#F5F5F5"
        frame_bg = "#FFFFFF"
        
        self.window.configure(bg=bg_color)
        
        # Configure ttk styles to match main window
        style.configure("APSupport.TFrame", background=frame_bg)
        style.configure("APSupport.TLabelframe", background=frame_bg, borderwidth=0, relief="flat")
        style.configure("APSupport.TLabelframe.Label", background=frame_bg, foreground="#333333", 
                       font=("Segoe UI", 11, "bold"))
        
        # Main container with padding
        main_container = ttk.Frame(self.window, padding=15, style="APSupport.TFrame")
        main_container.pack(fill="both", expand=True)
        
        # LEFT COLUMN
        left_column = ttk.Frame(main_container, style="APSupport.TFrame")
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # RIGHT COLUMN
        right_column = ttk.Frame(main_container, style="APSupport.TFrame", width=350)
        right_column.pack(side="right", fill="both", padx=(10, 0))
        right_column.pack_propagate(False)
        
        # === LEFT TOP: AP Information Section ===
        info_frame = ttk.LabelFrame(left_column, text="AP Information", padding=15, 
                                    style="APSupport.TLabelframe")
        info_frame.pack(fill="x", pady=(0, 10))
        
        # Create info grid
        info_grid = ttk.Frame(info_frame, style="APSupport.TFrame")
        info_grid.pack(fill="x")
        
        info_labels = [
            ("AP ID:", "ap_id"),
            ("Store ID:", "store_id"),
            ("IP Address:", "ip_address"),
            ("Type:", "type"),
            ("Serial Number:", "serial_number"),
            ("Software Version:", "software_version"),
            ("Firmware Version:", "firmware_version"),
            ("Hardware Revision:", "hardware_revision"),
            ("MAC Address:", "mac_address"),
            ("Uptime:", "uptime"),
        ]
        
        self.info_labels = {}
        for idx, (label_text, field) in enumerate(info_labels):
            row = idx // 2
            col = (idx % 2) * 2
            
            tk.Label(info_grid, text=label_text, font=("Segoe UI", 9, "bold"), anchor="w", 
                    width=18, bg=frame_bg).grid(row=row, column=col, sticky="w", padx=5, pady=3)
            value_label = tk.Label(info_grid, text="", font=("Segoe UI", 9), anchor="w", bg=frame_bg)
            value_label.grid(row=row, column=col+1, sticky="w", padx=5, pady=3)
            self.info_labels[field] = value_label
        
        # === LEFT: Status Section ===
        status_frame = ttk.LabelFrame(left_column, text="Status", padding=15, 
                                      style="APSupport.TLabelframe")
        status_frame.pack(fill="x", pady=(0, 10))
        
        status_inner = ttk.Frame(status_frame, style="APSupport.TFrame")
        status_inner.pack(fill="x")
        
        tk.Label(status_inner, text="Support Status:", font=("Segoe UI", 9, "bold"), 
                bg=frame_bg).pack(side="left")
        self.support_status_var = tk.StringVar(value=self.ap.get('support_status', 'active'))
        status_combo = ttk.Combobox(status_inner, textvariable=self.support_status_var, 
                                    width=15, state="readonly")
        status_combo['values'] = ("active", "in_progress", "pending", "resolved", "closed")
        status_combo.pack(side="left", padx=10)
        status_combo.bind("<<ComboboxSelected>>", self._on_status_change)
        
        tk.Button(status_inner, text="Refresh Data", command=self._refresh_ap_data,
                 bg="#17A2B8", fg="white", cursor="hand2", padx=15, pady=6,
                 font=("Segoe UI", 9), relief="flat", bd=0,
                 activebackground="#138496").pack(side="left", padx=5)
        
        # === LEFT MIDDLE: Placeholder for future features ===
        middle_frame = ttk.Frame(left_column, style="APSupport.TFrame", height=100)
        middle_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # === LEFT BOTTOM: Connection Section ===
        connections_container = ttk.Frame(left_column, style="APSupport.TFrame")
        connections_container.pack(fill="x")
        
        # Web Connection
        web_frame = ttk.LabelFrame(connections_container, text="Web", padding=15, 
                                   style="APSupport.TLabelframe")
        web_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        tk.Button(web_frame, text="Open in Browser", command=self._connect_browser, 
                 bg="#007BFF", fg="white", cursor="hand2", padx=20, pady=10,
                 font=("Segoe UI", 10), relief="flat", bd=0,
                 activebackground="#0056b3").pack()
        
        # SSH Connection
        ssh_frame = ttk.LabelFrame(connections_container, text="SSH", padding=15, 
                                   style="APSupport.TLabelframe")
        ssh_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))
        
        tk.Button(ssh_frame, text="SSH Connection", command=self._connect_ssh, 
                 bg="#6C757D", fg="white", cursor="hand2", padx=20, pady=10,
                 font=("Segoe UI", 10), state="disabled", relief="flat", bd=0,
                 activebackground="#5A6268").pack()
        
        # === RIGHT TOP: Notes Section ===
        notes_frame = ttk.LabelFrame(right_column, text="Notes", padding=10, 
                                     style="APSupport.TLabelframe")
        notes_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Notes list with scrollbar (2-row format: date/user, then headline)
        notes_canvas = tk.Canvas(notes_frame, bg=frame_bg, highlightthickness=0)
        notes_scroll = ttk.Scrollbar(notes_frame, orient="vertical", command=notes_canvas.yview)
        self.notes_container = tk.Frame(notes_canvas, bg=frame_bg)
        
        self.notes_container.bind(
            "<Configure>",
            lambda e: notes_canvas.configure(scrollregion=notes_canvas.bbox("all"))
        )
        
        notes_canvas.create_window((0, 0), window=self.notes_container, anchor="nw")
        notes_canvas.configure(yscrollcommand=notes_scroll.set)
        
        notes_canvas.pack(side="left", fill="both", expand=True)
        notes_scroll.pack(side="right", fill="y")
        
        # Mouse wheel scrolling for notes
        def _on_notes_mousewheel(event):
            notes_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        notes_canvas.bind_all("<MouseWheel>", _on_notes_mousewheel)
        
        # Store notes data
        self.notes_data = []
        self.note_widgets = []
        self.note_window = None
        self.note_window_modified = False
        
        # === RIGHT MIDDLE: Jira Tickets Placeholder ===
        jira_frame = ttk.LabelFrame(right_column, text="Jira Tickets", padding=10, 
                                    style="APSupport.TLabelframe")
        jira_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(jira_frame, text="Jira integration coming soon...", 
                font=("Segoe UI", 9, "italic"), fg="#888888", bg=frame_bg).pack()
        
        # === RIGHT BOTTOM: Action Buttons ===
        action_frame = ttk.Frame(right_column, style="APSupport.TFrame")
        action_frame.pack(fill="x")
        
        tk.Button(action_frame, text="Open Another AP", command=self._open_another_ap,
                 bg="#007BFF", fg="white", cursor="hand2", padx=20, pady=10,
                 font=("Segoe UI", 10), relief="flat", bd=0,
                 activebackground="#0056b3").pack(fill="x", pady=(0, 5))
        
        tk.Button(action_frame, text="Close Window", command=self._on_close,
                 bg="#6C757D", fg="white", cursor="hand2", padx=20, pady=10,
                 font=("Segoe UI", 10), relief="flat", bd=0,
                 activebackground="#5A6268").pack(fill="x")
    
    def _load_data(self):
        """Load AP data into the UI."""
        # Populate info labels
        for field, label in self.info_labels.items():
            value = self.ap.get(field, '')
            if value:
                label.config(text=str(value))
            else:
                label.config(text="-", fg="gray")
        
        # Update support status
        self.support_status_var.set(self.ap.get('support_status', 'active'))
        
        # Load support notes
        self._refresh_notes()
    
    def _refresh_ap_data(self):
        """Refresh AP data from database."""
        # Reload AP from database
        updated_ap = self.db.get_access_point(self.ap_id)
        if updated_ap:
            self.ap = updated_ap
            
            # Update all info labels
            for field, label in self.info_labels.items():
                value = self.ap.get(field, '')
                if value:
                    label.config(text=str(value), fg="black")
                else:
                    label.config(text="-", fg="gray")
            
            # Update support status
            self.support_status_var.set(self.ap.get('support_status', 'active'))
            
            # Refresh notes
            self._refresh_notes()
            
            messagebox.showinfo("Data Refreshed", 
                              f"AP data for {self.ap_id} has been refreshed from database.",
                              parent=self.window)
        else:
            messagebox.showerror("Error", 
                               f"Failed to reload AP data for {self.ap_id}.",
                               parent=self.window)
    
    def _refresh_notes(self):
        """Refresh the notes list with new 2-row format."""
        # Clear existing widgets
        for widget in self.note_widgets:
            widget.destroy()
        self.note_widgets.clear()
        
        # Load notes from database
        self.notes_data = self.db.get_support_notes(self.ap_id)
        
        # Create note items in 2-row format
        for idx, note in enumerate(self.notes_data):
            note_frame = tk.Frame(self.notes_container, bg="#FFFFFF", relief="solid", 
                                 borderwidth=1, cursor="hand2", highlightbackground="#E0E0E0",
                                 highlightthickness=1)
            note_frame.pack(fill="x", pady=3, padx=3)
            
            # Row 1: Date/Time and User
            row1 = tk.Label(note_frame, text=f"{note['created_at']} - {note['user']}", 
                          font=("Segoe UI", 8), fg="#888888", bg="#FFFFFF", anchor="w")
            row1.pack(fill="x", padx=8, pady=(5, 0))
            
            # Row 2: Headline
            row2 = tk.Label(note_frame, text=note['headline'], 
                          font=("Segoe UI", 9, "bold"), bg="#FFFFFF", anchor="w", fg="#333333")
            row2.pack(fill="x", padx=8, pady=(0, 5))
            
            # Bind click events
            for widget in [note_frame, row1, row2]:
                widget.bind("<Button-1>", lambda e, n=note: self._open_note_window(n))
            
            self.note_widgets.append(note_frame)
    
    def _on_status_change(self, event=None):
        """Handle support status change."""
        new_status = self.support_status_var.get()
        success, message = self.db.update_support_status(self.ap_id, new_status)
        if success:
            messagebox.showinfo("Status Updated", f"Support status changed to: {new_status}", parent=self.window)
        else:
            messagebox.showerror("Error", f"Failed to update status: {message}", parent=self.window)
    
    def _connect_browser(self):
        """Open AP in browser."""
        if self.browser_helper:
            # Use Quick Connect functionality
            ip = self.ap.get('ip_address', '')
            username = self.ap.get('username_webui', '')
            password = self.ap.get('password_webui', '')
            
            if ip and username and password:
                messagebox.showinfo("Connecting", f"Opening browser for {self.ap_id}...", parent=self.window)
                # TODO: Call browser helper's quick connect
            else:
                messagebox.showwarning("Missing Info", "IP address or credentials not available.", parent=self.window)
        else:
            messagebox.showwarning("Not Available", "Browser connection not available.", parent=self.window)
    
    def _connect_ssh(self):
        """Connect via SSH (placeholder for future implementation)."""
        messagebox.showinfo("Coming Soon", "SSH connection will be available in a future update.", parent=self.window)
    
    def _open_another_ap(self):
        """Open the AP search dialog to open another AP support window."""
        # Import here to avoid circular dependency
        from ap_support_ui import APSearchDialog
        
        search_dialog = APSearchDialog(self.window, self.db, self.current_user)
        selected_ap = search_dialog.get_selected_ap()
        
        if selected_ap:
            # Open new support window (will check if already open)
            APSupportWindow(self.window, selected_ap, self.current_user, 
                          self.db, self.browser_helper)
    
    def _open_note_window(self, note):
        """Open or update the note detail window."""
        # Check if window exists and has unsaved changes
        if self.note_window and self.note_window.winfo_exists():
            if self.note_window_modified:
                response = messagebox.askyesnocancel(
                    "Unsaved Changes",
                    "You have unsaved changes. Do you want to save them?",
                    parent=self.note_window
                )
                if response is None:  # Cancel
                    return
                elif response:  # Yes, save
                    self._save_note_from_window()
            
            # Update existing window with new note
            self._update_note_window(note)
        else:
            # Create new note window
            self._create_note_window(note)
    
    def _create_note_window(self, note):
        """Create a new note detail/edit window."""
        self.note_window = tk.Toplevel(self.window)
        self.note_window.title(f"Note - {note['headline']}")
        self.note_window.geometry("650x550")
        self.note_window.configure(bg="#FFFFFF")
        self.note_window_modified = False
        
        # Store current note ID
        self.current_note_id = note['id']
        
        # Header with note info
        header = tk.Frame(self.note_window, bg="#F8F9FA", relief="solid", borderwidth=1)
        header.pack(fill="x", padx=15, pady=15)
        
        tk.Label(header, text=f"Created: {note['created_at']}", 
                font=("Segoe UI", 9), bg="#F8F9FA").pack(anchor="w", padx=15, pady=3)
        tk.Label(header, text=f"By: {note['user']}", 
                font=("Segoe UI", 9), bg="#F8F9FA").pack(anchor="w", padx=15, pady=3)
        
        if note.get('updated_at') and note['updated_at'] != note['created_at']:
            tk.Label(header, text=f"Last edited: {note['updated_at']} by {note.get('updated_by', 'unknown')}", 
                    font=("Segoe UI", 8, "italic"), fg="#888888", bg="#F8F9FA").pack(anchor="w", padx=15, pady=3)
        
        # Headline
        headline_frame = tk.Frame(self.note_window, bg="#FFFFFF")
        headline_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        tk.Label(headline_frame, text="Headline:", font=("Segoe UI", 10, "bold"), 
                bg="#FFFFFF").pack(anchor="w", pady=(0, 5))
        self.note_window_headline = tk.Entry(headline_frame, font=("Segoe UI", 10), 
                                             relief="solid", borderwidth=1)
        self.note_window_headline.pack(fill="x")
        self.note_window_headline.insert(0, note['headline'])
        
        # Check if this is the user's note and latest
        is_latest = self.db.is_latest_note(note['id'], self.ap_id)
        is_owner = note['user'] == self.current_user
        can_edit = is_latest and is_owner
        
        if not can_edit:
            self.note_window_headline.config(state="readonly")
        
        # Note content
        content_frame = tk.Frame(self.note_window, bg="#FFFFFF")
        content_frame.pack(fill="both", expand=True, padx=15)
        
        tk.Label(content_frame, text="Note:", font=("Segoe UI", 10, "bold"), 
                bg="#FFFFFF").pack(anchor="w", pady=(0, 5))
        self.note_window_text = scrolledtext.ScrolledText(content_frame, font=("Segoe UI", 10), 
                                                          wrap=tk.WORD, height=12, relief="solid", 
                                                          borderwidth=1)
        self.note_window_text.pack(fill="both", expand=True)
        self.note_window_text.insert("1.0", note['note'])
        
        if not can_edit:
            self.note_window_text.config(state="disabled")
        else:
            # Track modifications
            def on_modify(event=None):
                self.note_window_modified = True
            self.note_window_text.bind("<<Modified>>", on_modify)
            self.note_window_headline.bind("<KeyRelease>", on_modify)
        
        # Reply section
        reply_frame = tk.LabelFrame(self.note_window, text="Add Reply", padx=15, pady=10,
                                    bg="#FFFFFF", font=("Segoe UI", 10, "bold"))
        reply_frame.pack(fill="x", padx=15, pady=(10, 0))
        
        tk.Label(reply_frame, text="Reply:", bg="#FFFFFF", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 5))
        self.note_window_reply = scrolledtext.ScrolledText(reply_frame, height=4, 
                                                           font=("Segoe UI", 10), wrap=tk.WORD,
                                                           relief="solid", borderwidth=1)
        self.note_window_reply.pack(fill="x")
        
        # Buttons
        btn_frame = tk.Frame(self.note_window, bg="#FFFFFF")
        btn_frame.pack(fill="x", padx=15, pady=15)
        
        if can_edit:
            tk.Button(btn_frame, text="Save Changes", command=self._save_note_from_window,
                     bg="#28A745", fg="white", padx=20, pady=10, relief="flat", bd=0,
                     cursor="hand2", font=("Segoe UI", 10),
                     activebackground="#218838").pack(side="left", padx=5)
            
            tk.Button(btn_frame, text="Delete Note", command=self._delete_note_from_window,
                     bg="#DC3545", fg="white", padx=20, pady=10, relief="flat", bd=0,
                     cursor="hand2", font=("Segoe UI", 10),
                     activebackground="#C82333").pack(side="left", padx=5)
        
        tk.Button(btn_frame, text="Add Reply", command=self._add_reply_from_window,
                 bg="#007BFF", fg="white", padx=20, pady=10, relief="flat", bd=0,
                 cursor="hand2", font=("Segoe UI", 10),
                 activebackground="#0056b3").pack(side="left", padx=5)
        
        tk.Button(btn_frame, text="Close", command=self._close_note_window,
                 bg="#6C757D", fg="white", padx=20, pady=10, relief="flat", bd=0,
                 cursor="hand2", font=("Segoe UI", 10),
                 activebackground="#5A6268").pack(side="right", padx=5)
    
    def _update_note_window(self, note):
        """Update the existing note window with different note."""
        self.current_note_id = note['id']
        self.note_window_modified = False
        
        # Update title
        self.note_window.title(f"Note - {note['headline']}")
        
        # Update headline
        self.note_window_headline.config(state="normal")
        self.note_window_headline.delete(0, tk.END)
        self.note_window_headline.insert(0, note['headline'])
        
        # Update note content
        self.note_window_text.config(state="normal")
        self.note_window_text.delete("1.0", tk.END)
        self.note_window_text.insert("1.0", note['note'])
        
        # Check permissions
        is_latest = self.db.is_latest_note(note['id'], self.ap_id)
        is_owner = note['user'] == self.current_user
        can_edit = is_latest and is_owner
        
        if not can_edit:
            self.note_window_headline.config(state="readonly")
            self.note_window_text.config(state="disabled")
        
        # Clear reply
        self.note_window_reply.delete("1.0", tk.END)
    
    def _save_note_from_window(self):
        """Save note edits from the note window."""
        headline = self.note_window_headline.get().strip()
        content = self.note_window_text.get("1.0", tk.END).strip()
        
        if not headline or not content:
            messagebox.showwarning("Missing Data", "Headline and note content are required.", 
                                 parent=self.note_window)
            return
        
        success, message = self.db.update_support_note(self.current_note_id, headline, 
                                                       content, self.current_user)
        if success:
            self.note_window_modified = False
            self._refresh_notes()
            messagebox.showinfo("Saved", "Note updated successfully.", parent=self.note_window)
        else:
            messagebox.showerror("Error", f"Failed to save: {message}", parent=self.note_window)
    
    def _delete_note_from_window(self):
        """Delete note from the note window."""
        response = messagebox.askyesno("Confirm Delete", 
                                      "Are you sure you want to delete this note?",
                                      parent=self.note_window)
        if not response:
            return
        
        success, message = self.db.delete_support_note(self.current_note_id, self.current_user)
        if success:
            self._refresh_notes()
            self.note_window.destroy()
            self.note_window = None
            messagebox.showinfo("Deleted", "Note deleted successfully.", parent=self.window)
        else:
            messagebox.showerror("Error", f"Failed to delete: {message}", parent=self.note_window)
    
    def _add_reply_from_window(self):
        """Add a reply to the current note."""
        reply_text = self.note_window_reply.get("1.0", tk.END).strip()
        
        if not reply_text:
            messagebox.showwarning("Empty Reply", "Please enter reply text.", 
                                 parent=self.note_window)
            return
        
        # Get original note to create reply headline
        note = next((n for n in self.notes_data if n['id'] == self.current_note_id), None)
        if not note:
            return
        
        headline = f"Re: {note['headline']}"
        
        success, message, note_id = self.db.add_support_note(self.ap_id, self.current_user, 
                                                             headline, reply_text)
        if success:
            self._refresh_notes()
            self.note_window_reply.delete("1.0", tk.END)
            messagebox.showinfo("Reply Added", "Reply added successfully.", parent=self.note_window)
        else:
            messagebox.showerror("Error", f"Failed to add reply: {message}", parent=self.note_window)
    
    def _close_note_window(self):
        """Close the note window with unsaved changes check."""
        if self.note_window_modified:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them?",
                parent=self.note_window
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes, save
                self._save_note_from_window()
        
        self.note_window.destroy()
        self.note_window = None
    
    def _on_close(self):
        """Handle window close."""
        # Unregister window
        if self.ap_id in APSupportWindow._open_windows:
            del APSupportWindow._open_windows[self.ap_id]
        self.window.destroy()
