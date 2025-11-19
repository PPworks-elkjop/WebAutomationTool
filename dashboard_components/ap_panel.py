"""
AP Panel - Upper Left
Shows multiple AP tabs, each with Overview/Browser/SSH sub-tabs
"""

import tkinter as tk
from tkinter import ttk, messagebox
from ap_support_ui_v3 import APSupportWindowModern
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from custom_notebook import CustomNotebook


class APPanel:
    """Upper left panel - Multi-tab AP support interface."""
    
    # Track open APs to prevent duplicates
    _open_aps = {}
    
    def __init__(self, parent, current_user, db, on_ap_change=None, on_tab_change=None, log_callback=None, content_panel=None):
        self.parent = parent
        self.current_user = current_user
        self.db = db
        self.on_ap_change = on_ap_change
        self.on_tab_change = on_tab_change
        self.log_callback = log_callback
        self.content_panel = content_panel  # Reference to content panel for browser actions
        
        # AP data storage
        self.ap_tabs = {}  # {tab_id: {ap_data, frame, widgets}}
        
        self._create_ui()
    
    def _create_ui(self):
        """Create AP panel UI."""
        # Header
        header = tk.Frame(self.parent, bg="#2B5A8A", height=40)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        tk.Label(header, text="AP Support", font=('Segoe UI', 12, 'bold'),
                bg="#2B5A8A", fg="white").pack(side=tk.LEFT, padx=15, pady=8)
        
        # Custom Notebook for AP tabs with full control over appearance
        self.notebook = CustomNotebook(self.parent, tab_font=('Segoe UI', 11), tab_height=36)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.parent.bind("<<NotebookTabChanged>>", self._on_notebook_tab_changed)
        
        # Add Search AP as first tab
        self._create_search_tab()
        
        # Show welcome message if no APs open
        # (Search tab is always present, so no need for welcome tab)
    
    def _create_search_tab(self):
        """Create Search AP tab."""
        search_frame = tk.Frame(self.notebook.content_area, bg="#FFFFFF")
        self.notebook.add(search_frame, text="Search AP")
        
        content = tk.Frame(search_frame, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text="Search for Access Points", font=('Segoe UI', 14, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(0, 20))
        
        # Search input
        search_input_frame = tk.Frame(content, bg="#FFFFFF")
        search_input_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.search_entry = tk.Entry(search_input_frame, font=('Segoe UI', 11), 
                                     bd=1, relief=tk.SOLID, highlightthickness=0)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=8)
        self.search_entry.bind('<Return>', lambda e: self._perform_search())
        
        tk.Button(search_input_frame, text="Search", command=self._perform_search,
                 bg="#2B5A8A", fg="white", font=('Segoe UI', 10, 'bold'),
                 padx=20, pady=8, relief=tk.FLAT, cursor="hand2",
                 activebackground="#1F4366").pack(side=tk.LEFT)
        
        # Info note about Jira counts
        tk.Label(content, text="Note: 'Include Jira' fetches live ticket counts (slower but current). Uncheck for faster searches.",
                font=('Segoe UI', 8, 'italic'), bg="#FFFFFF", fg="#6C757D").pack(anchor="w", pady=(0, 10))
        
        # Custom styled checkboxes
        checkbox_frame = tk.Frame(content, bg="#FFFFFF")
        checkbox_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(checkbox_frame, text="Search in:", font=('Segoe UI', 10),
                bg="#FFFFFF", fg="#495057").pack(side=tk.LEFT, padx=(0, 15))
        
        # AP ID checkbox (default checked)
        self.search_ap_id = tk.BooleanVar(value=True)
        self._create_custom_checkbox(checkbox_frame, "AP ID", self.search_ap_id)
        
        # Store ID checkbox
        self.search_store_id = tk.BooleanVar(value=False)
        self._create_custom_checkbox(checkbox_frame, "Store ID", self.search_store_id)
        
        # IP Address checkbox
        self.search_ip_address = tk.BooleanVar(value=False)
        self._create_custom_checkbox(checkbox_frame, "IP Address", self.search_ip_address)
        
        # Separator
        tk.Label(checkbox_frame, text=" | ", font=('Segoe UI', 10),
                bg="#FFFFFF", fg="#CED4DA").pack(side=tk.LEFT, padx=5)
        
        # Include Jira checkbox (default checked)
        self.search_include_jira = tk.BooleanVar(value=True)
        self._create_custom_checkbox(checkbox_frame, "Include Jira", self.search_include_jira)
        
        # Results listbox
        tk.Label(content, text="Search Results (double-click to open):", font=('Segoe UI', 10, 'bold'),
                bg="#FFFFFF", fg="#495057").pack(anchor="w", pady=(0, 5))
        
        list_frame = tk.Frame(content, bg="#FFFFFF")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 0))
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.search_results = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                        font=('Segoe UI', 10), bd=1, relief=tk.SOLID,
                                        selectmode=tk.SINGLE)
        self.search_results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.search_results.yview)
        
        self.search_results.bind('<Double-Button-1>', lambda e: self._open_selected_ap())
        
        # Store AP data for results
        self.search_ap_data = []
    
    def _create_custom_checkbox(self, parent, text, variable):
        """Create a custom styled checkbox with larger size."""
        frame = tk.Frame(parent, bg="#FFFFFF", cursor="hand2")
        frame.pack(side=tk.LEFT, padx=10)
        
        # Checkbox box (larger custom square)
        checkbox_canvas = tk.Canvas(frame, width=20, height=20, bg="#FFFFFF", 
                                    highlightthickness=0, bd=0,
                                    cursor="hand2")
        checkbox_canvas.pack(side=tk.LEFT, padx=(0, 8))
        
        # Label
        label = tk.Label(frame, text=text, font=('Segoe UI', 10), 
                        bg="#FFFFFF", fg="#212529", cursor="hand2")
        label.pack(side=tk.LEFT)
        
        def draw_checkbox():
            """Draw the checkbox state."""
            checkbox_canvas.delete("all")
            if variable.get():
                # Draw filled checkbox with checkmark
                checkbox_canvas.create_rectangle(1, 1, 19, 19, fill="#2B5A8A", outline="#000000", width=1)
                # Draw checkmark
                checkbox_canvas.create_line(6, 10, 9, 14, fill="white", width=2)
                checkbox_canvas.create_line(9, 14, 15, 6, fill="white", width=2)
            else:
                # Draw empty checkbox with black border
                checkbox_canvas.create_rectangle(1, 1, 19, 19, fill="#FFFFFF", outline="#000000", width=1)
        
        def toggle():
            """Toggle checkbox state."""
            variable.set(not variable.get())
            draw_checkbox()
        
        # Bind click events
        checkbox_canvas.bind("<Button-1>", lambda e: toggle())
        label.bind("<Button-1>", lambda e: toggle())
        frame.bind("<Button-1>", lambda e: toggle())
        
        # Initial draw
        draw_checkbox()
    
    def _perform_search(self):
        """Perform AP search."""
        search_term = self.search_entry.get().strip()
        
        if not search_term:
            messagebox.showwarning("Search", "Please enter a search term", parent=self.parent)
            return
        
        # Check if at least one field is selected
        if not (self.search_ap_id.get() or self.search_store_id.get() or self.search_ip_address.get()):
            messagebox.showwarning("Search", "Please select at least one search field", parent=self.parent)
            return
        
        self.search_results.delete(0, tk.END)
        self.search_ap_data = []
        
        try:
            # Build search fields list
            search_fields = []
            if self.search_ap_id.get():
                search_fields.append('ap_id')
            if self.search_store_id.get():
                search_fields.append('store_id')
            if self.search_ip_address.get():
                search_fields.append('ip_address')
            
            # Search database with specific fields
            results = self.db.search_access_points(search_term, fields=search_fields)
            
            if results:
                # Check if user wants Jira data
                include_jira = self.search_include_jira.get()
                
                if include_jira:
                    self._log(f"Found {len(results)} APs, fetching Jira data...")
                    
                    # Import Jira integration to fetch fresh data
                    from jira_integration import JiraIntegration
                    from jira_db_manager import JiraDBManager
                    from credentials_manager import CredentialsManager
                    
                    jira_integration = JiraIntegration(self.db)
                    jira_db = JiraDBManager(self.db)
                    credentials = CredentialsManager(self.db).get_credentials('jira')
                    jira_base_url = credentials.get('url', '').rstrip('/') if credentials else ''
                else:
                    self._log(f"Found {len(results)} APs (Jira lookup skipped)")
                
                # Display results for each AP
                for ap in results:
                    ap_id = ap['ap_id']
                    jira_indicator = ""
                    
                    # Fetch fresh Jira data if requested
                    if include_jira:
                        try:
                            if jira_integration.is_configured():
                                # Search Jira for this AP ID
                                search_term_jira = f"{ap_id}*" if ap_id.isdigit() else ap_id
                                jql = f'(text ~ "{search_term_jira}" OR summary ~ "{search_term_jira}" OR description ~ "{search_term_jira}" OR comment ~ "{search_term_jira}")'
                                
                                success, result, message = jira_integration.search_issues(jql, max_results=50)
                                
                                if success and result:
                                    issues = result.get('issues', [])
                                    # Store/update in database
                                    for issue in issues:
                                        jira_db.store_issue(ap_id, issue, jira_base_url)
                            
                            # Now get open ticket count from database
                            all_issues = jira_db.get_issues_for_ap(ap_id)
                            open_issues = []
                            for issue in all_issues:
                                status = issue.get('status', '').strip()
                                if status.lower() not in ['resolved', 'closed', 'done']:
                                    open_issues.append(issue)
                            
                            jira_count = len(open_issues)
                            jira_indicator = f" [Jira: {jira_count}]" if jira_count > 0 else ""
                            
                        except Exception as e:
                            jira_indicator = ""
                            self._log(f"Error getting Jira for AP {ap_id}: {str(e)}", "error")
                    
                    display_text = f"{ap['ap_id']} - Store: {ap.get('store_id', 'N/A')} - {ap.get('ip_address', 'N/A')}{jira_indicator}"
                    self.search_results.insert(tk.END, display_text)
                    self.search_ap_data.append(ap)
                
                if include_jira:
                    self._log(f"Search complete with Jira data for {len(results)} APs")
                else:
                    self._log(f"Search complete for {len(results)} APs")
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
                if tab_text and (tab_text.startswith(ap_id) or tab_text.endswith(ap_id)):
                    self.notebook.select(i)
                    break
            self._log(f"AP {ap_id} already open, switched to tab")
            return
        
        # Create embedded AP support frame
        ap_frame = tk.Frame(self.notebook.content_area, bg="#FFFFFF")
        tab_name = f"AP {ap_id}"
        
        # Add tab with close button
        self.notebook.add(ap_frame, text=tab_name, closeable=True, 
                         close_callback=lambda idx: self._close_tab_by_index(idx))
        
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
        
        # Show AP overview in content panel by default (since Overview tab is selected)
        if self.content_panel:
            self.content_panel.show_ap_overview(ap_data)
    
    def _create_embedded_ap_support(self, parent, ap_data):
        """Create embedded AP support interface (simplified from APSupportWindowModern)."""
        # Use CustomNotebook for sub-tabs with full control
        sub_notebook = CustomNotebook(parent, tab_font=('Segoe UI', 11), tab_height=36)
        sub_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Track current sub-tab
        ap_id = ap_data['ap_id']
        
        def on_subtab_change(event):
            current_tab = sub_notebook.current_tab
            if current_tab is not None:
                tab_text = sub_notebook.tab(current_tab, "text")
                if self.on_tab_change and tab_text:
                    self.on_tab_change(ap_id, tab_text)
        
        parent.bind("<<NotebookTabChanged>>", on_subtab_change)
        
        # Overview Tab
        overview_frame = tk.Frame(sub_notebook.content_area, bg="#FFFFFF")
        self._populate_overview_tab(overview_frame, ap_data)
        sub_notebook.add(overview_frame, text="Overview")
        
        # Browser Tab
        browser_frame = tk.Frame(sub_notebook.content_area, bg="#FFFFFF")
        self._populate_browser_tab(browser_frame, ap_data)
        sub_notebook.add(browser_frame, text="Browser")
        
        # SSH Tab
        ssh_frame = tk.Frame(sub_notebook.content_area, bg="#FFFFFF")
        self._populate_ssh_tab(ssh_frame, ap_data)
        sub_notebook.add(ssh_frame, text="SSH Terminal")
        
        # Store reference
        self.ap_tabs.setdefault(ap_id, {})['sub_notebook'] = sub_notebook
    
    def _populate_overview_tab(self, frame, ap_data):
        """Populate overview tab content."""
        # Create sticky ping section at bottom FIRST (so it gets priority)
        ping_frame = tk.Frame(frame, bg="#F8F9FA", relief=tk.FLAT, bd=0)
        ping_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)
        
        # Create canvas for scrolling AFTER ping frame
        canvas = tk.Canvas(frame, bg="#FFFFFF", highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#FFFFFF")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Content within scrollable frame
        content = tk.Frame(scrollable_frame, bg="#FFFFFF", padx=20, pady=15)
        content.pack(fill=tk.BOTH, expand=True)
        
        # AP ID row
        header_row = tk.Frame(content, bg="#FFFFFF")
        header_row.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(header_row, text="AP ID:", font=('Segoe UI', 11, 'bold'),
                bg="#FFFFFF", fg="#495057").pack(side=tk.LEFT)
        
        ap_id_entry = tk.Entry(header_row, font=('Segoe UI', 11),
                              bd=0, relief=tk.FLAT, highlightthickness=0)
        ap_id_entry.insert(0, ap_data.get('ap_id', 'N/A'))
        ap_id_entry.config(state='readonly', readonlybackground="#FFFFFF", fg="#212529")
        ap_id_entry.pack(side=tk.LEFT, padx=(10, 20))
        
        # Extract store number from store_id (e.g., "elgiganten_se.2001" -> "2001")
        store_id_full = ap_data.get('store_id', 'N/A')
        store_number = store_id_full.split('.')[-1] if '.' in store_id_full else store_id_full
        
        # Info fields with copyable entries
        info_fields = [
            ('Store ID', store_number),
            ('Retail Domain', store_id_full),
            ('IP Address', ap_data.get('ip_address', 'N/A')),
            ('MAC Address', ap_data.get('mac_address', 'N/A')),
            ('Software Version', ap_data.get('software_version', 'N/A')),
            ('Build', ap_data.get('build', 'N/A')),
        ]
        
        for label, value in info_fields:
            self._create_copyable_field(content, label, value)
        
        # Setup ping button in the ping_frame we created at the top
        # Ping button and result container - pack to the left side
        ping_container = tk.Frame(ping_frame, bg="#F8F9FA")
        ping_container.pack(side=tk.LEFT, anchor="w", padx=5, pady=10)
        
        # Store ping state
        ping_state = {'running': False, 'job': None}
        
        # Store ping state in ap_tabs for close tab checking
        ap_id = ap_data['ap_id']
        if ap_id in self.ap_tabs:
            self.ap_tabs[ap_id]['ping_state'] = ping_state
        
        # Ping button with play icon
        ping_btn = tk.Button(ping_container, text="▶ Ping AP", 
                            command=lambda: self._toggle_continuous_ping(ap_data, ping_result_label, ping_btn, ping_state),
                            bg="#2B5A8A", fg="white", font=('Segoe UI', 9),
                            padx=15, pady=6, relief=tk.FLAT, cursor="hand2",
                            activebackground="#1F4366")
        ping_btn.pack(side=tk.LEFT, padx=(5, 15))
        
        # Ping result label
        ping_result_label = tk.Label(ping_container, text="", font=('Segoe UI', 10),
                                     bg="#F8F9FA", fg="#6C757D", anchor="w")
        ping_result_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _create_copyable_field(self, parent, label_text, value):
        """Create a field with copyable text entry."""
        row = tk.Frame(parent, bg="#FFFFFF")
        row.pack(fill=tk.X, pady=5)
        
        tk.Label(row, text=f"{label_text}:", font=('Segoe UI', 10, 'bold'),
                bg="#FFFFFF", fg="#495057", width=18, anchor="w").pack(side=tk.LEFT)
        
        entry = tk.Entry(row, font=('Segoe UI', 10),
                        bd=0, relief=tk.FLAT, highlightthickness=0)
        entry.insert(0, str(value))
        entry.config(state='readonly', readonlybackground="#FFFFFF", fg="#212529")
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
    
    def _populate_all_fields_tab(self, frame, ap_data):
        """Populate all fields tab with all available data in 2 columns."""
        from tkinter import scrolledtext
        
        # Scrollable container with both vertical and horizontal scrollbars
        canvas = tk.Canvas(frame, bg="#FFFFFF", highlightthickness=0)
        v_scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        h_scrollbar = tk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
        scrollable_frame = tk.Frame(canvas, bg="#FFFFFF")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and canvas
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # Create 2-column layout
        left_column = tk.Frame(scrollable_frame, bg="#FFFFFF")
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_column = tk.Frame(scrollable_frame, bg="#FFFFFF")
        right_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # All fields from database
        all_fields = [
            'ap_id', 'store_id', 'store_alias', 'retail_chain', 'ip_address',
            'type', 'mac_address', 'serial_number', 'software_version', 
            'firmware_version', 'hardware_revision', 'build', 'configuration_mode',
            'service_status', 'uptime', 'communication_daemon_status',
            'connectivity_internet', 'connectivity_provisioning', 
            'connectivity_ntp_server', 'connectivity_apc_address',
            'status', 'last_seen', 'last_ping_time', 'username_webui',
            'username_ssh', 'notes', 'created_at', 'updated_at'
        ]
        
        # Split fields between columns
        mid_point = (len(all_fields) + 1) // 2
        left_fields = all_fields[:mid_point]
        right_fields = all_fields[mid_point:]
        
        # Populate left column
        for field in left_fields:
            value = ap_data.get(field, 'N/A')
            # Format field name
            field_label = field.replace('_', ' ').title()
            self._create_copyable_field(left_column, field_label, value)
        
        # Populate right column
        for field in right_fields:
            value = ap_data.get(field, 'N/A')
            field_label = field.replace('_', ' ').title()
            self._create_copyable_field(right_column, field_label, value)
    
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
    
    def _populate_browser_tab(self, frame, ap_data):
        """Populate browser tab content."""
        # Main content with padding
        content = tk.Frame(frame, bg="#FFFFFF")
        content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Control panel (styled like Jira filters)
        control_frame = tk.Frame(content, bg="#F8F9FA", padx=10, pady=10)
        control_frame.pack(fill=tk.X)
        
        # Top row with title and status
        top_row = tk.Frame(control_frame, bg="#F8F9FA")
        top_row.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(top_row, text="Browser Control", font=('Segoe UI', 11, 'bold'),
                bg="#F8F9FA", fg="#212529").pack(side=tk.LEFT)
        
        # Status indicator on the right
        browser_status_label = tk.Label(top_row, text="● Not Running", 
                                        font=('Segoe UI', 10),
                                        bg="#F8F9FA", fg="#6C757D")
        browser_status_label.pack(side=tk.RIGHT)
        
        # Store reference for updates
        ap_data['browser_status_label'] = browser_status_label
        
        # Buttons row
        btn_row = tk.Frame(control_frame, bg="#F8F9FA")
        btn_row.pack(fill=tk.X, pady=(0, 5))
        
        start_btn = tk.Button(btn_row, text="Start Browser", 
                             command=lambda: self._browser_action(ap_data, 'start'),
                             bg="#28A745", fg="white", font=('Segoe UI', 9, 'bold'),
                             padx=15, pady=6, relief=tk.FLAT, cursor="hand2",
                             borderwidth=0, activebackground="#218838")
        start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        stop_btn = tk.Button(btn_row, text="Stop Browser",
                            command=lambda: self._browser_action(ap_data, 'stop'),
                            bg="#DC3545", fg="white", font=('Segoe UI', 9, 'bold'),
                            padx=15, pady=6, relief=tk.FLAT, cursor="hand2",
                            borderwidth=0, state=tk.DISABLED, activebackground="#C82333")
        stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        open_ap_btn = tk.Button(btn_row, text="Open This AP",
                               command=lambda: self._browser_action(ap_data, 'open_ap'),
                               bg="#007BFF", fg="white", font=('Segoe UI', 9, 'bold'),
                               padx=15, pady=6, relief=tk.FLAT, cursor="hand2",
                               borderwidth=0, state=tk.DISABLED, activebackground="#0069D9")
        open_ap_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        maximize_btn = tk.Button(btn_row, text="⬜ Maximize",
                                command=lambda: self._browser_action(ap_data, 'maximize'),
                                bg="#6C757D", fg="white", font=('Segoe UI', 9, 'bold'),
                                padx=15, pady=6, relief=tk.FLAT, cursor="hand2",
                                borderwidth=0, state=tk.DISABLED, activebackground="#5A6268")
        maximize_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        minimize_btn = tk.Button(btn_row, text="▬ Minimize",
                                command=lambda: self._browser_action(ap_data, 'minimize'),
                                bg="#6C757D", fg="white", font=('Segoe UI', 9, 'bold'),
                                padx=15, pady=6, relief=tk.FLAT, cursor="hand2",
                                borderwidth=0, state=tk.DISABLED, activebackground="#5A6268")
        minimize_btn.pack(side=tk.LEFT)
        
        # Store button references
        ap_data['browser_start_btn'] = start_btn
        ap_data['browser_stop_btn'] = stop_btn
        ap_data['browser_open_ap_btn'] = open_ap_btn
        ap_data['browser_maximize_btn'] = maximize_btn
        ap_data['browser_minimize_btn'] = minimize_btn
        
        # Info box
        info_frame = tk.Frame(content, bg="#E7F3FF", relief=tk.SOLID, borderwidth=1)
        info_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(info_frame, text="ℹ About Browser Manager", font=('Segoe UI', 10, 'bold'),
                bg="#E7F3FF", fg="#004085").pack(anchor="w", padx=10, pady=(10, 5))
        
        info_text = ("• Opens Chrome window for AP web interface\n"
                    "• Handles CATO Network warnings automatically\n"
                    "• Uses HTTP Basic Auth from AP credentials\n"
                    "• Browser view appears in bottom-right panel")
        
        tk.Label(info_frame, text=info_text, font=('Segoe UI', 9),
                bg="#E7F3FF", fg="#004085", justify=tk.LEFT, anchor="w").pack(anchor="w", padx=10, pady=(0, 10))
    
    def _populate_ssh_tab(self, frame, ap_data):
        """Populate SSH tab content."""
        content = tk.Frame(frame, bg="#FFFFFF", padx=20, pady=15)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text="Commands will open SSH terminal automatically in a separate window",
                font=('Segoe UI', 9), bg="#FFFFFF", fg="#6C757D").pack(anchor="w", pady=(0, 15))
        
        # Servicemode Enabled group
        tk.Label(content, text="Servicemode Enabled", font=('Segoe UI', 10, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(5, 8))
        
        servicemode_frame = tk.Frame(content, bg="#FFFFFF")
        servicemode_frame.pack(fill="x", pady=5)
        
        servicemode_commands = [
            ("Check Status", lambda: self._ssh_send_command(ap_data, "status"), "#17A2B8"),
            ("Get Java Version", lambda: self._ssh_get_java_version(ap_data), "#007BFF"),
            ("Exit Servicemode", lambda: self._ssh_send_command(ap_data, "exit_service"), "#DC3545"),
        ]
        
        for i, (text, command, color) in enumerate(servicemode_commands):
            btn = tk.Button(servicemode_frame, text=text, command=command,
                          bg=color, fg="white", font=('Segoe UI', 9, 'bold'),
                          padx=12, pady=6, relief=tk.FLAT, cursor="hand2",
                          activebackground=color, width=15)
            btn.grid(row=0, column=i, padx=3, pady=3, sticky="ew")
        
        servicemode_frame.grid_columnconfigure(0, weight=1)
        servicemode_frame.grid_columnconfigure(1, weight=1)
        servicemode_frame.grid_columnconfigure(2, weight=1)
        
        # Separator
        tk.Frame(content, bg="#DEE2E6", height=1).pack(fill="x", pady=15)
        
        # Operations group
        tk.Label(content, text="Operations", font=('Segoe UI', 10, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(5, 8))
        
        operations_frame = tk.Frame(content, bg="#FFFFFF")
        operations_frame.pack(fill="x", pady=5)
        
        operations_commands = [
            ("Start Servicemode", lambda: self._ssh_send_command(ap_data, "servicemode"), "#FFC107"),
            ("Disk Space", lambda: self._ssh_send_command(ap_data, "df -h"), "#17A2B8"),
            ("List Logs", lambda: self._ssh_send_command(ap_data, "cd /opt/esl/accesspoint && ls -la *20*log* 2>/dev/null || echo 'No log files found'"), "#28A745"),
            ("Download Logs", lambda: self._ssh_download_logs(ap_data), "#FD7E14"),
            ("Delete Logs", lambda: self._ssh_remove_old_logs(ap_data), "#DC3545"),
            ("System Info", lambda: self._ssh_send_command(ap_data, "uname -a && uptime"), "#20C997"),
            ("Check DNS", lambda: self._ssh_send_command(ap_data, "cat /etc/resolv.conf"), "#6F42C1"),
        ]
        
        for i, (text, command, color) in enumerate(operations_commands):
            row = i // 2
            col = i % 2
            
            btn = tk.Button(operations_frame, text=text, command=command,
                          bg=color, fg="white", font=('Segoe UI', 9, 'bold'),
                          padx=12, pady=6, relief=tk.FLAT, cursor="hand2",
                          activebackground=color, width=15)
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
        
        operations_frame.grid_columnconfigure(0, weight=1)
        operations_frame.grid_columnconfigure(1, weight=1)
    
    def _browser_action(self, ap_data, action):
        """Handle browser actions."""
        self._log(f"Browser action: {action} for AP {ap_data['ap_id']}")
        
        if not self.content_panel:
            self._log("Error: Content panel not available")
            messagebox.showerror("Error", "Content panel not available", parent=self.parent)
            return
        
        if action == 'start':
            if self.content_panel.start_browser():
                # Update button states
                ap_data.get('browser_status_label', tk.Label()).config(
                    text="● Running", fg="#28A745")
                ap_data.get('browser_start_btn', tk.Button()).config(state=tk.DISABLED)
                ap_data.get('browser_stop_btn', tk.Button()).config(state=tk.NORMAL)
                ap_data.get('browser_open_ap_btn', tk.Button()).config(state=tk.NORMAL)
                ap_data.get('browser_maximize_btn', tk.Button()).config(state=tk.NORMAL)
                ap_data.get('browser_minimize_btn', tk.Button()).config(state=tk.NORMAL)
                
                # Notify content panel to update with browser operations
                self.content_panel.show_ap_overview(ap_data)
                
        elif action == 'stop':
            if messagebox.askyesno("Stop Browser", 
                                  "Are you sure you want to stop the browser?\n"
                                  "All AP connections will be closed.",
                                  parent=self.parent):
                self.content_panel.stop_browser()
                # Update button states
                ap_data.get('browser_status_label', tk.Label()).config(
                    text="● Not Running", fg="#6C757D")
                ap_data.get('browser_start_btn', tk.Button()).config(state=tk.NORMAL)
                ap_data.get('browser_stop_btn', tk.Button()).config(state=tk.DISABLED)
                ap_data.get('browser_open_ap_btn', tk.Button()).config(state=tk.DISABLED)
                ap_data.get('browser_maximize_btn', tk.Button()).config(state=tk.DISABLED)
                ap_data.get('browser_minimize_btn', tk.Button()).config(state=tk.DISABLED)
                
                # Notify content panel to update
                self.content_panel.show_ap_overview(ap_data)
                
        elif action == 'open_ap':
            self.content_panel.open_ap_in_browser(ap_data)
            
        elif action == 'nav_status':
            self._browser_navigate(ap_data, 'status')
            
        elif action == 'refresh':
            self._browser_refresh(ap_data)
            
        elif action == 'screenshot':
            self._browser_screenshot(ap_data)
            
        elif action == 'view_source':
            self._browser_view_source(ap_data)
            
        elif action == 'provisioning':
            self._show_provisioning_dialog(ap_data)
            return  # Don't trigger tab change, provisioning view will handle its own display
            
        elif action == 'ssh':
            self._show_ssh_dialog(ap_data)
            return  # Don't trigger tab change, SSH view will handle its own display
            
        elif action == 'maximize':
            self._browser_maximize()
            
        elif action == 'minimize':
            self._browser_minimize()
                
        # Notify parent to show browser status in content panel
        if self.on_tab_change:
            self.on_tab_change(ap_data['ap_id'], "Browser")
    
    def _browser_navigate(self, ap_data, page):
        """Navigate browser to a specific page."""
        if not self.content_panel or not self.content_panel.browser_manager:
            messagebox.showerror("Error", "Browser not running", parent=self.parent)
            return
        
        try:
            import threading
            
            def navigate_and_collect():
                try:
                    driver = self.content_panel.browser_manager.driver
                    ip = ap_data.get('ip_address', '').strip()
                    if ip.startswith('http'):
                        ip = ip.split('://')[1]
                    if '@' in ip:
                        ip = ip.split('@')[1]
                    
                    if page == 'status':
                        url = f"https://{ip}/service/status.xml"
                        driver.get(url)
                        
                        def log_nav():
                            self._log(f"Navigated to status page: {url}")
                        self.parent.after(0, log_nav)
                    
                    elif page == 'provisioning':
                        url = f"https://{ip}/service/config/provisioningEnabled.xml"
                        driver.get(url)
                        def log_nav():
                            self._log(f"Navigated to provisioning page: {url}")
                        self.parent.after(0, log_nav)
                    
                    elif page == 'ssh':
                        url = f"https://{ip}/service/config/ssh.xml"
                        driver.get(url)
                        def log_nav():
                            self._log(f"Navigated to SSH page: {url}")
                        self.parent.after(0, log_nav)
                        
                except Exception as e:
                    error_msg = f"Navigation error: {str(e)}"
                    def show_error():
                        self._log(error_msg)
                        messagebox.showerror("Error", f"Navigation failed:\n{str(e)}", parent=self.parent)
                    self.parent.after(0, show_error)
            
            # Run in background thread
            thread = threading.Thread(target=navigate_and_collect, daemon=True)
            thread.start()
            
        except Exception as e:
            self._log(f"Navigation error: {str(e)}")
            messagebox.showerror("Error", f"Navigation failed:\n{str(e)}", parent=self.parent)
    
    def _show_provisioning_dialog(self, ap_data):
        """Show provisioning actions in content panel."""
        self._log(f"_show_provisioning_dialog called for AP {ap_data.get('ap_id')}")
        if not self.content_panel or not self.content_panel.browser_manager:
            self._log("Error: Browser not running or content panel not available")
            messagebox.showerror("Error", "Browser not running", parent=self.parent)
            return
        
        self._log("Calling content_panel.show_provisioning_actions")
        # Show provisioning actions in content panel
        self.content_panel.show_provisioning_actions(ap_data, self)
    
    def _show_ssh_dialog(self, ap_data):
        """Show SSH actions in content panel."""
        if not self.content_panel or not self.content_panel.browser_manager:
            messagebox.showerror("Error", "Browser not running", parent=self.parent)
            return
        
        # Show SSH actions in content panel
        self.content_panel.show_ssh_actions(ap_data, self)
    
    def _provisioning_action(self, ap_data, action):
        """Handle provisioning actions."""
        self._log(f"Provisioning {action} for AP {ap_data.get('ap_id')}")
        
        if not self.content_panel or not self.content_panel.browser_manager:
            messagebox.showerror("Error", "Browser not running", parent=self.parent)
            return
        
        import threading
        
        def perform_action():
            try:
                from selenium.webdriver.common.by import By
                import time
                
                driver = self.content_panel.browser_manager.driver
                ip = ap_data.get('ip_address', '').strip()
                if ip.startswith('http'):
                    ip = ip.split('://')[1]
                if '@' in ip:
                    ip = ip.split('@')[1]
                
                url = f"https://{ip}/service/config/provisioningEnabled.xml"
                
                def log(msg):
                    self.parent.after(0, lambda: self._log(msg))
                
                log(f"Navigating to {url}")
                driver.get(url)
                time.sleep(2)
                
                # Find the checkbox
                checkboxes = driver.find_elements(By.NAME, "provisioningEnabled")
                provisioning_checkbox = None
                for cb in checkboxes:
                    if cb.get_attribute("type") == "checkbox":
                        provisioning_checkbox = cb
                        break
                
                if not provisioning_checkbox:
                    log("✗ Could not find provisioning checkbox")
                    return
                
                is_enabled = provisioning_checkbox.is_selected()
                
                if action == 'check':
                    status = 'Enabled' if is_enabled else 'Disabled'
                    log(f"Provisioning status: {status}")
                    def show_msg():
                        messagebox.showinfo("Provisioning Status", 
                                          f"Provisioning is currently: {status}",
                                          parent=self.parent)
                    self.parent.after(0, show_msg)
                    return
                
                elif action == 'activate':
                    if is_enabled:
                        log("Provisioning is already enabled")
                        return
                    
                    log("Enabling provisioning...")
                    try:
                        provisioning_checkbox.click()
                    except:
                        driver.execute_script("arguments[0].click();", provisioning_checkbox)
                    time.sleep(1)
                    
                    # Click save
                    save_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Save']")
                    try:
                        save_button.click()
                    except:
                        driver.execute_script("arguments[0].click();", save_button)
                    time.sleep(2)
                    
                    log("✓ Provisioning enabled")
                    def show_success():
                        messagebox.showinfo("Success", "Provisioning has been enabled", parent=self.parent)
                    self.parent.after(0, show_success)
                
                elif action == 'deactivate':
                    if not is_enabled:
                        log("Provisioning is already disabled")
                        return
                    
                    log("Disabling provisioning...")
                    try:
                        provisioning_checkbox.click()
                    except:
                        driver.execute_script("arguments[0].click();", provisioning_checkbox)
                    time.sleep(1)
                    
                    # Click save
                    save_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Save']")
                    try:
                        save_button.click()
                    except:
                        driver.execute_script("arguments[0].click();", save_button)
                    time.sleep(2)
                    
                    log("✓ Provisioning disabled")
                    def show_success():
                        messagebox.showinfo("Success", "Provisioning has been disabled", parent=self.parent)
                    self.parent.after(0, show_success)
                    
            except Exception as e:
                error_msg = f"Provisioning error: {str(e)}"
                def show_error():
                    self._log(error_msg)
                    messagebox.showerror("Error", f"Operation failed:\n{str(e)}", parent=self.parent)
                self.parent.after(0, show_error)
        
        # Run in background thread
        thread = threading.Thread(target=perform_action, daemon=True)
        thread.start()
    
    def _ssh_action(self, ap_data, action):
        """Handle SSH actions with provisioning coordination."""
        self._log(f"SSH {action} for AP {ap_data.get('ap_id')}")
        
        if not self.content_panel or not self.content_panel.browser_manager:
            messagebox.showerror("Error", "Browser not running", parent=self.parent)
            return
        
        import threading
        
        def perform_action():
            try:
                from selenium.webdriver.common.by import By
                import time
                
                driver = self.content_panel.browser_manager.driver
                ip = ap_data.get('ip_address', '').strip()
                if ip.startswith('http'):
                    ip = ip.split('://')[1]
                if '@' in ip:
                    ip = ip.split('@')[1]
                
                url = f"https://{ip}/service/config/ssh.xml"
                
                def log(msg):
                    self.parent.after(0, lambda: self._log(msg))
                
                log(f"Navigating to {url}")
                driver.get(url)
                time.sleep(2)
                
                # Find the SSH checkbox
                ssh_checkboxes = driver.find_elements(By.NAME, "enabled")
                ssh_checkbox = None
                for cb in ssh_checkboxes:
                    if cb.get_attribute("type") == "checkbox":
                        ssh_checkbox = cb
                        break
                
                if not ssh_checkbox:
                    log("✗ Could not find SSH checkbox")
                    return
                
                is_enabled = ssh_checkbox.is_selected()
                is_disabled = ssh_checkbox.get_attribute("disabled")
                
                if action == 'check':
                    status = 'Enabled' if is_enabled else 'Disabled'
                    accessible = 'accessible' if not is_disabled else 'disabled (provisioning must be disabled first)'
                    log(f"SSH status: {status} (checkbox {accessible})")
                    def show_msg():
                        msg = f"SSH is currently: {status}\n\n"
                        if is_disabled:
                            msg += "Note: SSH checkbox is disabled.\nProvisioning must be disabled before SSH can be modified."
                        messagebox.showinfo("SSH Status", msg, parent=self.parent)
                    self.parent.after(0, show_msg)
                    return
                
                elif action == 'activate':
                    if is_enabled:
                        log("SSH is already enabled")
                        return
                    
                    # Track if provisioning was originally enabled
                    provisioning_was_enabled = False
                    
                    # Check if we need to disable provisioning first
                    if is_disabled:
                        log("SSH checkbox is disabled - checking provisioning status...")
                        
                        # Check provisioning status
                        prov_url = f"https://{ip}/service/config/provisioningEnabled.xml"
                        driver.get(prov_url)
                        time.sleep(2)
                        
                        prov_checkboxes = driver.find_elements(By.NAME, "provisioningEnabled")
                        prov_checkbox = None
                        for cb in prov_checkboxes:
                            if cb.get_attribute("type") == "checkbox":
                                prov_checkbox = cb
                                break
                        
                        if prov_checkbox and prov_checkbox.is_selected():
                            provisioning_was_enabled = True
                            log("Provisioning is enabled - will be restored after SSH activation")
                            log("Disabling provisioning...")
                            try:
                                prov_checkbox.click()
                            except:
                                driver.execute_script("arguments[0].click();", prov_checkbox)
                            time.sleep(1)
                            
                            save_btn = driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Save']")
                            try:
                                save_btn.click()
                            except:
                                driver.execute_script("arguments[0].click();", save_btn)
                            time.sleep(3)
                            log("✓ Provisioning disabled")
                        
                        # Return to SSH page
                        driver.get(url)
                        time.sleep(2)
                        
                        # Find SSH checkbox again
                        ssh_checkboxes = driver.find_elements(By.NAME, "enabled")
                        ssh_checkbox = None
                        for cb in ssh_checkboxes:
                            if cb.get_attribute("type") == "checkbox":
                                ssh_checkbox = cb
                                break
                    
                    log("Enabling SSH...")
                    try:
                        ssh_checkbox.click()
                    except:
                        driver.execute_script("arguments[0].click();", ssh_checkbox)
                    time.sleep(1)
                    
                    # Click save
                    save_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Save']")
                    try:
                        save_button.click()
                    except:
                        driver.execute_script("arguments[0].click();", save_button)
                    time.sleep(2)
                    
                    log("✓ SSH enabled")
                    
                    # Re-enable provisioning if it was originally enabled
                    if provisioning_was_enabled:
                        log("Re-enabling provisioning to restore original state...")
                        prov_url = f"https://{ip}/service/config/provisioningEnabled.xml"
                        driver.get(prov_url)
                        time.sleep(2)
                        
                        prov_checkboxes = driver.find_elements(By.NAME, "provisioningEnabled")
                        prov_checkbox = None
                        for cb in prov_checkboxes:
                            if cb.get_attribute("type") == "checkbox":
                                prov_checkbox = cb
                                break
                        
                        if prov_checkbox and not prov_checkbox.is_selected():
                            try:
                                prov_checkbox.click()
                            except:
                                driver.execute_script("arguments[0].click();", prov_checkbox)
                            time.sleep(1)
                            
                            save_btn = driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Save']")
                            try:
                                save_btn.click()
                            except:
                                driver.execute_script("arguments[0].click();", save_btn)
                            time.sleep(2)
                            log("✓ Provisioning re-enabled")
                    
                    def show_success():
                        msg = "SSH has been enabled"
                        if provisioning_was_enabled:
                            msg += "\n\nProvisioning has been restored to its original state (enabled)."
                        messagebox.showinfo("Success", msg, parent=self.parent)
                    self.parent.after(0, show_success)
                
                elif action == 'deactivate':
                    if not is_enabled:
                        log("SSH is already disabled")
                        return
                    
                    log("Disabling SSH...")
                    try:
                        ssh_checkbox.click()
                    except:
                        driver.execute_script("arguments[0].click();", ssh_checkbox)
                    time.sleep(1)
                    
                    # Click save
                    save_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Save']")
                    try:
                        save_button.click()
                    except:
                        driver.execute_script("arguments[0].click();", save_button)
                    time.sleep(2)
                    
                    log("✓ SSH disabled")
                    def show_success():
                        messagebox.showinfo("Success", "SSH has been disabled", parent=self.parent)
                    self.parent.after(0, show_success)
                    
            except Exception as e:
                error_msg = f"SSH error: {str(e)}"
                def show_error():
                    self._log(error_msg)
                    messagebox.showerror("Error", f"Operation failed:\n{str(e)}", parent=self.parent)
                self.parent.after(0, show_error)
        
        # Run in background thread
        thread = threading.Thread(target=perform_action, daemon=True)
        thread.start()
    
    def _ssh_open_terminal(self, ap_data):
        """Open SSH terminal session in content panel."""
        self._log(f"Opening SSH terminal for AP {ap_data.get('ap_id')}")
        if self.content_panel:
            self.content_panel.show_ssh_terminal(ap_data)
        else:
            messagebox.showerror("Error", "Content panel not available", parent=self.parent)
    
    def _ssh_send_command(self, ap_data, command):
        """Send command to SSH terminal (opens terminal if needed)."""
        from ssh_helper import SSHManager, SSHConnection
        import threading
        import time
        
        ap_id = ap_data.get('ap_id')
        
        def send_when_ready():
            # Ensure terminal is open first
            if self.content_panel:
                self.content_panel.show_ssh_terminal(ap_data)
            
            # Wait for connection to be established
            max_attempts = 20  # 10 seconds total
            for attempt in range(max_attempts):
                window = SSHManager._windows.get("default")
                if window and ap_id in window.tabs:
                    connection = window.tabs[ap_id].connection
                    if connection.connected:
                        # Connection is ready
                        if command == "exit_service":
                            # Special sequence for exiting service mode
                            self.parent.after(0, lambda: self._log(f"Exiting service mode for AP {ap_id}"))
                            
                            commands = [
                                ("extended matex2010", 2),
                                ("enableshell true", 2),
                                ("exit", 1),
                                ("exit", 2)  # This will close the connection
                            ]
                            for cmd, delay in commands:
                                connection.send_command(cmd)
                                time.sleep(delay)
                            
                            # Wait a moment for disconnection
                            time.sleep(1)
                            
                            # Reconnect
                            self.parent.after(0, lambda: self._log(f"Reconnecting to AP {ap_id}..."))
                            terminal_tab = window.tabs[ap_id]
                            terminal_tab.is_reconnecting = True  # Flag to prevent "Connection closed" message
                            
                            # Create new connection
                            new_connection = SSHConnection(
                                ap_id=ap_data.get('ap_id'),
                                host=ap_data.get('ip_address'),
                                username=ap_data.get('username_ssh', 'esl'),
                                password=ap_data.get('password_ssh', ''),
                                port=22
                            )
                            
                            success, message = new_connection.connect()
                            if success:
                                # Replace old connection with new one
                                terminal_tab.connection = new_connection
                                terminal_tab.is_reconnecting = False
                                self.parent.after(0, lambda: self._log(f"Reconnected to AP {ap_id}"))
                            else:
                                self.parent.after(0, lambda msg=message: self._log(f"Failed to reconnect to AP {ap_id}: {msg}"))
                                terminal_tab.is_reconnecting = False
                        else:
                            # Regular command
                            connection.send_command(command)
                        
                        self.parent.after(0, lambda: self._log(f"Sent command to SSH terminal for AP {ap_id}"))
                        return
                
                time.sleep(0.5)
            
            # Timeout
            def show_warning():
                messagebox.showwarning("Connection Timeout", 
                                     f"SSH terminal for AP {ap_id} did not connect in time.\nPlease try again.",
                                     parent=self.parent)
            self.parent.after(0, show_warning)
        
        threading.Thread(target=send_when_ready, daemon=True).start()
    
    def _ssh_get_java_version(self, ap_data):
        """Get Java version from status command and save to database."""
        from ssh_helper import SSHManager
        import threading
        import time
        import re
        
        ap_id = ap_data.get('ap_id')
        
        def get_version_when_ready():
            # Ensure terminal is open
            if self.content_panel:
                self.content_panel.show_ssh_terminal(ap_data)
            
            # Wait for connection
            max_attempts = 20
            for attempt in range(max_attempts):
                window = SSHManager._windows.get("default")
                if window and ap_id in window.tabs:
                    connection = window.tabs[ap_id].connection
                    if connection.connected:
                        # Send status command
                        connection.send_command("status")
                        time.sleep(3)
                        
                        # Get output from automation buffer
                        output = connection.get_automation_output(last_chars=2000)
                        
                        # Parse Java Version
                        java_match = re.search(r'Java Version[:\s]+([^\n\r]+)', output, re.IGNORECASE)
                        if java_match:
                            java_version = java_match.group(1).strip()
                            self.parent.after(0, lambda jv=java_version: self._log(f"Found Java Version: {jv}"))
                            
                            # Save to database
                            try:
                                self.db.update_access_point(ap_id, {'java_version': java_version})
                                
                                def show_success():
                                    messagebox.showinfo("Success", 
                                                      f"Java Version: {java_version}\n\nSaved to database!",
                                                      parent=self.parent)
                                self.parent.after(0, show_success)
                            except Exception as e:
                                self.parent.after(0, lambda err=str(e): self._log(f"Error saving Java Version: {err}"))
                        else:
                            self.parent.after(0, lambda: self._log("Could not find Java Version in output"))
                            
                            def show_warning():
                                messagebox.showwarning("Not Found", 
                                                     "Could not find Java Version in status output.\n\nMake sure you're in Service Mode.",
                                                     parent=self.parent)
                            self.parent.after(0, show_warning)
                        return
                
                time.sleep(0.5)
            
            # Timeout
            def show_warning():
                messagebox.showwarning("Connection Timeout", 
                                     f"SSH terminal for AP {ap_id} did not connect in time.",
                                     parent=self.parent)
            self.parent.after(0, show_warning)
        
        threading.Thread(target=get_version_when_ready, daemon=True).start()
    
    def _ssh_download_logs(self, ap_data):
        """Download log files from the AP via SCP."""
        from ssh_helper import SSHManager
        from tkinter import filedialog
        import threading
        
        ap_id = ap_data.get('ap_id')
        
        # Ask user for destination folder
        dest_folder = filedialog.askdirectory(
            title="Select destination folder for log files", 
            parent=self.parent
        )
        
        if not dest_folder:
            return
        
        self._log(f"Downloading logs to: {dest_folder}")
        
        def download_when_ready():
            import paramiko
            import os
            import time
            
            # Ensure terminal is open
            if self.content_panel:
                self.content_panel.show_ssh_terminal(ap_data)
            
            # Wait for connection
            max_attempts = 20
            for attempt in range(max_attempts):
                window = SSHManager._windows.get("default")
                if window and ap_id in window.tabs:
                    connection = window.tabs[ap_id].connection
                    if connection.connected:
                        # Check if in service mode and exit if needed
                        time.sleep(1)
                        output = connection.get_automation_output(last_chars=500)
                        
                        if "servicemode>" in output.lower():
                            self.parent.after(0, lambda: self._log("Exiting service mode first..."))
                            connection.send_command("extended matex2010")
                            time.sleep(2)
                            connection.send_command("enableshell true")
                            time.sleep(2)
                            connection.send_command("exit")
                            time.sleep(1)
                            connection.send_command("exit")
                            time.sleep(2)
                        
                        # Navigate to log folder and list files
                        connection.send_command("cd /opt/esl/accesspoint")
                        time.sleep(1)
                        connection.send_command("ls -la *20*log* 2>/dev/null || echo 'No log files found'")
                        time.sleep(2)
                        
                        # Get file list for display
                        output = connection.get_automation_output(last_chars=2000)
                        self.parent.after(0, lambda o=output: self._log(f"Log files found:\n{o}"))
                        
                        # Use SFTP to download files
                        try:
                            # Create SFTP client using existing SSH connection
                            sftp_client = paramiko.SFTPClient.from_transport(connection.client.get_transport())
                            
                            # Get list of files matching pattern
                            remote_path = "/opt/esl/accesspoint"
                            try:
                                files = sftp_client.listdir(remote_path)
                                log_files = [f for f in files if '20' in f and 'log' in f.lower()]
                                
                                if not log_files:
                                    self.parent.after(0, lambda: self._log("No log files found to download"))
                                    def show_info():
                                        messagebox.showinfo("No Logs", 
                                                          "No log files found matching pattern *20*log*",
                                                          parent=self.parent)
                                    self.parent.after(0, show_info)
                                    return
                                
                                # Download each file
                                for filename in log_files:
                                    remote_file = f"{remote_path}/{filename}"
                                    local_file = os.path.join(dest_folder, filename)
                                    
                                    self.parent.after(0, lambda f=filename: self._log(f"Downloading: {f}"))
                                    sftp_client.get(remote_file, local_file)
                                    self.parent.after(0, lambda f=filename: self._log(f"✓ Downloaded: {f}"))
                                
                                self.parent.after(0, lambda: self._log(f"✓ All log files downloaded to {dest_folder}"))
                                
                                def show_success():
                                    messagebox.showinfo("Success", 
                                                      f"Downloaded {len(log_files)} log file(s) to:\n{dest_folder}",
                                                      parent=self.parent)
                                self.parent.after(0, show_success)
                                
                            finally:
                                sftp_client.close()
                                
                        except Exception as e:
                            self.parent.after(0, lambda err=str(e): self._log(f"✗ Error downloading logs: {err}"))
                            def show_error():
                                messagebox.showerror("Error", 
                                                   f"Failed to download logs:\n{str(e)}",
                                                   parent=self.parent)
                            self.parent.after(0, show_error)
                        return
                
                time.sleep(0.5)
            
            # Timeout
            def show_warning():
                messagebox.showwarning("Connection Timeout", 
                                     f"SSH terminal for AP {ap_id} did not connect in time.",
                                     parent=self.parent)
            self.parent.after(0, show_warning)
        
        threading.Thread(target=download_when_ready, daemon=True).start()
    
    def _ssh_quick_command(self, ap_data, action_name, command):
        """Execute a quick SSH command on the active terminal."""
        self._log(f"SSH Quick Command: {action_name} for AP {ap_data.get('ap_id')}")
        if self.content_panel:
            self.content_panel.ssh_execute_command(ap_data, command, action_name)
        else:
            messagebox.showerror("Error", "Content panel not available", parent=self.parent)
    
    def _ssh_remove_old_logs(self, ap_data):
        """Remove old log files from the AP."""
        if not messagebox.askyesno("Confirm", 
                                   "This will remove old log files (matching *20*log*).\n\nContinue?",
                                   parent=self.parent):
            return
        
        from ssh_helper import SSHManager
        import threading
        import time
        
        ap_id = ap_data.get('ap_id')
        self._log(f"Removing old logs for AP {ap_id}")
        
        def remove_when_ready():
            # Ensure terminal is open
            if self.content_panel:
                self.content_panel.show_ssh_terminal(ap_data)
            
            # Wait for connection
            max_attempts = 20
            for attempt in range(max_attempts):
                window = SSHManager._windows.get("default")
                if window and ap_id in window.tabs:
                    connection = window.tabs[ap_id].connection
                    if connection.connected:
                        # Send commands
                        commands = [
                            ("cd /opt/esl/accesspoint", 1),
                            ("ls -la *20*log* 2>/dev/null", 1),
                            ("rm -f *20*log*", 1),
                            ("echo 'Log files removed'", 0.5)
                        ]
                        
                        for cmd, delay in commands:
                            connection.send_command(cmd)
                            time.sleep(delay)
                        
                        self.parent.after(0, lambda: self._log(f"✓ Old log files removed from AP {ap_id}"))
                        
                        def show_success():
                            messagebox.showinfo("Success", 
                                              f"Log files removed from AP {ap_id}",
                                              parent=self.parent)
                        self.parent.after(0, show_success)
                        return
                
                time.sleep(0.5)
            
            # Timeout
            def show_warning():
                messagebox.showwarning("Connection Timeout", 
                                     f"SSH terminal for AP {ap_id} did not connect in time.",
                                     parent=self.parent)
            self.parent.after(0, show_warning)
        
        threading.Thread(target=remove_when_ready, daemon=True).start()
    
    def _ssh_download_logs(self, ap_data):
        """Download log files from the AP via SCP."""
        from tkinter import filedialog
        
        dest_folder = filedialog.askdirectory(title="Select destination folder for log files", parent=self.parent)
        if not dest_folder:
            return
        
        self._log(f"Downloading logs from AP {ap_data.get('ap_id')} to {dest_folder}")
        
        if self.content_panel:
            self.content_panel.ssh_download_logs(ap_data, dest_folder)
        else:
            messagebox.showerror("Error", "Content panel not available", parent=self.parent)
    
    def _ssh_exit_service_mode(self, ap_data):
        """Exit service mode with full command sequence."""
        self._log(f"Exiting service mode for AP {ap_data.get('ap_id')}")
        
        if self.content_panel:
            self.content_panel.ssh_exit_service_mode(ap_data)
        else:
            messagebox.showerror("Error", "Content panel not available", parent=self.parent)
    
    def _ssh_check_dns(self, ap_data):
        """Check DNS settings, exiting service mode first if needed."""
        self._log(f"Checking DNS settings for AP {ap_data.get('ap_id')}")
        
        if self.content_panel:
            self.content_panel.ssh_check_dns(ap_data)
        else:
            messagebox.showerror("Error", "Content panel not available", parent=self.parent)
    
    def _toggle_ssh_server(self, ap_data, enable):
        """Toggle SSH server on/off via browser automation."""
        if not self.content_panel or not self.content_panel.browser_manager:
            messagebox.showerror("Error", "Browser not running", parent=self.parent)
            return
        
        try:
            import threading
            
            def toggle_in_thread():
                try:
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    import time
                    
                    driver = self.content_panel.browser_manager.driver
                    
                    # Wait for checkbox element
                    checkbox = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.NAME, "ssh_enable"))
                    )
                    
                    # Check current state
                    is_checked = checkbox.is_selected()
                    
                    # Click if state needs to change
                    if (enable and not is_checked) or (not enable and is_checked):
                        checkbox.click()
                        
                        # Find and click Submit button
                        submit_btn = driver.find_element(By.NAME, "submit")
                        submit_btn.click()
                        
                        time.sleep(2)  # Wait for action to complete
                        
                        action = "enabled" if enable else "disabled"
                        def show_success():
                            self._log(f"SSH server {action} successfully")
                            messagebox.showinfo("Success", 
                                              f"SSH server has been {action}", 
                                              parent=self.parent)
                        self.parent.after(0, show_success)
                    else:
                        def show_info():
                            state = "already enabled" if is_checked else "already disabled"
                            self._log(f"SSH server is {state}")
                            messagebox.showinfo("Info", 
                                              f"SSH server is {state}", 
                                              parent=self.parent)
                        self.parent.after(0, show_info)
                        
                except Exception as e:
                    error_msg = f"Failed to toggle SSH: {str(e)}"
                    def show_error():
                        self._log(error_msg)
                        messagebox.showerror("Error", error_msg, parent=self.parent)
                    self.parent.after(0, show_error)
            
            thread = threading.Thread(target=toggle_in_thread, daemon=True)
            thread.start()
            
        except Exception as e:
            self._log(f"SSH toggle error: {str(e)}")
            messagebox.showerror("Error", f"Failed to toggle SSH:\n{str(e)}", parent=self.parent)
    
    def _browser_maximize(self):
        """Maximize browser window."""
        if not self.content_panel or not self.content_panel.browser_manager:
            messagebox.showerror("Error", "Browser not running", parent=self.parent)
            return
        
        try:
            driver = self.content_panel.browser_manager.driver
            driver.maximize_window()
            self._log("Browser window maximized")
        except Exception as e:
            self._log(f"Maximize error: {str(e)}")
    
    def _browser_minimize(self):
        """Minimize browser window."""
        if not self.content_panel or not self.content_panel.browser_manager:
            messagebox.showerror("Error", "Browser not running", parent=self.parent)
            return
        
        try:
            driver = self.content_panel.browser_manager.driver
            driver.minimize_window()
            self._log("Browser window minimized")
        except Exception as e:
            self._log(f"Minimize error: {str(e)}")
    
    def _browser_refresh(self, ap_data):
        """Refresh current browser page."""
        if not self.content_panel or not self.content_panel.browser_manager:
            messagebox.showerror("Error", "Browser not running", parent=self.parent)
            return
        
        try:
            driver = self.content_panel.browser_manager.driver
            driver.refresh()
            self._log("Browser page refreshed")
        except Exception as e:
            self._log(f"Refresh error: {str(e)}")
    
    def _browser_screenshot(self, ap_data):
        """Take a screenshot of current browser page."""
        if not self.content_panel or not self.content_panel.browser_manager:
            messagebox.showerror("Error", "Browser not running", parent=self.parent)
            return
        
        try:
            import os
            from datetime import datetime
            driver = self.content_panel.browser_manager.driver
            
            # Create screenshots directory
            screenshots_dir = os.path.join(os.path.dirname(__file__), "..", "screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"AP_{ap_data.get('ap_id')}_{timestamp}.png"
            filepath = os.path.join(screenshots_dir, filename)
            
            # Take screenshot
            driver.save_screenshot(filepath)
            self._log(f"Screenshot saved: {filepath}")
            messagebox.showinfo("Screenshot", f"Screenshot saved to:\n{filepath}", 
                              parent=self.parent)
        except Exception as e:
            self._log(f"Screenshot error: {str(e)}")
            messagebox.showerror("Error", f"Screenshot failed:\n{str(e)}", parent=self.parent)
    
    def _browser_view_source(self, ap_data):
        """View page source in a dialog."""
        if not self.content_panel or not self.content_panel.browser_manager:
            messagebox.showerror("Error", "Browser not running", parent=self.parent)
            return
        
        try:
            driver = self.content_panel.browser_manager.driver
            page_source = driver.page_source
            
            # Create dialog
            dialog = tk.Toplevel(self.parent)
            dialog.title(f"Page Source - AP {ap_data.get('ap_id')}")
            dialog.geometry("800x600")
            dialog.transient(self.parent)
            
            # Try to grab focus, but don't fail if another window has it
            try:
                dialog.grab_set()
            except:
                pass
            
            # Text widget with scrollbar
            text_frame = tk.Frame(dialog)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=text_widget.yview)
            
            text_widget.insert('1.0', page_source)
            text_widget.config(state='disabled')
            
            self._log("Showing page source")
        except Exception as e:
            self._log(f"View source error: {str(e)}")
            messagebox.showerror("Error", f"Failed to view source:\n{str(e)}", parent=self.parent)
    
    def _on_notebook_tab_changed(self, event):
        """Handle notebook tab change."""
        current_tab = self.notebook.current_tab
        if current_tab is None:
            return
        tab_text = self.notebook.tab(current_tab, "text")
        if not tab_text:
            return
        
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
    
    def _toggle_continuous_ping(self, ap_data, result_label, ping_btn, ping_state):
        """Toggle continuous ping on/off."""
        if ping_state['running']:
            # Stop pinging
            ping_state['running'] = False
            if ping_state['job']:
                self.parent.after_cancel(ping_state['job'])
                ping_state['job'] = None
            ping_btn.config(text="▶ Ping AP", bg="#2B5A8A", activebackground="#1F4366")
            result_label.config(text="Stopped", fg="#6C757D")
            self._log(f"Continuous ping stopped: {ap_data.get('ip_address', 'N/A')}", "info")
        else:
            # Start pinging
            ping_state['running'] = True
            ping_btn.config(text="⏸ Ping AP", bg="#DC3545", activebackground="#C82333")
            self._continuous_ping(ap_data, result_label, ping_state)
            self._log(f"Continuous ping started: {ap_data.get('ip_address', 'N/A')}", "info")
    
    def _continuous_ping(self, ap_data, result_label, ping_state):
        """Perform continuous ping in a background thread."""
        if not ping_state['running']:
            return
        
        ip_address = ap_data.get('ip_address', '')
        if not ip_address or ip_address == 'N/A':
            result_label.config(text="No IP address available", fg="#DC3545")
            ping_state['running'] = False
            return
        
        # Run ping in a separate thread to avoid blocking UI
        import threading
        
        def ping_thread():
            import subprocess
            import platform
            import re
            
            try:
                # Determine ping command based on OS
                param = '-n' if platform.system().lower() == 'windows' else '-c'
                
                # Execute ping command
                result = subprocess.run(
                    ['ping', param, '1', ip_address],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                # Update UI from main thread
                def update_ui():
                    if not ping_state['running']:
                        return
                    
                    if result.returncode == 0:
                        # Success - extract time if possible
                        output = result.stdout
                        time_match = re.search(r'time[=<](\d+)', output, re.IGNORECASE)
                        if time_match:
                            ping_time = time_match.group(1)
                            result_label.config(text=f"✓ Response from {ip_address} (time={ping_time}ms)", fg="#28A745")
                            self._log(f"Ping: {ip_address} responded in {ping_time}ms", "success")
                        else:
                            result_label.config(text=f"✓ Response from {ip_address}", fg="#28A745")
                            self._log(f"Ping: {ip_address} responded", "success")
                    else:
                        result_label.config(text=f"✗ Timeout - No response from {ip_address}", fg="#DC3545")
                        self._log(f"Ping timeout: {ip_address}", "warning")
                
                self.parent.after(0, update_ui)
                    
            except subprocess.TimeoutExpired:
                def update_timeout():
                    if ping_state['running']:
                        result_label.config(text=f"✗ Timeout - No response from {ip_address}", fg="#DC3545")
                        self._log(f"Ping timeout: {ip_address}", "warning")
                self.parent.after(0, update_timeout)
            except Exception as e:
                def update_error():
                    if ping_state['running']:
                        result_label.config(text=f"✗ Error: {str(e)}", fg="#DC3545")
                        self._log(f"Ping error for {ip_address}: {str(e)}", "error")
                self.parent.after(0, update_error)
        
        # Start ping in background thread
        thread = threading.Thread(target=ping_thread, daemon=True)
        thread.start()
        
        # Schedule next ping
        if ping_state['running']:
            ping_state['job'] = self.parent.after(2000, lambda: self._continuous_ping(ap_data, result_label, ping_state))
    
    def _close_tab_by_index(self, tab_index):
        """Close a tab by its index."""
        # Find which AP this tab corresponds to
        ap_id_to_close = None
        for ap_id, tab_info in self.ap_tabs.items():
            if tab_info.get('tab_id') == tab_index:
                ap_id_to_close = ap_id
                break
        
        if ap_id_to_close:
            self.close_ap_tab(ap_id_to_close)
    
    def close_ap_tab(self, ap_id):
        """Close an AP tab with warning if there's ongoing work."""
        if ap_id not in self.ap_tabs:
            return
        
        tab_info = self.ap_tabs[ap_id]
        
        # Check for ongoing ping job
        has_ongoing_work = False
        ping_state = tab_info.get('ping_state')
        if ping_state and ping_state.get('running'):
            has_ongoing_work = True
        
        # Warn user if there's ongoing work
        if has_ongoing_work:
            from tkinter import messagebox
            response = messagebox.askyesno(
                "Close AP Tab",
                f"AP {ap_id} has ongoing ping operations.\\n\\nAre you sure you want to close this tab?",
                parent=self.parent
            )
            if not response:
                return
            
            # Stop ping if running
            if ping_state and ping_state.get('job'):
                self.parent.after_cancel(ping_state['job'])
                ping_state['running'] = False
        
        # Get tab index
        tab_id = tab_info['tab_id']
        
        # Remove tab from notebook
        self.notebook.forget(tab_id)
        
        # Remove from our tracking
        del self.ap_tabs[ap_id]
        
        # Update tab_id for remaining tabs (they shifted down)
        for ap_id_remaining, info in self.ap_tabs.items():
            if info['tab_id'] > tab_id:
                info['tab_id'] -= 1
        
        self._log(f"Closed AP {ap_id} tab")
    
    def _log(self, message, level="info"):
        """Log activity."""
        if self.log_callback:
            self.log_callback("AP Panel", message, level)
