"""
Context Panel - Upper Right
Shows contextual lists based on active AP (Jira tickets, Vusion data)
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext


class ContextPanel:
    """Upper right panel - Contextual lists (Jira, Vusion) for active AP."""
    
    def __init__(self, parent, db, on_selection=None, log_callback=None):
        self.parent = parent
        self.db = db
        self.on_selection = on_selection
        self.log_callback = log_callback
        
        self.active_ap = None
        self.active_ap_data = None
        
        self._create_ui()
    
    def _create_ui(self):
        """Create context panel UI."""
        # Header
        header = tk.Frame(self.parent, bg="#0066CC", height=40)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        self.header_label = tk.Label(header, text="Contextual Data", font=('Segoe UI', 12, 'bold'),
                                     bg="#0066CC", fg="white")
        self.header_label.pack(side=tk.LEFT, padx=15, pady=8)
        
        # Notebook for different context types
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Jira tab
        self.jira_frame = self._create_jira_tab()
        self.notebook.add(self.jira_frame, text="🎫 Jira Tickets")
        
        # Vusion tab
        self.vusion_frame = self._create_vusion_tab()
        self.notebook.add(self.vusion_frame, text="🏷️ Vusion Integration")
        
        # Show placeholder
        self._show_placeholder()
    
    def _create_jira_tab(self):
        """Create Jira tickets tab."""
        frame = ttk.Frame(self.notebook)
        
        # Search/filter bar
        filter_frame = tk.Frame(frame, bg="#F8F9FA", height=40)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        filter_frame.pack_propagate(False)
        
        tk.Label(filter_frame, text="Filter:", font=('Segoe UI', 9),
                bg="#F8F9FA", fg="#495057").pack(side=tk.LEFT, padx=5)
        
        self.jira_filter = tk.Entry(filter_frame, font=('Segoe UI', 9), bd=1, relief=tk.SOLID)
        self.jira_filter.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        tk.Button(filter_frame, text="🔄 Refresh", command=self._refresh_jira,
                 bg="#0066CC", fg="white", font=('Segoe UI', 8),
                 padx=10, pady=2, relief=tk.FLAT, cursor="hand2").pack(side=tk.RIGHT, padx=5)
        
        # Listbox for tickets
        list_frame = tk.Frame(frame, bg="#FFFFFF")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.jira_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                       font=('Segoe UI', 9), bd=1, relief=tk.SOLID,
                                       selectmode=tk.SINGLE)
        self.jira_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.jira_listbox.yview)
        
        self.jira_listbox.bind('<<ListboxSelect>>', self._on_jira_select)
        
        # Store ticket data
        self.jira_tickets = []
        
        return frame
    
    def _create_vusion_tab(self):
        """Create Vusion integration tab."""
        frame = ttk.Frame(self.notebook)
        
        content = tk.Frame(frame, bg="#FFFFFF", padx=20, pady=15)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text="Vusion Integration Data", font=('Segoe UI', 12, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(0, 10))
        
        # Placeholder for Vusion data
        self.vusion_text = scrolledtext.ScrolledText(content, font=('Segoe UI', 9),
                                                      wrap=tk.WORD, height=20)
        self.vusion_text.pack(fill=tk.BOTH, expand=True)
        
        return frame
    
    def set_active_ap(self, ap_id, ap_data):
        """Update context panel for a new active AP."""
        self.active_ap = ap_id
        self.active_ap_data = ap_data
        
        self.header_label.config(text=f"Context: AP {ap_id}")
        
        # Load Jira tickets for this AP
        self._load_jira_tickets()
        
        # Load Vusion data for this AP
        self._load_vusion_data()
        
        self._log(f"Context updated for AP {ap_id}")
    
    def _load_jira_tickets(self):
        """Load Jira tickets related to active AP."""
        self.jira_listbox.delete(0, tk.END)
        self.jira_tickets = []
        
        if not self.active_ap:
            return
        
        # TODO: Query Jira for tickets related to this AP
        # For now, show placeholder
        try:
            # Check if Jira integration is available
            from jira_integration import search_jira_tickets
            
            # Search for tickets mentioning this AP
            tickets = search_jira_tickets(self.active_ap)
            
            if tickets:
                for ticket in tickets:
                    display_text = f"{ticket['key']} - {ticket['summary']}"
                    self.jira_listbox.insert(tk.END, display_text)
                    self.jira_tickets.append(ticket)
                self._log(f"Loaded {len(tickets)} Jira tickets")
            else:
                self.jira_listbox.insert(tk.END, "No Jira tickets found for this AP")
                
        except Exception as e:
            self.jira_listbox.insert(tk.END, f"Jira integration not available: {str(e)}")
            self._log(f"Jira error: {str(e)}", "warning")
    
    def _load_vusion_data(self):
        """Load Vusion integration data for active AP."""
        self.vusion_text.delete('1.0', tk.END)
        
        if not self.active_ap_data:
            return
        
        # Display AP store/integration info
        store_id = self.active_ap_data.get('store_id', 'N/A')
        
        vusion_info = f"""Vusion Integration Status
        
Store ID: {store_id}
AP ID: {self.active_ap}
        
Integration Data:
- Status: Active
- Last Sync: 2025-11-16 12:00:00
- Labels Synced: 1,234
- Errors: 0

TODO: Implement actual Vusion API integration
"""
        
        self.vusion_text.insert('1.0', vusion_info)
        self._log("Vusion data loaded")
    
    def _refresh_jira(self):
        """Refresh Jira ticket list."""
        self._log("Refreshing Jira tickets...")
        self._load_jira_tickets()
    
    def _on_jira_select(self, event):
        """Handle Jira ticket selection."""
        selection = self.jira_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index < len(self.jira_tickets):
            ticket = self.jira_tickets[index]
            self._log(f"Selected Jira ticket: {ticket['key']}")
            
            if self.on_selection:
                self.on_selection("jira", ticket)
    
    def _show_placeholder(self):
        """Show placeholder when no AP is active."""
        self.jira_listbox.delete(0, tk.END)
        self.jira_listbox.insert(tk.END, "Select an AP to view related tickets")
        
        self.vusion_text.delete('1.0', tk.END)
        self.vusion_text.insert('1.0', "Select an AP to view Vusion integration data")
    
    def _log(self, message, level="info"):
        """Log activity."""
        if self.log_callback:
            self.log_callback("Context Panel", message, level)
