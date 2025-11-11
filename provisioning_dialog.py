"""Dialog for provisioning management."""

import tkinter as tk
from tkinter import ttk


class ProvisioningDialog:
    """Dialog for selecting provisioning management action."""
    
    def __init__(self, parent):
        self.result = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Provisioning Management")
        self.dialog.geometry("400x320")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        bg_color = "#F5F5F5"
        frame_bg = "#FFFFFF"
        accent_color = "#28A745"
        cancel_color = "#6C757D"
        
        self.dialog.configure(bg=bg_color)
        
        style.configure("Prov.TFrame", background=frame_bg)
        style.configure("Prov.TLabel", background=frame_bg, foreground="#333333", font=("Segoe UI", 10))
        style.configure("Prov.Title.TLabel", background=frame_bg, foreground="#333333", font=("Segoe UI", 12, "bold"))
        style.configure("Prov.Desc.TLabel", background=frame_bg, foreground="#666666", font=("Segoe UI", 9))
        style.configure("Prov.TRadiobutton", background=frame_bg, foreground="#333333", font=("Segoe UI", 10))
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (320 // 2)
        self.dialog.geometry(f"400x320+{x}+{y}")
        
        # Main frame with padding
        main_frame = ttk.Frame(self.dialog, padding="20", style="Prov.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title label
        title_label = ttk.Label(
            main_frame,
            text="Select Provisioning Action",
            style="Prov.Title.TLabel"
        )
        title_label.pack(pady=(0, 15))
        
        # Radio button variable
        self.action_var = tk.StringVar(value="report")
        
        # Radio buttons frame
        radio_frame = ttk.Frame(main_frame, style="Prov.TFrame")
        radio_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Option 1: Report only
        rb1 = ttk.Radiobutton(
            radio_frame,
            text="Report Status Only",
            variable=self.action_var,
            value="report",
            style="Prov.TRadiobutton"
        )
        rb1.pack(anchor=tk.W, pady=5)
        
        desc1 = ttk.Label(
            radio_frame,
            text="   → Check and display current provisioning status",
            style="Prov.Desc.TLabel"
        )
        desc1.pack(anchor=tk.W, padx=(20, 0))
        
        # Option 2: Enable
        rb2 = ttk.Radiobutton(
            radio_frame,
            text="Enable Provisioning",
            variable=self.action_var,
            value="enable",
            style="Prov.TRadiobutton"
        )
        rb2.pack(anchor=tk.W, pady=(15, 5))
        
        desc2 = ttk.Label(
            radio_frame,
            text="   → Enable provisioning if currently disabled",
            style="Prov.Desc.TLabel"
        )
        desc2.pack(anchor=tk.W, padx=(20, 0))
        
        # Option 3: Disable
        rb3 = ttk.Radiobutton(
            radio_frame,
            text="Disable Provisioning",
            variable=self.action_var,
            value="disable",
            style="Prov.TRadiobutton"
        )
        rb3.pack(anchor=tk.W, pady=(15, 5))
        
        desc3 = ttk.Label(
            radio_frame,
            text="   → Disable provisioning if currently enabled",
            style="Prov.Desc.TLabel"
        )
        desc3.pack(anchor=tk.W, padx=(20, 0))
        
        # Button frame
        button_frame = ttk.Frame(main_frame, style="Prov.TFrame")
        button_frame.pack(fill=tk.X)
        
        # OK button
        ok_button = tk.Button(
            button_frame,
            text="OK",
            command=self._on_ok,
            width=12,
            bg="#28A745",
            fg="white",
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            cursor="hand2",
            activebackground="#218838",
            activeforeground="white"
        )
        ok_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Cancel button
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=12,
            bg="#6C757D",
            fg="white",
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            cursor="hand2",
            activebackground="#5A6268",
            activeforeground="white"
        )
        cancel_button.pack(side=tk.RIGHT)
        
        # Bind Enter key to OK
        self.dialog.bind("<Return>", lambda e: self._on_ok())
        self.dialog.bind("<Escape>", lambda e: self._on_cancel())
        
        # Focus on dialog
        self.dialog.focus_set()
    
    def _on_ok(self):
        """Handle OK button click."""
        self.result = self.action_var.get()
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Handle Cancel button click."""
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and wait for result."""
        self.dialog.wait_window()
        return self.result
