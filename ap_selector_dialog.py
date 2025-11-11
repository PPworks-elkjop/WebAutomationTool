"""Dialog for selecting multiple APs from credential database."""

import tkinter as tk
from tkinter import ttk, messagebox
from credential_manager import CredentialManager


class APSelectorDialog:
    """Multi-select dialog for choosing APs with search functionality."""
    
    def __init__(self, parent):
        self.result = []  # Will store selected AP credentials
        self.credential_manager = CredentialManager()
        self.all_aps = self.credential_manager.get_all()
        self.filtered_aps = self.all_aps.copy()
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Select Access Points")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        bg_color = "#F5F5F5"
        frame_bg = "#FFFFFF"
        
        self.dialog.configure(bg=bg_color)
        
        style.configure("AP.TFrame", background=frame_bg)
        style.configure("AP.TLabel", background=frame_bg, foreground="#333333", font=("Segoe UI", 10))
        style.configure("AP.Title.TLabel", background=frame_bg, foreground="#333333", font=("Segoe UI", 14, "bold"))
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"800x600+{x}+{y}")
        
        self._build_ui()
        self._populate_list()
        
        # Bind keys
        self.dialog.bind("<Return>", lambda e: self._on_ok())
        self.dialog.bind("<Escape>", lambda e: self._on_cancel())
    
    def _build_ui(self):
        """Build the dialog UI."""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="20", style="AP.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Select Access Points",
            style="AP.Title.TLabel"
        )
        title_label.pack(pady=(0, 10))
        
        # Info label
        info_label = ttk.Label(
            main_frame,
            text="Search and select one or more APs to connect to. Operations will be performed on all selected APs.",
            style="AP.TLabel"
        )
        info_label.pack(pady=(0, 15))
        
        # Search frame
        search_frame = ttk.Frame(main_frame, style="AP.TFrame")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="🔍 Search:", style="AP.TLabel").pack(side=tk.LEFT, padx=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search_changed)
        
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=50)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        clear_btn = tk.Button(
            search_frame,
            text="Clear",
            command=self._clear_search,
            bg="#6C757D",
            fg="white",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            cursor="hand2"
        )
        clear_btn.pack(side=tk.LEFT)
        
        # Selection info frame
        info_frame = ttk.Frame(main_frame, style="AP.TFrame")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.selection_label = ttk.Label(
            info_frame,
            text="Selected: 0 APs | Total: 0 APs",
            style="AP.TLabel",
            font=("Segoe UI", 9, "bold")
        )
        self.selection_label.pack(side=tk.LEFT)
        
        # Select/Deselect all buttons
        btn_frame = ttk.Frame(info_frame, style="AP.TFrame")
        btn_frame.pack(side=tk.RIGHT)
        
        select_all_btn = tk.Button(
            btn_frame,
            text="Select All",
            command=self._select_all,
            bg="#28A745",
            fg="white",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            cursor="hand2"
        )
        select_all_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        deselect_all_btn = tk.Button(
            btn_frame,
            text="Deselect All",
            command=self._deselect_all,
            bg="#DC3545",
            fg="white",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            cursor="hand2"
        )
        deselect_all_btn.pack(side=tk.LEFT)
        
        # Treeview with scrollbar
        tree_frame = ttk.Frame(main_frame, style="AP.TFrame")
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("retail_chain", "store_id", "store_alias", "ap_id", "ip_address", "type"),
            show="tree headings",
            selectmode="none",  # We'll handle selection with checkboxes
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configure columns
        self.tree.heading("#0", text="✓")
        self.tree.heading("retail_chain", text="Retail Chain")
        self.tree.heading("store_id", text="Store ID")
        self.tree.heading("store_alias", text="Store Alias")
        self.tree.heading("ap_id", text="AP ID")
        self.tree.heading("ip_address", text="IP Address")
        self.tree.heading("type", text="Type")
        
        self.tree.column("#0", width=40, anchor=tk.CENTER)
        self.tree.column("retail_chain", width=100)
        self.tree.column("store_id", width=80)
        self.tree.column("store_alias", width=120)
        self.tree.column("ap_id", width=80)
        self.tree.column("ip_address", width=120)
        self.tree.column("type", width=80)
        
        # Pack treeview and scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind click event
        self.tree.bind("<Button-1>", self._on_tree_click)
        
        # Bottom button frame
        button_frame = ttk.Frame(main_frame, style="AP.TFrame")
        button_frame.pack(fill=tk.X)
        
        # OK button
        ok_button = tk.Button(
            button_frame,
            text="Connect to Selected APs",
            command=self._on_ok,
            width=20,
            bg="#28A745",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            activebackground="#218838",
            activeforeground="white"
        )
        ok_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Cancel button
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=12,
            bg="#6C757D",
            fg="white",
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            cursor="hand2",
            activebackground="#5A6268",
            activeforeground="white"
        )
        cancel_button.pack(side=tk.RIGHT)
    
    def _populate_list(self):
        """Populate the treeview with APs."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add filtered APs
        for ap in self.filtered_aps:
            self.tree.insert(
                "",
                tk.END,
                text="☐",  # Unchecked checkbox
                values=(
                    ap.get('retail_chain', ''),
                    ap.get('store_id', ''),
                    ap.get('store_alias', ''),
                    ap.get('ap_id', ''),
                    ap.get('ip_address', ''),
                    ap.get('type', '')
                ),
                tags=("unchecked",)
            )
        
        self._update_selection_label()
    
    def _on_search_changed(self, *args):
        """Handle search text changes."""
        query = self.search_var.get()
        
        if query:
            self.filtered_aps = self.credential_manager.search(query)
        else:
            self.filtered_aps = self.all_aps.copy()
        
        self._populate_list()
    
    def _clear_search(self):
        """Clear search field."""
        self.search_var.set("")
    
    def _on_tree_click(self, event):
        """Handle click on tree item to toggle checkbox."""
        region = self.tree.identify_region(event.x, event.y)
        if region == "tree":
            item = self.tree.identify_row(event.y)
            if item:
                self._toggle_checkbox(item)
    
    def _toggle_checkbox(self, item):
        """Toggle checkbox for an item."""
        current_text = self.tree.item(item, "text")
        
        if current_text == "☐":
            self.tree.item(item, text="☑", tags=("checked",))
        else:
            self.tree.item(item, text="☐", tags=("unchecked",))
        
        self._update_selection_label()
    
    def _select_all(self):
        """Select all visible items."""
        for item in self.tree.get_children():
            self.tree.item(item, text="☑", tags=("checked",))
        self._update_selection_label()
    
    def _deselect_all(self):
        """Deselect all items."""
        for item in self.tree.get_children():
            self.tree.item(item, text="☐", tags=("unchecked",))
        self._update_selection_label()
    
    def _update_selection_label(self):
        """Update the selection count label."""
        checked_count = sum(1 for item in self.tree.get_children() 
                           if self.tree.item(item, "text") == "☑")
        total_count = len(self.tree.get_children())
        
        self.selection_label.config(
            text=f"Selected: {checked_count} APs | Showing: {total_count} of {len(self.all_aps)} APs"
        )
    
    def _get_selected_aps(self):
        """Get list of selected AP credentials."""
        selected = []
        
        for item in self.tree.get_children():
            if self.tree.item(item, "text") == "☑":
                values = self.tree.item(item, "values")
                # Find the matching AP in filtered list
                ap_id = values[3]  # AP ID is at index 3
                for ap in self.filtered_aps:
                    if ap.get('ap_id') == ap_id:
                        selected.append(ap)
                        break
        
        return selected
    
    def _on_ok(self):
        """Handle OK button click."""
        selected = self._get_selected_aps()
        
        if not selected:
            messagebox.showwarning(
                "No Selection",
                "Please select at least one AP to connect to.",
                parent=self.dialog
            )
            return
        
        # Validate that selected APs have required credentials
        invalid_aps = []
        for ap in selected:
            if not ap.get('ip_address'):
                invalid_aps.append(f"{ap.get('ap_id', 'Unknown')} - Missing IP Address")
            if not ap.get('username_webui') or not ap.get('password_webui'):
                invalid_aps.append(f"{ap.get('ap_id', 'Unknown')} - Missing Web UI credentials")
        
        if invalid_aps:
            messagebox.showerror(
                "Invalid Credentials",
                "The following APs have incomplete credentials:\n\n" + "\n".join(invalid_aps),
                parent=self.dialog
            )
            return
        
        self.result = selected
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Handle Cancel button click."""
        self.result = []
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and wait for result."""
        self.dialog.wait_window()
        return self.result
