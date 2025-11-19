"""
Modern ESL AP Credential Manager - Enhanced UI with audit logging
Manage, search, import/export AP credentials with modern design
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from credential_manager_v2 import CredentialManager
from datetime import datetime
import re


class ModernCredentialManager:
    """Modern credential manager with enhanced UI and audit logging."""
    
    def __init__(self, current_user=None, parent=None, db_manager=None):
        """
        Initialize the modern credential manager.
        
        Args:
            current_user: Current user dict with role information
            parent: Parent window (optional)
            db_manager: Database manager for audit logging
        """
        self.current_user = current_user
        self.db_manager = db_manager
        
        if parent:
            self.root = tk.Toplevel(parent)
            self.root.transient(parent)
        else:
            self.root = tk.Tk()
        
        # Set title with user context
        if current_user:
            self.root.title(f"AP Credential Manager - {current_user['full_name']} ({current_user['role']})")
        else:
            self.root.title("AP Credential Manager")
        
        self.root.geometry("1400x800")
        self.root.configure(bg="#F5F5F5")
        
        # Initialize credential manager
        self.credential_manager = CredentialManager()
        self.selected_credential = None
        self.sort_reverse = {}
        self.search_timer = None
        
        # Check permissions
        self.is_admin = (current_user.get('role', '').lower() == 'admin' if current_user else False)
        
        self._build_ui()
        self._refresh_list()
        
        # Center window
        self._center_window()
    
    def _center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _build_ui(self):
        """Build the modern UI."""
        # Header
        header_frame = tk.Frame(self.root, bg="#2C3E50", height=70)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🔐 AP Credential Manager",
            font=("Segoe UI", 18, "bold"),
            bg="#2C3E50",
            fg="white"
        ).pack(side="left", padx=20, pady=15)
        
        # Stats in header
        self.stats_label = tk.Label(
            header_frame,
            text="Loading...",
            font=("Segoe UI", 11),
            bg="#2C3E50",
            fg="#BDC3C7"
        )
        self.stats_label.pack(side="right", padx=20)
        
        # Main content area
        content_frame = tk.Frame(self.root, bg="#F5F5F5")
        content_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Toolbar
        self._build_toolbar(content_frame)
        
        # Search frame
        self._build_search_frame(content_frame)
        
        # Credentials list
        self._build_credentials_list(content_frame)
        
        # Status bar
        self._build_status_bar()
    
    def _build_toolbar(self, parent):
        """Build the toolbar with action buttons."""
        toolbar = tk.Frame(parent, bg="#F5F5F5")
        toolbar.pack(fill="x", pady=(0, 10))
        
        # Left side buttons
        left_frame = tk.Frame(toolbar, bg="#F5F5F5")
        left_frame.pack(side="left")
        
        self._create_button(left_frame, "➕ Add New", "#28A745", self._add_credential).pack(side="left", padx=(0, 5))
        self._create_button(left_frame, "✏️ Edit", "#17A2B8", self._edit_credential).pack(side="left", padx=(0, 5))
        self._create_button(left_frame, "🗑️ Delete", "#DC3545", self._delete_credential).pack(side="left", padx=(0, 5))
        self._create_button(left_frame, "🔍 View Details", "#6C757D", self._view_details).pack(side="left", padx=(0, 5))
        
        # Admin-only buttons
        if self.is_admin:
            tk.Frame(left_frame, bg="#DEE2E6", width=2, height=30).pack(side="left", padx=10)
            self._create_button(left_frame, "📤 Import Excel", "#FFC107", self._import_excel).pack(side="left", padx=(0, 5))
            self._create_button(left_frame, "📥 Export Excel", "#FFC107", self._export_excel).pack(side="left", padx=(0, 5))
        
        # Right side buttons
        right_frame = tk.Frame(toolbar, bg="#F5F5F5")
        right_frame.pack(side="right")
        
        self._create_button(right_frame, "🔄 Refresh", "#6C757D", self._refresh_list).pack(side="left", padx=(0, 5))
        self._create_button(right_frame, "❌ Close", "#6C757D", self.root.destroy).pack(side="left")
    
    def _create_button(self, parent, text, color, command):
        """Create a modern styled button."""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=8,
            bd=0
        )
        
        # Hover effects
        def on_enter(e):
            btn.config(bg=self._darken_color(color))
        
        def on_leave(e):
            btn.config(bg=color)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    def _darken_color(self, color):
        """Darken a hex color by 10%."""
        # Simple darkening - subtract from RGB values
        color = color.lstrip('#')
        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        r = max(0, r - 25)
        g = max(0, g - 25)
        b = max(0, b - 25)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _build_search_frame(self, parent):
        """Build the search frame."""
        search_frame = tk.Frame(parent, bg="white", relief="solid", bd=1)
        search_frame.pack(fill="x", pady=(0, 10))
        
        # Padding frame
        inner_frame = tk.Frame(search_frame, bg="white")
        inner_frame.pack(fill="x", padx=15, pady=12)
        
        tk.Label(
            inner_frame,
            text="🔎 Search:",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg="#2C3E50"
        ).pack(side="left", padx=(0, 10))
        
        self.search_var = tk.StringVar()
        
        self.search_entry = tk.Entry(
            inner_frame,
            textvariable=self.search_var,
            font=("Segoe UI", 11),
            bg="#F8F9FA",
            fg="#495057",
            relief="solid",
            bd=1,
            width=50
        )
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=6)
        self.search_entry.focus_set()
        
        # Bind events for search
        self.search_entry.bind('<Return>', lambda e: self._on_search())
        self.search_entry.bind('<KeyRelease>', lambda e: self._on_search_delayed())
        
        # Search button
        search_btn = tk.Button(
            inner_frame,
            text="🔍",
            command=self._on_search,
            bg="#007BFF",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=10,
            bd=0
        )
        search_btn.pack(side="left", padx=(5, 0))
        
        # Clear button
        def clear_search():
            self.search_entry.delete(0, tk.END)
            self._on_search()  # Refresh to show all
        
        clear_btn = tk.Button(
            inner_frame,
            text="✖",
            command=clear_search,
            bg="#E9ECEF",
            fg="#6C757D",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=10,
            bd=0
        )
        clear_btn.pack(side="left", padx=(5, 0))
        
        # Result count
        self.result_label = tk.Label(
            inner_frame,
            text="",
            font=("Segoe UI", 10),
            bg="white",
            fg="#6C757D"
        )
        self.result_label.pack(side="left", padx=(15, 0))
    
    def _build_credentials_list(self, parent):
        """Build the credentials list with treeview."""
        list_frame = tk.Frame(parent, bg="white", relief="solid", bd=1)
        list_frame.pack(fill="both", expand=True)
        
        # Scrollbars
        vsb = ttk.Scrollbar(list_frame, orient="vertical")
        hsb = ttk.Scrollbar(list_frame, orient="horizontal")
        
        # Treeview
        columns = ("Retail Chain", "Store ID", "Store Name", "AP ID", "IP Address", 
                  "Type", "Web User", "SSH User", "Notes")
        
        style = ttk.Style()
        style.configure("Treeview", 
                       font=("Segoe UI", 10),
                       rowheight=28)
        style.configure("Treeview.Heading", 
                       font=("Segoe UI", 10, "bold"),
                       background="#E9ECEF",
                       foreground="#212529")
        style.map("Treeview",
                 background=[("selected", "#007BFF")],
                 foreground=[("selected", "white")])
        
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configure columns
        column_widths = [120, 90, 180, 110, 130, 100, 120, 120, 280]
        for col, width in zip(columns, column_widths):
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_by_column(c))
            self.tree.column(col, width=width, anchor="w")
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Bindings
        self.tree.bind('<Double-Button-1>', lambda e: self._on_double_click())
        self.tree.bind('<<TreeviewSelect>>', lambda e: self._on_select())
        self.tree.bind('<Return>', lambda e: self._view_details())
        
        # Context menu
        self._create_context_menu()
    
    def _create_context_menu(self):
        """Create right-click context menu."""
        self.context_menu = tk.Menu(self.root, tearoff=0, font=("Segoe UI", 10))
        self.context_menu.add_command(label="View Details", command=self._view_details)
        self.context_menu.add_command(label="Edit", command=self._edit_credential)
        self.context_menu.add_command(label="Copy AP ID", command=self._copy_ap_id)
        self.context_menu.add_command(label="Copy IP Address", command=self._copy_ip)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete", command=self._delete_credential, foreground="#DC3545")
        
        self.tree.bind("<Button-3>", self._show_context_menu)
    
    def _show_context_menu(self, event):
        """Show context menu on right click."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self._on_select()
            self.context_menu.post(event.x_root, event.y_root)
    
    def _build_status_bar(self):
        """Build status bar at bottom."""
        status_bar = tk.Frame(self.root, bg="#E9ECEF", height=30)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_bar,
            text="Ready",
            font=("Segoe UI", 9),
            bg="#E9ECEF",
            fg="#495057",
            anchor="w"
        )
        self.status_label.pack(side="left", padx=10)
    
    def _refresh_list(self, credentials=None):
        """Refresh the credentials list."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get credentials
        if credentials is None:
            credentials = self.credential_manager.get_all()
        
        # Populate tree
        for cred in credentials:
            notes = cred.get('notes', '')
            notes_preview = notes[:50] + '...' if len(notes) > 50 else notes
            
            values = (
                cred.get('retail_chain', ''),
                cred.get('store_id', ''),
                cred.get('store_alias', ''),
                cred.get('ap_id', ''),
                cred.get('ip_address', ''),
                cred.get('type', ''),
                cred.get('username_webui', ''),
                cred.get('username_ssh', ''),
                notes_preview
            )
            self.tree.insert('', 'end', values=values, 
                           tags=(str(cred.get('store_id', '')), str(cred.get('ap_id', ''))))
        
        # Update stats
        total = self.credential_manager.count()
        showing = len(credentials)
        self.stats_label.config(text=f"Total: {total} APs")
        self.result_label.config(text=f"Showing {showing} of {total}")
        self.status_label.config(text=f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    
    def _on_search_delayed(self):
        """Debounced search - waits for user to stop typing."""
        # Cancel previous timer if exists
        if self.search_timer:
            self.root.after_cancel(self.search_timer)
        
        # Set new timer for 300ms delay
        self.search_timer = self.root.after(300, self._on_search)
    
    def _on_search(self):
        """Handle search input with detailed logging."""
        # Get value directly from entry widget (more reliable than StringVar)
        query = self.search_entry.get().strip() if hasattr(self, 'search_entry') else ""
        
        print(f"[SEARCH] Query: '{query}'")
        
        if query:
            try:
                print(f"[SEARCH] Calling credential_manager.search('{query}')...")
                results = self.credential_manager.search(query)
                print(f"[SEARCH] Results type: {type(results)}")
                print(f"[SEARCH] Results count: {len(results) if results else 0}")
                
                if results:
                    print(f"[SEARCH] First result: {results[0] if results else 'None'}")
                    self._refresh_list(results)
                    self.status_label.config(text=f"Search: '{query}' - Found {len(results)} results")
                    print(f"[SEARCH] Successfully displayed {len(results)} results")
                    
                    # Log search action
                    if self.db_manager and self.current_user:
                        self._log_action(
                            'search',
                            f"Searched AP credentials: '{query}' - Found {len(results)} results",
                            None,
                            True
                        )
                else:
                    # No results found - clear list and show message
                    print(f"[SEARCH] No results found for '{query}'")
                    self._refresh_list([])
                    self.status_label.config(text=f"Search: '{query}' - No results found")
                    
                    # Log search action
                    if self.db_manager and self.current_user:
                        self._log_action(
                            'search',
                            f"Searched AP credentials: '{query}' - No results",
                            None,
                            True
                        )
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"[SEARCH ERROR] Exception: {e}")
                print(f"[SEARCH ERROR] Traceback:\n{error_details}")
                self.status_label.config(text=f"Search error: {str(e)}")
                
                # Log search error
                if self.db_manager and self.current_user:
                    self._log_action(
                        'search',
                        f"Search error: '{query}' - {str(e)}",
                        None,
                        False
                    )
        else:
            print(f"[SEARCH] Empty query, showing all results")
            self._refresh_list()
            self.status_label.config(text="Ready")
    
    def _on_select(self):
        """Handle credential selection."""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            if values and len(values) >= 4:
                store_id = str(values[1]).strip()
                ap_id = str(values[3]).strip()
                # Try to find by AP ID first (more reliable)
                self.selected_credential = self.credential_manager.find_by_ap_id(ap_id)
                if not self.selected_credential:
                    # Fallback to store and AP combo
                    self.selected_credential = self.credential_manager.find_by_store_and_ap(store_id, ap_id)
    
    def _on_double_click(self):
        """Handle double-click to view details."""
        if self.selected_credential:
            self._view_details()
    
    def _sort_by_column(self, col):
        """Sort treeview by column."""
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children('')]
        
        # Toggle sort direction
        reverse = self.sort_reverse.get(col, False)
        self.sort_reverse[col] = not reverse
        
        items.sort(reverse=reverse)
        
        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)
    
    def _add_credential(self):
        """Add new credential."""
        dialog = CredentialDialog(self.root, "Add New AP Credential", current_user=self.current_user)
        if dialog.result:
            success, message = self.credential_manager.add_credential(dialog.result)
            if success:
                self._log_action("ADD", dialog.result.get('ap_id', 'unknown'))
                messagebox.showinfo("Success", message, parent=self.root)
                self._refresh_list()
            else:
                messagebox.showerror("Error", message, parent=self.root)
    
    def _edit_credential(self):
        """Edit selected credential."""
        if not self.selected_credential:
            messagebox.showwarning("No Selection", "Please select a credential to edit", parent=self.root)
            return
        
        dialog = CredentialDialog(self.root, "Edit AP Credential", 
                                 credential=self.selected_credential,
                                 current_user=self.current_user)
        if dialog.result:
            # Check if delete was requested from dialog
            if dialog.result.get('_delete'):
                success, message = self.credential_manager.delete_credential(
                    dialog.result['store_id'],
                    dialog.result['ap_id']
                )
                if success:
                    self._log_action("DELETE", dialog.result['ap_id'])
                    messagebox.showinfo("Success", message, parent=self.root)
                    self._refresh_list()
                else:
                    messagebox.showerror("Error", message, parent=self.root)
            else:
                # Normal edit
                success, message = self.credential_manager.update_credential(
                    self.selected_credential['store_id'],
                    self.selected_credential['ap_id'],
                    dialog.result
                )
                if success:
                    self._log_action("EDIT", self.selected_credential.get('ap_id', 'unknown'))
                    messagebox.showinfo("Success", message, parent=self.root)
                    self._refresh_list()
                else:
                    messagebox.showerror("Error", message, parent=self.root)
    
    def _delete_credential(self):
        """Delete selected credential."""
        if not self.selected_credential:
            messagebox.showwarning("No Selection", "Please select a credential to delete", parent=self.root)
            return
        
        ap_id = self.selected_credential.get('ap_id', 'unknown')
        store_id = self.selected_credential.get('store_id', 'unknown')
        
        if messagebox.askyesno("Confirm Delete",
                              f"Are you sure you want to delete credentials for:\n\n"
                              f"Store: {store_id}\n"
                              f"AP ID: {ap_id}\n\n"
                              f"This action cannot be undone.",
                              parent=self.root):
            success, message = self.credential_manager.delete_credential(store_id, ap_id)
            if success:
                self._log_action("DELETE", ap_id)
                messagebox.showinfo("Success", message, parent=self.root)
                self._refresh_list()
            else:
                messagebox.showerror("Error", message, parent=self.root)
    
    def _view_details(self):
        """View detailed information about selected credential."""
        if not self.selected_credential:
            messagebox.showwarning("No Selection", "Please select a credential to view", parent=self.root)
            return
        
        CredentialDetailDialog(self.root, self.selected_credential)
    
    def _copy_ap_id(self):
        """Copy AP ID to clipboard."""
        if self.selected_credential:
            ap_id = self.selected_credential.get('ap_id', '')
            self.root.clipboard_clear()
            self.root.clipboard_append(ap_id)
            self.status_label.config(text=f"Copied AP ID: {ap_id}")
    
    def _copy_ip(self):
        """Copy IP address to clipboard."""
        if self.selected_credential:
            ip = self.selected_credential.get('ip_address', '')
            if ip:
                self.root.clipboard_clear()
                self.root.clipboard_append(ip)
                self.status_label.config(text=f"Copied IP: {ip}")
    
    def _import_excel(self):
        """Import credentials from Excel."""
        if not self.is_admin:
            messagebox.showerror("Access Denied", "Only administrators can import credentials", parent=self.root)
            return
        
        filename = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
            parent=self.root
        )
        
        if filename:
            self.status_label.config(text="Importing...")
            self.root.update()
            
            success, message = self.credential_manager.import_from_excel(filename)
            if success:
                self._log_action("IMPORT", Path(filename).name)
                messagebox.showinfo("Import Success", message, parent=self.root)
                self._refresh_list()
            else:
                messagebox.showerror("Import Error", message, parent=self.root)
    
    def _export_excel(self):
        """Export credentials to Excel."""
        if not self.is_admin:
            messagebox.showerror("Access Denied", "Only administrators can export credentials", parent=self.root)
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Excel File",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            parent=self.root
        )
        
        if filename:
            self.status_label.config(text="Exporting...")
            self.root.update()
            
            success, message = self.credential_manager.export_to_excel(filename)
            if success:
                self._log_action("EXPORT", Path(filename).name)
                messagebox.showinfo("Export Success", message, parent=self.root)
            else:
                messagebox.showerror("Export Error", message, parent=self.root)
    
    def _log_action(self, action, target):
        """Log credential management action."""
        if self.db_manager and self.current_user:
            try:
                username = self.current_user.get('username', 'unknown')
                self.db_manager.log_user_activity(
                    username=username,
                    activity_type=f"CREDENTIAL_{action}",
                    description=f"Credential {action.lower()} for AP: {target}",
                    ap_id=target,
                    success=True
                )
            except Exception as e:
                print(f"Failed to log action: {e}")


class CredentialDialog:
    """Dialog for adding/editing credentials."""
    
    def __init__(self, parent, title, credential=None, current_user=None):
        self.result = None
        self.credential = credential
        self.current_user = current_user
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("850x680")
        self.dialog.configure(bg="#F5F5F5")
        self.dialog.transient(parent)
        
        self._build_dialog()
        self._center_dialog(parent)
        
        # Safer grab handling - wait for window to be ready
        self.dialog.update_idletasks()
        try:
            self.dialog.grab_set()
        except tk.TclError:
            # If grab fails, continue without it
            pass
        
        self.dialog.wait_window()
    
    def _center_dialog(self, parent):
        """Center dialog on parent."""
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _build_dialog(self):
        """Build the dialog UI with improved two-column layout."""
        # Header with AP ID - left aligned, no icon
        header = tk.Frame(self.dialog, bg="#2C3E50", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        header_inner = tk.Frame(header, bg="#2C3E50")
        header_inner.pack(fill="both", expand=True, padx=20, pady=12)
        
        # Title on left
        title_text = "Edit AP Credential" if self.credential else "Add New AP Credential"
        tk.Label(
            header_inner,
            text=title_text,
            font=("Segoe UI", 14, "bold"),
            bg="#2C3E50",
            fg="white",
            anchor="w"
        ).pack(side="left")
        
        # AP ID on right (if editing)
        if self.credential:
            ap_id = self.credential.get('ap_id', 'N/A')
            tk.Label(
                header_inner,
                text=f"AP ID: {ap_id}",
                font=("Segoe UI", 12),
                bg="#2C3E50",
                fg="#BDC3C7",
                anchor="e"
            ).pack(side="right")
        
        # Main content area with form on left, buttons on right
        content_area = tk.Frame(self.dialog, bg="#F5F5F5")
        content_area.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Left side: Form with scrollbar
        form_container = tk.Frame(content_area, bg="#F5F5F5")
        form_container.pack(side="left", fill="both", expand=True)
        
        canvas = tk.Canvas(form_container, bg="#F5F5F5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(form_container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#F5F5F5")
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Form fields in white card
        form_frame = tk.Frame(scroll_frame, bg="white", relief="solid", bd=1)
        form_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        inner_form = tk.Frame(form_frame, bg="white")
        inner_form.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.fields = {}
        
        # Two-column layout for better space usage
        field_specs = [
            # Left column fields
            [("retail_chain", "Retail Chain", False, "entry", "e.g., Elkjop, Elgiganten"),
             ("store_id", "Store ID", True, "entry", "Store identification number"),
             ("store_alias", "Store Name/Alias", False, "entry", "Store name or alias"),
             ("ap_id", "AP ID", True, "entry", "Access Point ID (required)"),
             ("ip_address", "IP Address", False, "entry", "192.168.1.100"),
             ("type", "AP Type", False, "combo", "VERA, MobileRouter, etc.")],
            # Right column fields
            [("username_webui", "Web UI Username", False, "entry", "admin, root, etc."),
             ("password_webui", "Web UI Password", False, "password", "Password for web interface"),
             ("username_ssh", "SSH Username", False, "entry", "root, admin, etc."),
             ("password_ssh", "SSH Password", False, "password", "Password for SSH access"),
             ("su_password", "SU Password", False, "password", "Superuser password"),
             ("", "", False, "", "")]  # Spacer
        ]
        
        # Create two-column grid
        for col_idx, column_fields in enumerate(field_specs):
            col_frame = tk.Frame(inner_form, bg="white")
            col_frame.grid(row=0, column=col_idx, sticky="nsew", padx=(0, 15 if col_idx == 0 else 0))
            
            for row, (field_name, label_text, required, field_type, hint) in enumerate(column_fields):
                if not field_name:  # Skip spacer
                    continue
                    
                # Label
                label = tk.Label(
                    col_frame,
                    text=label_text + (" *" if required else ""),
                    font=("Segoe UI", 9, "bold"),
                    bg="white",
                    fg="#2C3E50",
                    anchor="w"
                )
                label.grid(row=row*3, column=0, sticky="w", pady=(8 if row > 0 else 0, 2))
                
                # Field widget
                if field_type == "combo":
                    widget = ttk.Combobox(col_frame, font=("Segoe UI", 9),
                                         values=["VERA", "MobileRouter", "Other"], width=25)
                    widget.grid(row=row*3+1, column=0, sticky="ew", ipady=3)
                    if self.credential:
                        widget.set(self.credential.get(field_name, ""))
                else:
                    widget = tk.Entry(col_frame, font=("Segoe UI", 9),
                                    bg="#F8F9FA", relief="solid", bd=1)
                    if field_type == "password":
                        widget.config(show="●")
                    widget.grid(row=row*3+1, column=0, sticky="ew", ipady=5)
                    if self.credential:
                        widget.insert(0, self.credential.get(field_name, ""))
                
                self.fields[field_name] = widget
                
                # Hint
                hint_label = tk.Label(
                    col_frame,
                    text=hint,
                    font=("Segoe UI", 7),
                    bg="white",
                    fg="#6C757D",
                    anchor="w"
                )
                hint_label.grid(row=row*3+2, column=0, sticky="w")
                
                col_frame.columnconfigure(0, weight=1)
        
        # Notes field spans both columns
        notes_label = tk.Label(
            inner_form,
            text="Notes",
            font=("Segoe UI", 9, "bold"),
            bg="white",
            fg="#2C3E50",
            anchor="w"
        )
        notes_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(15, 2))
        
        notes_widget = tk.Text(inner_form, height=4, font=("Segoe UI", 9),
                              bg="#F8F9FA", relief="solid", bd=1)
        notes_widget.grid(row=2, column=0, columnspan=2, sticky="ew")
        if self.credential:
            notes_widget.insert("1.0", self.credential.get("notes", ""))
        self.fields["notes"] = notes_widget
        
        notes_hint = tk.Label(
            inner_form,
            text="Additional notes or information",
            font=("Segoe UI", 7),
            bg="white",
            fg="#6C757D",
            anchor="w"
        )
        notes_hint.grid(row=3, column=0, columnspan=2, sticky="w")
        
        inner_form.columnconfigure(0, weight=1)
        inner_form.columnconfigure(1, weight=1)
        
        # Right side: Vertical button panel
        button_panel = tk.Frame(content_area, bg="white", relief="solid", bd=1, width=140)
        button_panel.pack(side="right", fill="y", padx=(10, 0))
        button_panel.pack_propagate(False)
        
        tk.Label(
            button_panel,
            text="Actions",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#2C3E50"
        ).pack(pady=(15, 15))
        
        # Save button with modern styling
        save_btn = tk.Button(
            button_panel,
            text="💾 Save",
            command=self._save,
            bg="#28A745",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            width=12,
            height=2,
            bd=0,
            activebackground="#218838",
            activeforeground="white"
        )
        save_btn.pack(pady=(0, 8), padx=10)
        
        # Enhanced hover effect for save
        def on_save_enter(e):
            save_btn.config(bg="#218838", relief="raised")
        def on_save_leave(e):
            save_btn.config(bg="#28A745", relief="flat")
        save_btn.bind("<Enter>", on_save_enter)
        save_btn.bind("<Leave>", on_save_leave)
        
        # Cancel button with modern styling
        cancel_btn = tk.Button(
            button_panel,
            text="✖ Cancel",
            command=self.dialog.destroy,
            bg="#6C757D",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            width=12,
            height=2,
            bd=0,
            activebackground="#5A6268",
            activeforeground="white"
        )
        cancel_btn.pack(pady=(0, 8), padx=10)
        
        # Enhanced hover effect for cancel
        def on_cancel_enter(e):
            cancel_btn.config(bg="#5A6268", relief="raised")
        def on_cancel_leave(e):
            cancel_btn.config(bg="#6C757D", relief="flat")
        cancel_btn.bind("<Enter>", on_cancel_enter)
        cancel_btn.bind("<Leave>", on_cancel_leave)
        
        # If editing, add delete button
        if self.credential:
            # Separator
            tk.Frame(button_panel, bg="#DEE2E6", height=1).pack(fill="x", padx=10, pady=15)
            
            delete_btn = tk.Button(
                button_panel,
                text="🗑️ Delete",
                command=self._delete,
                bg="#DC3545",
                fg="white",
                font=("Segoe UI", 9, "bold"),
                relief="flat",
                cursor="hand2",
                width=12,
                height=2,
                bd=0,
                activebackground="#C82333",
                activeforeground="white"
            )
            delete_btn.pack(pady=(0, 10), padx=10)
            
            def on_delete_enter(e):
                delete_btn.config(bg="#C82333", relief="raised")
            def on_delete_leave(e):
                delete_btn.config(bg="#DC3545", relief="flat")
            delete_btn.bind("<Enter>", on_delete_enter)
            delete_btn.bind("<Leave>", on_delete_leave)
    
    def _save(self):
        """Save credential data."""
        data = {}
        for field_name, widget in self.fields.items():
            if isinstance(widget, tk.Text):
                data[field_name] = widget.get("1.0", "end-1c").strip()
            else:
                data[field_name] = widget.get().strip()
        
        # Validate required fields
        if not data.get('store_id'):
            messagebox.showerror("Validation Error", "Store ID is required", parent=self.dialog)
            return
        
        if not data.get('ap_id'):
            messagebox.showerror("Validation Error", "AP ID is required", parent=self.dialog)
            return
        
        # Validate IP address format if provided
        if data.get('ip_address'):
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if not re.match(ip_pattern, data['ip_address']):
                messagebox.showerror("Validation Error", 
                                   "Invalid IP address format\nExpected format: xxx.xxx.xxx.xxx",
                                   parent=self.dialog)
                return
        
        self.result = data
        self.dialog.destroy()
    
    def _delete(self):
        """Delete the current credential."""
        if not self.credential:
            return
        
        ap_id = self.credential.get('ap_id', 'unknown')
        store_id = self.credential.get('store_id', 'unknown')
        
        if messagebox.askyesno("Confirm Delete",
                              f"Delete credentials for:\n\nStore: {store_id}\nAP ID: {ap_id}\n\nThis cannot be undone.",
                              parent=self.dialog):
            self.result = {'_delete': True, 'store_id': store_id, 'ap_id': ap_id}
            self.dialog.destroy()


class CredentialDetailDialog:
    """Dialog for viewing detailed credential information."""
    
    def __init__(self, parent, credential):
        self.credential = credential
        self.password_visible = {}  # Track visibility state for each password field
        self.password_fields = {}  # Store password values
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"AP Details - {credential.get('ap_id', 'Unknown')}")
        self.dialog.geometry("730x750")
        self.dialog.configure(bg="#F5F5F5")
        self.dialog.transient(parent)
        
        self._build_dialog()
        self._center_dialog(parent)
        
        # Optional grab for detail dialog (non-blocking)
        self.dialog.update_idletasks()
        try:
            self.dialog.grab_set()
        except tk.TclError:
            pass
    
    def _center_dialog(self, parent):
        """Center dialog on parent."""
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _build_dialog(self):
        """Build the detail view dialog with enhanced styling."""
        # Modern header with gradient-like effect
        header = tk.Frame(self.dialog, bg="#17A2B8", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        header_inner = tk.Frame(header, bg="#17A2B8")
        header_inner.pack(fill="both", expand=True, padx=25, pady=15)
        
        # Title
        tk.Label(
            header_inner,
            text="AP Credential Details",
            font=("Segoe UI", 16, "bold"),
            bg="#17A2B8",
            fg="white",
            anchor="w"
        ).pack(side="left")
        
        # AP ID badge on right
        ap_id = self.credential.get('ap_id', 'N/A')
        badge_frame = tk.Frame(header_inner, bg="#138496", relief="flat", bd=0)
        badge_frame.pack(side="right", padx=5)
        
        tk.Label(
            badge_frame,
            text=f"  {ap_id}  ",
            font=("Segoe UI", 14, "bold"),
            bg="#138496",
            fg="white"
        ).pack(padx=12, pady=6)
        
        # Content area with better spacing
        content = tk.Frame(self.dialog, bg="#F5F5F5")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Card-style container
        card = tk.Frame(content, bg="white", relief="solid", bd=1)
        card.pack(fill="both", expand=True)
        
        # Scrollable text with modern styling
        text_frame = tk.Frame(card, bg="white")
        text_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        text_widget = tk.Text(
            text_frame,
            font=("Segoe UI", 10),
            bg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=15,
            wrap="word",
            yscrollcommand=scrollbar.set
        )
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # Configure modern tags
        text_widget.tag_configure("section", font=("Segoe UI", 12, "bold"), foreground="#17A2B8", spacing3=8)
        text_widget.tag_configure("label", font=("Segoe UI", 10, "bold"), foreground="#495057")
        text_widget.tag_configure("value", font=("Segoe UI", 10), foreground="#212529")
        text_widget.tag_configure("password", font=("Segoe UI", 10), foreground="#DC3545", background="#FFF3CD")
        text_widget.tag_configure("empty", font=("Segoe UI", 9, "italic"), foreground="#ADB5BD")
        
        # Store text widget for password reveal functionality
        self.text_widget = text_widget
        
        # Insert data with modern formatting
        # Store Information Section
        text_widget.insert("end", "📍 Store Information\n", "section")
        text_widget.insert("end", "─" * 45 + "\n")
        
        store_fields = [
            ("Retail Chain", "retail_chain"),
            ("Store ID", "store_id"),
            ("Store Name/Alias", "store_alias"),
        ]
        
        for label, field in store_fields:
            text_widget.insert("end", f"{label:.<30} ", "label")
            value = self.credential.get(field, "")
            if value:
                text_widget.insert("end", f"{value}\n", "value")
            else:
                text_widget.insert("end", "(not set)\n", "empty")
        
        # Access Point Information Section
        text_widget.insert("end", "\n🔌 Access Point Information\n", "section")
        text_widget.insert("end", "─" * 45 + "\n")
        
        ap_fields = [
            ("AP ID", "ap_id"),
            ("IP Address", "ip_address"),
            ("AP Type", "type"),
        ]
        
        for label, field in ap_fields:
            text_widget.insert("end", f"{label:.<30} ", "label")
            value = self.credential.get(field, "")
            if value:
                text_widget.insert("end", f"{value}\n", "value")
            else:
                text_widget.insert("end", "(not set)\n", "empty")
        
        # Credentials Section with password reveal buttons
        text_widget.insert("end", "\n🔐 Credentials\n", "section")
        text_widget.insert("end", "─" * 45 + "\n")
        
        cred_fields = [
            ("Web UI Username", "username_webui", False),
            ("Web UI Password", "password_webui", True),
            ("SSH Username", "username_ssh", False),
            ("SSH Password", "password_ssh", True),
            ("SU Password", "su_password", True),
        ]
        
        for label, field, is_password in cred_fields:
            text_widget.insert("end", f"{label:.<30} ", "label")
            value = self.credential.get(field, "")
            
            if is_password and value:
                # Store password value and create reveal button
                self.password_fields[field] = value
                self.password_visible[field] = False
                
                # Insert masked password with marker
                start_idx = text_widget.index("end-1c")
                text_widget.insert("end", f"{'●' * 10}", "password")
                text_widget.insert("end", "  ")
                
                # Create reveal button
                reveal_btn = tk.Button(
                    text_widget,
                    text="👁",
                    command=lambda f=field: self._toggle_password(f),
                    bg="#FFF3CD",
                    fg="#856404",
                    font=("Segoe UI", 9),
                    relief="flat",
                    cursor="hand2",
                    width=2,
                    bd=0,
                    padx=2,
                    pady=0
                )
                text_widget.window_create("end", window=reveal_btn)
                
                # Store button reference
                if not hasattr(self, 'password_buttons'):
                    self.password_buttons = {}
                self.password_buttons[field] = (reveal_btn, start_idx)
                
                text_widget.insert("end", "\n")
            elif value:
                text_widget.insert("end", f"{value}\n", "value")
            else:
                text_widget.insert("end", "(not set)\n", "empty")
        
        # Notes Section
        notes = self.credential.get("notes", "")
        if notes:
            text_widget.insert("end", "\n📝 Notes\n", "section")
            text_widget.insert("end", "─" * 45 + "\n")
            text_widget.insert("end", f"{notes}\n", "value")
        
        text_widget.insert("end", "\n" + "─" * 45 + "\n")
        text_widget.config(state="disabled")
        
        # Button with modern styling
        btn_frame = tk.Frame(self.dialog, bg="#F5F5F5")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        close_btn = tk.Button(
            btn_frame,
            text="✓ Close",
            command=self.dialog.destroy,
            bg="#17A2B8",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            cursor="hand2",
            padx=30,
            pady=10,
            activebackground="#138496",
            activeforeground="white"
        )
        close_btn.pack(side="right")
        
        # Hover effect
        def on_close_enter(e):
            close_btn.config(bg="#138496", relief="raised")
        def on_close_leave(e):
            close_btn.config(bg="#17A2B8", relief="flat")
        close_btn.bind("<Enter>", on_close_enter)
        close_btn.bind("<Leave>", on_close_leave)
    
    def _toggle_password(self, field):
        """Toggle password visibility."""
        if field not in self.password_buttons:
            return
        
        button, start_idx = self.password_buttons[field]
        self.text_widget.config(state="normal")
        
        # Calculate end index (start + 10 chars for bullets)
        end_idx = f"{start_idx}+10c"
        
        # Delete current content
        self.text_widget.delete(start_idx, end_idx)
        
        # Toggle visibility and insert appropriate content
        if self.password_visible[field]:
            # Hide password
            self.text_widget.insert(start_idx, f"{'●' * 10}", "password")
            self.password_visible[field] = False
        else:
            # Show password
            password = self.password_fields[field]
            # Pad to 10 chars for consistent layout
            display_text = password.ljust(10)[:10]
            self.text_widget.insert(start_idx, display_text, "password")
            self.password_visible[field] = True
        
        self.text_widget.config(state="disabled")


# Convenience function
def open_credential_manager(current_user=None, parent=None, db_manager=None):
    """Open the modern credential manager."""
    return ModernCredentialManager(current_user, parent, db_manager)


if __name__ == "__main__":
    # Test standalone
    app = ModernCredentialManager()
    app.root.mainloop()
