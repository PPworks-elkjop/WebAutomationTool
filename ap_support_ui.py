"""
AP Support System UI
Provides comprehensive support interface for managing ESL Access Points
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from database_manager import DatabaseManager
from typing import Dict, List, Optional


class APSearchDialog:
    """Dialog for searching and selecting APs for support."""
    
    def __init__(self, parent, current_user: str, db_manager: DatabaseManager):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("AP Support - Search")
        self.dialog.geometry("1000x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.current_user = current_user
        self.db = db_manager
        self.selected_ap = None
        
        self._create_ui()
        self._perform_search()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"1000x600+{x}+{y}")
    
    def _create_ui(self):
        """Create the search UI."""
        # Search criteria frame
        search_frame = tk.LabelFrame(self.dialog, text="Search Criteria", padx=10, pady=10)
        search_frame.pack(fill="x", padx=10, pady=10)
        
        # Row 1: AP ID / IP Address
        row1 = tk.Frame(search_frame)
        row1.pack(fill="x", pady=5)
        
        tk.Label(row1, text="AP ID / IP Address:", width=15, anchor="w").pack(side="left")
        self.search_var = tk.StringVar()
        tk.Entry(row1, textvariable=self.search_var, width=30).pack(side="left", padx=5)
        
        # Row 2: Store ID
        row2 = tk.Frame(search_frame)
        row2.pack(fill="x", pady=5)
        
        tk.Label(row2, text="Store ID:", width=15, anchor="w").pack(side="left")
        self.store_var = tk.StringVar()
        tk.Entry(row2, textvariable=self.store_var, width=30).pack(side="left", padx=5)
        
        # Row 3: Support Status
        row3 = tk.Frame(search_frame)
        row3.pack(fill="x", pady=5)
        
        tk.Label(row3, text="Support Status:", width=15, anchor="w").pack(side="left")
        self.status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(row3, textvariable=self.status_var, width=27, state="readonly")
        status_combo['values'] = ("All", "active", "in_progress", "pending", "resolved", "closed")
        status_combo.pack(side="left", padx=5)
        
        # Row 4: Jira Tickets
        row4 = tk.Frame(search_frame)
        row4.pack(fill="x", pady=5)
        
        tk.Label(row4, text="Jira Tickets:", width=15, anchor="w").pack(side="left")
        self.tickets_var = tk.StringVar(value="All")
        tickets_combo = ttk.Combobox(row4, textvariable=self.tickets_var, width=27, state="readonly")
        tickets_combo['values'] = ("All", "With Open Tickets", "Without Open Tickets")
        tickets_combo.pack(side="left", padx=5)
        
        # Search button
        tk.Button(row4, text="Search", command=self._perform_search, bg="#007BFF", fg="white", 
                 cursor="hand2", padx=20).pack(side="left", padx=10)
        
        # Results frame
        results_frame = tk.LabelFrame(self.dialog, text="Search Results", padx=10, pady=10)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Treeview for results
        tree_frame = tk.Frame(results_frame)
        tree_frame.pack(fill="both", expand=True)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("ap_id", "store_id", "ip_address", "type", "status", "support_status", "tickets"),
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configure columns
        self.tree.heading("ap_id", text="AP ID")
        self.tree.heading("store_id", text="Store ID")
        self.tree.heading("ip_address", text="IP Address")
        self.tree.heading("type", text="Type")
        self.tree.heading("status", text="Status")
        self.tree.heading("support_status", text="Support Status")
        self.tree.heading("tickets", text="Open Tickets")
        
        self.tree.column("ap_id", width=120, anchor="w")
        self.tree.column("store_id", width=100, anchor="center")
        self.tree.column("ip_address", width=120, anchor="center")
        self.tree.column("type", width=100, anchor="w")
        self.tree.column("status", width=80, anchor="center")
        self.tree.column("support_status", width=120, anchor="center")
        self.tree.column("tickets", width=100, anchor="center")
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Double-click to open
        self.tree.bind("<Double-1>", self._on_double_click)
        
        # Buttons frame
        btn_frame = tk.Frame(self.dialog)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(btn_frame, text="Open Selected", command=self._on_open, bg="#28A745", fg="white",
                 cursor="hand2", padx=20, pady=5).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", command=self.dialog.destroy, bg="#6C757D", fg="white",
                 cursor="hand2", padx=20, pady=5).pack(side="right", padx=5)
        
        # Result count label
        self.count_label = tk.Label(btn_frame, text="0 APs found", fg="#666666")
        self.count_label.pack(side="left", padx=20)
    
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
        self.window.geometry("900x700")
        
        self.ap = ap
        self.ap_id = ap_id
        self.current_user = current_user
        self.db = db_manager
        self.browser_helper = browser_helper
        
        # Register this window
        APSupportWindow._open_windows[ap_id] = self
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self._create_ui()
        self._load_data()
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.window.winfo_screenheight() // 2) - (700 // 2)
        self.window.geometry(f"900x700+{x}+{y}")
    
    def _create_ui(self):
        """Create the support window UI."""
        # Main container with scrollbar
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill="both", expand=True)
        
        # Canvas and scrollbar
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # === AP Information Section ===
        info_frame = tk.LabelFrame(scrollable_frame, text="AP Information", padx=15, pady=15)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        # Create info grid
        info_grid = tk.Frame(info_frame)
        info_grid.pack(fill="x")
        
        info_labels = [
            ("AP ID:", "ap_id"),
            ("Store ID:", "store_id"),
            ("IP Address:", "ip_address"),
            ("Type:", "type"),
            ("Status:", "status"),
            ("Support Status:", "support_status"),
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
            
            tk.Label(info_grid, text=label_text, font=("Arial", 9, "bold"), anchor="w", width=18).grid(
                row=row, column=col, sticky="w", padx=5, pady=3)
            value_label = tk.Label(info_grid, text="", font=("Arial", 9), anchor="w")
            value_label.grid(row=row, column=col+1, sticky="w", padx=5, pady=3)
            self.info_labels[field] = value_label
        
        # Support Status dropdown
        status_row = tk.Frame(info_frame)
        status_row.pack(fill="x", pady=(10, 0))
        
        tk.Label(status_row, text="Change Support Status:", font=("Arial", 9, "bold")).pack(side="left")
        self.support_status_var = tk.StringVar(value=self.ap.get('support_status', 'active'))
        status_combo = ttk.Combobox(status_row, textvariable=self.support_status_var, width=15, state="readonly")
        status_combo['values'] = ("active", "in_progress", "pending", "resolved", "closed")
        status_combo.pack(side="left", padx=10)
        status_combo.bind("<<ComboboxSelected>>", self._on_status_change)
        
        # Refresh button
        tk.Button(status_row, text="🔄 Refresh Data", command=self._refresh_ap_data,
                 bg="#17A2B8", fg="white", cursor="hand2", padx=15, pady=5,
                 font=("Arial", 9)).pack(side="left", padx=10)
        
        # === Connection Section ===
        connect_frame = tk.LabelFrame(scrollable_frame, text="Connect to AP", padx=15, pady=15)
        connect_frame.pack(fill="x", padx=10, pady=10)
        
        btn_row = tk.Frame(connect_frame)
        btn_row.pack()
        
        tk.Button(btn_row, text="🌐 Open in Browser", command=self._connect_browser, 
                 bg="#007BFF", fg="white", cursor="hand2", padx=15, pady=8,
                 font=("Arial", 10)).pack(side="left", padx=5)
        
        tk.Button(btn_row, text="🖥️ SSH Connection", command=self._connect_ssh, 
                 bg="#17A2B8", fg="white", cursor="hand2", padx=15, pady=8,
                 font=("Arial", 10), state="disabled").pack(side="left", padx=5)
        
        # === Support Notes Section ===
        notes_frame = tk.LabelFrame(scrollable_frame, text="Support Notes", padx=15, pady=15)
        notes_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # New note entry
        new_note_frame = tk.LabelFrame(notes_frame, text="New Note", padx=10, pady=10)
        new_note_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(new_note_frame, text="Headline:").pack(anchor="w")
        self.headline_var = tk.StringVar()
        tk.Entry(new_note_frame, textvariable=self.headline_var, font=("Arial", 10)).pack(fill="x", pady=(0, 5))
        
        tk.Label(new_note_frame, text="Note:").pack(anchor="w")
        self.note_text = scrolledtext.ScrolledText(new_note_frame, height=4, font=("Arial", 10), wrap=tk.WORD)
        self.note_text.pack(fill="x", pady=(0, 10))
        
        note_btn_frame = tk.Frame(new_note_frame)
        note_btn_frame.pack(fill="x")
        
        tk.Button(note_btn_frame, text="Save Note", command=self._save_note, bg="#28A745", 
                 fg="white", cursor="hand2", padx=20, pady=5).pack(side="left")
        tk.Button(note_btn_frame, text="Clear", command=self._clear_note_form, bg="#6C757D", 
                 fg="white", cursor="hand2", padx=20, pady=5).pack(side="left", padx=5)
        
        # Existing notes list
        existing_notes_frame = tk.LabelFrame(notes_frame, text="Previous Notes", padx=10, pady=10)
        existing_notes_frame.pack(fill="both", expand=True)
        
        # Notes listbox
        notes_list_frame = tk.Frame(existing_notes_frame)
        notes_list_frame.pack(fill="both", expand=True)
        
        notes_scroll = ttk.Scrollbar(notes_list_frame, orient="vertical")
        self.notes_listbox = tk.Listbox(notes_list_frame, yscrollcommand=notes_scroll.set, 
                                        font=("Arial", 9), height=8)
        notes_scroll.config(command=self.notes_listbox.yview)
        
        self.notes_listbox.pack(side="left", fill="both", expand=True)
        notes_scroll.pack(side="right", fill="y")
        
        self.notes_listbox.bind("<<ListboxSelect>>", self._on_note_select)
        
        # Note detail/edit area
        note_detail_frame = tk.Frame(existing_notes_frame)
        note_detail_frame.pack(fill="x", pady=(10, 0))
        
        self.note_detail_text = scrolledtext.ScrolledText(note_detail_frame, height=6, 
                                                          font=("Arial", 9), wrap=tk.WORD, state="disabled")
        self.note_detail_text.pack(fill="both", expand=True)
        
        # Note action buttons
        note_action_frame = tk.Frame(existing_notes_frame)
        note_action_frame.pack(fill="x", pady=(5, 0))
        
        self.edit_note_btn = tk.Button(note_action_frame, text="Edit", command=self._edit_selected_note,
                                       state="disabled", bg="#FFC107", cursor="hand2", padx=15)
        self.edit_note_btn.pack(side="left", padx=2)
        
        self.delete_note_btn = tk.Button(note_action_frame, text="Delete", command=self._delete_selected_note,
                                         state="disabled", bg="#DC3545", fg="white", cursor="hand2", padx=15)
        self.delete_note_btn.pack(side="left", padx=2)
        
        self.save_edit_btn = tk.Button(note_action_frame, text="Save Changes", command=self._save_note_edit,
                                       state="disabled", bg="#28A745", fg="white", cursor="hand2", padx=15)
        self.save_edit_btn.pack(side="left", padx=2)
        
        self.cancel_edit_btn = tk.Button(note_action_frame, text="Cancel Edit", command=self._cancel_note_edit,
                                         state="disabled", bg="#6C757D", fg="white", cursor="hand2", padx=15)
        self.cancel_edit_btn.pack(side="left", padx=2)
        
        # Store notes data
        self.notes_data = []
        self.selected_note_id = None
        self.editing_note = False
    
    def _load_data(self):
        """Load AP data into the UI."""
        # Populate info labels
        for field, label in self.info_labels.items():
            value = self.ap.get(field, '')
            if value:
                label.config(text=str(value))
            else:
                label.config(text="-", fg="gray")
        
        # Update support status
        self.support_status_var.set(self.ap.get('support_status', 'active'))
        
        # Load support notes
        self._refresh_notes()
    
    def _refresh_ap_data(self):
        """Refresh AP data from database."""
        # Reload AP from database
        updated_ap = self.db.get_access_point(self.ap_id)
        if updated_ap:
            self.ap = updated_ap
            
            # Update all info labels
            for field, label in self.info_labels.items():
                value = self.ap.get(field, '')
                if value:
                    label.config(text=str(value), fg="black")
                else:
                    label.config(text="-", fg="gray")
            
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
        """Refresh the notes list."""
        self.notes_listbox.delete(0, tk.END)
        self.notes_data = self.db.get_support_notes(self.ap_id)
        
        for note in self.notes_data:
            created_at = note['created_at']
            user = note['user']
            headline = note['headline']
            display = f"{created_at} - {user} - {headline}"
            self.notes_listbox.insert(tk.END, display)
    
    def _on_status_change(self, event=None):
        """Handle support status change."""
        new_status = self.support_status_var.get()
        success, message = self.db.update_support_status(self.ap_id, new_status)
        if success:
            messagebox.showinfo("Status Updated", f"Support status changed to: {new_status}", parent=self.window)
        else:
            messagebox.showerror("Error", f"Failed to update status: {message}", parent=self.window)
    
    def _connect_browser(self):
        """Open AP in browser."""
        if self.browser_helper:
            # Use Quick Connect functionality
            ip = self.ap.get('ip_address', '')
            username = self.ap.get('username_webui', '')
            password = self.ap.get('password_webui', '')
            
            if ip and username and password:
                messagebox.showinfo("Connecting", f"Opening browser for {self.ap_id}...", parent=self.window)
                # TODO: Call browser helper's quick connect
            else:
                messagebox.showwarning("Missing Info", "IP address or credentials not available.", parent=self.window)
        else:
            messagebox.showwarning("Not Available", "Browser connection not available.", parent=self.window)
    
    def _connect_ssh(self):
        """Connect via SSH (placeholder for future implementation)."""
        messagebox.showinfo("Coming Soon", "SSH connection will be available in a future update.", parent=self.window)
    
    def _save_note(self):
        """Save a new support note."""
        headline = self.headline_var.get().strip()
        note = self.note_text.get("1.0", tk.END).strip()
        
        if not headline:
            messagebox.showwarning("Missing Headline", "Please enter a headline for the note.", parent=self.window)
            return
        
        if not note:
            messagebox.showwarning("Missing Note", "Please enter note content.", parent=self.window)
            return
        
        success, message, note_id = self.db.add_support_note(self.ap_id, self.current_user, headline, note)
        if success:
            self._clear_note_form()
            self._refresh_notes()
            messagebox.showinfo("Note Saved", "Support note added successfully.", parent=self.window)
        else:
            messagebox.showerror("Error", f"Failed to save note: {message}", parent=self.window)
    
    def _clear_note_form(self):
        """Clear the new note form."""
        self.headline_var.set("")
        self.note_text.delete("1.0", tk.END)
    
    def _on_note_select(self, event=None):
        """Handle note selection from list."""
        if self.editing_note:
            return  # Don't allow selection change while editing
        
        selection = self.notes_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        note = self.notes_data[idx]
        self.selected_note_id = note['id']
        
        # Display note details
        self.note_detail_text.config(state="normal")
        self.note_detail_text.delete("1.0", tk.END)
        
        detail = f"Date: {note['created_at']}\n"
        detail += f"User: {note['user']}\n"
        detail += f"Headline: {note['headline']}\n"
        detail += f"\n{note['note']}"
        
        if note.get('updated_at') and note['updated_at'] != note['created_at']:
            detail += f"\n\n(Edited: {note['updated_at']} by {note.get('updated_by', 'unknown')})"
        
        self.note_detail_text.insert("1.0", detail)
        self.note_detail_text.config(state="disabled")
        
        # Enable edit/delete only for latest note
        is_latest = self.db.is_latest_note(note['id'], self.ap_id)
        if is_latest:
            self.edit_note_btn.config(state="normal")
            self.delete_note_btn.config(state="normal")
        else:
            self.edit_note_btn.config(state="disabled")
            self.delete_note_btn.config(state="disabled")
    
    def _edit_selected_note(self):
        """Enter edit mode for selected note."""
        if not self.selected_note_id:
            return
        
        note = next((n for n in self.notes_data if n['id'] == self.selected_note_id), None)
        if not note:
            return
        
        self.editing_note = True
        
        # Enable text area and populate with editable content
        self.note_detail_text.config(state="normal")
        self.note_detail_text.delete("1.0", tk.END)
        self.note_detail_text.insert("1.0", note['note'])
        
        # Update button states
        self.edit_note_btn.config(state="disabled")
        self.delete_note_btn.config(state="disabled")
        self.save_edit_btn.config(state="normal")
        self.cancel_edit_btn.config(state="normal")
        self.notes_listbox.config(state="disabled")
    
    def _save_note_edit(self):
        """Save edited note."""
        if not self.selected_note_id:
            return
        
        edited_text = self.note_detail_text.get("1.0", tk.END).strip()
        note = next((n for n in self.notes_data if n['id'] == self.selected_note_id), None)
        
        if not note:
            return
        
        success, message = self.db.update_support_note(self.selected_note_id, note['headline'], 
                                                       edited_text, self.current_user)
        if success:
            self.editing_note = False
            self._refresh_notes()
            self.note_detail_text.config(state="disabled")
            self.save_edit_btn.config(state="disabled")
            self.cancel_edit_btn.config(state="disabled")
            self.notes_listbox.config(state="normal")
            messagebox.showinfo("Note Updated", "Note updated successfully.", parent=self.window)
        else:
            messagebox.showerror("Error", f"Failed to update note: {message}", parent=self.window)
    
    def _cancel_note_edit(self):
        """Cancel note editing."""
        self.editing_note = False
        self.note_detail_text.config(state="disabled")
        self.save_edit_btn.config(state="disabled")
        self.cancel_edit_btn.config(state="disabled")
        self.notes_listbox.config(state="normal")
        
        # Reload the note detail
        self._on_note_select()
    
    def _delete_selected_note(self):
        """Delete the selected note."""
        if not self.selected_note_id:
            return
        
        response = messagebox.askyesno("Confirm Delete", 
                                      "Are you sure you want to delete this note?",
                                      parent=self.window)
        if not response:
            return
        
        success, message = self.db.delete_support_note(self.selected_note_id, self.current_user)
        if success:
            self.selected_note_id = None
            self._refresh_notes()
            self.note_detail_text.config(state="normal")
            self.note_detail_text.delete("1.0", tk.END)
            self.note_detail_text.config(state="disabled")
            self.edit_note_btn.config(state="disabled")
            self.delete_note_btn.config(state="disabled")
            messagebox.showinfo("Note Deleted", "Note deleted successfully.", parent=self.window)
        else:
            messagebox.showerror("Error", f"Failed to delete note: {message}", parent=self.window)
    
    def _on_close(self):
        """Handle window close."""
        # Unregister window
        if self.ap_id in APSupportWindow._open_windows:
            del APSupportWindow._open_windows[self.ap_id]
        self.window.destroy()
