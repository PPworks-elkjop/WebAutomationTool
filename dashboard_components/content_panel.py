"""
Content Panel - Lower Right
Dynamic content area showing SSH terminal, browser status, Jira details, etc.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox


class ContentPanel:
    """Lower right panel - Dynamic content display."""
    
    def __init__(self, parent, db, log_callback=None):
        self.parent = parent
        self.db = db
        self.log_callback = log_callback
        
        self.current_content_type = None
        self.current_data = None
        
        self._create_ui()
    
    def _create_ui(self):
        """Create content panel UI."""
        # Header
        self.header = tk.Frame(self.parent, bg="#0066CC", height=40)
        self.header.pack(fill=tk.X, side=tk.TOP)
        self.header.pack_propagate(False)
        
        self.header_label = tk.Label(self.header, text="Content View", font=('Segoe UI', 12, 'bold'),
                                     bg="#0066CC", fg="white")
        self.header_label.pack(side=tk.LEFT, padx=15, pady=8)
        
        self.popout_button = tk.Button(self.header, text="↗ Pop Out", command=self._popout,
                                       bg="#28A745", fg="white", font=('Segoe UI', 8),
                                       padx=10, pady=2, relief=tk.FLAT, cursor="hand2",
                                       activebackground="#218838")
        self.popout_button.pack(side=tk.RIGHT, padx=10)
        self.popout_button.pack_forget()  # Hidden by default
        
        # Content frame (will be replaced based on content type)
        self.content_frame = tk.Frame(self.parent, bg="#FFFFFF")
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Show default placeholder
        self._show_placeholder()
    
    def _show_placeholder(self):
        """Show placeholder when no content is active."""
        self._clear_content()
        
        self.header_label.config(text="Content View")
        self.popout_button.pack_forget()
        
        placeholder = tk.Frame(self.content_frame, bg="#FFFFFF")
        placeholder.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(placeholder, text="Select an item to view details",
                font=('Segoe UI', 14, 'bold'), bg="#FFFFFF", fg="#6C757D").pack(expand=True)
    
    def _clear_content(self):
        """Clear current content."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_ap_overview(self, ap_data):
        """Show AP overview information."""
        self._clear_content()
        self.current_content_type = "ap_overview"
        self.current_data = ap_data
        
        self.header_label.config(text=f"AP Overview - {ap_data['ap_id']}")
        self.popout_button.pack_forget()
        
        content = tk.Frame(self.content_frame, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text=f"AP {ap_data['ap_id']}", font=('Segoe UI', 16, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(0, 20))
        
        # Display key information
        info_fields = [
            ('Store ID', ap_data.get('store_id', 'N/A')),
            ('IP Address', ap_data.get('ip_address', 'N/A')),
            ('Type', ap_data.get('type', 'N/A')),
            ('Serial Number', ap_data.get('serial_number', 'N/A')),
            ('Software Version', ap_data.get('software_version', 'N/A')),
            ('Firmware Version', ap_data.get('firmware_version', 'N/A')),
            ('Hardware Revision', ap_data.get('hardware_revision', 'N/A')),
            ('MAC Address', ap_data.get('mac_address', 'N/A')),
            ('Uptime', ap_data.get('uptime', 'N/A')),
            ('Status', ap_data.get('current_status', 'N/A')),
            ('Service Status', ap_data.get('service_status', 'N/A')),
        ]
        
        for label, value in info_fields:
            self._create_info_row(content, label, value)
        
        self._log(f"Showing overview for AP {ap_data['ap_id']}")
    
    def show_ssh_terminal(self, ap_id):
        """Show SSH terminal for AP."""
        self._clear_content()
        self.current_content_type = "ssh"
        self.current_data = ap_id
        
        self.header_label.config(text=f"SSH Terminal - AP {ap_id}")
        self.popout_button.pack(side=tk.RIGHT, padx=10)
        
        content = tk.Frame(self.content_frame, bg="#000000", padx=10, pady=10)
        content.pack(fill=tk.BOTH, expand=True)
        
        # SSH terminal placeholder
        terminal_text = scrolledtext.ScrolledText(content, font=('Consolas', 10),
                                                  bg="#000000", fg="#00FF00",
                                                  insertbackground="white")
        terminal_text.pack(fill=tk.BOTH, expand=True)
        
        terminal_text.insert('1.0', f"SSH Terminal - AP {ap_id}\n")
        terminal_text.insert(tk.END, "Connecting...\n\n")
        terminal_text.insert(tk.END, "TODO: Embed SSH terminal widget here\n")
        terminal_text.insert(tk.END, "Or show SSH output/commands\n\n")
        terminal_text.insert(tk.END, f"root@ap-{ap_id}:~# ")
        
        self._log(f"Opening SSH terminal for AP {ap_id}")
    
    def show_browser_status(self, ap_id):
        """Show browser connection status and actions."""
        self._clear_content()
        self.current_content_type = "browser"
        self.current_data = ap_id
        
        self.header_label.config(text=f"Browser - AP {ap_id}")
        self.popout_button.pack(side=tk.RIGHT, padx=10)
        
        content = tk.Frame(self.content_frame, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text=f"Browser Control - AP {ap_id}", font=('Segoe UI', 14, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(0, 20))
        
        # Status
        status_frame = tk.Frame(content, bg="#F8F9FA", relief=tk.FLAT, bd=1)
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        status_content = tk.Frame(status_frame, bg="#F8F9FA", padx=20, pady=15)
        status_content.pack(fill=tk.X)
        
        tk.Label(status_content, text="Connection Status:", font=('Segoe UI', 10, 'bold'),
                bg="#F8F9FA", fg="#495057").pack(anchor="w")
        
        tk.Label(status_content, text="Not Connected", font=('Segoe UI', 10),
                bg="#F8F9FA", fg="#DC3545").pack(anchor="w", pady=(5, 0))
        
        # Actions
        tk.Label(content, text="Quick Actions:", font=('Segoe UI', 11, 'bold'),
                bg="#FFFFFF", fg="#495057").pack(anchor="w", pady=(10, 10))
        
        actions = [
            ("Connect Browser", lambda: self._log(f"Connecting browser to AP {ap_id}")),
            ("Navigate to Status", lambda: self._log("Navigating to status page")),
            ("Show Browser Window", lambda: self._log("Showing browser window")),
            ("Hide Browser Window", lambda: self._log("Hiding browser window")),
        ]
        
        for action_text, action_cmd in actions:
            tk.Button(content, text=action_text, command=action_cmd,
                     bg="#17A2B8", fg="white", font=('Segoe UI', 9),
                     padx=15, pady=8, relief=tk.FLAT, cursor="hand2",
                     activebackground="#138496", width=25).pack(anchor="w", pady=5)
        
        self._log(f"Showing browser controls for AP {ap_id}")
    
    def show_notes(self, ap_id):
        """Show notes for AP."""
        self._clear_content()
        self.current_content_type = "notes"
        self.current_data = ap_id
        
        self.header_label.config(text=f"Notes - AP {ap_id}")
        self.popout_button.pack_forget()
        
        content = tk.Frame(self.content_frame, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text=f"Support Notes - AP {ap_id}", font=('Segoe UI', 14, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(0, 10))
        
        # Get notes from database
        notes = self.db.get_support_notes(ap_id)
        
        if notes:
            for note in notes:
                self._create_note_card(content, note)
        else:
            tk.Label(content, text="No notes found for this AP",
                    font=('Segoe UI', 10), bg="#FFFFFF", fg="#6C757D").pack(pady=20)
        
        self._log(f"Showing notes for AP {ap_id}")
    
    def show_jira_details(self, ticket_data):
        """Show Jira ticket details."""
        self._clear_content()
        self.current_content_type = "jira"
        self.current_data = ticket_data
        
        ticket_key = ticket_data.get('key', 'Unknown')
        self.header_label.config(text=f"Jira Ticket - {ticket_key}")
        self.popout_button.pack_forget()
        
        content = tk.Frame(self.content_frame, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text=ticket_key, font=('Segoe UI', 16, 'bold'),
                bg="#FFFFFF", fg="#0066CC").pack(anchor="w", pady=(0, 5))
        
        tk.Label(content, text=ticket_data.get('summary', 'No summary'),
                font=('Segoe UI', 12), bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(0, 20))
        
        # Ticket details
        details = [
            ('Status', ticket_data.get('status', 'N/A')),
            ('Priority', ticket_data.get('priority', 'N/A')),
            ('Assignee', ticket_data.get('assignee', 'Unassigned')),
            ('Reporter', ticket_data.get('reporter', 'N/A')),
            ('Created', ticket_data.get('created', 'N/A')),
            ('Updated', ticket_data.get('updated', 'N/A')),
        ]
        
        for label, value in details:
            self._create_info_row(content, label, value)
        
        # Description
        tk.Label(content, text="Description:", font=('Segoe UI', 11, 'bold'),
                bg="#FFFFFF", fg="#495057").pack(anchor="w", pady=(20, 5))
        
        desc_text = scrolledtext.ScrolledText(content, font=('Segoe UI', 9),
                                             wrap=tk.WORD, height=10)
        desc_text.pack(fill=tk.BOTH, expand=True)
        desc_text.insert('1.0', ticket_data.get('description', 'No description available'))
        desc_text.config(state='disabled')
        
        self._log(f"Showing Jira ticket {ticket_key}")
    
    def show_vusion_details(self, vusion_data):
        """Show Vusion integration details."""
        self._clear_content()
        self.current_content_type = "vusion"
        self.current_data = vusion_data
        
        self.header_label.config(text="Vusion Integration Details")
        self.popout_button.pack_forget()
        
        content = tk.Frame(self.content_frame, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text="Vusion Integration", font=('Segoe UI', 16, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(0, 20))
        
        tk.Label(content, text="TODO: Display Vusion integration details",
                font=('Segoe UI', 10), bg="#FFFFFF", fg="#6C757D").pack(pady=20)
        
        self._log("Showing Vusion details")
    
    def show_note_details(self, note_data):
        """Show note with replies."""
        self._clear_content()
        self.current_content_type = "note"
        self.current_data = note_data
        
        self.header_label.config(text=f"Note - {note_data.get('headline', 'Note')}")
        self.popout_button.pack_forget()
        
        content = tk.Frame(self.content_frame, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Note header
        tk.Label(content, text=note_data.get('headline', 'Note'), font=('Segoe UI', 14, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(0, 5))
        
        tk.Label(content, text=f"By {note_data.get('user', 'Unknown')} • {note_data.get('created_at', '')}",
                font=('Segoe UI', 9), bg="#FFFFFF", fg="#6C757D").pack(anchor="w", pady=(0, 15))
        
        # Note content
        note_text = scrolledtext.ScrolledText(content, font=('Segoe UI', 10),
                                             wrap=tk.WORD, height=8)
        note_text.pack(fill=tk.X, pady=(0, 20))
        note_text.insert('1.0', note_data.get('note', ''))
        note_text.config(state='disabled')
        
        # Replies section
        tk.Label(content, text="Replies:", font=('Segoe UI', 11, 'bold'),
                bg="#FFFFFF", fg="#495057").pack(anchor="w", pady=(0, 10))
        
        # TODO: Load and display replies
        tk.Label(content, text="No replies yet",
                font=('Segoe UI', 9), bg="#FFFFFF", fg="#6C757D").pack(anchor="w")
        
        self._log(f"Showing note: {note_data.get('headline')}")
    
    def _create_info_row(self, parent, label, value):
        """Create an information row."""
        row = tk.Frame(parent, bg="#FFFFFF")
        row.pack(fill=tk.X, pady=3)
        
        tk.Label(row, text=f"{label}:", font=('Segoe UI', 10, 'bold'),
                bg="#FFFFFF", fg="#495057", width=20, anchor="w").pack(side=tk.LEFT)
        
        tk.Label(row, text=str(value), font=('Segoe UI', 10),
                bg="#FFFFFF", fg="#212529", anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _create_note_card(self, parent, note):
        """Create a note card."""
        card = tk.Frame(parent, bg="#F8F9FA", relief=tk.FLAT, bd=1)
        card.pack(fill=tk.X, pady=(0, 10))
        
        card_content = tk.Frame(card, bg="#F8F9FA", padx=15, pady=12)
        card_content.pack(fill=tk.X)
        
        tk.Label(card_content, text=note['headline'], font=('Segoe UI', 11, 'bold'),
                bg="#F8F9FA", fg="#212529").pack(anchor="w", pady=(0, 5))
        
        tk.Label(card_content, text=f"{note['user']} • {note['created_at'][:16]}",
                font=('Segoe UI', 8), bg="#F8F9FA", fg="#6C757D").pack(anchor="w")
        
        note_text = tk.Text(card_content, wrap=tk.WORD, height=3, font=('Segoe UI', 9),
                           bg="#FFFFFF", relief=tk.FLAT, bd=1, padx=10, pady=8)
        note_text.insert('1.0', note['note'])
        note_text.config(state='disabled')
        note_text.pack(fill=tk.X, pady=(10, 0))
    
    def _popout(self):
        """Pop out current content to separate window."""
        if self.current_content_type == "ssh":
            self._log(f"Popping out SSH terminal for AP {self.current_data}")
            messagebox.showinfo("Pop Out", "SSH terminal pop-out will be implemented")
        elif self.current_content_type == "browser":
            self._log(f"Showing browser window for AP {self.current_data}")
            messagebox.showinfo("Pop Out", "Browser window pop-out will be implemented")
    
    def _log(self, message, level="info"):
        """Log activity."""
        if self.log_callback:
            self.log_callback("Content Panel", message, level)
