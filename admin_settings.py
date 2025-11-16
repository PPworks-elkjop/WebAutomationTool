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
        
        # Check if user is admin
        if not current_user.get('is_admin'):
            messagebox.showerror("Access Denied", "Only administrators can access this section.")
            return
        
        self.credentials_manager = CredentialsManager(db_manager)
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Admin Settings - API Integrations")
        self.dialog.geometry("800x600")
        self.dialog.configure(bg="#F5F5F5")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"800x600+{x}+{y}")
        
        self._build_ui()
    
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
        
        # Vusion Cloud tab
        self.vusion_tab = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.vusion_tab, text="Vusion Cloud (Future)")
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
        
        # Show/Hide token button
        self.jira_show_token = tk.BooleanVar(value=False)
        tk.Checkbutton(
            token_frame,
            text="Show API Token",
            variable=self.jira_show_token,
            command=self._toggle_jira_token_visibility,
            bg="white",
            font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(5, 0))
        
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
        """Build Vusion Cloud configuration tab (placeholder for future)."""
        main_frame = tk.Frame(self.vusion_tab, bg="white", padx=30, pady=30)
        main_frame.pack(fill="both", expand=True)
        
        tk.Label(
            main_frame,
            text="Vusion Cloud Integration",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg="#2C3E50"
        ).pack(anchor="w", pady=(0, 10))
        
        tk.Label(
            main_frame,
            text="Coming Soon",
            font=("Segoe UI", 12),
            bg="white",
            fg="#999999"
        ).pack(anchor="w", pady=(20, 10))
        
        tk.Label(
            main_frame,
            text="Vusion Cloud API integration will be available in a future update.\nThis will enable direct communication with Vusion Group's cloud platform.",
            font=("Segoe UI", 9),
            bg="white",
            fg="#666666",
            wraplength=700,
            justify="left"
        ).pack(anchor="w", pady=(0, 20))
    
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
            
            # Show masked token if it exists
            if credentials.get('api_token'):
                self.jira_token_entry.delete(0, tk.END)
                self.jira_token_entry.insert(0, credentials.get('api_token', ''))
                self.jira_status_label.config(
                    text="✓ Credentials loaded (encrypted)",
                    fg="#28A745"
                )
    
    def _save_jira_credentials(self):
        """Save Jira credentials (encrypted)."""
        url = self.jira_url_entry.get().strip()
        username = self.jira_username_entry.get().strip()
        api_token = self.jira_token_entry.get().strip()
        
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
                'api_token': api_token
            }
            
            self.credentials_manager.store_credentials('jira', credentials)
            
            self.jira_status_label.config(
                text="✓ Credentials saved successfully (encrypted in database)",
                fg="#28A745"
            )
            
            messagebox.showinfo(
                "Success",
                "Jira credentials have been saved securely.",
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
                'api_token': api_token
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
                messagebox.showerror(
                    "Connection Failed",
                    f"Could not connect to Jira:\n\n{message}",
                    parent=self.dialog
                )
                
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
                self.jira_token_entry.delete(0, tk.END)
                
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
