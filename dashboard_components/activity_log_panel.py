"""
Activity Log Panel - Lower Left
Unified activity log from all panels
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import time


class ActivityLogPanel:
    """Lower left panel - Unified activity log."""
    
    def __init__(self, parent):
        self.parent = parent
        self._create_ui()
    
    def _create_ui(self):
        """Create activity log UI."""
        # Header
        header = tk.Frame(self.parent, bg="#0066CC", height=40)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        tk.Label(header, text="Activity Log", font=('Segoe UI', 12, 'bold'),
                bg="#0066CC", fg="white").pack(side=tk.LEFT, padx=15, pady=8)
        
        tk.Button(header, text="Clear", command=self._clear_log,
                 bg="#DC3545", fg="white", font=('Segoe UI', 8),
                 padx=10, pady=2, relief=tk.FLAT, cursor="hand2").pack(side=tk.RIGHT, padx=10)
        
        tk.Button(header, text="Export", command=self._export_log,
                 bg="#28A745", fg="white", font=('Segoe UI', 8),
                 padx=10, pady=2, relief=tk.FLAT, cursor="hand2").pack(side=tk.RIGHT, padx=5)
        
        # Filter frame
        filter_frame = tk.Frame(self.parent, bg="#F8F9FA", height=35)
        filter_frame.pack(fill=tk.X)
        filter_frame.pack_propagate(False)
        
        tk.Label(filter_frame, text="Filter:", font=('Segoe UI', 8),
                bg="#F8F9FA", fg="#495057").pack(side=tk.LEFT, padx=10)
        
        self.filter_var = tk.StringVar(value="All")
        filters = ["All", "Info", "Warning", "Error", "Success"]
        
        for f in filters:
            tk.Radiobutton(filter_frame, text=f, variable=self.filter_var, value=f,
                          font=('Segoe UI', 8), bg="#F8F9FA", command=self._apply_filter,
                          activebackground="#E9ECEF").pack(side=tk.LEFT, padx=3)
        
        # Log text area
        log_frame = tk.Frame(self.parent, bg="#FFFFFF")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, font=('Consolas', 9),
                                                  wrap=tk.WORD, bg="#F8F9FA", fg="#212529",
                                                  bd=0, padx=10, pady=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for different log levels
        self.log_text.tag_config("info", foreground="#0066CC")
        self.log_text.tag_config("success", foreground="#28A745")
        self.log_text.tag_config("warning", foreground="#FFC107")
        self.log_text.tag_config("error", foreground="#DC3545")
        self.log_text.tag_config("timestamp", foreground="#6C757D")
        self.log_text.tag_config("source", foreground="#6F42C1", font=('Consolas', 9, 'bold'))
        
        # Store all log entries
        self.log_entries = []
    
    def log_message(self, source, message, level="info"):
        """Add a message to the activity log.
        
        Args:
            source: Source of the message (e.g., "AP Panel", "Browser", "SSH")
            message: The log message
            level: Log level - "info", "success", "warning", or "error"
        """
        timestamp = time.strftime("%H:%M:%S")
        
        # Store entry
        entry = {
            'timestamp': timestamp,
            'source': source,
            'message': message,
            'level': level
        }
        self.log_entries.append(entry)
        
        # Check filter
        filter_value = self.filter_var.get()
        if filter_value != "All" and filter_value.lower() != level.lower():
            return
        
        # Format message
        log_line = f"[{timestamp}] [{source}] {message}\n"
        
        # Insert with appropriate tags
        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.log_text.insert(tk.END, f"[{source}] ", "source")
        self.log_text.insert(tk.END, f"{message}\n", level)
        
        # Auto-scroll to bottom
        self.log_text.see(tk.END)
        
        # Limit log size (keep last 1000 entries)
        if len(self.log_entries) > 1000:
            self.log_entries = self.log_entries[-1000:]
            # Also trim visible text
            lines = self.log_text.get('1.0', tk.END).count('\n')
            if lines > 1000:
                self.log_text.delete('1.0', '500.0')
    
    def _apply_filter(self):
        """Apply current filter to log display."""
        filter_value = self.filter_var.get()
        
        # Clear display
        self.log_text.delete('1.0', tk.END)
        
        # Re-add filtered entries
        for entry in self.log_entries:
            if filter_value == "All" or filter_value.lower() == entry['level'].lower():
                self.log_text.insert(tk.END, f"[{entry['timestamp']}] ", "timestamp")
                self.log_text.insert(tk.END, f"[{entry['source']}] ", "source")
                self.log_text.insert(tk.END, f"{entry['message']}\n", entry['level'])
        
        self.log_text.see(tk.END)
    
    def _clear_log(self):
        """Clear the activity log."""
        if len(self.log_entries) > 0:
            from tkinter import messagebox
            if messagebox.askyesno("Clear Log", "Are you sure you want to clear the activity log?",
                                   parent=self.parent):
                self.log_text.delete('1.0', tk.END)
                self.log_entries = []
                self.log_message("System", "Activity log cleared", "info")
    
    def _export_log(self):
        """Export activity log to file."""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Export Activity Log"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("Activity Log Export\n")
                    f.write(f"Exported: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 80 + "\n\n")
                    
                    for entry in self.log_entries:
                        f.write(f"[{entry['timestamp']}] [{entry['source']}] "
                               f"[{entry['level'].upper()}] {entry['message']}\n")
                
                self.log_message("System", f"Log exported to {filename}", "success")
            except Exception as e:
                self.log_message("System", f"Failed to export log: {e}", "error")
