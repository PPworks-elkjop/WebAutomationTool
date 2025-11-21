"""
Certificate Trust Dialog - UI for certificate verification and trust decisions
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from certificate_manager import CertificateManager


class CertificateTrustDialog:
    """Dialog for reviewing and trusting SSL certificates."""
    
    def __init__(self, parent, hostname: str, port: int, cert_info: dict, 
                 status: str, on_trust: Optional[Callable] = None):
        """
        Initialize certificate trust dialog.
        
        Args:
            parent: Parent window
            hostname: Server hostname
            port: Server port
            cert_info: Certificate information dictionary
            status: Certificate status ('new', 'changed', 'error')
            on_trust: Callback function to call when user trusts the certificate
        """
        self.hostname = hostname
        self.port = port
        self.cert_info = cert_info
        self.status = status
        self.on_trust = on_trust
        self.user_decision = False
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Certificate Verification - {hostname}")
        self.dialog.geometry("700x600")
        self.dialog.transient(parent)
        
        # Make dialog modal
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        self._create_ui()
        
        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Set grab after everything is set up and centered
        try:
            self.dialog.grab_set()
        except tk.TclError:
            # If grab fails, continue anyway - dialog will still be functional
            pass
    
    def _create_ui(self):
        """Create the dialog UI."""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Warning header
        if self.status == 'new':
            warning_text = "🔐 New Certificate Detected"
            warning_msg = (
                f"This is the first time connecting to {self.hostname}.\n"
                "Please verify the certificate details below before trusting."
            )
            bg_color = "#FFF4E6"  # Light orange
        elif self.status == 'changed':
            warning_text = "⚠️ CERTIFICATE CHANGED!"
            warning_msg = (
                f"The certificate for {self.hostname} has CHANGED!\n"
                "This could indicate a Man-in-the-Middle attack.\n"
                "Only proceed if you know the certificate was legitimately updated."
            )
            bg_color = "#FFE6E6"  # Light red
        else:
            warning_text = "❌ Certificate Error"
            warning_msg = f"Unable to retrieve certificate information for {self.hostname}"
            bg_color = "#FFE6E6"
        
        # Warning frame
        warning_frame = tk.Frame(main_frame, bg=bg_color, relief=tk.RIDGE, borderwidth=2)
        warning_frame.pack(fill=tk.X, pady=(0, 15))
        
        warning_label = tk.Label(
            warning_frame,
            text=warning_text,
            font=('Segoe UI', 12, 'bold'),
            bg=bg_color,
            fg="#000000"
        )
        warning_label.pack(pady=(10, 5))
        
        warning_detail = tk.Label(
            warning_frame,
            text=warning_msg,
            font=('Segoe UI', 9),
            bg=bg_color,
            fg="#000000",
            justify=tk.LEFT
        )
        warning_detail.pack(pady=(0, 10), padx=10)
        
        # Certificate details
        details_frame = ttk.LabelFrame(main_frame, text="Certificate Details", padding=15)
        details_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Create scrollable text for certificate info
        details_text = tk.Text(
            details_frame,
            height=20,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg="#F5F5F5"
        )
        details_text.pack(fill=tk.BOTH, expand=True)
        
        # Populate certificate details
        if self.cert_info:
            cert_mgr = CertificateManager()
            
            details = []
            details.append(f"Server: {self.hostname}:{self.port}\n")
            details.append("-" * 70 + "\n\n")
            
            # Subject
            subject = self.cert_info.get('subject', {})
            details.append("SUBJECT:\n")
            details.append(f"  Common Name (CN):  {subject.get('commonName', 'N/A')}\n")
            details.append(f"  Organization (O):   {subject.get('organizationName', 'N/A')}\n")
            details.append(f"  Country (C):        {subject.get('countryName', 'N/A')}\n\n")
            
            # Issuer
            issuer = self.cert_info.get('issuer', {})
            details.append("ISSUER:\n")
            details.append(f"  Common Name (CN):  {issuer.get('commonName', 'N/A')}\n")
            details.append(f"  Organization (O):   {issuer.get('organizationName', 'N/A')}\n")
            details.append(f"  Country (C):        {issuer.get('countryName', 'N/A')}\n\n")
            
            # Validity
            details.append("VALIDITY:\n")
            details.append(f"  Not Before: {self.cert_info.get('notBefore', 'N/A')}\n")
            details.append(f"  Not After:  {self.cert_info.get('notAfter', 'N/A')}\n\n")
            
            # Fingerprint
            fingerprint = cert_mgr.format_fingerprint(self.cert_info.get('fingerprint', ''))
            details.append("FINGERPRINT (SHA-256):\n")
            details.append(f"  {fingerprint}\n\n")
            
            # Subject Alternative Names
            san = self.cert_info.get('subjectAltName', [])
            if san:
                details.append("SUBJECT ALTERNATIVE NAMES:\n")
                for item in san:
                    details.append(f"  {item[0]}: {item[1]}\n")
                details.append("\n")
            
            # Serial number
            details.append(f"Serial Number: {self.cert_info.get('serialNumber', 'N/A')}\n")
            details.append(f"Version: {self.cert_info.get('version', 'N/A')}\n")
            
            details_text.insert('1.0', ''.join(details))
        else:
            details_text.insert('1.0', "Unable to retrieve certificate information.")
        
        details_text.config(state=tk.DISABLED)
        
        # Warning checkbox
        if self.status in ['new', 'changed']:
            checkbox_frame = tk.Frame(main_frame)
            checkbox_frame.pack(fill=tk.X, pady=(0, 15))
            
            self.confirm_var = tk.BooleanVar(master=self.dialog, value=False)
            
            if self.status == 'new':
                checkbox_text = "I have verified the certificate details and trust this certificate"
            else:
                checkbox_text = "I understand the risks and want to trust this new certificate"
            
            confirm_check = tk.Checkbutton(
                checkbox_frame,
                text=checkbox_text,
                variable=self.confirm_var,
                font=('Segoe UI', 9),
                anchor=tk.W,
                onvalue=True,
                offvalue=False
            )
            confirm_check.pack(anchor=tk.W, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        if self.status in ['new', 'changed']:
            trust_btn = ttk.Button(
                button_frame,
                text="Trust Certificate",
                command=self._on_trust,
                style='Accent.TButton'
            )
            trust_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        cancel_btn = ttk.Button(
            button_frame,
            text="Cancel" if self.status in ['new', 'changed'] else "Close",
            command=self._on_cancel
        )
        cancel_btn.pack(side=tk.RIGHT)
        
        # Copy fingerprint button
        copy_btn = ttk.Button(
            button_frame,
            text="Copy Fingerprint",
            command=self._copy_fingerprint
        )
        copy_btn.pack(side=tk.LEFT)
    
    def _copy_fingerprint(self):
        """Copy certificate fingerprint to clipboard."""
        if self.cert_info:
            fingerprint = self.cert_info.get('fingerprint', '')
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(fingerprint)
            messagebox.showinfo("Copied", "Fingerprint copied to clipboard", parent=self.dialog)
    
    def _on_trust(self):
        """Handle trust button click."""
        # Check if confirm_var exists (it should for 'new' and 'changed' status)
        if hasattr(self, 'confirm_var'):
            checkbox_value = self.confirm_var.get()
            if not checkbox_value:
                messagebox.showwarning(
                    "Confirmation Required",
                    "Please check the confirmation box to proceed.",
                    parent=self.dialog
                )
                return
        
        self.user_decision = True
        
        if self.on_trust:
            self.on_trust()
        
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.user_decision = False
        self.dialog.destroy()
    
    def show(self) -> bool:
        """
        Show the dialog and wait for user decision.
        
        Returns:
            bool: True if user trusted the certificate
        """
        self.dialog.wait_window()
        return self.user_decision


def show_certificate_trust_dialog(parent, hostname: str, port: int = 443, 
                                  cert_manager: Optional[CertificateManager] = None) -> bool:
    """
    Show certificate trust dialog for a server.
    
    Args:
        parent: Parent window
        hostname: Server hostname
        port: Server port
        cert_manager: CertificateManager instance (creates new if None)
        
    Returns:
        bool: True if certificate was trusted
    """
    if cert_manager is None:
        cert_manager = CertificateManager()
    
    # Verify certificate
    trusted, status, cert_info = cert_manager.verify_certificate(hostname, port)
    
    if status == 'error':
        messagebox.showerror(
            "Certificate Error",
            f"Unable to retrieve certificate from {hostname}:{port}",
            parent=parent
        )
        return False
    
    if status == 'trusted':
        messagebox.showinfo(
            "Certificate Trusted",
            f"Certificate for {hostname} is already trusted.",
            parent=parent
        )
        return True
    
    # Show trust dialog
    def on_trust():
        cert_manager.trust_certificate(hostname, port, cert_info)
    
    dialog = CertificateTrustDialog(parent, hostname, port, cert_info, status, on_trust)
    return dialog.show()


if __name__ == '__main__':
    # Test the dialog
    root = tk.Tk()
    root.geometry("400x300")
    root.title("Certificate Trust Dialog Test")
    
    def test_dialog():
        # Test with google.com
        result = show_certificate_trust_dialog(root, "www.google.com", 443)
        print(f"User decision: {result}")
    
    btn = ttk.Button(root, text="Test Certificate Dialog", command=test_dialog)
    btn.pack(pady=50)
    
    root.mainloop()
