"""
Admin Settings Dialog - Configure API integrations (Jira, Vusion Cloud, etc.)
Only accessible to admin users.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from credentials_manager import CredentialsManager
from jira_api import JiraAPI


class AdminSettingsDialog:
    """Admin settings dialog for managing API credentials."""
    
    def __init__(self, parent, current_user: dict, db_manager):
        """
        Initialize admin settings dialog.
        
        Args:
            parent: Parent window
            current_user: Current user dictionary (must have is_admin = True)
            db_manager: Database manager instance
        """
        self.parent = parent
        self.current_user = current_user
        self.db = db_manager
        
        # Check if user is admin (case-insensitive)
        is_admin = (current_user.get('is_admin') or 
                   (current_user.get('role', '').lower() == 'admin'))
        if not is_admin:
            messagebox.showerror("Access Denied", "Only administrators can access this section.")
            return
        
        self.credentials_manager = CredentialsManager(db_manager)
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Admin Settings - API Integrations")
        self.dialog.geometry("800x600")
        self.dialog.configure(bg="#F5F5F5")
        self.dialog.transient(parent)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"800x600+{x}+{y}")
        
        self._build_ui()
        
        # Set grab after UI is built and window is visible
        try:
            self.dialog.grab_set()
        except tk.TclError:
            # If grab fails, continue without it (window will still work)
            pass
    
    def _build_ui(self):
        """Build the admin settings UI."""
        # Header
        header_frame = tk.Frame(self.dialog, bg="#2C3E50", height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="⚙️ Admin Settings - API Integrations",
            font=("Segoe UI", 16, "bold"),
            bg="#2C3E50",
            fg="white"
        ).pack(side="left", padx=20, pady=15)
        
        # Main content with notebook (tabs)
        content_frame = tk.Frame(self.dialog, bg="#F5F5F5")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create notebook for different integrations
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Jira tab
        self.jira_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.jira_tab, text="Jira Integration")
        self._build_jira_tab()
        
        # Vusion Manager Pro tab
        self.vusion_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.vusion_tab, text="Vusion Manager Pro")
        self._build_vusion_tab()
        
        # Bottom buttons
        button_frame = tk.Frame(self.dialog, bg="#F5F5F5")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        tk.Button(
            button_frame,
            text="Close",
            command=self.dialog.destroy,
            bg="#6C757D",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=30,
            pady=10
        ).pack(side="right")
    
    def _build_jira_tab(self):
        """Build Jira integration configuration tab."""
        # Scroll frame for content
        canvas = tk.Canvas(self.jira_tab, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.jira_tab, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="white")
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Content
        main_frame = tk.Frame(scroll_frame, bg="white", padx=30, pady=30)
        main_frame.pack(fill="both", expand=True)
        
        # Title and description
        tk.Label(
            main_frame,
            text="Jira API Configuration",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg="#2C3E50"
        ).pack(anchor="w", pady=(0, 10))
        
        tk.Label(
            main_frame,
            text="Configure Jira API credentials to enable issue tracking and integration features.",
            font=("Segoe UI", 9),
            bg="white",
            fg="#666666",
            wraplength=700,
            justify="left"
        ).pack(anchor="w", pady=(0, 20))
        
        # Jira URL
        url_frame = tk.Frame(main_frame, bg="white")
        url_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            url_frame,
            text="Jira URL:",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).pack(anchor="w")
        
        self.jira_url_entry = tk.Entry(
            url_frame,
            font=("Segoe UI", 10),
            bg="#F8F9FA",
            relief="solid",
            bd=1
        )
        self.jira_url_entry.pack(fill="x", pady=(5, 0), ipady=5)
        
        tk.Label(
            url_frame,
            text="Example: https://yourcompany.atlassian.net",
            font=("Segoe UI", 8),
            bg="white",
            fg="#999999"
        ).pack(anchor="w", pady=(2, 0))
        
        # Username/Email
        username_frame = tk.Frame(main_frame, bg="white")
        username_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            username_frame,
            text="Username/Email:",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).pack(anchor="w")
        
        self.jira_username_entry = tk.Entry(
            username_frame,
            font=("Segoe UI", 10),
            bg="#F8F9FA",
            relief="solid",
            bd=1
        )
        self.jira_username_entry.pack(fill="x", pady=(5, 0), ipady=5)
        
        tk.Label(
            username_frame,
            text="Your Jira account email address",
            font=("Segoe UI", 8),
            bg="white",
            fg="#999999"
        ).pack(anchor="w", pady=(2, 0))
        
        # API Token
        token_frame = tk.Frame(main_frame, bg="white")
        token_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            token_frame,
            text="API Token:",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).pack(anchor="w")
        
        self.jira_token_entry = tk.Entry(
            token_frame,
            font=("Segoe UI", 10),
            bg="#F8F9FA",
            relief="solid",
            bd=1,
            show="●"  # Mask token
        )
        self.jira_token_entry.pack(fill="x", pady=(5, 0), ipady=5)
        
        tk.Label(
            token_frame,
            text="Generate at: https://id.atlassian.com/manage-profile/security/api-tokens",
            font=("Segoe UI", 8),
            bg="white",
            fg="#007BFF",
            cursor="hand2"
        ).pack(anchor="w", pady=(2, 0))
        
        # Show/Hide token button (only visible when entering new token)
        self.jira_show_token = tk.BooleanVar(value=False)
        self.jira_show_token_check = tk.Checkbutton(
            token_frame,
            text="Show API Token",
            variable=self.jira_show_token,
            command=self._toggle_jira_token_visibility,
            bg="white",
            font=("Segoe UI", 9)
        )
        self.jira_show_token_check.pack(anchor="w", pady=(5, 0))
        
        # SSL Verification option
        ssl_frame = tk.Frame(main_frame, bg="white")
        ssl_frame.pack(fill="x", pady=(0, 15))
        
        self.jira_verify_ssl = tk.BooleanVar(value=True)
        tk.Checkbutton(
            ssl_frame,
            text="Verify SSL Certificate (uncheck if using corporate proxy with self-signed certificate)",
            variable=self.jira_verify_ssl,
            bg="white",
            font=("Segoe UI", 9)
        ).pack(anchor="w")
        
        tk.Label(
            ssl_frame,
            text="⚠️ Warning: Disabling SSL verification reduces security. Only use in trusted corporate networks.",
            font=("Segoe UI", 8),
            bg="white",
            fg="#DC3545",
            wraplength=700,
            justify="left"
        ).pack(anchor="w", pady=(2, 0))
        
        # Status label
        self.jira_status_label = tk.Label(
            main_frame,
            text="",
            font=("Segoe UI", 9),
            bg="white",
            wraplength=700,
            justify="left"
        )
        self.jira_status_label.pack(anchor="w", pady=(10, 15))
        
        # Buttons
        button_row = tk.Frame(main_frame, bg="white")
        button_row.pack(fill="x", pady=(10, 0))
        
        tk.Button(
            button_row,
            text="Test Connection",
            command=self._test_jira_connection,
            bg="#17A2B8",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8
        ).pack(side="left", padx=(0, 10))
        
        tk.Button(
            button_row,
            text="Save Credentials",
            command=self._save_jira_credentials,
            bg="#28A745",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8
        ).pack(side="left", padx=(0, 10))
        
        tk.Button(
            button_row,
            text="Clear Credentials",
            command=self._clear_jira_credentials,
            bg="#DC3545",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8
        ).pack(side="left")
        
        # Load existing credentials (masked)
        self._load_jira_credentials()
    
    def _build_vusion_tab(self):
        """Build Vusion Manager Pro configuration tab with multi-store support."""
        # Scroll frame for content
        canvas = tk.Canvas(self.vusion_tab, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.vusion_tab, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="white")
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Content
        main_frame = tk.Frame(scroll_frame, bg="white", padx=30, pady=30)
        main_frame.pack(fill="both", expand=True)
        
        # Title and description
        tk.Label(
            main_frame,
            text="Vusion Manager Pro API Configuration",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg="#2C3E50"
        ).pack(anchor="w", pady=(0, 10))
        
        tk.Label(
            main_frame,
            text="Configure Vusion Manager Pro API keys for all retail chains. This enables real-time AP/transmitter status display in the AP Panel.",
            font=("Segoe UI", 9),
            bg="white",
            fg="#666666",
            wraplength=700,
            justify="left"
        ).pack(anchor="w", pady=(0, 20))
        
        # Define stores with their details
        self.vusion_stores = [
            {"name": "Elkjøp Norway", "store_id": "elkjop_no", "country": "NO", "chain": "Elkjøp"},
            {"name": "Elgiganten Sweden", "store_id": "elgiganten_se", "country": "SE", "chain": "Elgiganten"},
            {"name": "Elgiganten Denmark", "store_id": "elgiganten_dk", "country": "DK", "chain": "Elgiganten"},
            {"name": "Gigantti Finland", "store_id": "gigantti_fi", "country": "FI", "chain": "Gigantti"},
            {"name": "Elkjøp SE Lab", "store_id": "elkjop_se_lab.lab5", "country": "LAB", "chain": "Elkjøp (Test)"},
        ]
        
        # Store entry widgets for later access
        self.vusion_entries = {}
        
        # Create configuration sections for each store
        for store in self.vusion_stores:
            self._create_store_config_section(main_frame, store)
        
        # Info section
        info_frame = tk.Frame(main_frame, bg="#E7F3FF", bd=1, relief=tk.SOLID)
        info_frame.pack(fill="x", pady=(20, 0))
        
        tk.Label(
            info_frame,
            text="ℹ️  Configuration Info",
            font=("Segoe UI", 9, "bold"),
            bg="#E7F3FF",
            fg="#004085"
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        tk.Label(
            info_frame,
            text="• API keys are encrypted and stored securely\n"
                 "• Each store/chain can have its own API key\n"
                 "• Test each connection after saving to verify it works\n"
                 "• The API displays real-time AP status (🟢 online / 🔴 offline) in AP Panel",
            font=("Segoe UI", 9),
            bg="#E7F3FF",
            fg="#004085",
            justify="left"
        ).pack(anchor="w", padx=10, pady=(0, 10))
        
        # Load existing credentials
        self._load_all_vusion_credentials()
    
    def _create_store_config_section(self, parent, store):
        """Create a configuration section for a single store."""
        # Container for this store
        store_frame = tk.Frame(parent, bg="white", bd=1, relief=tk.SOLID)
        store_frame.pack(fill="x", pady=(0, 15))
        
        # Header with store name
        header_frame = tk.Frame(store_frame, bg="#F8F9FA")
        header_frame.pack(fill="x")
        
        tk.Label(
            header_frame,
            text=f"{store['name']} - {store['chain']} (Country: {store['country']})",
            font=("Segoe UI", 11, "bold"),
            bg="#F8F9FA",
            fg="#2C3E50"
        ).pack(side="left", anchor="w", padx=15, pady=10)
        
        # Content
        content_frame = tk.Frame(store_frame, bg="white", padx=15, pady=10)
        content_frame.pack(fill="x")
        
        # Store ID (readonly display)
        tk.Label(
            content_frame,
            text=f"Store ID: {store['store_id']}",
            font=("Segoe UI", 9),
            bg="white",
            fg="#666666"
        ).pack(anchor="w")
        
        # API Key input
        key_frame = tk.Frame(content_frame, bg="white")
        key_frame.pack(fill="x", pady=(10, 0))
        
        tk.Label(
            key_frame,
            text="API Key:",
            font=("Segoe UI", 9, "bold"),
            bg="white"
        ).pack(anchor="w")
        
        key_input_frame = tk.Frame(key_frame, bg="white")
        key_input_frame.pack(fill="x", pady=(5, 0))
        
        api_key_entry = tk.Entry(
            key_input_frame,
            font=("Segoe UI", 9),
            bg="#F8F9FA",
            relief="solid",
            bd=1,
            show="●"
        )
        api_key_entry.pack(side="left", fill="x", expand=True, ipady=4)
        
        show_var = tk.BooleanVar(value=False)
        show_check = tk.Checkbutton(
            key_input_frame,
            text="Show",
            variable=show_var,
            command=lambda e=api_key_entry, v=show_var: e.config(show="" if v.get() else "●"),
            bg="white",
            font=("Segoe UI", 8)
        )
        show_check.pack(side="left", padx=(10, 0))
        
        # Status label
        status_label = tk.Label(
            content_frame,
            text="",
            font=("Segoe UI", 8),
            bg="white"
        )
        status_label.pack(anchor="w", pady=(5, 0))
        
        # Buttons
        button_frame = tk.Frame(content_frame, bg="white")
        button_frame.pack(fill="x", pady=(10, 0))
        
        tk.Button(
            button_frame,
            text="Save",
            command=lambda: self._save_store_key(store, api_key_entry, status_label, show_check),
            bg="#28A745",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=6
        ).pack(side="left", padx=(0, 5))
        
        tk.Button(
            button_frame,
            text="Test",
            command=lambda: self._test_store_connection(store, status_label),
            bg="#007BFF",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=6
        ).pack(side="left", padx=(0, 5))
        
        tk.Button(
            button_frame,
            text="Clear",
            command=lambda: self._clear_store_key(store, api_key_entry, status_label, show_check),
            bg="#DC3545",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=6
        ).pack(side="left")
        
        # Store references for later use
        self.vusion_entries[store['store_id']] = {
            'entry': api_key_entry,
            'status': status_label,
            'show_var': show_var,
            'show_check': show_check
        }
    
    def _toggle_jira_token_visibility(self):
        """Toggle visibility of Jira API token."""
        if self.jira_show_token.get():
            self.jira_token_entry.config(show="")
        else:
            self.jira_token_entry.config(show="●")
    
    def _load_jira_credentials(self):
        """Load existing Jira credentials (masked)."""
        credentials = self.credentials_manager.get_credentials('jira')
        
        if credentials:
            self.jira_url_entry.delete(0, tk.END)
            self.jira_url_entry.insert(0, credentials.get('url', ''))
            
            self.jira_username_entry.delete(0, tk.END)
            self.jira_username_entry.insert(0, credentials.get('username', ''))
            
            # Show placeholder for existing token (never show actual saved token)
            if credentials.get('api_token'):
                self.jira_token_entry.delete(0, tk.END)
                self.jira_token_entry.insert(0, '●●●●●●●●●●●●●●●●●●●●')
                self.jira_token_entry.config(state='disabled')  # Disable editing
                
                # Hide the show/hide checkbox when token is loaded from database
                self.jira_show_token_check.pack_forget()
                
                self.jira_status_label.config(
                    text="✓ Credentials loaded (encrypted) - To change token, clear credentials first",
                    fg="#28A745"
                )
            
            # Load SSL verification setting
            self.jira_verify_ssl.set(credentials.get('verify_ssl', True))
    
    def _save_jira_credentials(self):
        """Save Jira credentials (encrypted)."""
        url = self.jira_url_entry.get().strip()
        username = self.jira_username_entry.get().strip()
        api_token = self.jira_token_entry.get().strip()
        
        # Check if token is the masked placeholder (already saved)
        if api_token == '●●●●●●●●●●●●●●●●●●●●':
            messagebox.showinfo(
                "Already Saved",
                "These credentials are already saved.\n\nTo update them, please clear credentials first.",
                parent=self.dialog
            )
            return
        
        if not url or not username or not api_token:
            messagebox.showwarning(
                "Missing Information",
                "Please fill in all fields before saving.",
                parent=self.dialog
            )
            return
        
        # Validate URL format
        if not url.startswith('http://') and not url.startswith('https://'):
            messagebox.showwarning(
                "Invalid URL",
                "Jira URL must start with http:// or https://",
                parent=self.dialog
            )
            return
        
        try:
            # Save encrypted credentials
            credentials = {
                'url': url,
                'username': username,
                'api_token': api_token,
                'verify_ssl': self.jira_verify_ssl.get()
            }
            
            self.credentials_manager.store_credentials('jira', credentials)
            
            # After saving, mask the token and disable editing
            self.jira_token_entry.config(state='normal')
            self.jira_token_entry.delete(0, tk.END)
            self.jira_token_entry.insert(0, '●●●●●●●●●●●●●●●●●●●●')
            self.jira_token_entry.config(state='disabled')
            
            # Hide the show/hide checkbox
            self.jira_show_token.set(False)
            self.jira_show_token_check.pack_forget()
            
            self.jira_status_label.config(
                text="✓ Credentials saved successfully (encrypted) - To change token, clear credentials first",
                fg="#28A745"
            )
            
            messagebox.showinfo(
                "Success",
                "Jira credentials have been saved securely.\n\nNote: The API token is now encrypted and cannot be viewed again.",
                parent=self.dialog
            )
            
        except Exception as e:
            self.jira_status_label.config(
                text=f"✗ Error saving credentials: {str(e)}",
                fg="#DC3545"
            )
            messagebox.showerror(
                "Error",
                f"Failed to save credentials:\n{str(e)}",
                parent=self.dialog
            )
    
    def _test_jira_connection(self):
        """Test Jira connection with current credentials."""
        url = self.jira_url_entry.get().strip()
        username = self.jira_username_entry.get().strip()
        api_token = self.jira_token_entry.get().strip()
        
        # Check if token is the masked placeholder
        if api_token == '●●●●●●●●●●●●●●●●●●●●':
            messagebox.showinfo(
                "Test Existing Credentials",
                "Testing connection with saved credentials...",
                parent=self.dialog
            )
            # Load actual credentials from database
            credentials = self.credentials_manager.get_credentials('jira')
            if credentials:
                url = credentials.get('url', url)
                username = credentials.get('username', username)
                api_token = credentials.get('api_token', '')
            else:
                messagebox.showerror(
                    "Error",
                    "No saved credentials found. Please clear and re-enter credentials.",
                    parent=self.dialog
                )
                return
        
        if not url or not username or not api_token:
            messagebox.showwarning(
                "Missing Information",
                "Please fill in all fields before testing.",
                parent=self.dialog
            )
            return
        
        # Save credentials temporarily for testing
        self.jira_status_label.config(text="Testing connection...", fg="#007BFF")
        self.dialog.update()
        
        try:
            # Create temporary credentials
            temp_credentials = {
                'url': url,
                'username': username,
                'api_token': api_token,
                'verify_ssl': self.jira_verify_ssl.get()
            }
            self.credentials_manager.store_credentials('jira', temp_credentials)
            
            # Test connection
            jira_api = JiraAPI(self.credentials_manager)
            success, message = jira_api.test_connection()
            
            if success:
                self.jira_status_label.config(
                    text=f"✓ Connection successful! {message}",
                    fg="#28A745"
                )
                messagebox.showinfo(
                    "Success",
                    f"Jira connection successful!\n\n{message}",
                    parent=self.dialog
                )
            else:
                self.jira_status_label.config(
                    text=f"✗ Connection failed: {message}",
                    fg="#DC3545"
                )
                # Show error in a dialog with copyable text
                self._show_error_dialog("Connection Failed", 
                                       f"Could not connect to Jira:\n\n{message}")
                
        except Exception as e:
            self.jira_status_label.config(
                text=f"✗ Error: {str(e)}",
                fg="#DC3545"
            )
            messagebox.showerror(
                "Error",
                f"An error occurred:\n{str(e)}",
                parent=self.dialog
            )
    
    def _clear_jira_credentials(self):
        """Clear Jira credentials from database."""
        if messagebox.askyesno(
            "Confirm Clear",
            "Are you sure you want to delete the stored Jira credentials?",
            parent=self.dialog
        ):
            try:
                self.credentials_manager.delete_credentials('jira')
                
                # Clear entry fields
                self.jira_url_entry.delete(0, tk.END)
                self.jira_username_entry.delete(0, tk.END)
                
                # Re-enable token entry and show checkbox
                self.jira_token_entry.config(state='normal')
                self.jira_token_entry.delete(0, tk.END)
                self.jira_show_token_check.pack(anchor="w", pady=(5, 0))
                
                self.jira_status_label.config(
                    text="✓ Credentials cleared",
                    fg="#6C757D"
                )
                
                messagebox.showinfo(
                    "Success",
                    "Jira credentials have been deleted.",
                    parent=self.dialog
                )
                
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Failed to clear credentials:\n{str(e)}",
                    parent=self.dialog
                )
    
    def _show_error_dialog(self, title: str, message: str):
        """Show error in a dialog with copyable text."""
        error_dialog = tk.Toplevel(self.dialog)
        error_dialog.title(title)
        error_dialog.geometry("600x300")
        error_dialog.configure(bg="white")
        error_dialog.transient(self.dialog)
        error_dialog.grab_set()
        
        # Center dialog
        error_dialog.update_idletasks()
        x = (error_dialog.winfo_screenwidth() // 2) - (300)
        y = (error_dialog.winfo_screenheight() // 2) - (150)
        error_dialog.geometry(f"600x300+{x}+{y}")
        
        # Header
        header = tk.Frame(error_dialog, bg="#DC3545", height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=f"✗ {title}",
            font=("Segoe UI", 12, "bold"),
            bg="#DC3545",
            fg="white"
        ).pack(pady=15)
        
        # Message area (scrollable text)
        text_frame = tk.Frame(error_dialog, bg="white")
        text_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        text_widget = tk.Text(
            text_frame,
            wrap="word",
            font=("Consolas", 9),
            bg="#F8F9FA",
            relief="solid",
            bd=1,
            padx=10,
            pady=10
        )
        text_widget.pack(side="left", fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(text_frame, command=text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        text_widget.config(yscrollcommand=scrollbar.set)
        
        # Insert message
        text_widget.insert("1.0", message)
        text_widget.config(state="disabled")  # Make read-only
        
        # Buttons
        button_frame = tk.Frame(error_dialog, bg="white")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        def copy_to_clipboard():
            error_dialog.clipboard_clear()
            error_dialog.clipboard_append(message)
            copy_btn.config(text="✓ Copied!", bg="#28A745")
            error_dialog.after(2000, lambda: copy_btn.config(text="Copy to Clipboard", bg="#007BFF"))
        
        copy_btn = tk.Button(
            button_frame,
            text="Copy to Clipboard",
            command=copy_to_clipboard,
            bg="#007BFF",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8
        )
        copy_btn.pack(side="left", padx=(0, 10))
        
        tk.Button(
            button_frame,
            text="Close",
            command=error_dialog.destroy,
            bg="#6C757D",
            fg="white",
            font=("Segoe UI", 10),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8
        ).pack(side="left")
    
    def _load_all_vusion_credentials(self):
        """Load existing credentials for all stores."""
        try:
            from vusion_api_config import VusionAPIConfig
            config = VusionAPIConfig()
            
            for store in self.vusion_stores:
                country = store['country']
                store_id = store['store_id']
                
                api_key = config.get_api_key(country, 'vusion_pro')
                
                if api_key and store_id in self.vusion_entries:
                    widgets = self.vusion_entries[store_id]
                    
                    # Show masked key
                    widgets['entry'].delete(0, tk.END)
                    widgets['entry'].insert(0, '●●●●●●●●●●●●●●●●●●●●')
                    widgets['entry'].config(state='disabled')
                    
                    # Hide show checkbox
                    widgets['show_check'].pack_forget()
                    
                    # Update status
                    widgets['status'].config(
                        text="✓ API key configured (encrypted)",
                        fg="#28A745"
                    )
        except Exception as e:
            pass  # Silently fail if no config exists yet
    
    def _save_store_key(self, store, entry, status_label, show_check):
        """Save API key for a specific store."""
        api_key = entry.get().strip()
        
        # Check if it's the masked placeholder
        if api_key == '●●●●●●●●●●●●●●●●●●●●':
            messagebox.showinfo(
                "Already Saved",
                f"{store['name']} API key is already saved.\n\nTo update, clear it first.",
                parent=self.dialog
            )
            return
        
        if not api_key:
            messagebox.showerror(
                "Validation Error",
                "Please enter an API key.",
                parent=self.dialog
            )
            return
        
        try:
            from vusion_api_config import VusionAPIConfig
            config = VusionAPIConfig()
            
            # Save the API key for this country
            config.set_api_key(store['country'], 'vusion_pro', api_key)
            
            # Verify it was saved by reading it back
            saved_key = config.get_api_key(store['country'], 'vusion_pro')
            if not saved_key:
                raise Exception("Failed to verify saved API key")
            
            # Mask the entry
            entry.config(state='normal')
            entry.delete(0, tk.END)
            entry.insert(0, '●●●●●●●●●●●●●●●●●●●●')
            entry.config(state='disabled')
            
            # Hide show checkbox
            show_check.pack_forget()
            
            # Update status
            status_label.config(
                text="✓ API key saved successfully (encrypted)",
                fg="#28A745"
            )
            
            messagebox.showinfo(
                "Success",
                f"{store['name']} API key saved!\n\nThe key is encrypted and stored securely.",
                parent=self.dialog
            )
            
        except Exception as e:
            status_label.config(
                text=f"✗ Error: {str(e)}",
                fg="#DC3545"
            )
            messagebox.showerror(
                "Error",
                f"Failed to save API key:\n{str(e)}",
                parent=self.dialog
            )
    
    def _test_store_connection(self, store, status_label):
        """Test connection for a specific store."""
        try:
            # First verify API key exists
            from vusion_api_config import VusionAPIConfig
            config = VusionAPIConfig()
            api_key = config.get_api_key(store['country'], 'vusion_pro')
            
            if not api_key:
                status_label.config(
                    text=f"✗ No API key configured",
                    fg="#DC3545"
                )
                messagebox.showerror(
                    "No API Key",
                    f"No API key found for {store['name']} (country: {store['country']}).\n\nPlease save an API key first.",
                    parent=self.dialog
                )
                return
            
            from vusion_api_helper import VusionAPIHelper
            helper = VusionAPIHelper()
            
            status_label.config(text="⏳ Testing...", fg="#FFC107")
            self.dialog.update()
            
            success, data = helper.get_store_data(store['country'], store['store_id'])
            
            if success:
                # Extract transmitters from nested structure
                transmitters = data.get('transmissionSystems', {}).get('highFrequency', {}).get('transmitters', [])
                transmitter_count = len(transmitters)
                online_count = sum(1 for t in transmitters 
                                 if t.get('connectivity', {}).get('status') == 'ONLINE')
                
                status_label.config(
                    text=f"✓ Connected! {transmitter_count} transmitters ({online_count} online)",
                    fg="#28A745"
                )
                
                messagebox.showinfo(
                    "Connection Successful",
                    f"{store['name']} connection successful!\n\n"
                    f"Transmitters: {transmitter_count}\n"
                    f"Online: {online_count}\n"
                    f"Offline: {transmitter_count - online_count}",
                    parent=self.dialog
                )
            else:
                status_label.config(
                    text=f"✗ Connection failed",
                    fg="#DC3545"
                )
                messagebox.showerror(
                    "Connection Failed",
                    f"Failed to connect to {store['name']}:\n\n{data}",
                    parent=self.dialog
                )
        
        except ValueError as e:
            # This catches the "No API key configured" error from get_request_headers
            status_label.config(
                text=f"✗ No API key configured",
                fg="#DC3545"
            )
            messagebox.showerror(
                "Configuration Error",
                f"{str(e)}\n\nPlease save an API key for {store['name']} first.",
                parent=self.dialog
            )
        except Exception as e:
            status_label.config(
                text=f"✗ Error: {str(e)}",
                fg="#DC3545"
            )
            messagebox.showerror(
                "Error",
                f"Error testing {store['name']}:\n{str(e)}",
                parent=self.dialog
            )
    
    def _clear_store_key(self, store, entry, status_label, show_check):
        """Clear API key for a specific store."""
        result = messagebox.askyesno(
            "Confirm Clear",
            f"Clear API key for {store['name']}?",
            parent=self.dialog
        )
        
        if result:
            try:
                from vusion_api_config import VusionAPIConfig
                config = VusionAPIConfig()
                
                config.delete_api_key(store['country'], 'vusion_pro')
                
                # Reset entry
                entry.config(state='normal')
                entry.delete(0, tk.END)
                
                # Show the checkbox again
                show_check.pack(side="left", padx=(10, 0))
                
                # Update status
                status_label.config(
                    text="Configuration cleared",
                    fg="#6C757D"
                )
                
                messagebox.showinfo(
                    "Cleared",
                    f"{store['name']} API key cleared.",
                    parent=self.dialog
                )
                
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Error clearing {store['name']} key:\n{str(e)}",
                    parent=self.dialog
                )
