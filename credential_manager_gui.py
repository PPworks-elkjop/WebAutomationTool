"""
ESL AP Credential Manager GUI - Manage, search, import/export AP credentials
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from credential_manager import CredentialManager

class CredentialManagerGUI:
    def __init__(self, current_user=None, parent=None):
        self.current_user = current_user
        
        if parent:
            self.root = tk.Toplevel(parent)
        else:
            self.root = tk.Tk()
        
        # Set title with user context if available
        if current_user:
            self.root.title(f"ESL AP Credential Manager - {current_user['full_name']} ({current_user['role']})")
        else:
            self.root.title("ESL AP Credential Manager")
        
        self.root.geometry("1200x700")
        
        self.credential_manager = CredentialManager()
        self.selected_credential = None
        
        self._build_ui()
        self._refresh_list()
    
    def _build_ui(self):
        # Configure modern style
        style = ttk.Style()
        style.theme_use('clam')
        
        bg_color = "#F5F5F5"
        frame_bg = "#FFFFFF"
        accent_color = "#28A745"
        
        self.root.configure(bg=bg_color)
        
        style.configure("Modern.TFrame", background=frame_bg)
        style.configure("Modern.TLabelframe", background=frame_bg)
        style.configure("Modern.TLabelframe.Label", background=frame_bg, foreground="#333", font=("Segoe UI", 11, "bold"))
        style.configure("Modern.TLabel", background=frame_bg, foreground="#555", font=("Segoe UI", 10))
        style.configure("Modern.TButton", background=accent_color, foreground="white", font=("Segoe UI", 10), padding=6)
        
        # Main container
        main_frame = ttk.Frame(self.root, padding=15, style="Modern.TFrame")
        main_frame.pack(fill="both", expand=True)
        
        # Top toolbar
        toolbar = ttk.Frame(main_frame, style="Modern.TFrame")
        toolbar.pack(fill="x", pady=(0, 10))
        
        ttk.Button(toolbar, text="➕ Add New", command=self._add_credential, style="Modern.TButton").pack(side="left", padx=(0, 5))
        ttk.Button(toolbar, text="✏️ Edit", command=self._edit_credential, style="Modern.TButton").pack(side="left", padx=(0, 5))
        ttk.Button(toolbar, text="🗑️ Delete", command=self._delete_credential, style="Modern.TButton").pack(side="left", padx=(0, 5))
        ttk.Button(toolbar, text="📤 Import Excel", command=self._import_excel, style="Modern.TButton").pack(side="left", padx=(0, 5))
        ttk.Button(toolbar, text="📥 Export Excel", command=self._export_excel, style="Modern.TButton").pack(side="left", padx=(0, 5))
        ttk.Button(toolbar, text="🔄 Refresh", command=self._refresh_list, style="Modern.TButton").pack(side="left", padx=(0, 5))
        ttk.Button(toolbar, text="❌ Close", command=self.root.quit, style="Modern.TButton").pack(side="right")
        
        # Search frame
        search_frame = ttk.LabelFrame(main_frame, text="Search", padding=10, style="Modern.TLabelframe")
        search_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:", style="Modern.TLabel").pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._on_search())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40, font=("Segoe UI", 10))
        search_entry.pack(side="left", padx=5)
        
        ttk.Label(search_frame, text=f"Total: {self.credential_manager.count()}", style="Modern.TLabel", name="count_label").pack(side="right", padx=10)
        
        # Credentials list
        list_frame = ttk.LabelFrame(main_frame, text="Credentials", padding=10, style="Modern.TLabelframe")
        list_frame.pack(fill="both", expand=True)
        
        # Create Treeview with scrollbars
        tree_scroll_y = ttk.Scrollbar(list_frame)
        tree_scroll_y.pack(side="right", fill="y")
        
        tree_scroll_x = ttk.Scrollbar(list_frame, orient="horizontal")
        tree_scroll_x.pack(side="bottom", fill="x")
        
        columns = ("Retail Chain", "Store ID", "Store Alias", "AP ID", "IP Address", "Type", "Web User", "SSH User", "Notes")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings",
                                yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)
        
        # Configure columns
        column_widths = [120, 100, 150, 100, 130, 100, 120, 120, 250]
        for col, width in zip(columns, column_widths):
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_column(c))
            self.tree.column(col, width=width)
        
        self.tree.pack(fill="both", expand=True)
        self.tree.bind('<Double-Button-1>', lambda e: self._on_double_click(e))
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<ButtonRelease-1>', self._on_click)
    
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
            values = (
                cred.get('retail_chain', ''),
                cred.get('store_id', ''),
                cred.get('store_alias', ''),
                cred.get('ap_id', ''),
                cred.get('ip_address', ''),
                cred.get('type', ''),
                cred.get('username_webui', ''),
                cred.get('username_ssh', ''),
                cred.get('notes', '')[:50] + '...' if len(cred.get('notes', '')) > 50 else cred.get('notes', '')
            )
            item_id = self.tree.insert('', 'end', values=values, tags=(cred['store_id'], cred['ap_id']))
        
        # Update count
        count_label = search_frame_widgets = None
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.LabelFrame) and "Search" in str(child):
                        for label in child.winfo_children():
                            if isinstance(label, ttk.Label) and "Total" in label.cget("text"):
                                label.config(text=f"Total: {self.credential_manager.count()} | Showing: {len(credentials)}")
    
    def _on_search(self):
        """Handle search input."""
        query = self.search_var.get()
        if query.strip():
            results = self.credential_manager.search(query)
            self._refresh_list(results)
        else:
            self._refresh_list()
    
    def _on_select(self, event):
        """Handle credential selection."""
        self._update_selected_credential()
    
    def _on_click(self, event):
        """Handle mouse click."""
        self._update_selected_credential()
    
    def _on_double_click(self, event):
        """Handle double-click to edit."""
        self._update_selected_credential()
        if self.selected_credential:
            self._edit_credential()
    
    def _update_selected_credential(self):
        """Update the selected credential from tree selection."""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            if values and len(values) >= 4:
                # Store ID is at index 1, AP ID is at index 3
                store_id = str(values[1])
                ap_id = str(values[3])
                self.selected_credential = self.credential_manager.find_by_store_and_ap(store_id, ap_id)
        else:
            self.selected_credential = None
    
    def _add_credential(self):
        """Open dialog to add new credential."""
        dialog = CredentialDialog(self.root, "Add Credential")
        if dialog.result:
            success, message = self.credential_manager.add_credential(dialog.result)
            if success:
                messagebox.showinfo("Success", message)
                self._refresh_list()
            else:
                messagebox.showerror("Error", message)
    
    def _edit_credential(self):
        """Edit selected credential."""
        if not self.selected_credential:
            messagebox.showwarning("No Selection", "Please select a credential to edit")
            return
        
        dialog = CredentialDialog(self.root, "Edit Credential", self.selected_credential)
        if dialog.result:
            success, message = self.credential_manager.update_credential(
                self.selected_credential['store_id'],
                self.selected_credential['ap_id'],
                dialog.result
            )
            if success:
                messagebox.showinfo("Success", message)
                self._refresh_list()
            else:
                messagebox.showerror("Error", message)
    
    def _delete_credential(self):
        """Delete selected credential."""
        if not self.selected_credential:
            messagebox.showwarning("No Selection", "Please select a credential to delete")
            return
        
        if messagebox.askyesno("Confirm Delete",
                              f"Delete credential for Store {self.selected_credential['store_id']}, "
                              f"AP {self.selected_credential['ap_id']}?"):
            success, message = self.credential_manager.delete_credential(
                self.selected_credential['store_id'],
                self.selected_credential['ap_id']
            )
            if success:
                messagebox.showinfo("Success", message)
                self._refresh_list()
            else:
                messagebox.showerror("Error", message)
    
    def _import_excel(self):
        """Import credentials from Excel file."""
        filename = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if filename:
            success, message = self.credential_manager.import_from_excel(filename)
            if success:
                messagebox.showinfo("Import Success", message)
                self._refresh_list()
            else:
                messagebox.showerror("Import Error", message)
    
    def _export_excel(self):
        """Export credentials to Excel file."""
        filename = filedialog.asksaveasfilename(
            title="Save Excel File",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if filename:
            success, message = self.credential_manager.export_to_excel(filename)
            if success:
                messagebox.showinfo("Export Success", message)
            else:
                messagebox.showerror("Export Error", message)
    
    def _sort_column(self, col):
        """Sort treeview by column."""
        # TODO: Implement sorting
        pass
    
    def get_selected_credential(self):
        """Return the currently selected credential."""
        return self.selected_credential


class CredentialDialog:
    """Dialog for adding/editing credentials."""
    def __init__(self, parent, title, credential=None):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Create form
        form_frame = ttk.Frame(self.dialog, padding=20)
        form_frame.pack(fill="both", expand=True)
        
        self.fields = {}
        field_names = [
            ("retail_chain", "Retail Chain:", False),
            ("store_id", "Store ID:", False),
            ("store_alias", "Store Alias:", False),
            ("ap_id", "AP ID:", True),
            ("ip_address", "IP Address:", False),
            ("type", "Type:", False),
            ("username_webui", "Username Web UI:", False),
            ("password_webui", "Password Web UI:", True),
            ("username_ssh", "Username SSH:", False),
            ("password_ssh", "Password SSH:", True),
            ("su_password", "SU Password:", False),
            ("notes", "Notes:", False),
        ]
        
        for row, (field_name, label_text, required) in enumerate(field_names):
            label = ttk.Label(form_frame, text=label_text + (" *" if required else ""))
            label.grid(row=row, column=0, sticky="w", pady=5, padx=(0, 10))
            
            if field_name == "notes":
                # Text widget for notes
                text_widget = tk.Text(form_frame, height=4, width=40, font=("Segoe UI", 10))
                text_widget.grid(row=row, column=1, sticky="ew", pady=5)
                if credential:
                    text_widget.insert("1.0", credential.get(field_name, ""))
                self.fields[field_name] = text_widget
            else:
                # Entry widget for other fields
                entry = ttk.Entry(form_frame, width=40, font=("Segoe UI", 10))
                entry.grid(row=row, column=1, sticky="ew", pady=5)
                if credential:
                    entry.insert(0, credential.get(field_name, ""))
                self.fields[field_name] = entry
        
        form_frame.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog, padding=20)
        button_frame.pack(fill="x")
        
        ttk.Button(button_frame, text="Save", command=self._save).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side="right")
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.dialog.wait_window()
    
    def _save(self):
        """Save credential data."""
        # Get values from fields
        data = {}
        for field_name, widget in self.fields.items():
            if isinstance(widget, tk.Text):
                data[field_name] = widget.get("1.0", "end-1c").strip()
            else:
                data[field_name] = widget.get().strip()
        
        # Validate required fields
        if not data.get('store_id') or not data.get('ap_id'):
            messagebox.showerror("Validation Error", "Store ID and AP ID are required", parent=self.dialog)
            return
        
        self.result = data
        self.dialog.destroy()


def main():
    from login_dialog import LoginDialog
    import tkinter as tk
    
    # Show login dialog first (it creates its own Tk window)
    login = LoginDialog()
    current_user = login.show()
    
    if not current_user:
        # User cancelled login
        login.get_root().destroy()
        return
    
    # Destroy login window and create new one for credential manager
    login.get_root().destroy()
    
    # Show credential manager
    app = CredentialManagerGUI()
    app.root.title(f"Credential Manager - {current_user['full_name']} ({current_user['role']})")
    app.root.mainloop()


if __name__ == "__main__":
    main()
