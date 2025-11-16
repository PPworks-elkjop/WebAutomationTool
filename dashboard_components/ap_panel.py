"""
AP Panel - Upper Left
Shows multiple AP tabs, each with Overview/Notes/Browser/SSH/Actions sub-tabs
"""

import tkinter as tk
from tkinter import ttk, messagebox
from ap_support_ui_v3 import APSupportWindowModern


class APPanel:
    """Upper left panel - Multi-tab AP support interface."""
    
    # Track open APs to prevent duplicates
    _open_aps = {}
    
    def __init__(self, parent, current_user, db, on_ap_change=None, on_tab_change=None, log_callback=None):
        self.parent = parent
        self.current_user = current_user
        self.db = db
        self.on_ap_change = on_ap_change
        self.on_tab_change = on_tab_change
        self.log_callback = log_callback
        
        # AP data storage
        self.ap_tabs = {}  # {tab_id: {ap_data, frame, widgets}}
        
        self._create_ui()
    
    def _create_ui(self):
        """Create AP panel UI."""
        # Header
        header = tk.Frame(self.parent, bg="#0066CC", height=40)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        tk.Label(header, text="AP Support", font=('Segoe UI', 12, 'bold'),
                bg="#0066CC", fg="white").pack(side=tk.LEFT, padx=15, pady=8)
        
        # Notebook for AP tabs (with larger font)
        style = ttk.Style()
        style.configure('APPanel.TNotebook.Tab', font=('Segoe UI', 11), padding=[15, 8])
        
        self.notebook = ttk.Notebook(self.parent, style='APPanel.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_notebook_tab_changed)
        
        # Add Search AP as first tab
        self._create_search_tab()
        
        # Show welcome message if no APs open
        # (Search tab is always present, so no need for welcome tab)
    
    def _create_search_tab(self):
        """Create Search AP tab."""
        search_frame = ttk.Frame(self.notebook)
        self.notebook.add(search_frame, text="🔍 Search AP")
        
        content = tk.Frame(search_frame, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text="Search for Access Points", font=('Segoe UI', 14, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(0, 20))
        
        # Search input
        search_label_frame = tk.Frame(content, bg="#FFFFFF")
        search_label_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(search_label_frame, text="AP ID, Store ID, or IP Address:", 
                font=('Segoe UI', 10),
                bg="#FFFFFF", fg="#495057").pack(anchor="w")
        
        search_input_frame = tk.Frame(content, bg="#FFFFFF")
        search_input_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.search_entry = tk.Entry(search_input_frame, font=('Segoe UI', 11), 
                                     bd=1, relief=tk.SOLID)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.search_entry.bind('<Return>', lambda e: self._perform_search())
        
        tk.Button(search_input_frame, text="Search", command=self._perform_search,
                 bg="#0066CC", fg="white", font=('Segoe UI', 10, 'bold'),
                 padx=20, pady=8, relief=tk.FLAT, cursor="hand2",
                 activebackground="#0052A3").pack(side=tk.LEFT)
        
        # Results listbox
        tk.Label(content, text="Search Results:", font=('Segoe UI', 10, 'bold'),
                bg="#FFFFFF", fg="#495057").pack(anchor="w", pady=(0, 5))
        
        list_frame = tk.Frame(content, bg="#FFFFFF")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.search_results = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                        font=('Segoe UI', 10), bd=1, relief=tk.SOLID,
                                        selectmode=tk.SINGLE, height=15)
        self.search_results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.search_results.yview)
        
        self.search_results.bind('<Double-Button-1>', lambda e: self._open_selected_ap())
        
        # Store AP data for results
        self.search_ap_data = []
        
        # Button to open selected
        tk.Button(content, text="Open Selected AP", command=self._open_selected_ap,
                 bg="#28A745", fg="white", font=('Segoe UI', 10, 'bold'),
                 padx=20, pady=10, relief=tk.FLAT, cursor="hand2",
                 activebackground="#218838").pack(pady=(10, 0))
    
    def _perform_search(self):
        """Perform AP search."""
        search_term = self.search_entry.get().strip()
        
        if not search_term:
            messagebox.showwarning("Search", "Please enter a search term", parent=self.parent)
            return
        
        self.search_results.delete(0, tk.END)
        self.search_ap_data = []
        
        try:
            # Search database
            results = self.db.search_access_points(search_term)
            
            if results:
                for ap in results:
                    display_text = f"{ap['ap_id']} - Store: {ap.get('store_id', 'N/A')} - {ap.get('ip_address', 'N/A')}"
                    self.search_results.insert(tk.END, display_text)
                    self.search_ap_data.append(ap)
                
                self._log(f"Found {len(results)} APs matching '{search_term}'")
            else:
                self.search_results.insert(tk.END, "No results found")
                self._log(f"No APs found for '{search_term}'")
                
        except Exception as e:
            messagebox.showerror("Search Error", f"Failed to search: {e}", parent=self.parent)
            self._log(f"Search error: {e}", "error")
    
    def _open_selected_ap(self):
        """Open the selected AP from search results."""
        selection = self.search_results.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an AP to open", parent=self.parent)
            return
        
        index = selection[0]
        if index < len(self.search_ap_data):
            ap_data = self.search_ap_data[index]
            self.add_ap_tab(ap_data)
    
    def add_ap_tab(self, ap_data):
        """Add a new AP tab."""
        ap_id = ap_data['ap_id']
        
        # Check if already open
        if ap_id in self.ap_tabs:
            # Switch to existing tab
            for i in range(self.notebook.index("end")):
                tab_text = self.notebook.tab(i, "text")
                if tab_text.startswith(ap_id) or tab_text.endswith(ap_id):
                    self.notebook.select(i)
                    break
            self._log(f"AP {ap_id} already open, switched to tab")
            return
        
        # Create embedded AP support frame
        ap_frame = ttk.Frame(self.notebook)
        tab_name = f"AP {ap_id}"
        self.notebook.add(ap_frame, text=tab_name)
        
        # Embed AP support UI (without creating new Toplevel window)
        # We'll create a simplified embedded version
        self._create_embedded_ap_support(ap_frame, ap_data)
        
        # Store tab info
        self.ap_tabs[ap_id] = {
            'ap_data': ap_data,
            'frame': ap_frame,
            'tab_id': self.notebook.index("end") - 1
        }
        
        # Select the new tab
        self.notebook.select(self.notebook.index("end") - 1)
        
        self._log(f"Opened AP {ap_id}")
        
        # Notify parent
        if self.on_ap_change:
            self.on_ap_change(ap_id, ap_data)
    
    def _create_embedded_ap_support(self, parent, ap_data):
        """Create embedded AP support interface (simplified from APSupportWindowModern)."""
        # For now, create a sub-notebook with the AP tabs
        sub_notebook = ttk.Notebook(parent)
        sub_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Track current sub-tab
        ap_id = ap_data['ap_id']
        
        def on_subtab_change(event):
            current_tab = sub_notebook.index(sub_notebook.select())
            tab_text = sub_notebook.tab(current_tab, "text")
            if self.on_tab_change:
                self.on_tab_change(ap_id, tab_text)
        
        sub_notebook.bind("<<NotebookTabChanged>>", on_subtab_change)
        
        # Overview Tab
        overview_tab = self._create_overview_tab(sub_notebook, ap_data)
        sub_notebook.add(overview_tab, text="ℹ️ Overview")
        
        # Notes Tab
        notes_tab = self._create_notes_tab(sub_notebook, ap_data)
        sub_notebook.add(notes_tab, text="📝 Notes")
        
        # Browser Tab
        browser_tab = self._create_browser_tab(sub_notebook, ap_data)
        sub_notebook.add(browser_tab, text="🌐 Browser")
        
        # SSH Tab
        ssh_tab = self._create_ssh_tab(sub_notebook, ap_data)
        sub_notebook.add(ssh_tab, text="🖥️ SSH Terminal")
        
        # Actions Tab
        actions_tab = self._create_actions_tab(sub_notebook, ap_data)
        sub_notebook.add(actions_tab, text="⚡ Actions")
        
        # Store reference
        self.ap_tabs.setdefault(ap_id, {})['sub_notebook'] = sub_notebook
    
    def _create_overview_tab(self, parent, ap_data):
        """Create overview tab content."""
        frame = ttk.Frame(parent)
        
        content = tk.Frame(frame, bg="#FFFFFF", padx=20, pady=15)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text=f"AP {ap_data['ap_id']}", font=('Segoe UI', 14, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(0, 10))
        
        # Info display
        info_fields = [
            ('Store ID', ap_data.get('store_id', 'N/A')),
            ('IP Address', ap_data.get('ip_address', 'N/A')),
            ('Type', ap_data.get('type', 'N/A')),
            ('Software Version', ap_data.get('software_version', 'N/A')),
            ('Status', ap_data.get('current_status', 'N/A')),
        ]
        
        for label, value in info_fields:
            row = tk.Frame(content, bg="#FFFFFF")
            row.pack(fill=tk.X, pady=3)
            
            tk.Label(row, text=f"{label}:", font=('Segoe UI', 10, 'bold'),
                    bg="#FFFFFF", fg="#495057", width=20, anchor="w").pack(side=tk.LEFT)
            
            tk.Label(row, text=str(value), font=('Segoe UI', 10),
                    bg="#FFFFFF", fg="#212529", anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        return frame
    
    def _create_notes_tab(self, parent, ap_data):
        """Create notes tab content."""
        frame = ttk.Frame(parent)
        
        content = tk.Frame(frame, bg="#FFFFFF", padx=20, pady=15)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text="Support Notes", font=('Segoe UI', 12, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(0, 10))
        
        tk.Label(content, text="Notes functionality will be shown in lower right panel",
                font=('Segoe UI', 10), bg="#FFFFFF", fg="#6C757D").pack(pady=20)
        
        return frame
    
    def _create_browser_tab(self, parent, ap_data):
        """Create browser tab content."""
        frame = ttk.Frame(parent)
        
        content = tk.Frame(frame, bg="#FFFFFF", padx=20, pady=15)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text="Browser Control", font=('Segoe UI', 12, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(0, 10))
        
        tk.Button(content, text="Connect Browser", command=lambda: self._browser_action(ap_data, 'connect'),
                 bg="#17A2B8", fg="white", font=('Segoe UI', 10, 'bold'),
                 padx=20, pady=10, relief=tk.FLAT, cursor="hand2",
                 activebackground="#138496").pack(anchor="w", pady=5)
        
        tk.Label(content, text="Browser interface will be shown in lower right panel",
                font=('Segoe UI', 10), bg="#FFFFFF", fg="#6C757D").pack(pady=20)
        
        return frame
    
    def _create_ssh_tab(self, parent, ap_data):
        """Create SSH tab content."""
        frame = ttk.Frame(parent)
        
        content = tk.Frame(frame, bg="#FFFFFF", padx=20, pady=15)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text="SSH Terminal", font=('Segoe UI', 12, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(0, 10))
        
        tk.Button(content, text="Open SSH Terminal", command=lambda: self._ssh_action(ap_data, 'open'),
                 bg="#6F42C1", fg="white", font=('Segoe UI', 10, 'bold'),
                 padx=20, pady=10, relief=tk.FLAT, cursor="hand2",
                 activebackground="#5A32A3").pack(anchor="w", pady=5)
        
        tk.Label(content, text="SSH terminal will be shown in lower right panel",
                font=('Segoe UI', 10), bg="#FFFFFF", fg="#6C757D").pack(pady=20)
        
        return frame
    
    def _create_actions_tab(self, parent, ap_data):
        """Create actions tab content."""
        frame = ttk.Frame(parent)
        
        content = tk.Frame(frame, bg="#FFFFFF", padx=20, pady=15)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text="Quick Actions", font=('Segoe UI', 12, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(0, 10))
        
        actions = [
            ("Run Diagnostics", lambda: self._log("Running diagnostics...")),
            ("Check Logs", lambda: self._log("Checking logs...")),
            ("Reboot AP", lambda: self._log("Rebooting AP...")),
        ]
        
        for action_text, action_cmd in actions:
            tk.Button(content, text=action_text, command=action_cmd,
                     bg="#FFFFFF", fg="#212529", font=('Segoe UI', 9),
                     padx=15, pady=8, relief=tk.FLAT, cursor="hand2",
                     activebackground="#E9ECEF", bd=1, width=25).pack(anchor="w", pady=3)
        
        return frame
    
    def _browser_action(self, ap_data, action):
        """Handle browser actions."""
        self._log(f"Browser action: {action} for AP {ap_data['ap_id']}")
        # Notify parent to show browser in content panel
        if self.on_tab_change:
            self.on_tab_change(ap_data['ap_id'], "Browser")
    
    def _ssh_action(self, ap_data, action):
        """Handle SSH actions."""
        self._log(f"SSH action: {action} for AP {ap_data['ap_id']}")
        # Notify parent to show SSH in content panel
        if self.on_tab_change:
            self.on_tab_change(ap_data['ap_id'], "SSH Terminal")
    
    def _on_notebook_tab_changed(self, event):
        """Handle notebook tab change."""
        current_tab = self.notebook.index(self.notebook.select())
        tab_text = self.notebook.tab(current_tab, "text")
        
        # Skip Search tab
        if "Search" in tab_text:
            return
        
        # Extract AP ID from tab text (format: "AP 12345")
        if tab_text.startswith("AP "):
            ap_id = tab_text.replace("AP ", "").strip()
            if ap_id in self.ap_tabs:
                ap_data = self.ap_tabs[ap_id]['ap_data']
                self._log(f"Switched to AP {ap_id}")
                if self.on_ap_change:
                    self.on_ap_change(ap_id, ap_data)
    
    def _log(self, message):
        """Log activity."""
        if self.log_callback:
            self.log_callback("AP Panel", message, "info")
