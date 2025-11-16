"""
AP Support System UI
Provides comprehensive support interface for managing ESL Access Points
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from database_manager import DatabaseManager
from typing import Dict, List, Optional
import io
import base64
import threading
from jira_search_ui import open_jira_search

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class IconHelper:
    """Helper class to create and cache icons using Material Symbols font or fallback."""
    
    _cache = {}
    _font_loaded = False
    
    # Icon character codes from Material Symbols
    ICON_CODES = {
        'edit_document': '\ue873',
        'add_comment': '\ue266',
        'forum': '\ue0bf',
        'cancel': '\ue5c9',
        'comment': '\ue0b9',
        'add_notes': '\ue89c',
        'play_arrow': '\ue037',
        'open_in_browser': '\ue89d',
        'terminal': '\ueb8e',
        'router': '\ue328',
        'visibility': '\ue8f4',
        'visibility_off': '\ue8f5'
    }
    
    @classmethod
    def _load_material_symbols_font(cls):
        """Try to load Material Symbols font. Returns font object or None."""
        if cls._font_loaded:
            return True
        
        try:
            import urllib.request
            import os
            
            # Check if font file exists locally
            font_path = os.path.join(os.path.dirname(__file__), "MaterialSymbolsOutlined.ttf")
            
            if not os.path.exists(font_path):
                # Download the font (using a direct link to the font file)
                print("Downloading Material Symbols font...")
                url = "https://github.com/google/material-design-icons/raw/master/variablefont/MaterialSymbolsOutlined%5BFILL%2CGRAD%2Copsz%2Cwght%5D.ttf"
                urllib.request.urlretrieve(url, font_path)
                print("Font downloaded successfully")
            
            cls._font_loaded = True
            return True
        except Exception as e:
            print(f"Could not load Material Symbols font: {e}")
            return False
    
    @classmethod
    def get_icon(cls, icon_name, size=20, color="#333333"):
        """Get icon as PhotoImage using Material Symbols font. Returns None if not available."""
        if not PIL_AVAILABLE:
            return None
        
        cache_key = f"{icon_name}_{size}_{color}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]
        
        try:
            from PIL import ImageDraw, ImageFont
            import os
            
            # Try to load Material Symbols font
            font_path = os.path.join(os.path.dirname(__file__), "MaterialSymbolsOutlined.ttf")
            
            if not os.path.exists(font_path):
                cls._load_material_symbols_font()
            
            if os.path.exists(font_path) and icon_name in cls.ICON_CODES:
                # Create image
                img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
                draw = ImageDraw.Draw(img)
                
                # Load font
                font = ImageFont.truetype(font_path, size)
                
                # Get icon character code
                icon_char = cls.ICON_CODES[icon_name]
                
                # Parse color
                if color.startswith('#'):
                    rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
                else:
                    rgb = (51, 51, 51)
                
                # Draw the icon
                draw.text((0, 0), icon_char, font=font, fill=rgb)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(img)
                cls._cache[cache_key] = photo
                return photo
            
        except Exception as e:
            print(f"Error creating font icon: {e}")
        
        # Fallback to simple drawn icon
        return None
    
    @classmethod
    def get_edit_icon(cls, size=20, color="#333333"):
        """Get edit icon - wrapper for backward compatibility."""
        return cls.get_icon('edit_document', size, color)
    
    @classmethod
    def get_reply_icon(cls, size=20, color="#333333"):
        """Get reply/add comment icon."""
        return cls.get_icon('add_comment', size, color)
    
    @classmethod
    def get_forum_icon(cls, size=20, color="#333333"):
        """Get forum icon for replies section."""
        return cls.get_icon('forum', size, color)
    
    @classmethod
    def get_cancel_icon(cls, size=20, color="#333333"):
        """Get cancel icon."""
        return cls.get_icon('cancel', size, color)
    
    @classmethod
    def get_comment_icon(cls, size=20, color="#333333"):
        """Get comment icon."""
        return cls.get_icon('comment', size, color)
    
    @classmethod
    def get_add_notes_icon(cls, size=20, color="#333333"):
        """Get add notes icon."""
        return cls.get_icon('add_notes', size, color)
    
    @classmethod
    def get_play_icon(cls, size=20, color="#333333"):
        """Get play arrow icon."""
        return cls.get_icon('play_arrow', size, color)
    
    @classmethod
    def get_browser_icon(cls, size=20, color="#333333"):
        """Get open in browser icon."""
        return cls.get_icon('open_in_browser', size, color)
    
    @classmethod
    def get_terminal_icon(cls, size=20, color="#333333"):
        """Get terminal icon."""
        return cls.get_icon('terminal', size, color)


class APSearchDialog:
    """Dialog for searching and selecting APs for support."""
    
    def __init__(self, parent, current_user: str, db_manager: DatabaseManager, on_select_callback=None):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("AP Support - Search")
        self.dialog.geometry("1100x800")
        self.dialog.configure(bg="#FFFFFF")
        self.dialog.transient(parent)
        # Don't use grab_set() to make it non-modal
        
        self.current_user = current_user
        self.db = db_manager
        self.selected_ap = None
        self.sort_column = None
        self.sort_reverse = False
        self.on_select_callback = on_select_callback
        
        self._create_ui()
        self._perform_search()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (1100 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (800 // 2)
        self.dialog.geometry(f"1100x800+{x}+{y}")
    
    def _create_ui(self):
        """Create the search UI."""
        # Main container
        container = tk.Frame(self.dialog, bg="#FFFFFF")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title with router icon
        title_frame = tk.Frame(container, bg="#FFFFFF")
        title_frame.pack(anchor="w", pady=(0, 20))
        
        # Router icon
        router_icon = IconHelper.get_icon('router', size=28, color='#333333')
        if router_icon:
            icon_label = tk.Label(title_frame, image=router_icon, bg="#FFFFFF")
            icon_label.image = router_icon
            icon_label.pack(side="left", padx=(0, 10))
        
        title_label = tk.Label(title_frame, text="Search Access Points", 
                              font=("Segoe UI", 16, "bold"), bg="#FFFFFF", fg="#333333")
        title_label.pack(side="left")
        
        # Search criteria frame
        search_frame = tk.Frame(container, bg="#FFFFFF", relief="flat", bd=0)
        search_frame.pack(fill="x", pady=(0, 20))
        
        # Inner padding
        search_inner = tk.Frame(search_frame, bg="#FFFFFF")
        search_inner.pack(fill="x", padx=20, pady=20)
        
        # Row 1: AP ID / IP Address
        row1 = tk.Frame(search_inner, bg="#FFFFFF")
        row1.pack(fill="x", pady=8)
        
        tk.Label(row1, text="AP ID / IP Address:", width=18, anchor="w", 
                font=("Segoe UI", 10), bg="#FFFFFF", fg="#333333").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(row1, textvariable=self.search_var, width=35, 
                               font=("Segoe UI", 10), relief="flat", bd=0,
                               highlightthickness=1, highlightbackground="#CCCCCC", 
                               highlightcolor="#007BFF")
        search_entry.pack(side="left", padx=5, ipady=5)
        search_entry.bind("<Return>", lambda e: self._perform_search())
        
        # Row 2: Store ID
        row2 = tk.Frame(search_inner, bg="#FFFFFF")
        row2.pack(fill="x", pady=8)
        
        tk.Label(row2, text="Store ID:", width=18, anchor="w",
                font=("Segoe UI", 10), bg="#FFFFFF", fg="#333333").pack(side="left")
        self.store_var = tk.StringVar()
        store_entry = tk.Entry(row2, textvariable=self.store_var, width=35,
                              font=("Segoe UI", 10), relief="flat", bd=0,
                              highlightthickness=1, highlightbackground="#CCCCCC",
                              highlightcolor="#007BFF")
        store_entry.pack(side="left", padx=5, ipady=5)
        store_entry.bind("<Return>", lambda e: self._perform_search())
        
        # Row 3: Support Status
        row3 = tk.Frame(search_inner, bg="#FFFFFF")
        row3.pack(fill="x", pady=8)
        
        tk.Label(row3, text="Support Status:", width=18, anchor="w",
                font=("Segoe UI", 10), bg="#FFFFFF", fg="#333333").pack(side="left")
        self.status_var = tk.StringVar(value="All")
        
        # Style combobox to match AP support window
        status_frame = tk.Frame(row3, bg="#FFFFFF", highlightthickness=1,
                               highlightbackground="#CCCCCC", highlightcolor="#007BFF")
        status_frame.pack(side="left", padx=5)
        status_combo = ttk.Combobox(status_frame, textvariable=self.status_var, width=31, 
                                   state="readonly", font=("Segoe UI", 10), height=10)
        status_combo['values'] = ("All", "active", "in_progress", "pending", "resolved", "closed")
        status_combo.pack(ipady=3)
        
        # Row 4: Jira Tickets
        row4 = tk.Frame(search_inner, bg="#FFFFFF")
        row4.pack(fill="x", pady=8)
        
        tk.Label(row4, text="Jira Tickets:", width=18, anchor="w",
                font=("Segoe UI", 10), bg="#FFFFFF", fg="#333333").pack(side="left")
        self.tickets_var = tk.StringVar(value="All")
        
        # Style combobox to match AP support window
        tickets_frame = tk.Frame(row4, bg="#FFFFFF", highlightthickness=1,
                                highlightbackground="#CCCCCC", highlightcolor="#007BFF")
        tickets_frame.pack(side="left", padx=5)
        tickets_combo = ttk.Combobox(tickets_frame, textvariable=self.tickets_var, width=31,
                                    state="readonly", font=("Segoe UI", 10), height=10)
        tickets_combo['values'] = ("All", "With Open Tickets", "Without Open Tickets")
        tickets_combo.pack(ipady=3)
        
        # Row 5: Search button (below other fields, aligned with input fields)
        row5 = tk.Frame(search_inner, bg="#FFFFFF")
        row5.pack(fill="x", pady=8)
        
        # Spacer to align with input fields
        tk.Label(row5, text="", width=18, bg="#FFFFFF").pack(side="left")
        
        # Search button
        search_btn = tk.Button(row5, text="Search", command=self._perform_search, 
                              bg="#007BFF", fg="white", cursor="hand2", padx=30, pady=10,
                              font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                              activebackground="#0056B3")
        search_btn.pack(side="left", padx=5)
        
        # Results frame
        results_frame = tk.Frame(container, bg="#FFFFFF", relief="flat", bd=0)
        results_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Results header
        results_header = tk.Frame(results_frame, bg="#FFFFFF")
        results_header.pack(fill="x", padx=20, pady=(15, 5))
        
        tk.Label(results_header, text="Search Results", font=("Segoe UI", 12, "bold"),
                bg="#FFFFFF", fg="#333333").pack(side="left")
        
        # Treeview for results
        tree_frame = tk.Frame(results_frame, bg="#FFFFFF")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        # Configure modern scrollbar style (match AP support window)
        style = ttk.Style()
        style.layout('Search.Vertical.TScrollbar',
            [('Vertical.Scrollbar.trough',
              {'children': [('Vertical.Scrollbar.thumb',
                           {'expand': '1', 'sticky': 'nswe'})],
               'sticky': 'ns'})]
        )
        style.configure('Search.Vertical.TScrollbar',
                       background='#E0E0E0',
                       troughcolor='#F5F5F5',
                       borderwidth=0,
                       arrowsize=0,
                       width=12)
        style.map('Search.Vertical.TScrollbar',
                 background=[('active', '#BDBDBD'), ('!active', '#E0E0E0')])
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", style='Search.Vertical.TScrollbar')
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Configure treeview style
        style = ttk.Style()
        style.configure("Search.Treeview", 
                       background="#FFFFFF",
                       foreground="#333333",
                       fieldbackground="#FFFFFF",
                       font=("Segoe UI", 9))
        style.configure("Search.Treeview.Heading",
                       font=("Segoe UI", 10, "bold"),
                       background="#F0F0F0",
                       foreground="#333333")
        style.map("Search.Treeview",
                 background=[('selected', '#007BFF')],
                 foreground=[('selected', 'white')])
        
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("ap_id", "store_id", "ip_address", "type", "status", "support_status", "tickets"),
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            style="Search.Treeview"
        )
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configure columns with sortable headers
        self.tree.heading("ap_id", text="AP ID", command=lambda: self._sort_by_column("ap_id"))
        self.tree.heading("store_id", text="Store ID", command=lambda: self._sort_by_column("store_id"))
        self.tree.heading("ip_address", text="IP Address", command=lambda: self._sort_by_column("ip_address"))
        self.tree.heading("type", text="Type", command=lambda: self._sort_by_column("type"))
        self.tree.heading("status", text="Status", command=lambda: self._sort_by_column("status"))
        self.tree.heading("support_status", text="Support Status", command=lambda: self._sort_by_column("support_status"))
        self.tree.heading("tickets", text="Open Tickets", command=lambda: self._sort_by_column("tickets"))
        
        self.tree.column("ap_id", width=120, anchor="w")
        self.tree.column("store_id", width=100, anchor="center")
        self.tree.column("ip_address", width=130, anchor="center")
        self.tree.column("type", width=100, anchor="w")
        self.tree.column("status", width=90, anchor="center")
        self.tree.column("support_status", width=130, anchor="center")
        self.tree.column("tickets", width=110, anchor="center")
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Double-click to open
        self.tree.bind("<Double-1>", self._on_double_click)
        
        # Buttons frame
        btn_frame = tk.Frame(container, bg="#FFFFFF")
        btn_frame.pack(fill="x", pady=(0, 0))
        
        # Result count label (left side)
        self.count_label = tk.Label(btn_frame, text="0 APs found", 
                                    font=("Segoe UI", 10), fg="#666666", bg="#FFFFFF")
        self.count_label.pack(side="left", padx=0)
        
        # Buttons (right side)
        tk.Button(btn_frame, text="Cancel", command=self.dialog.destroy, 
                 bg="#6C757D", fg="white", cursor="hand2", padx=30, pady=10,
                 font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                 activebackground="#5A6268").pack(side="right", padx=(10, 0))
        
        tk.Button(btn_frame, text="Open Selected", command=self._on_open, 
                 bg="#28A745", fg="white", cursor="hand2", padx=30, pady=10,
                 font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                 activebackground="#218838").pack(side="right")
    
    def _sort_by_column(self, col):
        """Sort treeview by column."""
        # Toggle sort direction if same column, else start with ascending
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
        self.sort_column = col
        
        # Get all items
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children('')]
        
        # Sort items
        try:
            # Try numeric sort for tickets column
            if col == "tickets":
                items.sort(key=lambda x: (x[0] == '-', int(x[0]) if x[0] != '-' else 0), reverse=self.sort_reverse)
            else:
                items.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse)
        except:
            items.sort(key=lambda x: str(x[0]).lower(), reverse=self.sort_reverse)
        
        # Rearrange items in sorted order
        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)
        
        # Update column headings to show sort direction
        for column in self.tree['columns']:
            heading_text = {
                'ap_id': 'AP ID',
                'store_id': 'Store ID',
                'ip_address': 'IP Address',
                'type': 'Type',
                'status': 'Status',
                'support_status': 'Support Status',
                'tickets': 'Open Tickets'
            }.get(column, column)
            
            if column == col:
                arrow = ' ▼' if self.sort_reverse else ' ▲'
                self.tree.heading(column, text=heading_text + arrow)
            else:
                self.tree.heading(column, text=heading_text)
    
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
            # Call callback if provided (for non-modal usage)
            if self.on_select_callback:
                self.on_select_callback(ap)
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
        self.window.geometry("1100x700")
        
        self.ap = ap
        self.ap_id = ap_id
        self.current_user = current_user
        self.db = db_manager
        self.browser_helper = browser_helper
        
        # Each window gets its own browser driver instance
        self.driver = None
        self.browser_connected = False
        
        # Configure modern scrollbar style
        self._configure_scrollbar_style()
        
        # Register this window
        APSupportWindow._open_windows[ap_id] = self
        
        # Reload AP data from database to get the latest information (for multi-user scenarios)
        latest_ap = self.db.get_access_point(ap_id)
        if latest_ap:
            self.ap = latest_ap
        
        # Log audit: AP support window opened
        self.db.log_user_activity(
            username=current_user,
            activity_type='ap_support_open',
            description=f'Opened AP support window for {ap_id}',
            ap_id=ap_id,
            success=True
        )
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Configure modern scrollbar style
        self._configure_scrollbar_style()
        
        self._create_ui()
        self._load_data()
        
        # Start auto-refresh timer (every 10 seconds)
        self._auto_refresh()
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (1100 // 2)
        y = (self.window.winfo_screenheight() // 2) - (700 // 2)
        self.window.geometry(f"1100x700+{x}+{y}")
    
    def _configure_scrollbar_style(self):
        """Configure modern scrollbar styling."""
        style = ttk.Style()
        
        # Create custom scrollbar style with modern look
        style.theme_use('clam')  # Use clam theme as base for customization
        
        # Configure vertical scrollbar
        style.configure("Modern.Vertical.TScrollbar",
                       gripcount=0,
                       background="#C0C0C0",
                       darkcolor="#C0C0C0",
                       lightcolor="#C0C0C0",
                       troughcolor="#F5F5F5",
                       bordercolor="#F5F5F5",
                       arrowcolor="#808080",
                       width=10)
        
        # Configure scrollbar states for hover effect
        style.map("Modern.Vertical.TScrollbar",
                 background=[('active', '#A0A0A0'), ('!active', '#C0C0C0')],
                 arrowcolor=[('active', '#606060'), ('!active', '#808080')])
    
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
        style.configure("APSupport.TLabelframe", background=frame_bg, borderwidth=0, 
                       relief="flat")
        style.configure("APSupport.TLabelframe.Label", background=frame_bg, foreground="#333333", 
                       font=("Segoe UI", 11, "bold"))
        
        # Main container with padding
        main_container = ttk.Frame(self.window, padding=15, style="APSupport.TFrame")
        main_container.pack(fill="both", expand=True)
        
        # LEFT COLUMN
        left_column = ttk.Frame(main_container, style="APSupport.TFrame")
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # VERTICAL SEPARATOR with margin
        separator_container = tk.Frame(main_container, bg=frame_bg)
        separator_container.pack(side="left", fill="y", padx=5)
        
        tk.Frame(separator_container, bg=frame_bg, height=10).pack(side="top")
        tk.Frame(separator_container, bg="#CCCCCC", width=1).pack(side="top", fill="y", expand=True)
        tk.Frame(separator_container, bg=frame_bg, height=10).pack(side="bottom")
        
        # RIGHT COLUMN
        right_column = ttk.Frame(main_container, style="APSupport.TFrame", width=400)
        right_column.pack(side="right", fill="both", padx=(10, 0))
        right_column.pack_propagate(False)
        
        # === LEFT TOP: AP Information Section ===
        info_frame = ttk.LabelFrame(left_column, text="AP Information", padding=15, 
                                    style="APSupport.TLabelframe")
        info_frame.pack(fill="x", pady=(0, 5))
        
        # Create info grid
        info_grid = ttk.Frame(info_frame, style="APSupport.TFrame")
        info_grid.pack(fill="x")
        
        # Configure grid columns to expand properly
        info_grid.columnconfigure(1, weight=1)  # Left value column
        info_grid.columnconfigure(3, weight=1)  # Right value column
        
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
            
            # Use Entry widget for selectable/copyable text
            value_entry = tk.Entry(info_grid, font=("Segoe UI", 9), bg=frame_bg, 
                                  relief="flat", bd=0, readonlybackground=frame_bg,
                                  state="readonly", cursor="xterm", fg="#333333")
            value_entry.grid(row=row, column=col+1, sticky="ew", padx=5, pady=3)
            self.info_labels[field] = value_entry
        
        # Action buttons row at bottom of AP Information
        action_row = tk.Frame(info_frame, bg=frame_bg)
        action_row.pack(fill="x", pady=(10, 0))
        
        # Left side: Check Connection button and result label
        left_actions = tk.Frame(action_row, bg=frame_bg)
        left_actions.pack(side="left", fill="x", expand=True)
        
        tk.Button(left_actions, text="Check Connection", command=self._check_connection,
                 bg="#17A2B8", fg="white", cursor="hand2", padx=15, pady=6,
                 font=("Segoe UI", 9), relief="flat", bd=0,
                 activebackground="#138496").pack(side="left", padx=(0, 10))
        
        self.ping_result_label = tk.Label(left_actions, text="", font=("Segoe UI", 9), 
                                          bg=frame_bg, anchor="w", fg="#333333")
        self.ping_result_label.pack(side="left", fill="x", expand=True)
        
        # Right side: Show All button
        tk.Button(action_row, text="Show All", command=self._show_all_fields,
                 bg="#6C757D", fg="white", cursor="hand2", padx=20, pady=6,
                 font=("Segoe UI", 9), relief="flat", bd=0,
                 activebackground="#5A6268").pack(side="right")
        
        # Separator line
        tk.Frame(left_column, bg="#CCCCCC", height=1).pack(fill="x", pady=5)
        
        # === LEFT: Status Section ===
        status_frame = ttk.LabelFrame(left_column, text="Status", padding=15, 
                                      style="APSupport.TLabelframe")
        status_frame.pack(fill="x", pady=(0, 5))
        
        status_inner = ttk.Frame(status_frame, style="APSupport.TFrame")
        status_inner.pack(fill="x")
        
        tk.Label(status_inner, text="Support Status:", font=("Segoe UI", 9, "bold"), 
                bg=frame_bg).pack(side="left")
        self.support_status_var = tk.StringVar(value=self.ap.get('support_status', '') if self.ap.get('support_status') else '')
        status_combo = ttk.Combobox(status_inner, textvariable=self.support_status_var, 
                                    width=15, state="readonly", font=("Segoe UI", 10), height=12)
        status_combo['values'] = ("", "active", "in_progress", "pending", "resolved", "closed")
        status_combo.pack(side="left", padx=(10, 5), ipady=4)
        
        tk.Button(status_inner, text="Save", command=self._on_status_change,
                 bg="#28A745", fg="white", cursor="hand2", padx=20, pady=6,
                 font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                 activebackground="#218838").pack(side="left", padx=5)
        
        # Separator line
        tk.Frame(left_column, bg="#CCCCCC", height=1).pack(fill="x", pady=5)
        
        # === LEFT MIDDLE: Placeholder for future features ===
        middle_frame = ttk.Frame(left_column, style="APSupport.TFrame", height=100)
        middle_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # === LEFT BOTTOM: Connection Section ===
        connections_container = ttk.Frame(left_column, style="APSupport.TFrame")
        connections_container.pack(fill="x", pady=(0, 5))
        
        # Web Connection
        web_header_frame = tk.Frame(connections_container, bg=frame_bg)
        web_header_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        web_icon_frame = tk.Frame(web_header_frame, bg=frame_bg)
        web_icon_frame.pack(fill="x", pady=(0, 5))
        
        browser_icon = IconHelper.get_browser_icon(size=20, color="#424242")
        if browser_icon:
            icon_label = tk.Label(web_icon_frame, image=browser_icon, bg=frame_bg)
            icon_label.image = browser_icon
            icon_label.pack(side="left", padx=(0, 5))
        
        tk.Label(web_icon_frame, text="Web", font=("Segoe UI", 10, "bold"), 
                bg=frame_bg, fg="#333333").pack(side="left")
        
        # Spacer to push visibility icons to the right
        tk.Frame(web_icon_frame, bg=frame_bg).pack(side="left", fill="x", expand=True)
        
        # Browser visibility icons (on same row as Web heading)
        # Show browser icon
        show_icon = IconHelper.get_icon('visibility', size=20, color='#007BFF')
        if show_icon:
            self.show_browser_btn = tk.Label(web_icon_frame, image=show_icon, bg=frame_bg, cursor="hand2")
            self.show_browser_btn.image = show_icon
            self.show_browser_btn.pack(side="left", padx=(0, 8))
            self.show_browser_btn.bind("<Button-1>", lambda e: self._show_browser())
            self._create_tooltip(self.show_browser_btn, "Show")
            # Disable initially by making it transparent
            self.show_browser_enabled = False
        
        # Hide browser icon
        hide_icon = IconHelper.get_icon('visibility_off', size=20, color='#6C757D')
        if hide_icon:
            self.hide_browser_btn = tk.Label(web_icon_frame, image=hide_icon, bg=frame_bg, cursor="hand2")
            self.hide_browser_btn.image = hide_icon
            self.hide_browser_btn.pack(side="left")
            self.hide_browser_btn.bind("<Button-1>", lambda e: self._hide_browser())
            self._create_tooltip(self.hide_browser_btn, "Hide")
            # Disable initially by making it transparent
            self.hide_browser_enabled = False
        
        web_frame = tk.Frame(web_header_frame, bg=frame_bg)
        web_frame.pack(fill="both", expand=True)
        
        web_control_frame = tk.Frame(web_frame, bg=frame_bg)
        web_control_frame.pack(fill="x")
        
        self.web_action_var = tk.StringVar(value="Choose action")
        self.web_action_combo = ttk.Combobox(web_control_frame, textvariable=self.web_action_var,
                                             state="readonly", width=25, font=("Segoe UI", 10), height=12)
        self.web_action_combo['values'] = (
            "Choose action",
            "Open Web UI",
            "Navigate to Status",
            "Work with Provisioning",
            "Work with SSH",
            "Do a Software Update",
            "Show Log"
        )
        self.web_action_combo.pack(side="left", fill="x", expand=True, padx=(0, 5), ipady=4)
        self.web_action_combo.bind("<<ComboboxSelected>>", self._on_web_action_change)
        
        play_icon = IconHelper.get_play_icon(size=20, color="#FFFFFF")
        if play_icon:
            self.web_run_btn = tk.Button(web_control_frame, image=play_icon, command=self._run_web_action,
                                         bg="#007BFF", fg="white", cursor="hand2", relief="flat", bd=0,
                                         state="disabled", activebackground="#0056b3", width=40, height=30)
            self.web_run_btn.image = play_icon
            self._create_tooltip(self.web_run_btn, "Start Web")
        else:
            self.web_run_btn = tk.Button(web_control_frame, text="Run", command=self._run_web_action,
                                         bg="#007BFF", fg="white", cursor="hand2", padx=20, pady=6,
                                         font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                                         state="disabled", disabledforeground="white", activebackground="#0056b3")
        self.web_run_btn.pack(side="left")
        
        # Track browser state
        self.browser_connected = False
        
        # Track SSH state
        self.ssh_connected = False
        self.ssh_window_id = f"ap_{self.ap_id}"  # Unique ID for this AP's SSH window
        
        # Vertical separator between Web and SSH
        separator = tk.Frame(connections_container, bg="#CCCCCC", width=1)
        separator.pack(side="left", fill="y", padx=10)
        
        # SSH Connection
        ssh_header_frame = tk.Frame(connections_container, bg=frame_bg)
        ssh_header_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))
        
        ssh_icon_frame = tk.Frame(ssh_header_frame, bg=frame_bg)
        ssh_icon_frame.pack(fill="x", pady=(0, 5))
        
        terminal_icon = IconHelper.get_terminal_icon(size=20, color="#424242")
        if terminal_icon:
            icon_label = tk.Label(ssh_icon_frame, image=terminal_icon, bg=frame_bg)
            icon_label.image = terminal_icon
            icon_label.pack(side="left", padx=(0, 5))
        
        tk.Label(ssh_icon_frame, text="SSH", font=("Segoe UI", 10, "bold"), 
                bg=frame_bg, fg="#333333").pack(side="left")
        
        # Spacer to push visibility icons to the right
        tk.Frame(ssh_icon_frame, bg=frame_bg).pack(side="left", fill="x", expand=True)
        
        # SSH visibility icons (on same row as SSH heading)
        # Show SSH terminal icon
        show_ssh_icon = IconHelper.get_icon('visibility', size=20, color='#007BFF')
        if show_ssh_icon:
            self.show_ssh_btn = tk.Label(ssh_icon_frame, image=show_ssh_icon, bg=frame_bg, cursor="hand2")
            self.show_ssh_btn.image = show_ssh_icon
            self.show_ssh_btn.pack(side="left", padx=(0, 8))
            self.show_ssh_btn.bind("<Button-1>", lambda e: self._show_ssh())
            self._create_tooltip(self.show_ssh_btn, "Show SSH Terminal")
            # Disable initially by making it transparent
            self.show_ssh_enabled = False
        
        # Hide SSH terminal icon
        hide_ssh_icon = IconHelper.get_icon('visibility_off', size=20, color='#6C757D')
        if hide_ssh_icon:
            self.hide_ssh_btn = tk.Label(ssh_icon_frame, image=hide_ssh_icon, bg=frame_bg, cursor="hand2")
            self.hide_ssh_btn.image = hide_ssh_icon
            self.hide_ssh_btn.pack(side="left")
            self.hide_ssh_btn.bind("<Button-1>", lambda e: self._hide_ssh())
            self._create_tooltip(self.hide_ssh_btn, "Hide SSH Terminal")
            # Disable initially by making it transparent
            self.hide_ssh_enabled = False
        
        ssh_frame = tk.Frame(ssh_header_frame, bg=frame_bg)
        ssh_frame.pack(fill="both", expand=True)
        
        ssh_control_frame = tk.Frame(ssh_frame, bg=frame_bg)
        ssh_control_frame.pack(fill="x")
        
        self.ssh_action_var = tk.StringVar(value="Choose action")
        self.ssh_action_combo = ttk.Combobox(ssh_control_frame, textvariable=self.ssh_action_var,
                                            state="readonly", width=25, font=("Segoe UI", 10), height=12)
        self.ssh_action_combo['values'] = (
            "Choose action",
            "Connect",
            "Check available space",
            "Remove old logfiles",
            "Download log files"
        )
        self.ssh_action_combo.pack(side="left", fill="x", expand=True, padx=(0, 5), ipady=4)
        self.ssh_action_combo.bind("<<ComboboxSelected>>", self._on_ssh_action_change)
        
        play_icon_ssh = IconHelper.get_play_icon(size=20, color="#FFFFFF")
        if play_icon_ssh:
            self.ssh_run_btn = tk.Button(ssh_control_frame, image=play_icon_ssh, command=self._run_ssh_action,
                                         bg="#6C757D", fg="white", cursor="hand2", relief="flat", bd=0,
                                         state="disabled", activebackground="#5A6268", width=40, height=30)
            self.ssh_run_btn.image = play_icon_ssh
            self._create_tooltip(self.ssh_run_btn, "Start SSH")
        else:
            self.ssh_run_btn = tk.Button(ssh_control_frame, text="Run", command=self._run_ssh_action,
                                         bg="#6C757D", fg="white", cursor="hand2", padx=20, pady=6,
                                         font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                                         state="disabled", disabledforeground="white", activebackground="#5A6268")
        self.ssh_run_btn.pack(side="left")
        
        # Separator line
        tk.Frame(left_column, bg="#CCCCCC", height=1).pack(fill="x", pady=5)
        
        # === Activity Log ===
        activity_frame = ttk.LabelFrame(left_column, text="Activity", padding=10,
                                        style="APSupport.TLabelframe")
        activity_frame.pack(fill="x")
        
        self.activity_text = tk.Text(activity_frame, height=5, font=("Consolas", 8),
                                     bg="#F8F9FA", fg="#333333", wrap=tk.WORD,
                                     relief="flat", state="disabled")
        self.activity_text.pack(fill="x")
        
        # Add initial message
        self._log_activity("Ready")
        
        # === RIGHT TOP: Notes Section ===
        notes_frame = ttk.Frame(right_column, style="APSupport.TFrame", height=280)
        notes_frame.pack(fill="x", pady=(0, 10))
        notes_frame.pack_propagate(False)
        
        # Notes header
        notes_header = tk.Frame(notes_frame, bg=frame_bg)
        notes_header.pack(fill="x", pady=(0, 10))
        
        tk.Label(notes_header, text="Notes", font=("Segoe UI", 11, "bold"),
                bg=frame_bg, fg="#333333").pack(side="left")
        
        add_notes_icon = IconHelper.get_add_notes_icon(size=30, color="#FFFFFF")
        if add_notes_icon:
            add_note_btn = tk.Button(notes_header, image=add_notes_icon, command=self._open_write_note_dialog,
                                    bg="#28A745", fg="white", cursor="hand2", relief="flat", bd=0,
                                    activebackground="#218838", width=40, height=40)
            add_note_btn.image = add_notes_icon
            add_note_btn.pack(side="right")
            self._create_tooltip(add_note_btn, "Add note")
        else:
            tk.Button(notes_header, text="Write Note", command=self._open_write_note_dialog,
                     bg="#28A745", fg="white", cursor="hand2", padx=15, pady=6,
                     font=("Segoe UI", 9, "bold"), relief="flat", bd=0,
                     activebackground="#218838").pack(side="right")
        
        # Thin separator line
        tk.Frame(notes_frame, bg="#CCCCCC", height=1).pack(fill="x", pady=(0, 10))
        
        # Notes list container with scrollbar
        notes_list_frame = tk.Frame(notes_frame, bg=frame_bg)
        notes_list_frame.pack(fill="both", expand=True)
        
        # Notes list with scrollbar (2-row format: date/user, then headline)
        notes_canvas = tk.Canvas(notes_list_frame, bg=frame_bg, highlightthickness=0)
        notes_scroll = tk.Scrollbar(notes_list_frame, orient="vertical", command=notes_canvas.yview,
                                   bg="#F5F5F5", troughcolor="#F5F5F5", width=12,
                                   activebackground="#CCCCCC", bd=0, relief="flat")
        self.notes_container = tk.Frame(notes_canvas, bg=frame_bg)
        
        # Bind container size changes
        def _update_scroll_region(event):
            notes_canvas.configure(scrollregion=notes_canvas.bbox("all"))
            # Set canvas window width to match canvas width minus scrollbar
            canvas_width = notes_canvas.winfo_width()
            notes_canvas.itemconfig(notes_window, width=canvas_width)
        
        self.notes_container.bind("<Configure>", _update_scroll_region)
        notes_canvas.bind("<Configure>", _update_scroll_region)
        
        notes_window = notes_canvas.create_window((0, 0), window=self.notes_container, anchor="nw")
        notes_canvas.configure(yscrollcommand=notes_scroll.set)
        
        notes_canvas.pack(side="left", fill="both", expand=True)
        notes_scroll.pack(side="right", fill="y", padx=(2, 0))
        
        # Mouse wheel scrolling for notes - only when hovering over the canvas
        def _on_notes_mousewheel(event):
            notes_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_notes_mousewheel(event):
            notes_canvas.bind("<MouseWheel>", _on_notes_mousewheel)
        
        def _unbind_notes_mousewheel(event):
            notes_canvas.unbind("<MouseWheel>")
        
        notes_canvas.bind("<Enter>", _bind_notes_mousewheel)
        notes_canvas.bind("<Leave>", _unbind_notes_mousewheel)
        
        # Store notes data
        self.notes_data = []
        self.note_widgets = []
        self.note_window = None
        self.note_window_modified = False
        
        # === RIGHT MIDDLE: Jira Tickets Placeholder ===
        jira_frame = ttk.LabelFrame(right_column, text="Jira Tickets", padding=10, 
                                    style="APSupport.TLabelframe")
        jira_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        tk.Label(jira_frame, text="Jira integration coming soon...", 
                font=("Segoe UI", 9, "italic"), fg="#888888", bg=frame_bg).pack()
        
        # Separator line
        tk.Frame(right_column, bg="#CCCCCC", height=1).pack(fill="x", pady=5)
        
        # === RIGHT BOTTOM: Action Buttons ===
        action_frame = ttk.Frame(right_column, style="APSupport.TFrame")
        action_frame.pack(fill="x")
        
        tk.Button(action_frame, text="Search Jira Issues", command=self._open_jira_search,
                 bg="#0052CC", fg="white", cursor="hand2", padx=20, pady=10,
                 font=("Segoe UI", 10), relief="flat", bd=0,
                 activebackground="#0747A6").pack(fill="x", pady=(0, 5))
        
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
        # Populate info entry widgets
        for field, entry in self.info_labels.items():
            value = self.ap.get(field, '')
            entry.config(state="normal")
            entry.delete(0, tk.END)
            if value:
                entry.insert(0, str(value))
                entry.config(foreground="#333333")
            else:
                entry.insert(0, "-")
                entry.config(foreground="gray")
            entry.config(state="readonly")
        
        # Update support status
        self.support_status_var.set(self.ap.get('support_status', 'active'))
        
        # Load support notes
        self._refresh_notes()
    
    def _auto_refresh(self):
        """Auto-refresh data from database every 10 seconds."""
        if not self.window.winfo_exists():
            return  # Window closed, stop refreshing
        
        # Reload AP from database
        updated_ap = self.db.get_access_point(self.ap_id)
        if updated_ap:
            self.ap = updated_ap
            
            # Update all info entry widgets
            for field, entry in self.info_labels.items():
                value = self.ap.get(field, '')
                entry.config(state="normal")
                entry.delete(0, tk.END)
                if value:
                    entry.insert(0, str(value))
                    entry.config(foreground="#333333")
                else:
                    entry.insert(0, "-")
                    entry.config(foreground="gray")
                entry.config(state="readonly")
            
            # Update support status
            self.support_status_var.set(self.ap.get('support_status', 'active'))
            
            # Refresh notes
            self._refresh_notes()
        
        # Schedule next refresh in 10 seconds
        self.window.after(10000, self._auto_refresh)
    
    def _refresh_ap_data(self):
        """Manually refresh AP data from database."""
        # Reload AP from database
        updated_ap = self.db.get_access_point(self.ap_id)
        if updated_ap:
            self.ap = updated_ap
            
            # Update all info entry widgets
            for field, entry in self.info_labels.items():
                value = self.ap.get(field, '')
                entry.config(state="normal")
                entry.delete(0, tk.END)
                if value:
                    entry.insert(0, str(value))
                    entry.config(foreground="#333333")
                else:
                    entry.insert(0, "-")
                    entry.config(foreground="gray")
                entry.config(state="readonly")
            
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
            note_frame = tk.Frame(self.notes_container, bg="#FFFFFF", cursor="hand2")
            note_frame.pack(fill="x", pady=3, padx=0)
            
            # Row 1: Date/Time, User, and Reply count
            row1_frame = tk.Frame(note_frame, bg="#FFFFFF")
            row1_frame.pack(fill="x", padx=0, pady=(5, 0))
            
            tk.Label(row1_frame, text=f"{note['created_at']} - {note['user']}", 
                    font=("Segoe UI", 8), fg="#888888", bg="#FFFFFF", anchor="w").pack(side="left")
            
            # Get reply count
            reply_count = self.db.get_note_reply_count(note['id'])
            if reply_count > 0:
                reply_frame = tk.Frame(row1_frame, bg="#FFFFFF")
                reply_frame.pack(side="right", padx=5)
                
                comment_icon = IconHelper.get_comment_icon(size=12, color="#007BFF")
                if comment_icon:
                    icon_label = tk.Label(reply_frame, image=comment_icon, bg="#FFFFFF")
                    icon_label.image = comment_icon
                    icon_label.pack(side="left", padx=(0, 3))
                
                tk.Label(reply_frame, text=str(reply_count), 
                        font=("Segoe UI", 8), fg="#007BFF", bg="#FFFFFF").pack(side="left")
            
            # Row 2: Headline
            row2 = tk.Label(note_frame, text=note['headline'], 
                          font=("Segoe UI", 9, "bold"), bg="#FFFFFF", anchor="w", fg="#333333")
            row2.pack(fill="x", padx=0, pady=(0, 5))
            
            # Add thin separator line after each note
            tk.Frame(note_frame, bg="#E0E0E0", height=1).pack(fill="x", pady=(5, 0))
            
            # Bind click events
            for widget in [note_frame, row1_frame, row2]:
                widget.bind("<Button-1>", lambda e, n=note: self._open_note_window(n))
                for child in widget.winfo_children():
                    child.bind("<Button-1>", lambda e, n=note: self._open_note_window(n))
            
            self.note_widgets.append(note_frame)
    
    def _check_connection(self):
        """Ping the AP IP address 4 times and display result."""
        ip_address = self.ap.get('ip_address', '')
        if not ip_address:
            self.ping_result_label.config(text="No IP address available", fg="#DC3545")
            return
        
        # Log audit: connection check started
        self.db.log_user_activity(
            username=self.current_user,
            activity_type='ap_connection_check',
            description=f'Checking connection to {ip_address}',
            ap_id=self.ap_id,
            success=True
        )
        
        self.ping_result_label.config(text="Pinging...", fg="#888888")
        self.window.update_idletasks()
        
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
                for line in output_lines:
                    if 'Average' in line or 'avg' in line:
                        self.ping_result_label.config(text=f"✓ Connected - {line.strip()}", fg="#28A745")
                        return
                self.ping_result_label.config(text="✓ Connected (4/4 packets received)", fg="#28A745")
            else:
                self.ping_result_label.config(text="✗ Connection failed", fg="#DC3545")
        except subprocess.TimeoutExpired:
            self.ping_result_label.config(text="✗ Timeout", fg="#DC3545")
        except Exception as e:
            self.ping_result_label.config(text=f"✗ Error: {str(e)}", fg="#DC3545")
    
    def _show_all_fields(self):
        """Open a window showing all collected AP fields."""
        # Create new window
        all_fields_window = tk.Toplevel(self.window)
        all_fields_window.title(f"All Fields - {self.ap_id}")
        all_fields_window.geometry("800x600")
        all_fields_window.configure(bg="#F5F5F5")
        
        # Center window
        all_fields_window.update_idletasks()
        x = (all_fields_window.winfo_screenwidth() // 2) - (800 // 2)
        y = (all_fields_window.winfo_screenheight() // 2) - (600 // 2)
        all_fields_window.geometry(f"800x600+{x}+{y}")
        
        # Main container
        container = tk.Frame(all_fields_window, bg="#FFFFFF")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title (fixed at top)
        title_frame = tk.Frame(container, bg="#FFFFFF")
        title_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        tk.Label(title_frame, text=f"All Collected Fields for {self.ap_id}", 
                font=("Segoe UI", 14, "bold"), bg="#FFFFFF", fg="#333333").pack(anchor="w")
        
        # Separator line
        tk.Frame(container, bg="#CCCCCC", height=1).pack(fill="x", padx=20)
        
        # Scrollable content area
        content_frame = tk.Frame(container, bg="#FFFFFF")
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(content_frame, bg="#FFFFFF", highlightthickness=0)
        scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#FFFFFF")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Unbind on window close to avoid conflicts
        all_fields_window.protocol("WM_DELETE_WINDOW", lambda: (canvas.unbind_all("<MouseWheel>"), all_fields_window.destroy()))
        
        # Display all AP data fields with selectable text
        for idx, (key, value) in enumerate(sorted(self.ap.items())):
            row_frame = tk.Frame(scrollable_frame, bg="#F8F9FA" if idx % 2 == 0 else "#FFFFFF")
            row_frame.pack(fill="x", pady=1)
            
            # Key label
            key_label = tk.Label(row_frame, text=f"{key}:", font=("Segoe UI", 9, "bold"), 
                                anchor="w", width=25, bg=row_frame['bg'], padx=10, pady=5)
            key_label.pack(side="left")
            
            # Mask password fields
            display_value = value
            if 'password' in key.lower() and value:
                display_value = "**********"
            
            # Value as Text widget for copy functionality
            value_text = tk.Text(row_frame, font=("Segoe UI", 9), height=1, wrap="word",
                                bg=row_frame['bg'], relief="flat", bd=0, cursor="xterm",
                                highlightthickness=0)
            value_text.insert("1.0", str(display_value) if display_value else "-")
            value_text.config(state="disabled")  # Make read-only but still selectable
            value_text.pack(side="left", fill="x", expand=True, padx=10, pady=5)
            
            # Auto-adjust height based on content
            def adjust_height(widget, event=None):
                widget.configure(height=int(widget.index('end-1c').split('.')[0]))
            value_text.bind("<Configure>", lambda e, w=value_text: adjust_height(w))
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Separator line
        tk.Frame(container, bg="#CCCCCC", height=1).pack(fill="x", padx=20)
        
        # Close button (fixed at bottom)
        button_frame = tk.Frame(container, bg="#FFFFFF")
        button_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        tk.Button(button_frame, text="Close", command=all_fields_window.destroy,
                 bg="#6C757D", fg="white", cursor="hand2", padx=30, pady=10,
                 font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                 activebackground="#5A6268").pack()
    
    def _on_status_change(self, event=None):
        """Handle support status change."""
        old_status = self.ap.get('support_status', '')
        new_status = self.support_status_var.get()
        success, message = self.db.update_support_status(self.ap_id, new_status)
        if success:
            # Log audit: status change
            self.db.log_user_activity(
                username=self.current_user,
                activity_type='ap_status_change',
                description=f'Changed status from "{old_status}" to "{new_status}"',
                ap_id=self.ap_id,
                success=True,
                details={'old_status': old_status, 'new_status': new_status}
            )
            self.ap['support_status'] = new_status
            messagebox.showinfo("Status Updated", f"Support status changed to: {new_status}", parent=self.window)
        else:
            messagebox.showerror("Error", f"Failed to update status: {message}", parent=self.window)
    
    def _on_web_action_change(self, event=None):
        """Enable/disable Run button based on web action selection."""
        if self.web_action_var.get() == "Choose action":
            self.web_run_btn.config(state="disabled")
        else:
            self.web_run_btn.config(state="normal")
    
    def _on_ssh_action_change(self, event=None):
        """Enable/disable Run button based on SSH action selection."""
        if self.ssh_action_var.get() == "Choose action":
            self.ssh_run_btn.config(state="disabled")
        else:
            self.ssh_run_btn.config(state="normal")
    
    def _log_activity(self, message):
        """Add message to activity log."""
        import time
        timestamp = time.strftime("%H:%M:%S")
        self.activity_text.config(state="normal")
        self.activity_text.insert("end", f"[{timestamp}] {message}\n")
        self.activity_text.see("end")
        self.activity_text.config(state="disabled")
        self.window.update_idletasks()
    
    def _run_web_action(self):
        """Execute the selected web action."""
        action = self.web_action_var.get()
        self._log_activity(f"Executing: {action}")
        
        # Log audit: web action
        self.db.log_user_activity(
            username=self.current_user,
            activity_type='ap_web_action',
            description=f'Web action: {action}',
            ap_id=self.ap_id,
            success=True,
            details={'action': action}
        )
        
        if action == "Open Web UI":
            self._connect_browser()
        elif action == "Navigate to Status":
            self._navigate_to_status()
        elif action == "Work with Provisioning":
            self._work_with_provisioning()
        elif action == "Work with SSH":
            self._work_with_ssh()
        elif action == "Do a Software Update":
            self._do_software_update()
        elif action == "Show Log":
            self._show_log()
    
    def _run_ssh_action(self):
        """Execute the selected SSH action."""
        action = self.ssh_action_var.get()
        
        if action == "Choose action":
            return
        
        self._log_activity(f"Executing: {action}")
        
        # Log audit: SSH action
        self.db.log_user_activity(
            username=self.current_user,
            activity_type='ap_ssh_action',
            description=f'SSH action: {action}',
            ap_id=self.ap_id,
            success=True,
            details={'action': action}
        )
        
        if action == "Connect":
            self._connect_ssh()
        elif action == "Check available space":
            self._ssh_check_space()
        elif action == "Remove old logfiles":
            self._ssh_remove_old_logs()
        elif action == "Download log files":
            self._ssh_download_logs()
    
    def _handle_cato_warning(self):
        """Handle Cato Networks warning if present."""
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            import time
            
            time.sleep(1)
            
            # Check for Cato warning elements
            page_source = self.driver.page_source.lower()
            has_warning = 'cato networks' in page_source or 'your connection is not private' in page_source
            has_ssl_error = 'ssl' in page_source or 'certificate' in page_source
            
            if has_warning or has_ssl_error:
                self._log_activity("🚨 Cato Networks warning detected, clicking PROCEED button...")
                
                # Try to find and click the PROCEED button
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
    
    def _show_browser(self):
        """Show the browser window."""
        if not hasattr(self, 'show_browser_enabled') or not self.show_browser_enabled:
            return
        if self.driver:
            try:
                # Use CDP to set window state to normal/maximized
                self.driver.execute_cdp_cmd('Browser.setWindowBounds', {
                    'windowId': self.driver.current_window_handle,
                    'bounds': {'windowState': 'normal'}
                })
                # Then maximize
                self.driver.maximize_window()
                self._log_activity("✓ Browser window shown")
            except Exception as e:
                # Fallback to simple maximize
                try:
                    self.driver.maximize_window()
                    self._log_activity("✓ Browser window shown")
                except:
                    self._log_activity(f"✗ Error showing browser: {str(e)}")
        else:
            messagebox.showwarning("Not Connected", "Browser is not open.", parent=self.window)
    
    def _hide_browser(self):
        """Hide/minimize the browser window."""
        if not hasattr(self, 'hide_browser_enabled') or not self.hide_browser_enabled:
            return
        if self.driver:
            try:
                # Use CDP to minimize window
                self.driver.execute_cdp_cmd('Browser.setWindowBounds', {
                    'windowId': self.driver.current_window_handle,
                    'bounds': {'windowState': 'minimized'}
                })
                self._log_activity("✓ Browser window hidden")
            except Exception as e:
                # Fallback to minimize_window method
                try:
                    self.driver.minimize_window()
                    self._log_activity("✓ Browser window hidden")
                except:
                    self._log_activity(f"✗ Error hiding browser: {str(e)}")
        else:
            messagebox.showwarning("Not Connected", "Browser is not open.", parent=self.window)
    
    def _enable_web_actions(self):
        """Enable additional web actions after successful browser connection."""
        self.browser_connected = True
        # Enable browser control icons
        self.show_browser_enabled = True
        self.hide_browser_enabled = True
        # Update icon colors to indicate enabled state
        if hasattr(self, 'show_browser_btn'):
            show_icon_enabled = IconHelper.get_icon('visibility', size=24, color='#28A745')
            if show_icon_enabled:
                self.show_browser_btn.config(image=show_icon_enabled)
                self.show_browser_btn.image = show_icon_enabled
        if hasattr(self, 'hide_browser_btn'):
            hide_icon_enabled = IconHelper.get_icon('visibility_off', size=24, color='#007BFF')
            if hide_icon_enabled:
                self.hide_browser_btn.config(image=hide_icon_enabled)
                self.hide_browser_btn.image = hide_icon_enabled
        # Note: All actions are now visible from the start, we just manage button state
        self._log_activity("✓ Browser connected - all actions available")
    
    def _navigate_to_status(self):
        """Navigate to status page and fetch information."""
        if not self.browser_connected:
            messagebox.showwarning("Not Connected", "Please open Web UI first.", parent=self.window)
            return
        
        ip = self.ap.get('ip_address', '')
        if not ip:
            self._log_activity("✗ Missing IP address")
            return
        
        self._log_activity("Navigating to Status page...")
        
        try:
            status_url = f"http://{ip}/service/status.xml"
            self._log_activity(f"Loading {status_url}")
            self.driver.get(status_url)
            
            # Wait for page to load completely
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            import time
            
            try:
                # Wait for table elements to be present (status.xml displays as HTML table)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
                time.sleep(2)  # Additional buffer for full render
            except:
                time.sleep(5)  # Fallback wait if explicit wait fails
            
            page_source = self.driver.page_source
            self._log_activity(f"✓ Status page loaded ({len(page_source)} bytes)")
            
            # Debug: Log a snippet to verify content
            if "AP ID" in page_source:
                self._log_activity("✓ Page contains expected fields")
            else:
                self._log_activity("⚠ Warning: Page may not have loaded correctly")
                self._log_activity(f"Debug: Page source preview: {page_source[:500]}")
            
            # Extract and save the data
            success = self._extract_and_save_status_data(page_source, ip)
            
            if success:
                messagebox.showinfo("Success", "AP information extracted and saved successfully.", parent=self.window)
            else:
                messagebox.showwarning("Extraction Failed", "Could not extract AP information from status page.", parent=self.window)
            
        except Exception as e:
            self._log_activity(f"✗ Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to navigate: {str(e)}", parent=self.window)
    
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
            
            # Debug: Log extracted values
            extracted_count = sum(1 for v in [ap_id, transmitter, store_id, serial_number, software_version, 
                                              firmware_version, hardware_revision, build, uptime, mac_address,
                                              service_status, communication_daemon_status] if v)
            self._log_activity(f"Extracted {extracted_count} fields from status page")
            
            if not ap_id:
                self._log_activity("✗ Could not extract AP ID from status page")
                return False
            
            self._log_activity(f"✓ AP ID: {ap_id}, SW: {software_version}, Service: {service_status}")
            
            # Update in database
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
                # Reload AP data from database to get all updated fields
                updated_ap = self.db.get_access_point(ap_id)
                if updated_ap:
                    self.ap = updated_ap
                    # Refresh UI to show the new data
                    self._load_data()
                    self._log_activity("✓ UI refreshed with extracted data")
                    return True
                else:
                    # Fallback to just updating with extracted data
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
    
    def _work_with_provisioning(self):
        """Work with provisioning settings."""
        if not self.browser_connected:
            messagebox.showwarning("Not Connected", "Please open Web UI first.", parent=self.window)
            return
        
        # Show dialog to get action (same as main window)
        from provisioning_dialog import ProvisioningDialog
        dialog = ProvisioningDialog(self.window)
        action = dialog.show()
        
        if action is None:  # User canceled
            self._log_activity("Provisioning operation canceled")
            return
        
        self._log_activity(f"Executing provisioning action: {action}")
        
        try:
            worker = self.browser_helper.worker
            result = worker.manage_provisioning(action)
            
            if result['status'] == 'success':
                self._log_activity(f"✓ {result['message']}")
                messagebox.showinfo("Success", result['message'], parent=self.window)
            else:
                self._log_activity(f"✗ {result['message']}")
                messagebox.showerror("Error", result['message'], parent=self.window)
                
        except Exception as e:
            self._log_activity(f"✗ Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to manage provisioning: {str(e)}", parent=self.window)
    
    def _work_with_ssh(self):
        """Configure SSH settings in web UI."""
        if not self.browser_connected or not self.driver:
            messagebox.showwarning("Not Connected", "Please open Web UI first.", parent=self.window)
            return
        
        # Show dialog to get action (same as main window)
        from ssh_dialog import SSHDialog
        dialog = SSHDialog(self.window)
        action = dialog.show()
        
        if action is None:  # User canceled
            self._log_activity("SSH operation canceled")
            return
        
        self._log_activity(f"Executing SSH action: {action}")
        
        # Run in background thread
        thread = threading.Thread(target=self._work_with_ssh_thread, args=(action,), daemon=True)
        thread.start()
    
    def _work_with_ssh_thread(self, action):
        """Background thread to manage SSH via browser."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
        
        try:
            # Navigate to SSH page
            ip_address = self.ap.get('ip_address', '')
            self.driver.get(f"http://{ip_address}/service/config/ssh.xml")
            time.sleep(3)
            
            # Try multiple strategies to find the SSH control elements
            radio_clicked = False
            
            if action == "enable":
                # Try different methods to find enable radio
                try:
                    # Method 1: By value attribute
                    enable_radio = self.driver.find_element(By.XPATH, "//input[@type='radio' and @value='enable']")
                    enable_radio.click()
                    radio_clicked = True
                except:
                    try:
                        # Method 2: By name and checking following text
                        radios = self.driver.find_elements(By.XPATH, "//input[@type='radio' and @name='enabled']")
                        for radio in radios:
                            # Check if this is the enable option (usually first one or has id/value)
                            if radio.get_attribute('value') in ['enable', 'true', '1'] or radios.index(radio) == 0:
                                radio.click()
                                radio_clicked = True
                                break
                    except:
                        pass
                        
            elif action == "disable":
                # Try different methods to find disable radio
                try:
                    # Method 1: By value attribute
                    disable_radio = self.driver.find_element(By.XPATH, "//input[@type='radio' and @value='disable']")
                    disable_radio.click()
                    radio_clicked = True
                except:
                    try:
                        # Method 2: By name and checking following text
                        radios = self.driver.find_elements(By.XPATH, "//input[@type='radio' and @name='enabled']")
                        for radio in radios:
                            # Check if this is the disable option (usually second one or has specific value)
                            if radio.get_attribute('value') in ['disable', 'false', '0'] or radios.index(radio) == 1:
                                radio.click()
                                radio_clicked = True
                                break
                    except:
                        pass
            
            if not radio_clicked:
                raise Exception(f"Could not find radio button for '{action}'")
            
            time.sleep(1)
            
            # Find and click Apply/Submit button
            button_clicked = False
            try:
                # Try finding submit button
                buttons = self.driver.find_elements(By.XPATH, "//input[@type='submit'] | //input[@type='button'] | //button")
                for button in buttons:
                    value = button.get_attribute('value') or button.text
                    if value and ('apply' in value.lower() or 'submit' in value.lower() or 'ok' in value.lower()):
                        button.click()
                        button_clicked = True
                        break
            except:
                pass
            
            if not button_clicked:
                raise Exception("Could not find Apply/Submit button")
            
            time.sleep(2)
            
            self.window.after(0, lambda: self._log_activity(f"✓ SSH {action}d successfully"))
            self.window.after(0, lambda: messagebox.showinfo("Success", f"SSH {action}d successfully", parent=self.window))
            
        except Exception as e:
            error_msg = str(e)
            # Simplify selenium stack trace errors
            if "Stacktrace:" in error_msg:
                error_msg = error_msg.split("Stacktrace:")[0].strip()
            if not error_msg:
                error_msg = "Could not locate SSH control elements on the page"
            
            self.window.after(0, lambda: self._log_activity(f"✗ Error: {error_msg}"))
            self.window.after(0, lambda: messagebox.showerror("Error", f"Failed to manage SSH: {error_msg}", parent=self.window))
    
    def _do_software_update(self):
        """Perform software update."""
        if not self.browser_connected:
            messagebox.showwarning("Not Connected", "Please open Web UI first.", parent=self.window)
            return
        
        ip = self.ap.get('ip_address', '')
        if not ip:
            self._log_activity("✗ Missing IP address")
            return
        
        self._log_activity("Navigating to software update page...")
        
        try:
            worker = self.browser_helper.worker
            update_url = f"http://{ip}/admin/updateSoftware.xml"
            self._log_activity(f"Loading {update_url}")
            worker.driver.get(update_url)
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
        if not self.browser_connected:
            messagebox.showwarning("Not Connected", "Please open Web UI first.", parent=self.window)
            return
        
        ip = self.ap.get('ip_address', '')
        if not ip:
            self._log_activity("✗ Missing IP address")
            return
        
        self._log_activity("Navigating to system log page...")
        
        try:
            worker = self.browser_helper.worker
            log_url = f"http://{ip}/service/config/system/viewLog.xml"
            self._log_activity(f"Loading {log_url}")
            worker.driver.get(log_url)
            import time
            time.sleep(2)
            
            self._log_activity("✓ System log page loaded")
            
        except Exception as e:
            self._log_activity(f"✗ Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to navigate: {str(e)}", parent=self.window)
    
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
        
        # Run browser connection in separate thread to avoid blocking UI
        import threading
        thread = threading.Thread(target=self._connect_browser_thread, args=(ip, username, password), daemon=True)
        thread.start()
    
    def _connect_browser_thread(self, ip, username, password):
        """Browser connection thread - runs in background."""
        try:
            # Use the exact same approach as Quick Connect
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
                    # Start browser minimized
                    options.add_argument('--start-minimized')
                    
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=options)
                    # Minimize window after creation
                    try:
                        self.driver.minimize_window()
                        self._log_activity("✓ Chrome driver initialized (minimized)")
                    except:
                        self._log_activity("✓ Chrome driver initialized")
                except Exception as e:
                    self._log_activity(f"Failed to initialize browser: {str(e)}")
                    self.window.after(0, lambda: messagebox.showerror("Error", f"Failed to initialize browser: {str(e)}", parent=self.window))
                    return
            
            # Login using CDP authentication (same as Quick Connect)
            try:
                # Set authentication via CDP
                self._log_activity(f"Setting up authentication for {ip}")
                self.driver.execute_cdp_cmd('Network.enable', {})
                auth_header = 'Basic ' + base64.b64encode(f'{username}:{password}'.encode()).decode()
                self.driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': {'Authorization': auth_header}})
                
                # Navigate to main page first
                url = f"http://{ip}"
                self._log_activity(f"Navigating to {url}")
                self.driver.get(url)
                time.sleep(2)
                
                # Check for and handle Cato Networks warning
                self._handle_cato_warning()
                
                self._log_activity(f"✓ Successfully authenticated to {ip}")
                
                # Navigate to status.xml to fetch AP information (same as Quick Connect)
                try:
                    status_url = f"http://{ip}/service/status.xml"
                    self._log_activity(f"Fetching AP information from {status_url}")
                    self.driver.get(status_url)
                    time.sleep(3)
                    
                    # Parse the information
                    page_source = self.driver.page_source
                    self._log_activity(f"✓ AP information retrieved")
                    
                    # Extract and save the data immediately
                    self._extract_and_save_status_data(page_source, ip)
                    
                except Exception as e:
                    self._log_activity(f"⚠ Could not fetch status info: {str(e)}")
                
                self._log_activity(f"✓ Browser opened for {self.ap_id}")
                # Enable web actions on main thread
                self.window.after(0, self._enable_web_actions)
                
            except Exception as e:
                self._log_activity(f"Authentication failed: {str(e)}")
                self.window.after(0, lambda: messagebox.showerror("Error", f"Authentication failed: {str(e)}", parent=self.window))
                return
                
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self._log_activity(f"✗ Error: {str(e)}")
            self.window.after(0, lambda: messagebox.showerror("Browser Error", 
                               f"Failed to open browser: {str(e)}\n\nDetails:\n{error_detail}", 
                               parent=self.window))
    
    def _connect_ssh(self):
        """Connect via SSH in a separate thread."""
        if self.ssh_connected:
            # Already connected, just show window
            self._show_ssh()
            return
        
        # Check if we have SSH credentials
        ip_address = self.ap.get('ip_address', '')
        ssh_username = self.ap.get('username_ssh', '')
        ssh_password = self.ap.get('password_ssh', '')
        
        if not ip_address:
            messagebox.showerror("No IP Address", "No IP address available for SSH connection.", parent=self.window)
            return
        
        if not ssh_username or not ssh_password:
            messagebox.showerror("No SSH Credentials", 
                               "SSH username or password not configured for this AP.", 
                               parent=self.window)
            return
        
        # Show connecting message
        self.ssh_action_combo.config(state="disabled")
        self.ssh_run_btn.config(state="disabled")
        
        # Connect in background thread
        thread = threading.Thread(target=self._connect_ssh_thread, daemon=True)
        thread.start()
    
    def _connect_ssh_thread(self):
        """Background thread for SSH connection."""
        from ssh_helper import SSHManager
        
        ip_address = self.ap.get('ip_address', '')
        ssh_username = self.ap.get('username_ssh', '')
        ssh_password = self.ap.get('password_ssh', '')
        
        # Attempt connection
        success, message = SSHManager.open_ssh_connection(
            parent=self.window,
            ap_id=self.ap_id,
            host=ip_address,
            username=ssh_username,
            password=ssh_password,
            window_id=self.ssh_window_id
        )
        
        # Update UI on main thread
        self.window.after(0, lambda: self._on_ssh_connected(success, message))
    
    def _on_ssh_connected(self, success: bool, message: str):
        """Handle SSH connection result (runs on main thread)."""
        if success:
            self.ssh_connected = True
            self._enable_ssh_actions()
            
            # Log audit
            self.db.log_user_activity(
                username=self.current_user,
                activity_type='ap_ssh_connect',
                description=f'Connected to SSH: {self.ap.get("ip_address")}',
                ap_id=self.ap_id,
                success=True
            )
        else:
            messagebox.showerror("SSH Connection Failed", message, parent=self.window)
            self.ssh_action_combo.config(state="readonly")
            self.ssh_run_btn.config(state="normal")
            
            # Log audit
            self.db.log_user_activity(
                username=self.current_user,
                activity_type='ap_ssh_connect',
                description=f'SSH connection failed: {message}',
                ap_id=self.ap_id,
                success=False
            )
    
    def _enable_ssh_actions(self):
        """Enable SSH controls after successful connection."""
        self.ssh_action_combo.config(state="readonly")
        self.ssh_run_btn.config(state="normal")
        
        # Enable visibility icons
        self.show_ssh_enabled = True
        self.hide_ssh_enabled = True
        
        # Update icon colors
        show_icon = IconHelper.get_icon('visibility', size=20, color='#28A745')  # Green
        if show_icon:
            self.show_ssh_btn.config(image=show_icon)
            self.show_ssh_btn.image = show_icon
        
        hide_icon = IconHelper.get_icon('visibility_off', size=20, color='#007BFF')  # Blue
        if hide_icon:
            self.hide_ssh_btn.config(image=hide_icon)
            self.hide_ssh_btn.image = hide_icon
    
    def _show_ssh(self):
        """Show the SSH terminal window."""
        if not self.show_ssh_enabled:
            return
        
        from ssh_helper import SSHManager
        
        # Show the window if it exists
        if self.ssh_window_id in SSHManager._windows:
            window = SSHManager._windows[self.ssh_window_id]
            window.show()
    
    def _hide_ssh(self):
        """Hide/minimize the SSH terminal window."""
        if not self.hide_ssh_enabled:
            return
        
        from ssh_helper import SSHManager
        
        # Minimize the window if it exists
        if self.ssh_window_id in SSHManager._windows:
            window = SSHManager._windows[self.ssh_window_id]
            window.window.iconify()
    
    def _ssh_check_space(self):
        """Check available space on the AP via SSH."""
        if not self.ssh_connected:
            # Need to connect first
            messagebox.showinfo("Connect First", "Please connect to SSH first.", parent=self.window)
            return
        
        # Run in background thread
        thread = threading.Thread(target=self._ssh_check_space_thread, daemon=True)
        thread.start()
    
    def _ssh_check_space_thread(self):
        """Background thread to check disk space."""
        from ssh_helper import SSHManager
        import time
        
        if self.ssh_window_id not in SSHManager._windows:
            return
        
        window = SSHManager._windows[self.ssh_window_id]
        if self.ap_id not in window.tabs:
            return
        
        tab = window.tabs[self.ap_id]
        connection = tab.connection
        
        if not connection.connected:
            return
        
        # Try to run df -h command
        connection.send_command("df -h")
        time.sleep(3)
        
        # Get output from automation buffer and check if we're in service mode
        output = connection.get_automation_output(1000)
        
        # Check if command failed due to service mode
        if "unknown command" in output.lower() or ("fail" in output.lower() and "servicemode>" in output.lower()):
            self.window.after(0, lambda: self._log_activity("⚠️ Service mode detected, exiting and retrying..."))
            
            # Exit service mode and retry
            if not self._ssh_exit_service_mode_if_needed_v2(connection):
                self.window.after(0, lambda: self._log_activity("✗ Failed to exit service mode"))
                return
            
            # Retry the command
            time.sleep(2)
            connection.send_command("df -h")
            time.sleep(3)
            output = connection.get_automation_output(1000)
        
        # Log to activity
        self.window.after(0, lambda o=output: self._log_activity(f"Disk space check:\n{o}"))
    
    def _ssh_remove_old_logs(self):
        """Remove old log files from the AP via SSH."""
        if not self.ssh_connected:
            messagebox.showinfo("Connect First", "Please connect to SSH first.", parent=self.window)
            return
        
        # Confirm action
        if not messagebox.askyesno("Confirm", 
                                   "This will remove old log files (matching *20*log*).\n\nContinue?",
                                   parent=self.window):
            return
        
        # Run in background thread
        thread = threading.Thread(target=self._ssh_remove_old_logs_thread, daemon=True)
        thread.start()
    
    def _ssh_remove_old_logs_thread(self):
        """Background thread to remove old log files."""
        from ssh_helper import SSHManager
        import time
        
        if self.ssh_window_id not in SSHManager._windows:
            return
        
        window = SSHManager._windows[self.ssh_window_id]
        if self.ap_id not in window.tabs:
            return
        
        tab = window.tabs[self.ap_id]
        connection = tab.connection
        
        if not connection.connected:
            return
        
        # Check if in service mode and exit if needed
        if not self._ssh_exit_service_mode_if_needed(connection):
            self.window.after(0, lambda: self._log_activity("✗ Failed to exit service mode"))
            return
        
        # Check space before
        time.sleep(1)
        connection.send_command("df -h")
        time.sleep(2)
        before_output = connection.get_output()
        self.window.after(0, lambda: self._log_activity(f"Space before cleanup:\n{before_output}"))
        
        # Navigate to log folder
        time.sleep(0.5)
        connection.send_command("cd /opt/esl/accesspoint")
        time.sleep(1)
        
        # Remove old log files
        connection.send_command("rm -rf *20*log*")
        time.sleep(2)
        
        # Check space after
        connection.send_command("df -h")
        time.sleep(2)
        after_output = connection.get_output()
        self.window.after(0, lambda: self._log_activity(f"Space after cleanup:\n{after_output}"))
        self.window.after(0, lambda: self._log_activity("✓ Old log files removed"))
    
    def _ssh_download_logs(self):
        """Download log files from the AP via SCP."""
        if not self.ssh_connected:
            messagebox.showinfo("Connect First", "Please connect to SSH first.", parent=self.window)
            return
        
        # Ask user for destination folder
        from tkinter import filedialog
        dest_folder = filedialog.askdirectory(title="Select destination folder for log files", parent=self.window)
        
        if not dest_folder:
            return
        
        self._log_activity(f"Downloading logs to: {dest_folder}")
        
        # Run in background thread
        thread = threading.Thread(target=self._ssh_download_logs_thread, args=(dest_folder,), daemon=True)
        thread.start()
    
    def _ssh_download_logs_thread(self, dest_folder):
        """Background thread to download log files via SCP."""
        from ssh_helper import SSHManager
        import paramiko
        import os
        import time
        
        if self.ssh_window_id not in SSHManager._windows:
            return
        
        window = SSHManager._windows[self.ssh_window_id]
        if self.ap_id not in window.tabs:
            return
        
        tab = window.tabs[self.ap_id]
        connection = tab.connection
        
        if not connection.connected:
            return
        
        # Check if in service mode and exit if needed
        if not self._ssh_exit_service_mode_if_needed(connection):
            self.window.after(0, lambda: self._log_activity("✗ Failed to exit service mode"))
            return
        
        # Navigate to log folder and list files
        time.sleep(1)
        connection.send_command("cd /opt/esl/accesspoint")
        time.sleep(1)
        connection.send_command("ls -la *20*log* 2>/dev/null || echo 'No log files found'")
        time.sleep(2)
        
        # Get file list
        output = connection.get_output()
        self.window.after(0, lambda: self._log_activity(f"Log files found:\n{output}"))
        
        # Use SCP to download files
        try:
            # Create SCP client using existing SSH connection
            scp_client = paramiko.SFTPClient.from_transport(connection.client.get_transport())
            
            # Get list of files matching pattern
            remote_path = "/opt/esl/accesspoint"
            try:
                files = scp_client.listdir(remote_path)
                log_files = [f for f in files if '20' in f and 'log' in f.lower()]
                
                if not log_files:
                    self.window.after(0, lambda: self._log_activity("No log files found to download"))
                    return
                
                # Download each file
                for filename in log_files:
                    remote_file = f"{remote_path}/{filename}"
                    local_file = os.path.join(dest_folder, filename)
                    
                    self.window.after(0, lambda f=filename: self._log_activity(f"Downloading: {f}"))
                    scp_client.get(remote_file, local_file)
                    self.window.after(0, lambda f=filename: self._log_activity(f"✓ Downloaded: {f}"))
                
                self.window.after(0, lambda: self._log_activity(f"✓ All log files downloaded to {dest_folder}"))
                
            finally:
                scp_client.close()
                
        except Exception as e:
            self.window.after(0, lambda: self._log_activity(f"✗ Error downloading logs: {str(e)}"))
    
    def _ssh_exit_service_mode_if_needed(self, connection):
        """Exit service mode if currently in it. Returns True if ready to execute commands."""
        import time
        
        # Peek at recent output to check current prompt
        time.sleep(1)
        output = connection.peek_output(500)
        
        # Log what we see for debugging
        self.window.after(0, lambda o=output: self._log_activity(f"Checking prompt. Last output: {repr(o[-100:])}"))
        
        # Check if in service mode (case insensitive)
        if "servicemode>" in output.lower():
            return self._ssh_exit_service_mode_if_needed_v2(connection)
        
        # Not in service mode, ready to execute
        self.window.after(0, lambda: self._log_activity("✓ Normal shell mode detected"))
        return True
    
    def _ssh_exit_service_mode_if_needed_v2(self, connection):
        """Actually exit service mode. Returns True if successful."""
        import time
        
        self.window.after(0, lambda: self._log_activity("⚠️ Exiting service mode..."))
        
        # Exit service mode
        connection.send_command("extended matex2010")
        time.sleep(2)
        connection.send_command("enableshell true")
        time.sleep(2)
        connection.send_command("exit")
        time.sleep(2)
        connection.send_command("exit")
        time.sleep(3)
        
        # Reconnect
        self.window.after(0, lambda: self._log_activity("Reconnecting..."))
        
        # Set reconnecting flag on terminal tab to preserve output
        tab = self.ssh_manager.get_tab(self.window_id, self.ap_id)
        if tab:
            tab.is_reconnecting = True
        
        # Disconnect current connection (preserve buffers)
        connection.disconnect(preserve_buffers=True)
        time.sleep(1)
        
        # Reconnect
        success, message = connection.connect()
        
        if tab:
            tab.is_reconnecting = False
        
        if success:
            time.sleep(3)
            self.window.after(0, lambda: self._log_activity("✓ Reconnected in normal mode"))
            return True
        else:
            self.window.after(0, lambda: self._log_activity(f"✗ Reconnection failed: {message}"))
            return False
    
    def _open_jira_search(self):
        """Open Jira search window for this AP."""
        try:
            open_jira_search(self.window, self.db, ap_id=self.ap_id)
            
            # Log audit
            self.db.log_user_activity(
                username=self.current_user,
                activity_type='jira_search',
                description=f'Opened Jira search for AP {self.ap_id}',
                ap_id=self.ap_id,
                success=True
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Jira search:\n{str(e)}", 
                               parent=self.window)
            self.db.log_user_activity(
                username=self.current_user,
                activity_type='jira_search',
                description=f'Failed to open Jira search for AP {self.ap_id}: {str(e)}',
                ap_id=self.ap_id,
                success=False
            )
    
    def _open_another_ap(self):
        """Open the AP search dialog to open another AP support window."""
        # Import here to avoid circular dependency
        from ap_support_ui import APSearchDialog
        
        # Define callback for when AP is selected
        def on_ap_selected(selected_ap):
            # Open new support window (will check if already open)
            APSupportWindow(self.window, selected_ap, self.current_user, 
                          self.db, self.browser_helper)
        
        # Open search dialog with callback
        search_dialog = APSearchDialog(self.window, self.current_user, self.db, on_select_callback=on_ap_selected)
    
    def _open_write_note_dialog(self):
        """Open a dialog to write a new note."""
        dialog = tk.Toplevel(self.window)
        dialog.title("Write Note")
        dialog.geometry("760x600")
        dialog.configure(bg="#FFFFFF")
        dialog.transient(self.window)
        # Don't use grab_set() to make it non-modal like the note window
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (760 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"760x600+{x}+{y}")
        
        # Main frame
        main_frame = tk.Frame(dialog, bg="#FFFFFF", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Headline
        tk.Label(main_frame, text="Headline:", font=("Segoe UI", 10, "bold"), 
                bg="#FFFFFF").pack(anchor="w", pady=(0, 5))
        headline_entry = tk.Entry(main_frame, font=("Segoe UI", 12, "bold"), 
                                 relief="flat", borderwidth=0, highlightthickness=1,
                                 highlightbackground="#CCCCCC", highlightcolor="#007BFF")
        headline_entry.pack(fill="x", ipady=5, pady=(0, 10))
        headline_entry.focus_set()
        
        # Note content
        tk.Label(main_frame, text="Note:", font=("Segoe UI", 10, "bold"), 
                bg="#FFFFFF").pack(anchor="w", pady=(0, 5))
        
        text_widget = scrolledtext.ScrolledText(main_frame, font=("Segoe UI", 10), 
                                               wrap=tk.WORD, height=12, relief="flat", 
                                               borderwidth=0, highlightthickness=1,
                                               highlightbackground="#CCCCCC", 
                                               highlightcolor="#007BFF")
        text_widget.pack(fill="both", expand=True)
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg="#FFFFFF")
        button_frame.pack(fill="x", pady=(10, 0))
        
        def save_note():
            headline = headline_entry.get().strip()
            content = text_widget.get("1.0", tk.END).strip()
            
            if not headline or not content:
                messagebox.showwarning("Missing Data", "Both headline and content are required.", 
                                     parent=dialog)
                return
            
            success, message, note_id = self.db.add_support_note(self.ap_id, self.current_user, 
                                                                 headline, content)
            if success:
                self._refresh_notes()
                self._log_activity(f"✓ Note added: {headline}")
                # Log audit: note created
                self.db.log_user_activity(
                    username=self.current_user,
                    activity_type='ap_note_create',
                    description=f'Created note: {headline}',
                    ap_id=self.ap_id,
                    success=True,
                    details={'note_id': note_id, 'headline': headline}
                )
                dialog.destroy()
            else:
                messagebox.showerror("Error", f"Failed to save note: {message}", parent=dialog)
        
        # Save button
        tk.Button(button_frame, text="Save Note", command=save_note,
                 bg="#28A745", fg="white", cursor="hand2", padx=20, pady=8,
                 font=("Segoe UI", 10), relief="flat", bd=0,
                 activebackground="#218838").pack(side="left", padx=(0, 5))
        
        # Cancel button
        tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                 bg="#6C757D", fg="white", cursor="hand2", padx=20, pady=8,
                 font=("Segoe UI", 10), relief="flat", bd=0,
                 activebackground="#5A6268").pack(side="left", padx=5)
    
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
    
    def _get_user_display_name(self, username: str) -> str:
        """Get user display name with full name and username."""
        user = self.db.get_user(username)
        if user and user.get('full_name'):
            return f"{user['full_name']} ({username})"
        return username
    
    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="#FFFFE0", relief="solid", 
                           borderwidth=1, font=("Segoe UI", 9), padx=4, pady=2)
            label.pack()
            widget.tooltip_window = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip_window'):
                widget.tooltip_window.destroy()
                del widget.tooltip_window
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def _create_note_window(self, note):
        """Create a new note detail/edit window."""
        self.note_window = tk.Toplevel(self.window)
        self.note_window.title(f"Note - {note['headline']}")
        self.note_window.geometry("760x700")
        self.note_window.configure(bg="#FFFFFF")
        self.note_window_modified = False
        self.note_edit_mode = False
        
        # Store current note ID and original content
        self.current_note_id = note['id']
        self.original_headline = note['headline']
        self.original_note_content = note['note']
        
        # Check if this is the user's note and latest
        is_latest = self.db.is_latest_note(note['id'], self.ap_id)
        is_owner = note['user'] == self.current_user
        self.can_edit_note = is_latest and is_owner
        
        # Header with note info
        header = tk.Frame(self.note_window, bg="#FFFFFF")
        header.pack(fill="x", padx=15, pady=15)
        
        tk.Label(header, text=f"Created: {note['created_at']}", 
                font=("Segoe UI", 9), bg="#FFFFFF").pack(anchor="w", pady=2)
        tk.Label(header, text=f"By: {self._get_user_display_name(note['user'])}", 
                font=("Segoe UI", 9), bg="#FFFFFF").pack(anchor="w", pady=2)
        
        if note.get('updated_at') and note['updated_at'] != note['created_at']:
            updated_by_display = self._get_user_display_name(note.get('updated_by', 'unknown'))
            tk.Label(header, text=f"Last edited: {note['updated_at']} by {updated_by_display}", 
                    font=("Segoe UI", 8, "italic"), fg="#888888", bg="#FFFFFF").pack(anchor="w", pady=2)
        
        # Separator line
        tk.Frame(self.note_window, bg="#CCCCCC", height=1).pack(fill="x", padx=15)
        
        # Content area with headline and note text (HTML-style display)
        content_container = tk.Frame(self.note_window, bg="#FFFFFF")
        content_container.pack(fill="both", expand=True, padx=15, pady=(5, 10))
        
        # Edit and Reply icon buttons (only for note owner) - positioned at top right
        if self.can_edit_note:
            buttons_container = tk.Frame(content_container, bg="#FFFFFF")
            buttons_container.pack(anchor="ne", pady=(0, 10))
            
            # Reply button
            reply_icon = IconHelper.get_reply_icon(size=30, color="#424242")
            if reply_icon:
                reply_btn = tk.Button(buttons_container, image=reply_icon, 
                                     command=self._show_reply_input,
                                     bg="#FFFFFF", relief="flat", bd=0, cursor="hand2", 
                                     padx=4, pady=4, activebackground="#F0F0F0")
                reply_btn.image = reply_icon
                self._create_tooltip(reply_btn, "Reply")
            else:
                reply_btn = tk.Button(buttons_container, text="💬", command=self._show_reply_input,
                                     bg="#FFFFFF", fg="#333333", font=("Segoe UI", 20), 
                                     relief="flat", bd=0, cursor="hand2", padx=4, pady=2,
                                     activebackground="#F0F0F0")
                self._create_tooltip(reply_btn, "Reply")
            reply_btn.pack(side="right", padx=2)
            
            # Edit button
            edit_icon = IconHelper.get_edit_icon(size=30, color="#424242")
            if edit_icon:
                self.note_edit_btn = tk.Button(buttons_container, image=edit_icon, 
                                              command=self._toggle_note_edit,
                                              bg="#FFFFFF", relief="flat", bd=0, cursor="hand2", 
                                              padx=4, pady=4, activebackground="#F0F0F0")
                self.note_edit_btn.image = edit_icon  # Keep reference
                self._create_tooltip(self.note_edit_btn, "Edit")
            else:
                self.note_edit_btn = tk.Button(buttons_container, text="✏", command=self._toggle_note_edit,
                                              bg="#FFFFFF", fg="#333333", font=("Segoe UI", 20), 
                                              relief="flat", bd=0, cursor="hand2", padx=4, pady=2,
                                              activebackground="#F0F0F0")
                self._create_tooltip(self.note_edit_btn, "Edit")
            self.note_edit_btn.pack(side="right", padx=2)
        
        # Add Reply section (initially hidden) - positioned after buttons
        self.add_reply_frame = tk.Frame(content_container, bg="#FFFFFF")
        self.add_reply_frame.pack(fill="x", pady=(10, 0))
        
        tk.Label(self.add_reply_frame, text="Reply:", bg="#FFFFFF", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 5))
        self.note_window_reply = scrolledtext.ScrolledText(self.add_reply_frame, height=4, 
                                                           font=("Segoe UI", 10), wrap=tk.WORD,
                                                           relief="flat", borderwidth=0,
                                                           highlightthickness=1,
                                                           highlightbackground="#CCCCCC",
                                                           highlightcolor="#007BFF")
        self.note_window_reply.pack(fill="x")
        
        # Buttons directly under text input
        reply_btn_frame = tk.Frame(self.add_reply_frame, bg="#FFFFFF")
        reply_btn_frame.pack(fill="x", pady=(10, 0))
        
        tk.Button(reply_btn_frame, text="Save Reply", command=self._add_reply_from_window,
                 bg="#28A745", fg="white", padx=20, pady=8, relief="flat", bd=0,
                 cursor="hand2", font=("Segoe UI", 10),
                 activebackground="#218838").pack(side="left", padx=(0, 5))
        
        tk.Button(reply_btn_frame, text="Cancel", command=self._hide_reply_input,
                 bg="#6C757D", fg="white", padx=20, pady=8, relief="flat", bd=0,
                 cursor="hand2", font=("Segoe UI", 10),
                 activebackground="#5A6268").pack(side="left", padx=5)
        
        self.add_reply_frame.pack_forget()  # Hide initially
        
        # Headline display (bold, H1-style)
        self.note_headline_display = tk.Label(content_container, font=("Segoe UI", 16, "bold"), 
                                             bg="#FFFFFF", fg="#333333", anchor="w", justify="left",
                                             wraplength=650)
        self.note_headline_display.pack(fill="x", pady=(0, 10))
        self.note_headline_display.config(text=note['headline'])
        
        # Note text display (normal paragraph style)
        self.note_text_display = tk.Label(content_container, font=("Segoe UI", 10), 
                                         bg="#FFFFFF", fg="#333333", anchor="nw", justify="left",
                                         wraplength=650)
        self.note_text_display.pack(fill="both", expand=True, pady=(0, 10))
        self.note_text_display.config(text=note['note'])
        
        # Edit widgets (hidden by default)
        self.note_edit_frame = tk.Frame(content_container, bg="#FFFFFF")
        
        tk.Label(self.note_edit_frame, text="Headline:", font=("Segoe UI", 10, "bold"), 
                bg="#FFFFFF").pack(anchor="w", pady=(0, 5))
        self.note_window_headline = tk.Entry(self.note_edit_frame, font=("Segoe UI", 12, "bold"), 
                                             relief="flat", borderwidth=0, highlightthickness=1,
                                             highlightbackground="#CCCCCC", highlightcolor="#007BFF")
        self.note_window_headline.pack(fill="x", ipady=5, pady=(0, 10))
        self.note_window_headline.insert(0, note['headline'])
        
        tk.Label(self.note_edit_frame, text="Note:", font=("Segoe UI", 10, "bold"), 
                bg="#FFFFFF").pack(anchor="w", pady=(0, 5))
        self.note_window_text = scrolledtext.ScrolledText(self.note_edit_frame, font=("Segoe UI", 10), 
                                                          wrap=tk.WORD, height=12, relief="flat", 
                                                          borderwidth=0, highlightthickness=1,
                                                          highlightbackground="#CCCCCC", 
                                                          highlightcolor="#007BFF")
        self.note_window_text.pack(fill="both", expand=True)
        self.note_window_text.insert("1.0", note['note'])
        
        # Save/Cancel/Delete buttons directly under text input
        note_buttons = tk.Frame(self.note_edit_frame, bg="#FFFFFF")
        note_buttons.pack(fill="x", pady=(10, 0))
        
        tk.Button(note_buttons, text="Save Changes", command=self._save_note_edit,
                 bg="#28A745", fg="white", padx=20, pady=8, relief="flat", bd=0,
                 cursor="hand2", font=("Segoe UI", 10),
                 activebackground="#218838").pack(side="left", padx=(0, 5))
        
        tk.Button(note_buttons, text="Cancel", command=self._cancel_note_edit,
                 bg="#6C757D", fg="white", padx=20, pady=8, relief="flat", bd=0,
                 cursor="hand2", font=("Segoe UI", 10),
                 activebackground="#5A6268").pack(side="left", padx=5)
        
        tk.Button(note_buttons, text="Delete Note", command=self._delete_note_from_window,
                 bg="#DC3545", fg="white", padx=20, pady=8, relief="flat", bd=0,
                 cursor="hand2", font=("Segoe UI", 10),
                 activebackground="#C82333").pack(side="right")
        
        # Don't pack edit frame yet (hidden by default)
        
        # Separator line
        tk.Frame(self.note_window, bg="#CCCCCC", height=1).pack(fill="x", padx=15, pady=(10, 0))
        
        # Existing Replies section
        replies = self.db.get_note_replies(note['id'])
        if replies:
            replies_outer = tk.Frame(self.note_window, bg="#FFFFFF")
            replies_outer.pack(fill="both", expand=True, padx=15, pady=(10, 0))
            
            # Replies header with icon
            replies_header = tk.Frame(replies_outer, bg="#FFFFFF")
            replies_header.pack(fill="x", pady=(0, 5))
            
            forum_icon = IconHelper.get_forum_icon(size=20, color="#424242")
            if forum_icon:
                icon_label = tk.Label(replies_header, image=forum_icon, bg="#FFFFFF")
                icon_label.image = forum_icon
                icon_label.pack(side="left", padx=(0, 5))
                self._create_tooltip(icon_label, "Replies")
            else:
                tk.Label(replies_header, text="💬", bg="#FFFFFF", font=("Segoe UI", 14)).pack(side="left", padx=(0, 5))
            
            tk.Label(replies_header, text=f"({len(replies)})", bg="#FFFFFF", 
                    font=("Segoe UI", 10, "bold"), fg="#424242").pack(side="left")
            
            replies_frame = tk.Frame(replies_outer, bg="#FFFFFF", padx=10, pady=10)
            replies_frame.pack(fill="both", expand=True)
            
            # Create scrollable frame for replies with modern scrollbar
            replies_canvas = tk.Canvas(replies_frame, bg="#FFFFFF", highlightthickness=0, height=150, width=680)
            replies_scroll = ttk.Scrollbar(replies_frame, orient="vertical", command=replies_canvas.yview, 
                                          style="Modern.Vertical.TScrollbar")
            replies_container = tk.Frame(replies_canvas, bg="#FFFFFF")
            
            replies_container.bind(
                "<Configure>",
                lambda e: replies_canvas.configure(scrollregion=replies_canvas.bbox("all"))
            )
            
            replies_canvas.create_window((0, 0), window=replies_container, anchor="nw")
            replies_canvas.configure(yscrollcommand=replies_scroll.set)
            
            replies_canvas.pack(side="left", fill="both", expand=True)
            replies_scroll.pack(side="right", fill="y")
            
            # Store reply widgets for editing
            self.reply_widgets = {}
            
            # Display replies (newest first)
            for idx, reply in enumerate(replies):
                reply_box = tk.Frame(replies_container, bg="#FFFFFF")
                reply_box.pack(fill="both", expand=True, padx=0, pady=0)
                
                # Reply header with Edit button
                reply_header = tk.Frame(reply_box, bg="#FFFFFF")
                reply_header.pack(fill="x", padx=10, pady=(8, 0))
                
                user_display = self._get_user_display_name(reply['user'])
                tk.Label(reply_header, text=f"{reply['created_at']} - {user_display}", 
                        font=("Segoe UI", 8), fg="#888888", bg="#FFFFFF", anchor="w").pack(side="left")
                
                # Edit icon for reply owner
                if reply['user'] == self.current_user:
                    reply_icon = IconHelper.get_edit_icon(size=20, color="#424242")
                    if reply_icon:
                        edit_btn = tk.Button(reply_header, image=reply_icon, 
                                            command=lambda r=reply: self._toggle_reply_edit(r['id']),
                                            bg="#FFFFFF", relief="flat", bd=0, cursor="hand2", 
                                            padx=4, pady=4, activebackground="#F0F0F0")
                        edit_btn.image = reply_icon  # Keep reference
                        self._create_tooltip(edit_btn, "Edit")
                    else:
                        edit_btn = tk.Button(reply_header, text="✏", 
                                            command=lambda r=reply: self._toggle_reply_edit(r['id']),
                                            bg="#FFFFFF", fg="#333333", font=("Segoe UI", 14), 
                                            relief="flat", bd=0, cursor="hand2", padx=4, pady=4,
                                            activebackground="#F0F0F0")
                        self._create_tooltip(edit_btn, "Edit")
                    edit_btn.pack(side="right")
                
                # Reply display label (no grey box)
                reply_display_label = tk.Label(reply_box, font=("Segoe UI", 9), 
                                              bg="#FFFFFF", fg="#333333", anchor="w", justify="left",
                                              wraplength=680, text=reply['reply_text'])
                reply_display_label.pack(fill="both", expand=True, padx=10, pady=(5, 8))
                
                # Reply edit widget (hidden by default)
                reply_edit_container = tk.Frame(reply_box, bg="#FFFFFF")
                
                reply_text_widget = scrolledtext.ScrolledText(reply_edit_container, font=("Segoe UI", 9), 
                                           bg="#FFFFFF", wrap="word", height=6,
                                           relief="flat", borderwidth=0, highlightthickness=1,
                                           highlightbackground="#CCCCCC", highlightcolor="#007BFF")
                reply_text_widget.pack(fill="x", padx=10, pady=(5, 0))
                reply_text_widget.insert("1.0", reply['reply_text'])
                
                # Edit buttons for reply directly under text input
                reply_edit_buttons = tk.Frame(reply_edit_container, bg="#FFFFFF")
                reply_edit_buttons.pack(fill="x", padx=10, pady=(10, 8))
                
                tk.Button(reply_edit_buttons, text="Save", 
                         command=lambda r=reply: self._save_reply_edit(r['id']),
                         bg="#28A745", fg="white", padx=15, pady=5, relief="flat", bd=0,
                         cursor="hand2", font=("Segoe UI", 9),
                         activebackground="#218838").pack(side="left", padx=(0, 5))
                
                tk.Button(reply_edit_buttons, text="Cancel", 
                         command=lambda r=reply: self._cancel_reply_edit(r['id']),
                         bg="#6C757D", fg="white", padx=15, pady=5, relief="flat", bd=0,
                         cursor="hand2", font=("Segoe UI", 9),
                         activebackground="#5A6268").pack(side="left", padx=5)
                
                tk.Button(reply_edit_buttons, text="Delete", 
                         command=lambda r=reply: self._delete_reply(r['id']),
                         bg="#DC3545", fg="white", padx=15, pady=5, relief="flat", bd=0,
                         cursor="hand2", font=("Segoe UI", 9),
                         activebackground="#C82333").pack(side="left", padx=5)
                
                # Don't pack edit container yet (hidden by default)
                
                # Store widgets for this reply
                self.reply_widgets[reply['id']] = {
                    'text': reply_text_widget,
                    'display': reply_display_label,
                    'edit_container': reply_edit_container,
                    'original_text': reply['reply_text']
                }
                
                # Add separator line after each reply except the last
                if idx < len(replies) - 1:
                    tk.Frame(reply_box, bg="#CCCCCC", height=1).pack(fill="x")
        
        # Separator line
        tk.Frame(self.note_window, bg="#CCCCCC", height=1).pack(fill="x", padx=15, pady=(10, 0))
        
        # Bottom buttons
        btn_frame = tk.Frame(self.note_window, bg="#FFFFFF")
        btn_frame.pack(fill="x", padx=15, pady=15)
        
        tk.Button(btn_frame, text="Close", command=self._close_note_window,
                 bg="#6C757D", fg="white", padx=20, pady=10, relief="flat", bd=0,
                 cursor="hand2", font=("Segoe UI", 10),
                 activebackground="#5A6268").pack(side="right", padx=5)
    
    def _update_note_window(self, note):
        """Update the existing note window with different note - recreate to show replies."""
        # Destroy existing window and create new one with updated note
        self.note_window.destroy()
        self.note_window = None
        self._create_note_window(note)
    
    def _toggle_note_edit(self):
        """Toggle edit mode for the note."""
        if not self.note_edit_mode:
            # Enter edit mode - hide display widgets, show edit widgets
            self.note_edit_mode = True
            self.note_headline_display.pack_forget()
            self.note_text_display.pack_forget()
            self.note_edit_frame.pack(fill="both", expand=True)
            # Change button to cancel mode
            cancel_icon = IconHelper.get_cancel_icon(size=30, color="#424242")
            if cancel_icon:
                self.note_edit_btn.config(image=cancel_icon, text="", bg="#FFFFFF", fg="white")
                self.note_edit_btn.image = cancel_icon
                # Unbind old tooltip and create new one
                self.note_edit_btn.unbind("<Enter>")
                self.note_edit_btn.unbind("<Leave>")
                self._create_tooltip(self.note_edit_btn, "Cancel Edit")
            else:
                self.note_edit_btn.config(text="✖", font=("Segoe UI", 16), bg="#6C757D", fg="white")
        else:
            # Exit edit mode without saving
            self._cancel_note_edit()
    
    def _cancel_note_edit(self):
        """Cancel note editing and revert to read-only mode."""
        self.note_edit_mode = False
        
        # Restore original content
        self.note_window_headline.delete(0, tk.END)
        self.note_window_headline.insert(0, self.original_headline)
        self.note_window_text.delete("1.0", tk.END)
        self.note_window_text.insert("1.0", self.original_note_content)
        
        # Hide edit widgets, show display widgets
        self.note_edit_frame.pack_forget()
        self.note_headline_display.pack(fill="x", pady=(0, 10))
        self.note_text_display.pack(fill="both", expand=True, pady=(0, 10))
        
        # Restore edit button
        if hasattr(self.note_edit_btn, 'image'):
            edit_icon = IconHelper.get_edit_icon(size=30, color="#424242")
            if edit_icon:
                self.note_edit_btn.config(image=edit_icon, text="", bg="#FFFFFF", fg="#333333")
                self.note_edit_btn.image = edit_icon
                # Unbind old tooltip and create new one
                self.note_edit_btn.unbind("<Enter>")
                self.note_edit_btn.unbind("<Leave>")
                self._create_tooltip(self.note_edit_btn, "Edit")
            else:
                self.note_edit_btn.config(image='', text="✏", font=("Segoe UI", 20), bg="#FFFFFF", fg="#333333")
        else:
            self.note_edit_btn.config(text="✏", font=("Segoe UI", 20), bg="#FFFFFF", fg="#333333")
        
        self.note_window_modified = False
    
    def _save_note_edit(self):
        """Save note edits."""
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
            
            # Update original content and display labels
            self.original_headline = headline
            self.original_note_content = content
            self.note_headline_display.config(text=headline)
            self.note_text_display.config(text=content)
            
            # Log audit: note updated
            self.db.log_user_activity(
                username=self.current_user,
                activity_type='ap_note_update',
                description=f'Updated note: {headline}',
                ap_id=self.ap_id,
                success=True,
                details={'note_id': self.current_note_id, 'headline': headline}
            )
            
            self._cancel_note_edit()  # Exit edit mode
        else:
            messagebox.showerror("Error", f"Failed to save: {message}", parent=self.note_window)
    
    def _show_reply_input(self):
        """Show the reply input area."""
        self.add_reply_frame.pack(fill="x", pady=(10, 0))
    
    def _hide_reply_input(self):
        """Hide the reply input area."""
        self.note_window_reply.delete("1.0", tk.END)
        self.add_reply_frame.pack_forget()
    
    def _toggle_reply_edit(self, reply_id):
        """Toggle edit mode for a specific reply."""
        if reply_id not in self.reply_widgets:
            return
        
        widgets = self.reply_widgets[reply_id]
        
        # Check if edit container is currently shown
        if not widgets['edit_container'].winfo_ismapped():
            # Enter edit mode - hide display, show edit
            widgets['display'].pack_forget()
            widgets['edit_container'].pack(fill="x", padx=0, pady=0)
        else:
            # Exit edit mode without saving
            self._cancel_reply_edit(reply_id)
    
    def _cancel_reply_edit(self, reply_id):
        """Cancel reply editing and revert to read-only mode."""
        if reply_id not in self.reply_widgets:
            return
        
        widgets = self.reply_widgets[reply_id]
        text_widget = widgets['text']
        
        # Revert to original text
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", widgets['original_text'])
        
        # Hide edit, show display
        widgets['edit_container'].pack_forget()
        widgets['display'].pack(fill="x", padx=10, pady=(5, 8))
    
    def _save_reply_edit(self, reply_id):
        """Save reply edits."""
        if reply_id not in self.reply_widgets:
            return
        
        widgets = self.reply_widgets[reply_id]
        text_widget = widgets['text']
        new_text = text_widget.get("1.0", tk.END).strip()
        
        if not new_text:
            messagebox.showwarning("Empty Reply", "Reply text cannot be empty.", 
                                 parent=self.note_window)
            return
        
        success, message = self.db.update_note_reply(reply_id, new_text, self.current_user)
        if success:
            widgets['original_text'] = new_text
            widgets['display'].config(text=new_text)
            widgets['edit_container'].pack_forget()
            widgets['display'].pack(fill="x", padx=10, pady=(5, 8))
            self._refresh_notes()
            # Log audit: reply updated
            self.db.log_user_activity(
                username=self.current_user,
                activity_type='ap_reply_update',
                description=f'Updated reply',
                ap_id=self.ap_id,
                success=True,
                details={'note_id': self.current_note_id, 'reply_id': reply_id}
            )
        else:
            messagebox.showerror("Error", f"Failed to save: {message}", parent=self.note_window)
    
    def _delete_reply(self, reply_id):
        """Delete a reply."""
        response = messagebox.askyesno("Confirm Delete", 
                                      "Are you sure you want to delete this reply?",
                                      parent=self.note_window)
        if not response:
            return
        
        success, message = self.db.delete_note_reply(reply_id, self.current_user)
        if success:
            self._refresh_notes()
            # Log audit: reply deleted
            self.db.log_user_activity(
                username=self.current_user,
                activity_type='ap_reply_delete',
                description=f'Deleted reply',
                ap_id=self.ap_id,
                success=True,
                details={'note_id': self.current_note_id, 'reply_id': reply_id}
            )
            # Refresh the note window to show updated replies
            note = next((n for n in self.notes_data if n['id'] == self.current_note_id), None)
            if note:
                self._update_note_window(note)
        else:
            messagebox.showerror("Error", f"Failed to delete: {message}", parent=self.note_window)
    
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
            # Log audit: note deleted
            self.db.log_user_activity(
                username=self.current_user,
                activity_type='ap_note_delete',
                description=f'Deleted note',
                ap_id=self.ap_id,
                success=True,
                details={'note_id': self.current_note_id}
            )
            self.note_window.destroy()
            self.note_window = None
        else:
            messagebox.showerror("Error", f"Failed to delete: {message}", parent=self.note_window)
    
    def _add_reply_from_window(self):
        """Add a reply to the current note."""
        reply_text = self.note_window_reply.get("1.0", tk.END).strip()
        
        if not reply_text:
            messagebox.showwarning("Empty Reply", "Please enter reply text.", 
                                 parent=self.note_window)
            return
        
        success, message, reply_id = self.db.add_note_reply(self.current_note_id, 
                                                            self.current_user, reply_text)
        if success:
            self._refresh_notes()
            # Log audit: reply created
            self.db.log_user_activity(
                username=self.current_user,
                activity_type='ap_reply_create',
                description=f'Added reply to note',
                ap_id=self.ap_id,
                success=True,
                details={'note_id': self.current_note_id, 'reply_id': reply_id}
            )
            self.note_window_reply.delete("1.0", tk.END)
            self._hide_reply_input()
            # Refresh the note window to show the new reply
            note = next((n for n in self.notes_data if n['id'] == self.current_note_id), None)
            if note:
                self._update_note_window(note)
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
        # Close browser if open
        if self.driver:
            try:
                self.driver.quit()
                self._log_activity("✓ Browser closed")
            except:
                pass
        
        # Close SSH if connected
        if self.ssh_connected:
            try:
                from ssh_helper import SSHManager
                SSHManager.close_window(self.ssh_window_id)
                self._log_activity("✓ SSH closed")
            except:
                pass
        
        # Unregister window
        if self.ap_id in APSupportWindow._open_windows:
            del APSupportWindow._open_windows[self.ap_id]
        self.window.destroy()
