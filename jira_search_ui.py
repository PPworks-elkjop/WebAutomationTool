"""
Jira Search UI - Search for Jira issues related to APs and display results
"""

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from typing import Optional
from database_manager import DatabaseManager
from jira_integration import JiraIntegration
from jira_db_manager import JiraDBManager


class JiraSearchWindow:
    """Window for searching and viewing Jira issues related to APs."""
    
    def __init__(self, parent, db_manager: DatabaseManager, ap_id: str = ""):
        """
        Initialize Jira Search window.
        
        Args:
            parent: Parent window
            db_manager: Database manager instance
            ap_id: Optional AP ID to pre-fill search
        """
        self.parent = parent
        self.db_manager = db_manager
        self.jira = JiraIntegration(db_manager)
        self.jira_db = JiraDBManager(db_manager)
        self.window = None
        self.ap_id = ap_id
        
        self._create_window()
    
    def _create_window(self):
        """Create the main window."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Jira Issue Search")
        self.window.geometry("1200x800")
        
        # Main container
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Search frame
        search_frame = ttk.LabelFrame(main_frame, text="Search", padding="10")
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        # AP ID search
        ttk.Label(search_frame, text="ESL AP ID:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.ap_id_entry = ttk.Entry(search_frame, width=30)
        self.ap_id_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        if self.ap_id:
            self.ap_id_entry.insert(0, self.ap_id)
        
        # Search buttons
        button_frame = ttk.Frame(search_frame)
        button_frame.grid(row=0, column=2, sticky=tk.E)
        
        ttk.Button(button_frame, text="Search Jira", 
                  command=self._search_jira).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="View Cached", 
                  command=self._view_cached).pack(side=tk.LEFT, padx=2)
        
        # Status indicator
        self.status_label = ttk.Label(main_frame, text="Ready", foreground="gray")
        self.status_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        # Results frame with paned window
        results_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        results_paned.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Left pane: Issue list
        issues_frame = ttk.Frame(results_paned)
        results_paned.add(issues_frame, weight=1)
        
        # Issue list with scrollbar
        list_container = ttk.Frame(issues_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        self.issues_tree = ttk.Treeview(list_container, columns=('key', 'summary', 'status', 'updated'),
                                        show='headings', selectmode='browse')
        
        self.issues_tree.heading('key', text='Key')
        self.issues_tree.heading('summary', text='Summary')
        self.issues_tree.heading('status', text='Status')
        self.issues_tree.heading('updated', text='Updated')
        
        self.issues_tree.column('key', width=100)
        self.issues_tree.column('summary', width=300)
        self.issues_tree.column('status', width=100)
        self.issues_tree.column('updated', width=150)
        
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.issues_tree.yview)
        self.issues_tree.configure(yscrollcommand=scrollbar.set)
        
        self.issues_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.issues_tree.bind('<<TreeviewSelect>>', self._on_issue_selected)
        self.issues_tree.bind('<Double-Button-1>', self._open_in_browser)
        
        # Right pane: Issue details
        details_frame = ttk.Frame(results_paned)
        results_paned.add(details_frame, weight=2)
        
        # Details notebook
        details_notebook = ttk.Notebook(details_frame)
        details_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Issue details tab
        issue_tab = ttk.Frame(details_notebook)
        details_notebook.add(issue_tab, text="Issue Details")
        
        self.details_text = tk.Text(issue_tab, wrap=tk.WORD, state='disabled',
                                    font=('Segoe UI', 10))
        details_scroll = ttk.Scrollbar(issue_tab, orient=tk.VERTICAL, 
                                      command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scroll.set)
        
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Comments tab
        comments_tab = ttk.Frame(details_notebook)
        details_notebook.add(comments_tab, text="Comments")
        
        self.comments_text = tk.Text(comments_tab, wrap=tk.WORD, state='disabled',
                                    font=('Segoe UI', 10))
        comments_scroll = ttk.Scrollbar(comments_tab, orient=tk.VERTICAL,
                                       command=self.comments_text.yview)
        self.comments_text.configure(yscrollcommand=comments_scroll.set)
        
        self.comments_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        comments_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure text tags for styling
        self.details_text.tag_configure('heading', font=('Segoe UI', 10, 'bold'))
        self.details_text.tag_configure('link', foreground='blue', underline=True)
        self.details_text.tag_configure('label', font=('Segoe UI', 9, 'bold'))
        
        self.comments_text.tag_configure('internal', background='#fff3cd', 
                                        font=('Segoe UI', 9, 'bold'))
        self.comments_text.tag_configure('public', background='#d4edda',
                                        font=('Segoe UI', 9, 'bold'))
        self.comments_text.tag_configure('author', font=('Segoe UI', 9, 'bold'))
        self.comments_text.tag_configure('date', foreground='gray', font=('Segoe UI', 8))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, sticky=tk.E, pady=(10, 0))
        
        ttk.Button(button_frame, text="Open in Browser",
                  command=self._open_in_browser).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Refresh",
                  command=self._refresh_current).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close",
                  command=self.window.destroy).pack(side=tk.LEFT, padx=5)
        
        # Check if Jira is configured
        if not self.jira.is_configured():
            self.status_label.config(text="⚠ Jira not configured. Please configure in Admin Settings.",
                                   foreground="red")
        
        # Auto-search if AP ID provided
        if self.ap_id:
            self.window.after(100, self._view_cached)
    
    def _set_status(self, message: str, color: str = "black"):
        """Update status label."""
        self.status_label.config(text=message, foreground=color)
        self.window.update_idletasks()
    
    def _search_jira(self):
        """Search Jira for issues related to AP ID."""
        ap_id = self.ap_id_entry.get().strip()
        
        if not ap_id:
            messagebox.showwarning("Missing AP ID", "Please enter an ESL AP ID to search.",
                                 parent=self.window)
            return
        
        if not self.jira.is_configured():
            messagebox.showerror("Jira Not Configured",
                               "Jira is not configured. Please configure in Admin Settings.",
                               parent=self.window)
            return
        
        self._set_status(f"Searching Jira for {ap_id}...", "blue")
        self.window.update()
        
        # Build JQL query
        jql = f'textfields ~ "{ap_id}" ORDER BY updated DESC'
        
        # Search Jira
        success, results, message = self.jira.search_issues(jql, max_results=50)
        
        if not success:
            self._set_status(f"Search failed: {message}", "red")
            messagebox.showerror("Search Failed", message, parent=self.window)
            return
        
        # Get Jira base URL for constructing issue URLs
        credentials = self.jira.credentials_manager.get_credentials('jira')
        jira_base_url = credentials.get('url', '').rstrip('/') if credentials else ''
        
        # Store results in database
        issues = results.get('issues', [])
        stored_count = 0
        
        for issue in issues:
            try:
                link_id = self.jira_db.store_issue(ap_id, issue, jira_base_url)
                
                # Store comments if available
                comment_data = issue.get('fields', {}).get('comment', {})
                comments = comment_data.get('comments', []) if isinstance(comment_data, dict) else []
                if comments:
                    self.jira_db.store_comments(link_id, comments)
                
                stored_count += 1
            except Exception as e:
                print(f"Error storing issue {issue.get('key', 'unknown')}: {e}")
        
        self._set_status(f"Found {len(issues)} issues, stored {stored_count} in database", "green")
        
        # Display results
        self._display_cached_issues(ap_id)
    
    def _view_cached(self):
        """View cached issues from database."""
        ap_id = self.ap_id_entry.get().strip()
        
        if not ap_id:
            messagebox.showwarning("Missing AP ID", "Please enter an ESL AP ID.",
                                 parent=self.window)
            return
        
        self._display_cached_issues(ap_id)
    
    def _display_cached_issues(self, ap_id: str):
        """Display cached issues for an AP from database."""
        # Clear current items
        for item in self.issues_tree.get_children():
            self.issues_tree.delete(item)
        
        # Get issues from database
        issues = self.jira_db.get_issues_for_ap(ap_id)
        
        if not issues:
            self._set_status(f"No cached issues found for {ap_id}", "gray")
            return
        
        # Populate tree
        for issue in issues:
            updated_date = issue['updated_date'][:10] if issue['updated_date'] else 'N/A'
            
            self.issues_tree.insert('', tk.END, 
                                   values=(issue['jira_key'], 
                                          issue['summary'], 
                                          issue['status'],
                                          updated_date),
                                   tags=(str(issue['id']),))
        
        self._set_status(f"Showing {len(issues)} cached issues for {ap_id}", "green")
        
        # Select first item
        if self.issues_tree.get_children():
            first_item = self.issues_tree.get_children()[0]
            self.issues_tree.selection_set(first_item)
            self.issues_tree.focus(first_item)
    
    def _on_issue_selected(self, event):
        """Handle issue selection."""
        selection = self.issues_tree.selection()
        if not selection:
            return
        
        # Get the database ID from tags
        item = selection[0]
        tags = self.issues_tree.item(item, 'tags')
        if not tags:
            return
        
        db_id = int(tags[0])
        
        # Get issue details from database
        with self.db_manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM jira_ap_links WHERE id = ?', (db_id,))
            row = cursor.fetchone()
            
            if row:
                issue = dict(row)
                self._display_issue_details(issue)
                self._display_comments(db_id)
    
    def _display_issue_details(self, issue: dict):
        """Display issue details in the details pane."""
        self.details_text.config(state='normal')
        self.details_text.delete('1.0', tk.END)
        
        # Format and insert details
        self.details_text.insert(tk.END, f"{issue['jira_key']}\n", 'heading')
        self.details_text.insert(tk.END, f"{issue['jira_url']}\n\n", 'link')
        
        self._insert_field("Summary:", issue['summary'])
        self._insert_field("Type:", issue['issue_type'])
        self._insert_field("Status:", issue['status'])
        self._insert_field("Priority:", issue['priority'])
        self._insert_field("Resolution:", issue['resolution'] or 'Unresolved')
        
        self.details_text.insert(tk.END, "\n")
        self._insert_field("Created:", issue['created_date'][:19] if issue['created_date'] else 'N/A')
        self._insert_field("Updated:", issue['updated_date'][:19] if issue['updated_date'] else 'N/A')
        self._insert_field("Resolved:", issue['resolved_date'][:19] if issue['resolved_date'] else 'N/A')
        
        self.details_text.insert(tk.END, "\n")
        self._insert_field("Creator:", issue['creator'])
        self._insert_field("Reporter:", issue['reporter'])
        self._insert_field("Assignee:", issue['assignee'] or 'Unassigned')
        
        if issue['description_preview']:
            self.details_text.insert(tk.END, "\nDescription:\n", 'label')
            self.details_text.insert(tk.END, f"{issue['description_preview']}\n")
        
        self.details_text.insert(tk.END, f"\n\nComments: {issue['comment_count']}\n", 'label')
        self.details_text.insert(tk.END, f"Last Synced: {issue['last_synced']}\n", 'date')
        
        self.details_text.config(state='disabled')
        
        # Store URL for open in browser
        self.current_url = issue['jira_url']
    
    def _insert_field(self, label: str, value: str):
        """Insert a labeled field."""
        self.details_text.insert(tk.END, f"{label:<15}", 'label')
        self.details_text.insert(tk.END, f"{value}\n")
    
    def _display_comments(self, jira_link_id: int):
        """Display comments for the selected issue."""
        self.comments_text.config(state='normal')
        self.comments_text.delete('1.0', tk.END)
        
        # Get comments from database
        comments = self.jira_db.get_comments_for_issue(jira_link_id, include_internal=True)
        
        if not comments:
            self.comments_text.insert(tk.END, "No comments found.")
            self.comments_text.config(state='disabled')
            return
        
        # Display each comment
        for idx, comment in enumerate(comments, 1):
            # Header with internal/public badge
            badge = "[INTERNAL] " if comment['is_internal'] else "[PUBLIC] "
            tag = 'internal' if comment['is_internal'] else 'public'
            
            self.comments_text.insert(tk.END, f"\n{badge}", tag)
            self.comments_text.insert(tk.END, f"Comment #{idx}\n", 'author')
            self.comments_text.insert(tk.END, 
                                    f"{comment['author']} - {comment['created_date'][:19]}\n",
                                    'date')
            self.comments_text.insert(tk.END, "-" * 80 + "\n")
            self.comments_text.insert(tk.END, f"{comment['comment_text']}\n\n")
        
        self.comments_text.config(state='disabled')
    
    def _open_in_browser(self, event=None):
        """Open the selected issue in browser."""
        if hasattr(self, 'current_url') and self.current_url:
            webbrowser.get('windows-default').open(self.current_url)
    
    def _refresh_current(self):
        """Refresh the currently selected issue from Jira."""
        ap_id = self.ap_id_entry.get().strip()
        if ap_id:
            self._search_jira()


def open_jira_search(parent, db_manager: DatabaseManager, ap_id: str = ""):
    """
    Open Jira search window.
    
    Args:
        parent: Parent window
        db_manager: Database manager instance
        ap_id: Optional AP ID to pre-fill
    """
    JiraSearchWindow(parent, db_manager, ap_id)
