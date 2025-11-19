"""
Vusion API Configuration GUI
Manages API keys and tests connections for Vusion services.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from vusion_api_config import VusionAPIConfig, get_vusion_config
from vusion_api_helper import VusionAPIHelper


class VusionAPIConfigDialog:
    """Dialog for managing Vusion API configurations."""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.config = get_vusion_config()
        self.helper = VusionAPIHelper(self.config)
        
        # Create dialog window
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title("Vusion API Configuration")
        self.window.geometry("900x700")
        self.window.configure(bg="#F8F9FA")
        
        # Modal if parent exists
        if parent:
            self.window.transient(parent)
            self.window.grab_set()
        
        self._create_ui()
        self._load_existing_keys()
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
    
    def _create_ui(self):
        """Create the UI components."""
        # Header
        header = tk.Frame(self.window, bg="#3D6B9E", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="Vusion API Configuration",
                font=('Segoe UI', 16, 'bold'),
                bg="#3D6B9E", fg="white").pack(side=tk.LEFT, padx=20, pady=20)
        
        tk.Label(header, text="Manage API keys for multiple countries and services",
                font=('Segoe UI', 9),
                bg="#3D6B9E", fg="#E0E0E0").pack(side=tk.LEFT, padx=(0, 20), pady=20)
        
        # Main content area
        content = tk.Frame(self.window, bg="#F8F9FA", padx=20, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        info_frame = tk.Frame(content, bg="#E7F3FF", bd=1, relief=tk.SOLID)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(info_frame, text="ℹ️  Configure API subscription keys for each country and service combination.",
                font=('Segoe UI', 9),
                bg="#E7F3FF", fg="#004085",
                justify=tk.LEFT).pack(anchor=tk.W, padx=10, pady=8)
        
        # Create notebook for different sections
        notebook = ttk.Notebook(content)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Manage Keys
        manage_frame = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(manage_frame, text="  Manage API Keys  ")
        self._create_manage_tab(manage_frame)
        
        # Tab 2: Test Connections
        test_frame = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(test_frame, text="  Test Connections  ")
        self._create_test_tab(test_frame)
        
        # Tab 3: Configured Keys
        list_frame = tk.Frame(notebook, bg="#FFFFFF")
        notebook.add(list_frame, text="  Configured Keys  ")
        self._create_list_tab(list_frame)
        
        # Bottom buttons
        btn_frame = tk.Frame(self.window, bg="#F8F9FA", pady=15)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        tk.Button(btn_frame, text="Close", command=self.window.destroy,
                 bg="#6C757D", fg="white", font=('Segoe UI', 10, 'bold'),
                 padx=30, pady=8, relief=tk.FLAT, cursor="hand2").pack(side=tk.RIGHT, padx=20)
    
    def _create_manage_tab(self, parent):
        """Create the manage keys tab."""
        container = tk.Frame(parent, bg="#FFFFFF", padx=30, pady=30)
        container.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(container, text="Add/Update API Key",
                font=('Segoe UI', 12, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor=tk.W, pady=(0, 15))
        
        # Country selection
        tk.Label(container, text="Country:",
                font=('Segoe UI', 10),
                bg="#FFFFFF", fg="#495057").pack(anchor=tk.W, pady=(5, 0))
        
        self.country_var = tk.StringVar(value='NO')
        country_frame = tk.Frame(container, bg="#FFFFFF")
        country_frame.pack(fill=tk.X, pady=(5, 15))
        
        for country in VusionAPIConfig.COUNTRIES:
            tk.Radiobutton(country_frame, text=country,
                          variable=self.country_var, value=country,
                          bg="#FFFFFF", font=('Segoe UI', 9),
                          activebackground="#FFFFFF").pack(side=tk.LEFT, padx=(0, 15))
        
        # Service selection
        tk.Label(container, text="Service:",
                font=('Segoe UI', 10),
                bg="#FFFFFF", fg="#495057").pack(anchor=tk.W, pady=(5, 0))
        
        self.service_var = tk.StringVar(value='vusion_pro')
        service_frame = tk.Frame(container, bg="#FFFFFF")
        service_frame.pack(fill=tk.X, pady=(5, 15))
        
        for service_key, service_info in VusionAPIConfig.SERVICES.items():
            tk.Radiobutton(service_frame, text=service_info['name'],
                          variable=self.service_var, value=service_key,
                          bg="#FFFFFF", font=('Segoe UI', 9),
                          activebackground="#FFFFFF").pack(anchor=tk.W, pady=2)
        
        # API Key input
        tk.Label(container, text="API Subscription Key:",
                font=('Segoe UI', 10),
                bg="#FFFFFF", fg="#495057").pack(anchor=tk.W, pady=(5, 0))
        
        key_frame = tk.Frame(container, bg="#FFFFFF")
        key_frame.pack(fill=tk.X, pady=(5, 15))
        
        self.api_key_entry = tk.Entry(key_frame,
                                      font=('Consolas', 10),
                                      relief=tk.SOLID, bd=1)
        self.api_key_entry.pack(fill=tk.X, side=tk.LEFT, expand=True, ipady=5)
        
        tk.Button(key_frame, text="Show/Hide",
                 command=self._toggle_key_visibility,
                 bg="#6C757D", fg="white", font=('Segoe UI', 8),
                 padx=10, relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=(10, 0))
        
        self.api_key_entry.config(show="•")
        
        # Save button
        tk.Button(container, text="Save API Key",
                 command=self._save_api_key,
                 bg="#28A745", fg="white", font=('Segoe UI', 10, 'bold'),
                 padx=40, pady=10, relief=tk.FLAT, cursor="hand2").pack(anchor=tk.W, pady=(10, 0))
        
        # Separator
        tk.Frame(container, bg="#DEE2E6", height=1).pack(fill=tk.X, pady=20)
        
        # Quick load existing key
        tk.Label(container, text="Load Existing Key for Editing",
                font=('Segoe UI', 11, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor=tk.W, pady=(0, 10))
        
        load_frame = tk.Frame(container, bg="#FFFFFF")
        load_frame.pack(fill=tk.X)
        
        tk.Button(load_frame, text="Load Key",
                 command=self._load_key_for_edit,
                 bg="#007BFF", fg="white", font=('Segoe UI', 9, 'bold'),
                 padx=20, pady=8, relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT)
        
        tk.Label(load_frame, text="Loads the key for currently selected country/service",
                font=('Segoe UI', 8),
                bg="#FFFFFF", fg="#6C757D").pack(side=tk.LEFT, padx=10)
    
    def _create_test_tab(self, parent):
        """Create the test connections tab."""
        container = tk.Frame(parent, bg="#FFFFFF", padx=30, pady=30)
        container.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(container, text="Test API Connection",
                font=('Segoe UI', 12, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor=tk.W, pady=(0, 15))
        
        # Test selection
        test_frame = tk.Frame(container, bg="#FFFFFF")
        test_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(test_frame, text="Country:",
                font=('Segoe UI', 10),
                bg="#FFFFFF", fg="#495057").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.test_country_var = tk.StringVar(value='NO')
        country_combo = ttk.Combobox(test_frame, textvariable=self.test_country_var,
                                    values=VusionAPIConfig.COUNTRIES,
                                    state='readonly', width=15)
        country_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        tk.Label(test_frame, text="Service:",
                font=('Segoe UI', 10),
                bg="#FFFFFF", fg="#495057").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.test_service_var = tk.StringVar(value='vusion_pro')
        service_names = [info['name'] for info in VusionAPIConfig.SERVICES.values()]
        service_keys = list(VusionAPIConfig.SERVICES.keys())
        
        service_combo = ttk.Combobox(test_frame, textvariable=self.test_service_var,
                                    values=service_keys,
                                    state='readonly', width=25)
        service_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Test button
        tk.Button(container, text="Test Connection",
                 command=self._test_connection,
                 bg="#17A2B8", fg="white", font=('Segoe UI', 10, 'bold'),
                 padx=40, pady=10, relief=tk.FLAT, cursor="hand2").pack(anchor=tk.W, pady=(10, 20))
        
        # Result area
        tk.Label(container, text="Test Results:",
                font=('Segoe UI', 10, 'bold'),
                bg="#FFFFFF", fg="#495057").pack(anchor=tk.W, pady=(0, 5))
        
        result_frame = tk.Frame(container, bg="#F8F9FA", bd=1, relief=tk.SOLID)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        self.test_result_text = tk.Text(result_frame,
                                        font=('Consolas', 9),
                                        bg="#F8F9FA", fg="#212529",
                                        wrap=tk.WORD, height=12)
        self.test_result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Separator
        tk.Frame(container, bg="#DEE2E6", height=1).pack(fill=tk.X, pady=20)
        
        # Example store query
        tk.Label(container, text="Test Store Query",
                font=('Segoe UI', 11, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor=tk.W, pady=(0, 10))
        
        query_frame = tk.Frame(container, bg="#FFFFFF")
        query_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(query_frame, text="Store Number:",
                font=('Segoe UI', 9),
                bg="#FFFFFF").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.store_number_entry = tk.Entry(query_frame, font=('Segoe UI', 9), width=15)
        self.store_number_entry.insert(0, "4010")
        self.store_number_entry.grid(row=0, column=1, sticky=tk.W)
        
        tk.Button(query_frame, text="Query Store",
                 command=self._query_store,
                 bg="#28A745", fg="white", font=('Segoe UI', 9, 'bold'),
                 padx=20, pady=5, relief=tk.FLAT, cursor="hand2").grid(row=0, column=2, padx=(20, 0))
    
    def _create_list_tab(self, parent):
        """Create the list of configured keys tab."""
        container = tk.Frame(parent, bg="#FFFFFF", padx=30, pady=30)
        container.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(container, text="Configured API Keys",
                font=('Segoe UI', 12, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor=tk.W, pady=(0, 15))
        
        # Treeview for keys
        tree_frame = tk.Frame(container, bg="#FFFFFF")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        columns = ('Country', 'Service', 'Status')
        self.keys_tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                     yscrollcommand=scrollbar.set, height=15)
        
        for col in columns:
            self.keys_tree.heading(col, text=col)
            self.keys_tree.column(col, width=150)
        
        self.keys_tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.keys_tree.yview)
        
        # Buttons
        btn_frame = tk.Frame(container, bg="#FFFFFF")
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        tk.Button(btn_frame, text="Refresh List",
                 command=self._refresh_keys_list,
                 bg="#007BFF", fg="white", font=('Segoe UI', 9, 'bold'),
                 padx=20, pady=8, relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT)
        
        tk.Button(btn_frame, text="Delete Selected",
                 command=self._delete_selected_key,
                 bg="#DC3545", fg="white", font=('Segoe UI', 9, 'bold'),
                 padx=20, pady=8, relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=(10, 0))
    
    def _toggle_key_visibility(self):
        """Toggle API key visibility."""
        if self.api_key_entry.cget('show') == '•':
            self.api_key_entry.config(show='')
        else:
            self.api_key_entry.config(show='•')
    
    def _save_api_key(self):
        """Save the entered API key."""
        country = self.country_var.get()
        service = self.service_var.get()
        api_key = self.api_key_entry.get().strip()
        
        if not api_key:
            messagebox.showwarning("Missing Key", "Please enter an API subscription key.",
                                 parent=self.window)
            return
        
        try:
            self.config.set_api_key(country, service, api_key)
            
            service_name = VusionAPIConfig.SERVICES[service]['name']
            messagebox.showinfo("Success",
                              f"API key saved for {country} - {service_name}",
                              parent=self.window)
            
            # Clear entry
            self.api_key_entry.delete(0, tk.END)
            
            # Refresh list
            self._refresh_keys_list()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save API key:\n{str(e)}",
                               parent=self.window)
    
    def _load_key_for_edit(self):
        """Load existing key for editing."""
        country = self.country_var.get()
        service = self.service_var.get()
        
        api_key = self.config.get_api_key(country, service)
        
        if api_key:
            self.api_key_entry.delete(0, tk.END)
            self.api_key_entry.insert(0, api_key)
            messagebox.showinfo("Loaded", f"API key loaded for {country}/{service}",
                              parent=self.window)
        else:
            messagebox.showinfo("Not Found",
                              f"No API key configured for {country}/{service}",
                              parent=self.window)
    
    def _test_connection(self):
        """Test API connection."""
        country = self.test_country_var.get()
        service = self.test_service_var.get()
        
        self.test_result_text.delete('1.0', tk.END)
        self.test_result_text.insert('1.0', f"Testing connection for {country}/{service}...\n\n")
        self.window.update()
        
        success, message = self.helper.test_connection(country, service)
        
        if success:
            result = f"✓ SUCCESS\n\n{message}\n\nAPI key is valid and service is accessible."
            self.test_result_text.insert(tk.END, result)
            self.test_result_text.tag_add("success", "1.0", tk.END)
            self.test_result_text.tag_config("success", foreground="#28A745")
        else:
            result = f"✗ FAILED\n\n{message}\n\nPlease check your API key and network connection."
            self.test_result_text.insert(tk.END, result)
            self.test_result_text.tag_add("error", "1.0", tk.END)
            self.test_result_text.tag_config("error", foreground="#DC3545")
    
    def _query_store(self):
        """Query store information."""
        country = self.test_country_var.get()
        store_number = self.store_number_entry.get().strip()
        
        if not store_number:
            messagebox.showwarning("Missing Store Number",
                                 "Please enter a store number.",
                                 parent=self.window)
            return
        
        # Determine chain based on country
        chain_map = {
            'NO': 'elkjop',
            'SE': 'elgiganten',
            'FI': 'gigantti',
            'DK': 'elgiganten',
            'IS': 'elko'
        }
        
        chain = chain_map.get(country, 'elkjop')
        
        self.test_result_text.delete('1.0', tk.END)
        self.test_result_text.insert('1.0', f"Querying store {chain} {store_number} in {country}...\n\n")
        self.window.update()
        
        success, data = self.helper.get_store_info(country, chain, store_number)
        
        if success:
            result = f"✓ Store Found\n\n"
            result += f"Store ID: {data.get('id', 'N/A')}\n"
            result += f"Name: {data.get('name', 'N/A')}\n"
            result += f"Status: {data.get('status', 'N/A')}\n"
            result += f"Address: {data.get('address', 'N/A')}\n"
            result += f"\nFull Response:\n{json.dumps(data, indent=2)}"
            
            self.test_result_text.insert(tk.END, result)
        else:
            self.test_result_text.insert(tk.END, f"✗ Error\n\n{data}")
    
    def _load_existing_keys(self):
        """Load and display existing keys."""
        self._refresh_keys_list()
    
    def _refresh_keys_list(self):
        """Refresh the list of configured keys."""
        # Clear tree
        for item in self.keys_tree.get_children():
            self.keys_tree.delete(item)
        
        # Get configured keys
        keys = self.config.list_configured_keys()
        
        for key_info in keys:
            self.keys_tree.insert('', tk.END, values=(
                key_info['country'],
                key_info['service_name'],
                '✓ Configured'
            ))
    
    def _delete_selected_key(self):
        """Delete the selected API key."""
        selection = self.keys_tree.selection()
        
        if not selection:
            messagebox.showwarning("No Selection",
                                 "Please select a key to delete.",
                                 parent=self.window)
            return
        
        item = self.keys_tree.item(selection[0])
        values = item['values']
        country = values[0]
        service_name = values[1]
        
        # Find service key from name
        service_key = None
        for key, info in VusionAPIConfig.SERVICES.items():
            if info['name'] == service_name:
                service_key = key
                break
        
        if not service_key:
            return
        
        if messagebox.askyesno("Confirm Delete",
                              f"Delete API key for {country}/{service_name}?",
                              parent=self.window):
            self.config.delete_api_key(country, service_key)
            self._refresh_keys_list()
            messagebox.showinfo("Deleted", "API key deleted.", parent=self.window)
    
    def show(self):
        """Show the dialog and wait for it to close."""
        if self.parent:
            self.window.wait_window()
        else:
            self.window.mainloop()


if __name__ == '__main__':
    # Standalone test
    import json
    dialog = VusionAPIConfigDialog()
    dialog.show()
