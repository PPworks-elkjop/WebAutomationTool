import tkinter as tk
from tkinter import ttk

class ConnectionStatusDialog:
    """Dialog showing real-time connection status for multiple APs."""
    
    def __init__(self, parent, ap_list):
        """Initialize the connection status dialog.
        
        Args:
            parent: Parent window
            ap_list: List of AP dictionaries to display
        """
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Connection Status")
        self.dialog.geometry("900x600")
        self.dialog.configure(bg="#FFFFFF")
        
        # Make it non-modal (stay on top but don't block interaction)
        self.dialog.transient(parent)
        self.dialog.attributes('-topmost', True)
        
        # Store AP list
        self.ap_list = ap_list
        self.ap_rows = {}  # Map ap_id to tree item
        
        self._create_ui()
        self._populate_aps()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"900x600+{x}+{y}")
    
    def _create_ui(self):
        """Create the UI elements."""
        # Header
        header_frame = tk.Frame(self.dialog, bg="#FFFFFF", pady=10)
        header_frame.pack(fill="x", padx=20)
        
        title_label = tk.Label(
            header_frame,
            text="Connection Progress",
            font=("Arial", 16, "bold"),
            bg="#FFFFFF"
        )
        title_label.pack()
        
        # Create treeview with scrollbar
        tree_frame = tk.Frame(self.dialog, bg="#FFFFFF")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("store_id", "ap_id", "ip_address", "result", "status", "message"),
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            height=20
        )
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configure columns
        self.tree.heading("store_id", text="Store ID")
        self.tree.heading("ap_id", text="AP ID")
        self.tree.heading("ip_address", text="IP Address")
        self.tree.heading("result", text="")  # Visual indicator column (no header)
        self.tree.heading("status", text="Status")
        self.tree.heading("message", text="Message")
        
        self.tree.column("store_id", width=100, anchor="center")
        self.tree.column("ap_id", width=150, anchor="center")
        self.tree.column("ip_address", width=150, anchor="center")
        self.tree.column("result", width=40, anchor="center")  # Narrow column for ✓/✗
        self.tree.column("status", width=120, anchor="center")
        self.tree.column("message", width=310, anchor="w")
        
        # Configure tags for status colors
        self.tree.tag_configure("pending", background="#F8F9FA")
        self.tree.tag_configure("connecting", background="#FFF3CD")
        self.tree.tag_configure("connected", background="#D4EDDA")
        self.tree.tag_configure("failed", background="#F8D7DA")
        
        # Store full messages for tooltips
        self.full_messages = {}
        
        # Bind hover events for tooltips
        self.tree.bind("<Motion>", self._on_mouse_motion)
        self.tree.bind("<Leave>", self._on_mouse_leave)
        self.tooltip = None
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Summary label
        self.summary_label = tk.Label(
            self.dialog,
            text="Preparing to connect...",
            font=("Arial", 10),
            bg="#FFFFFF",
            fg="#666666"
        )
        self.summary_label.pack(pady=10)
        
        # Button frame
        button_frame = tk.Frame(self.dialog, bg="#FFFFFF")
        button_frame.pack(pady=10)
        
        # Export to Excel button
        self.export_button = tk.Button(
            button_frame,
            text="📊 Export to Excel",
            command=self._on_export,
            font=("Arial", 10),
            bg="#007BFF",
            fg="white",
            width=18,
            height=2
        )
        self.export_button.pack(side="left", padx=5)
        
        # Close button
        self.close_button = tk.Button(
            button_frame,
            text="Hide Window",
            command=self._on_close,
            font=("Arial", 10),
            bg="#6C757D",
            fg="white",
            width=15,
            height=2
        )
        self.close_button.pack(side="left", padx=5)
    
    def _populate_aps(self):
        """Populate the treeview with APs."""
        for ap in self.ap_list:
            store_id = ap.get('store_id', 'Unknown')
            ap_id = ap.get('ap_id', 'Unknown')
            ip_address = ap.get('ip_address', 'Unknown')
            
            item = self.tree.insert(
                "",
                "end",
                values=(store_id, ap_id, ip_address, "", "Pending", "Waiting to connect..."),
                tags=("pending",)
            )
            self.ap_rows[ap_id] = item
    
    def update_status(self, ap_id, status, message="", result_indicator=None):
        """Update the status of an AP.
        
        Args:
            ap_id: AP identifier
            status: One of: "connecting", "connected", "failed"
            message: Status message to display
            result_indicator: Optional visual indicator ("✓", "✗", or None)
        """
        if ap_id not in self.ap_rows:
            return
        
        item = self.ap_rows[ap_id]
        current_values = self.tree.item(item, "values")
        
        # Map status to display text and tag
        status_map = {
            "connecting": ("Connecting...", "connecting"),
            "connected": ("✓ Connected", "connected"),
            "failed": ("✗ Failed", "failed")
        }
        
        status_text, tag = status_map.get(status, (status, "pending"))
        
        # Auto-detect result indicator from message if not provided
        # Logic: ✓ = enabled/on, ✗ = disabled/off, empty = unknown/connection/processing
        if result_indicator is None:
            msg_lower = message.lower()
            # Check for explicit enabled/disabled states
            if "ssh is already enabled" in msg_lower or "ssh enabled successfully" in msg_lower:
                result_indicator = "✓"
            elif "ssh is currently enabled" in msg_lower and "disabled" not in msg_lower:
                result_indicator = "✓"
            elif "ssh is currently disabled" in msg_lower or "ssh is already disabled" in msg_lower:
                result_indicator = "✗"
            elif "provisioning is on" in msg_lower or "provisioning enabled" in msg_lower:
                result_indicator = "✓"
            elif "provisioning is off" in msg_lower or "provisioning disabled" in msg_lower:
                result_indicator = "✗"
            elif "provisioning: report" in msg_lower and "enabled" in msg_lower:
                result_indicator = "✓"
            elif "provisioning: report" in msg_lower and "disabled" in msg_lower:
                result_indicator = "✗"
            # For connection, processing, or unclear states, leave empty
            elif status == "connecting" or "connecting" in msg_lower or "processing" in msg_lower:
                result_indicator = ""
            elif status == "failed":
                result_indicator = ""  # Failed to check, so we don't know the state
            else:
                result_indicator = ""  # Unknown state
        
        # Store full message for tooltip
        self.full_messages[item] = message
        
        # Truncate message for display (show first 50 chars)
        display_message = message if len(message) <= 50 else message[:47] + "..."
        
        # Update the row
        self.tree.item(
            item,
            values=(current_values[0], current_values[1], current_values[2], result_indicator, status_text, display_message),
            tags=(tag,)
        )
        
        # Scroll to show this item
        self.tree.see(item)
        
        # Update the dialog to show changes immediately
        self.dialog.update_idletasks()
    
    def update_summary(self, message):
        """Update the summary label.
        
        Args:
            message: Summary message to display
        """
        self.summary_label.config(text=message)
        self.dialog.update_idletasks()
    
    def enable_close(self):
        """Update the close button styling when operations are complete."""
        self.close_button.config(bg="#28A745")
        self.dialog.update_idletasks()
    
    def _on_export(self):
        """Export the status data to Excel."""
        try:
            from tkinter import filedialog, messagebox
            from datetime import datetime
            
            # Try to import openpyxl for Excel export
            try:
                from openpyxl import Workbook
                from openpyxl.styles import Font, Alignment, PatternFill
                use_excel = True
            except ImportError:
                use_excel = False
            
            if use_excel:
                # Export to Excel (.xlsx)
                default_filename = f"ap_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                filepath = filedialog.asksaveasfilename(
                    parent=self.dialog,
                    title="Export to Excel",
                    defaultextension=".xlsx",
                    filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                    initialfile=default_filename
                )
                
                if not filepath:
                    return
                
                # Create workbook and worksheet
                wb = Workbook()
                ws = wb.active
                ws.title = "AP Status"
                
                # Write header with styling
                headers = ["Store ID", "AP ID", "IP Address", "Enabled/Disabled", "Status", "Message"]
                ws.append(headers)
                
                # Style header row
                header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                header_font = Font(bold=True, color="FFFFFF")
                for cell in ws[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                
                # Write data rows
                for item in self.tree.get_children():
                    values = self.tree.item(item, "values")
                    
                    store_id = values[0] if len(values) > 0 else ""
                    ap_id = values[1] if len(values) > 1 else ""
                    ip_address = values[2] if len(values) > 2 else ""
                    result = values[3] if len(values) > 3 else ""
                    status = values[4] if len(values) > 4 else ""
                    full_msg = self.full_messages.get(item, values[5] if len(values) > 5 else "")
                    
                    ws.append([store_id, ap_id, ip_address, result, status, full_msg])
                
                # Auto-adjust column widths
                ws.column_dimensions['A'].width = 20  # Store ID
                ws.column_dimensions['B'].width = 15  # AP ID
                ws.column_dimensions['C'].width = 18  # IP Address
                ws.column_dimensions['D'].width = 12  # Enabled/Disabled
                ws.column_dimensions['E'].width = 15  # Status
                ws.column_dimensions['F'].width = 60  # Message
                
                # Save workbook
                wb.save(filepath)
                messagebox.showinfo("Export Successful", f"Data exported to:\n{filepath}", parent=self.dialog)
                
            else:
                # Fallback to CSV if openpyxl not available
                import csv
                default_filename = f"ap_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                filepath = filedialog.asksaveasfilename(
                    parent=self.dialog,
                    title="Export to CSV",
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                    initialfile=default_filename
                )
                
                if not filepath:
                    return
                
                with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                    writer.writerow(["Store ID", "AP ID", "IP Address", "Enabled/Disabled", "Status", "Message"])
                    
                    for item in self.tree.get_children():
                        values = self.tree.item(item, "values")
                        store_id = values[0] if len(values) > 0 else ""
                        ap_id = values[1] if len(values) > 1 else ""
                        ip_address = values[2] if len(values) > 2 else ""
                        result = values[3] if len(values) > 3 else ""
                        status = values[4] if len(values) > 4 else ""
                        full_msg = self.full_messages.get(item, values[5] if len(values) > 5 else "")
                        clean_msg = full_msg.replace('\n', ' ').replace('\r', ' ').strip()
                        clean_msg = ' '.join(clean_msg.split())
                        writer.writerow([store_id, ap_id, ip_address, result, status, clean_msg])
                
                messagebox.showinfo("Export Successful", f"Data exported to:\n{filepath}\n\nNote: Install 'openpyxl' for native Excel format export.", parent=self.dialog)
            
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Export Failed", f"Failed to export data:\n{str(e)}", parent=self.dialog)
    
    def _on_close(self):
        """Hide the dialog (don't destroy it so we can show it again)."""
        self.dialog.withdraw()
    
    def show_window(self):
        """Show the dialog window."""
        self.dialog.deiconify()
        self.dialog.lift()
    
    def _on_mouse_motion(self, event):
        """Show tooltip on mouse hover."""
        item = self.tree.identify_row(event.y)
        if item and item in self.full_messages:
            # Get the full message
            full_message = self.full_messages[item]
            
            # Only show tooltip if message is truncated
            if len(full_message) > 50:
                # Destroy existing tooltip
                self._destroy_tooltip()
                
                # Create new tooltip
                x = event.x_root + 10
                y = event.y_root + 10
                
                self.tooltip = tk.Toplevel(self.dialog)
                self.tooltip.wm_overrideredirect(True)
                self.tooltip.wm_geometry(f"+{x}+{y}")
                # Keep tooltip above everything
                self.tooltip.attributes('-topmost', True)
                
                label = tk.Label(
                    self.tooltip,
                    text=full_message,
                    background="#FFFFE0",
                    relief="solid",
                    borderwidth=1,
                    font=("Arial", 9),
                    padx=5,
                    pady=3,
                    wraplength=400
                )
                label.pack()
        else:
            self._destroy_tooltip()
    
    def _on_mouse_leave(self, event):
        """Hide tooltip when mouse leaves."""
        self._destroy_tooltip()
    
    def _destroy_tooltip(self):
        """Destroy the tooltip if it exists."""
        if self.tooltip:
            try:
                self.tooltip.destroy()
            except:
                pass
            self.tooltip = None
    
    def destroy(self):
        """Destroy the dialog."""
        try:
            self._destroy_tooltip()
            self.dialog.destroy()
        except:
            pass
