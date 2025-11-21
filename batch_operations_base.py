"""
Base framework for batch operations on multiple APs
Provides common UI and threading functionality for batch operations
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import List, Dict, Callable, Optional
import threading
import queue
from datetime import datetime
from database_manager import DatabaseManager


class BatchOperationWindow:
    """Base class for batch operation windows."""
    
    def __init__(self, parent, title: str, current_user, db_manager: DatabaseManager):
        """
        Initialize batch operation window.
        
        Args:
            parent: Parent window
            title: Window title
            current_user: Current user info
            db_manager: Database manager instance
        """
        self.parent = parent
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title(title)
        self.window.geometry("1400x1000")
        self.window.configure(bg="#F0F0F0")
        
        self.current_user = current_user
        self.db = db_manager
        
        # State management
        self.selected_aps: List[Dict] = []  # List of selected AP data
        self.operation_running = False
        self.operation_thread = None
        self.operation_queue = queue.Queue()  # For thread-safe communication
        
        # Search state
        self.all_search_results: List[Dict] = []  # All APs from searches
        self.marked_ap_ids: set = set()  # Set of marked AP IDs
        
        self._create_ui()
        self._start_queue_processor()
    
    def _create_ui(self):
        """Create the main UI layout."""
        # Modern header with title and description
        header_frame = tk.Frame(self.window, bg="#3D6B9E", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text=self.window.title(), 
                              font=('Segoe UI', 16, 'bold'),
                              bg="#3D6B9E", fg="white")
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        # Main scrollable area
        main_container = tk.Frame(self.window, bg="#F0F0F0")
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Create canvas and scrollbar for scrolling
        self.canvas = tk.Canvas(main_container, bg="#F0F0F0", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=self.canvas.yview)
        
        # Create content frame inside canvas
        content_frame = tk.Frame(self.canvas, bg="#F0F0F0")
        self.content_frame = content_frame  # Store reference
        
        # Configure canvas scrolling
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas_frame = self.canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        # Pack scrollbar and canvas
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Update scroll region when content changes
        def configure_scroll_region(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # Bind to both content frame and canvas for resize
        content_frame.bind("<Configure>", configure_scroll_region)
        
        # Also update canvas window width when canvas is resized
        def on_canvas_configure(event):
            # Make the canvas window the same width as the canvas
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas_frame, width=canvas_width)
        
        self.canvas.bind("<Configure>", on_canvas_configure)
        
        # Enable mousewheel scrolling
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Step 1: Search and Select
        search_section = ttk.LabelFrame(content_frame, text="Step 1: Search and Select APs", 
                                       padding=15)
        search_section.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Search controls - modern layout
        search_controls = tk.Frame(search_section, bg="white", relief=tk.FLAT, bd=0)
        search_controls.pack(fill=tk.X, pady=(0, 10))
        
        # Search box with icon
        search_input_frame = tk.Frame(search_controls, bg="white")
        search_input_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        tk.Label(search_input_frame, text="🔍", font=('Segoe UI', 12),
                bg="white").pack(side=tk.LEFT, padx=(5, 5))
        
        self.search_entry = tk.Entry(search_input_frame, font=('Segoe UI', 11),
                                     relief=tk.SOLID, bd=1)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        self.search_entry.bind('<Return>', lambda e: self._search_aps())
        
        # Search button - modern style
        search_btn = tk.Button(search_controls, text="Search", 
                              command=self._search_aps,
                              bg="#3D6B9E", fg="white", 
                              font=('Segoe UI', 10, 'bold'),
                              relief=tk.FLAT, padx=20, pady=8,
                              cursor="hand2", activebackground="#2E5A8A")
        search_btn.pack(side=tk.LEFT, padx=2)
        
        # Selection controls frame
        select_controls = tk.Frame(search_section, bg="#F8F9FA", relief=tk.FLAT, bd=0)
        select_controls.pack(fill=tk.X, pady=(0, 10))
        
        # Selection buttons - modern flat style
        btn_style = {
            'font': ('Segoe UI', 9),
            'relief': tk.FLAT,
            'padx': 15,
            'pady': 6,
            'cursor': 'hand2',
            'bd': 0
        }
        
        tk.Button(select_controls, text="☑ Select All", 
                 command=self._select_all,
                 bg="#28A745", fg="white", 
                 activebackground="#218838",
                 **btn_style).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(select_controls, text="☐ Unselect All", 
                 command=self._unselect_all,
                 bg="#6C757D", fg="white",
                 activebackground="#5A6268",
                 **btn_style).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Add button - prominent (override font from btn_style)
        add_btn_style = btn_style.copy()
        add_btn_style['font'] = ('Segoe UI', 10, 'bold')
        tk.Button(select_controls, text="➕ Add Selected to List", 
                 command=self._add_selected_to_list,
                 bg="#007BFF", fg="white",
                 activebackground="#0056B3",
                 **add_btn_style).pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Status
        self.selection_status = tk.Label(search_section, 
                                        text="Enter search term and click Search",
                                        font=('Segoe UI', 9),
                                        bg="#F0F0F0", fg="#6C757D")
        self.selection_status.pack(anchor=tk.W, pady=(0, 10))
        
        # Search results tree - modern style
        tree_container = tk.Frame(search_section, bg="white", relief=tk.SOLID, bd=1)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        tree_scroll_y = ttk.Scrollbar(tree_container, orient=tk.VERTICAL)
        tree_scroll_x = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL)
        
        self.search_tree = ttk.Treeview(
            tree_container,
            columns=('select', 'ap_id', 'ip', 'mac', 'store', 'chain'),
            show='tree headings',
            selectmode='extended',
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set
        )
        
        tree_scroll_y.config(command=self.search_tree.yview)
        tree_scroll_x.config(command=self.search_tree.xview)
        
        # Configure modern tree style
        style = ttk.Style()
        style.configure("Treeview", 
                       rowheight=25,
                       font=('Segoe UI', 10))
        style.configure("Treeview.Heading",
                       font=('Segoe UI', 10, 'bold'),
                       background="#E9ECEF",
                       foreground="#212529")
        
        # Column configuration
        self.search_tree.heading('#0', text='☐')
        self.search_tree.heading('select', text='')
        self.search_tree.heading('ap_id', text='AP ID')
        self.search_tree.heading('ip', text='IP Address')
        self.search_tree.heading('mac', text='MAC Address')
        self.search_tree.heading('store', text='Store ID')
        self.search_tree.heading('chain', text='Retail Chain')
        
        self.search_tree.column('#0', width=40, anchor=tk.CENTER, stretch=False)
        self.search_tree.column('select', width=0, stretch=False)
        self.search_tree.column('ap_id', width=120)
        self.search_tree.column('ip', width=140)
        self.search_tree.column('mac', width=150)
        self.search_tree.column('store', width=100)
        self.search_tree.column('chain', width=130)
        
        # Pack tree and scrollbars
        self.search_tree.grid(row=0, column=0, sticky='nsew')
        tree_scroll_y.grid(row=0, column=1, sticky='ns')
        tree_scroll_x.grid(row=1, column=0, sticky='ew')
        
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        # Bind checkbox toggle on click
        self.search_tree.bind('<Button-1>', self._on_tree_click)
        
        # Step 3: Operation Configuration
        self.operation_frame = ttk.LabelFrame(content_frame, text="Step 3: Operation Settings", 
                                            padding=15)
        self.operation_frame.pack(fill=tk.X, pady=(0, 10))
        
        # This will be populated by subclasses
        self._create_operation_controls()
        
        # Execute button frame - prominent modern buttons
        execute_frame = tk.Frame(content_frame, bg="#F0F0F0")
        execute_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.execute_btn = tk.Button(execute_frame, text="▶ Execute Operation", 
                                     command=self._confirm_and_execute,
                                     bg="#28A745", fg="white",
                                     font=('Segoe UI', 12, 'bold'),
                                     relief=tk.FLAT, padx=30, pady=12,
                                     cursor="hand2", bd=0,
                                     activebackground="#218838")
        self.execute_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(execute_frame, text="⏹ Stop", 
                                 command=self._stop_operation, state='disabled',
                                 bg="#DC3545", fg="white",
                                 font=('Segoe UI', 12, 'bold'),
                                 relief=tk.FLAT, padx=30, pady=12,
                                 cursor="hand2", bd=0,
                                 activebackground="#C82333")
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Step 2: APs List for Operation
        list_section = ttk.LabelFrame(content_frame, text="Step 2: APs List for Operation", 
                                     padding=15)
        list_section.pack(fill=tk.X, pady=(0, 10))
        
        # Count label
        self.list_count_label = tk.Label(list_section, 
                                        text="No APs added yet",
                                        font=('Segoe UI', 10, 'bold'),
                                        bg="#F0F0F0", fg="#007BFF")
        self.list_count_label.pack(anchor=tk.W, pady=(0, 10))
        
        # List container
        list_container = tk.Frame(list_section, bg="white", relief=tk.SOLID, bd=1)
        list_container.pack(fill=tk.X, pady=(0, 10))
        
        marked_scroll = ttk.Scrollbar(list_container, orient=tk.VERTICAL)
        
        self.marked_tree = ttk.Treeview(
            list_container,
            columns=('store', 'ap_id', 'ip', 'mac'),
            show='headings',
            height=5,
            yscrollcommand=marked_scroll.set
        )
        
        marked_scroll.config(command=self.marked_tree.yview)
        
        self.marked_tree.heading('store', text='Store ID')
        self.marked_tree.heading('ap_id', text='AP ID')
        self.marked_tree.heading('ip', text='IP Address')
        self.marked_tree.heading('mac', text='MAC Address')
        
        self.marked_tree.column('store', width=100)
        self.marked_tree.column('ap_id', width=120)
        self.marked_tree.column('ip', width=140)
        self.marked_tree.column('mac', width=150)
        
        self.marked_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        marked_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Management buttons - modern style
        manage_btn_frame = tk.Frame(list_section, bg="#F0F0F0")
        manage_btn_frame.pack(fill=tk.X)
        
        manage_btn_style = {
            'font': ('Segoe UI', 9),
            'relief': tk.FLAT,
            'padx': 15,
            'pady': 6,
            'cursor': 'hand2',
            'bd': 0
        }
        
        tk.Button(manage_btn_frame, text="❌ Remove Selected",
                 command=self._remove_from_list,
                 bg="#DC3545", fg="white",
                 activebackground="#C82333",
                 **manage_btn_style).pack(side=tk.LEFT, padx=5)
        
        tk.Button(manage_btn_frame, text="🗑 Remove All",
                 command=self._remove_all_from_list,
                 bg="#6C757D", fg="white",
                 activebackground="#5A6268",
                 **manage_btn_style).pack(side=tk.LEFT, padx=5)
        
        # Step 4: Progress and Results
        progress_frame = ttk.LabelFrame(content_frame, text="Step 4: Operation Progress and Results", 
                                       padding=15)
        progress_frame.pack(fill=tk.BOTH, expand=True)
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                           variable=self.progress_var, 
                                           maximum=100,
                                           mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Progress status
        self.progress_status = ttk.Label(progress_frame, text="Ready", foreground="gray")
        self.progress_status.pack(anchor=tk.W, pady=(0, 10))
        
        # Split view: AP list on left, activity log on right
        split_frame = ttk.Frame(progress_frame)
        split_frame.pack(fill=tk.BOTH, expand=True)
        
        # AP list with status
        ap_list_frame = ttk.Frame(split_frame)
        ap_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        ttk.Label(ap_list_frame, text="APs in Operation:").pack(anchor=tk.W)
        
        ap_list_container = ttk.Frame(ap_list_frame)
        ap_list_container.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        ap_scroll = ttk.Scrollbar(ap_list_container, orient=tk.VERTICAL)
        
        self.ap_status_tree = ttk.Treeview(
            ap_list_container,
            columns=('store', 'ap_id', 'pings', 'status', 'result'),
            show='headings',
            yscrollcommand=ap_scroll.set
        )
        
        ap_scroll.config(command=self.ap_status_tree.yview)
        
        self.ap_status_tree.heading('store', text='Store ID')
        self.ap_status_tree.heading('ap_id', text='AP ID')
        self.ap_status_tree.heading('pings', text='Pings')
        self.ap_status_tree.heading('status', text='Status')
        self.ap_status_tree.heading('result', text='Result')
        
        self.ap_status_tree.column('store', width=80)
        self.ap_status_tree.column('ap_id', width=100)
        self.ap_status_tree.column('pings', width=60)
        self.ap_status_tree.column('status', width=80)
        self.ap_status_tree.column('result', width=200)
        
        self.ap_status_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ap_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Activity log
        log_frame = ttk.Frame(split_frame)
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        ttk.Label(log_frame, text="Activity Log:").pack(anchor=tk.W)
        
        self.activity_log = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=50,
            height=10,
            font=('Consolas', 9),
            state='disabled'
        )
        self.activity_log.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Configure text tags for colored output
        self.activity_log.tag_configure('info', foreground='black')
        self.activity_log.tag_configure('success', foreground='green')
        self.activity_log.tag_configure('warning', foreground='orange')
        self.activity_log.tag_configure('error', foreground='red')
        
        # Force update of scroll region after all UI is created
        self.window.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _create_operation_controls(self):
        """Override this method in subclasses to add operation-specific controls."""
        ttk.Label(self.operation_frame, 
                 text="Override _create_operation_controls() in subclass").pack()
    
    def _search_aps(self):
        """Search for APs in the database."""
        search_term = self.search_entry.get().strip()
        
        if not search_term:
            messagebox.showwarning("Empty Search", 
                                 "Please enter a search term (AP ID, hostname, IP, MAC, store ID)",
                                 parent=self.window)
            return
        
        self._log_activity(f"Searching for: {search_term}", "info")
        
        # Search using database manager
        results = self.db.search_aps_for_support(
            search_term=search_term
        )
        
        if not results:
            self._log_activity(f"No APs found matching '{search_term}'", "warning")
            messagebox.showinfo("No Results", 
                              f"No APs found matching '{search_term}'",
                              parent=self.window)
            return
        
        self._log_activity(f"Found {len(results)} APs", "success")
        
        # Replace old search results with new ones
        self.all_search_results = results
        
        self._update_search_tree()
    
    def _update_search_tree(self):
        """Update the search results tree with current search (replaces old results)."""
        # Clear tree
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)
        
        # Populate with current search results only (not accumulated)
        for ap in self.all_search_results:
            is_marked = ap['ap_id'] in self.marked_ap_ids
            checkbox = '☑' if is_marked else '☐'
            
            self.search_tree.insert('', tk.END, text=checkbox, values=(
                '',
                ap.get('ap_id', ''),
                ap.get('ip_address', ''),
                ap.get('mac_address', ''),
                ap.get('store_id', ''),
                ap.get('retail_chain', '')
            ), tags=(ap['ap_id'],))
        
        self._update_selection_status()
        self._update_marked_tree()
    
    def _update_marked_tree(self):
        """Update the operation list tree."""
        # Clear tree
        for item in self.marked_tree.get_children():
            self.marked_tree.delete(item)
        
        # Show APs in operation list
        for ap in self.selected_aps:
            self.marked_tree.insert('', tk.END, values=(
                ap.get('store_id', ''),
                ap.get('ap_id', ''),
                ap.get('ip_address', ''),
                ap.get('mac_address', '')
            ), tags=(ap['ap_id'],))
        
        # Update count label
        count = len(self.selected_aps)
        if count == 0:
            self.list_count_label.config(text="No APs added yet", fg="#6C757D")
        else:
            self.list_count_label.config(
                text=f"{count} AP{'s' if count != 1 else ''} ready for operation",
                fg="#28A745"
            )
    
    def _on_tree_click(self, event):
        """Handle checkbox click in search tree."""
        region = self.search_tree.identify_region(event.x, event.y)
        if region == 'tree':
            item = self.search_tree.identify_row(event.y)
            if item:
                tags = self.search_tree.item(item, 'tags')
                if tags:
                    ap_id = tags[0]
                    # Toggle marked status
                    if ap_id in self.marked_ap_ids:
                        self.marked_ap_ids.discard(ap_id)
                    else:
                        self.marked_ap_ids.add(ap_id)
                    
                    # Update checkbox display
                    is_marked = ap_id in self.marked_ap_ids
                    checkbox = '☑' if is_marked else '☐'
                    self.search_tree.item(item, text=checkbox)
                    
                    self._update_selection_status()
                    self._update_marked_tree()
    
    def _remove_from_list(self):
        """Remove selected APs from operation list."""
        selection = self.marked_tree.selection()
        
        if not selection:
            messagebox.showinfo("No Selection", 
                              "Please select APs to remove from the list",
                              parent=self.window)
            return
        
        removed = []
        for item in selection:
            tags = self.marked_tree.item(item, 'tags')
            if tags:
                ap_id = tags[0]
                self.selected_aps = [ap for ap in self.selected_aps 
                                    if ap['ap_id'] != ap_id]
                removed.append(ap_id)
        
        self._update_marked_tree()
        self._log_activity(f"Removed {len(removed)} AP(s) from operation list", "info")
    
    def _remove_all_from_list(self):
        """Remove all APs from operation list."""
        if not self.selected_aps:
            messagebox.showinfo("List Empty", 
                              "The operation list is already empty",
                              parent=self.window)
            return
        
        if messagebox.askyesno("Remove All", 
                              f"Remove all {len(self.selected_aps)} APs from operation list?",
                              parent=self.window):
            count = len(self.selected_aps)
            self.selected_aps.clear()
            self._update_marked_tree()
            self._log_activity(f"Removed all {count} APs from operation list", "info")
    
    def _select_all(self):
        """Select all APs in current search results."""
        for item in self.search_tree.get_children():
            self.search_tree.item(item, text='☑')
        
        self._update_selection_status()
        self._log_activity("Selected all APs in search results", "info")
    
    def _unselect_all(self):
        """Unselect all APs in current search results."""
        for item in self.search_tree.get_children():
            self.search_tree.item(item, text='☐')
        
        self._update_selection_status()
        self._log_activity("Unselected all APs in search results", "info")
    
    def _add_selected_to_list(self):
        """Add selected APs from search to operation list."""
        added = []
        
        for item in self.search_tree.get_children():
            if self.search_tree.item(item, 'text') == '☑':
                tags = self.search_tree.item(item, 'tags')
                if tags:
                    ap_id = tags[0]
                    # Find AP data
                    ap_data = next((ap for ap in self.all_search_results 
                                  if ap['ap_id'] == ap_id), None)
                    
                    if ap_data and ap_id not in [ap['ap_id'] for ap in self.selected_aps]:
                        self.selected_aps.append(ap_data)
                        added.append(ap_id)
        
        if added:
            self._log_activity(f"Added {len(added)} AP(s) to operation list", "success")
            self._update_marked_tree()
            
            # Clear selection in search tree
            self._unselect_all()
        else:
            messagebox.showinfo("No Selection", 
                              "No APs selected or all selected APs are already in the list",
                              parent=self.window)
    
    def _update_selection_status(self):
        """Update the selection status label."""
        selected_count = sum(1 for item in self.search_tree.get_children() 
                           if self.search_tree.item(item, 'text') == '☑')
        total_count = len(self.search_tree.get_children())
        
        if total_count == 0:
            self.selection_status.config(text="Enter search term and click Search")
        elif selected_count == 0:
            self.selection_status.config(
                text=f"0 of {total_count} APs selected - Click checkboxes or use Select All"
            )
        else:
            self.selection_status.config(
                text=f"{selected_count} of {total_count} APs selected - Click 'Add Selected to List' to add them"
            )
    
    def _confirm_and_execute(self):
        """Execute operation directly without confirmation."""
        if not self.selected_aps:
            messagebox.showwarning("No APs in List", 
                                 "Please add at least one AP to the operation list",
                                 parent=self.window)
            return
        
        # Execute directly
        self._execute_operation()
    
    def _get_operation_description(self) -> str:
        """Override this method to provide operation description."""
        return "Batch operation (override _get_operation_description() in subclass)"
    
    def _get_operation_params(self) -> dict:
        """Override this method to read tkinter variables before thread starts."""
        return {}
    
    def _execute_operation(self):
        """Start the batch operation in a background thread."""
        self.operation_running = True
        self.execute_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        # Clear previous results
        for item in self.ap_status_tree.get_children():
            self.ap_status_tree.delete(item)
        
        # Add APs to status tree
        for ap in self.selected_aps:
            self.ap_status_tree.insert('', tk.END, values=(
                ap.get('store_id', ''),
                ap['ap_id'],
                '-',  # Initial ping count (will show progress during operation)
                'Pending',
                ''
            ), tags=(ap['ap_id'],))
        
        self.progress_var.set(0)
        self._log_activity(f"Starting operation on {len(self.selected_aps)} APs...", "info")
        
        # Read operation parameters in main thread before starting worker thread
        operation_params = self._get_operation_params()
        
        # Start operation thread
        self.operation_thread = threading.Thread(
            target=self._run_operation,
            args=(operation_params,),
            daemon=True
        )
        self.operation_thread.start()
    
    def _run_operation(self, operation_params: dict = None):
        """
        Run the batch operation (in background thread).
        Override this method in subclasses to implement specific operation.
        
        Args:
            operation_params: Dictionary of parameters read from tkinter vars in main thread
        """
        total = len(self.selected_aps)
        
        for idx, ap in enumerate(self.selected_aps):
            if not self.operation_running:
                self.operation_queue.put(('log', 'Operation stopped by user', 'warning'))
                break
            
            ap_id = ap['ap_id']
            
            # Update status to "Running"
            self.operation_queue.put(('status', ap_id, 'Running', ''))
            self.operation_queue.put(('log', f"Processing {ap_id}...", 'info'))
            
            # Execute operation (to be implemented in subclass)
            success, result = self._execute_single_operation(ap)
            
            # Update status
            status = 'Success' if success else 'Failed'
            tag = 'success' if success else 'error'
            self.operation_queue.put(('status', ap_id, status, result))
            self.operation_queue.put(('log', f"{ap_id}: {result}", tag))
            
            # Update progress
            progress = ((idx + 1) / total) * 100
            self.operation_queue.put(('progress', progress, f"Processed {idx + 1} of {total}"))
        
        # Operation complete
        self.operation_queue.put(('complete', None, None))
    
    def _execute_single_operation(self, ap: Dict) -> tuple[bool, str]:
        """
        Execute operation on a single AP.
        Override this method in subclasses.
        
        Returns:
            tuple: (success: bool, result_message: str)
        """
        # This should be overridden in subclasses
        import time
        time.sleep(0.5)  # Simulate work
        return True, "Operation not implemented (override _execute_single_operation())"
    
    def _stop_operation(self):
        """Stop the running operation."""
        if self.operation_running:
            self.operation_running = False
            self._log_activity("Stopping operation...", "warning")
    
    def _start_queue_processor(self):
        """Start processing messages from the operation thread."""
        self._process_queue()
    
    def _process_queue(self):
        """Process messages from the operation queue (runs on main thread)."""
        try:
            while True:
                msg = self.operation_queue.get_nowait()
                
                if msg[0] == 'log':
                    self._log_activity(msg[1], msg[2])
                
                elif msg[0] == 'status':
                    # msg format: ('status', ap_id, status, result, pings)
                    pings = msg[4] if len(msg) > 4 else None
                    self._update_ap_status(msg[1], msg[2], msg[3], pings)
                
                elif msg[0] == 'progress':
                    self.progress_var.set(msg[1])
                    self.progress_status.config(text=msg[2])
                
                elif msg[0] == 'complete':
                    self._operation_complete()
                
        except queue.Empty:
            pass
        
        # Schedule next check
        self.window.after(100, self._process_queue)
    
    def _update_ap_status(self, ap_id: str, status: str, result: str, pings: str = None):
        """Update AP status in the tree."""
        for item in self.ap_status_tree.get_children():
            tags = self.ap_status_tree.item(item, 'tags')
            if tags and tags[0] == ap_id:
                current_values = self.ap_status_tree.item(item, 'values')
                store_id = current_values[0] if current_values else ''
                ping_count = pings if pings is not None else (current_values[2] if len(current_values) > 2 else '0')
                self.ap_status_tree.item(item, values=(store_id, ap_id, ping_count, status, result))
                
                # Color code
                if status == 'Success':
                    self.ap_status_tree.item(item, tags=(ap_id, 'success'))
                elif status == 'Failed':
                    self.ap_status_tree.item(item, tags=(ap_id, 'error'))
                break
        
        # Configure tags for colors
        self.ap_status_tree.tag_configure('success', foreground='green')
        self.ap_status_tree.tag_configure('error', foreground='red')
    
    def _operation_complete(self):
        """Called when operation completes."""
        self.operation_running = False
        self.execute_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        
        # Count results
        success_count = 0
        failed_count = 0
        
        for item in self.ap_status_tree.get_children():
            values = self.ap_status_tree.item(item, 'values')
            if len(values) >= 4:
                # Status is now at index 3 (store, ap_id, pings, status, result)
                if values[3] == 'Success':
                    success_count += 1
                elif values[3] == 'Failed':
                    failed_count += 1
        
        summary = f"Operation complete: {success_count} succeeded, {failed_count} failed"
        self._log_activity(summary, "success" if failed_count == 0 else "warning")
        self.progress_status.config(text=summary)
        
        messagebox.showinfo("Operation Complete", summary, parent=self.window)
    
    def _log_activity(self, message: str, level: str = "info"):
        """Add message to activity log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.activity_log.config(state='normal')
        self.activity_log.insert(tk.END, log_message, level)
        self.activity_log.see(tk.END)
        self.activity_log.config(state='disabled')


# Example usage for testing
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()
    
    # Create test database
    db = DatabaseManager()
    
    # Create window
    window = BatchOperationWindow(None, "Test Batch Operation", "test_user", db)
    window.window.mainloop()
