"""
SSH Helper - Tab-based SSH Terminal Manager
Handles multiple concurrent SSH connections with independent terminal tabs.
Similar architecture to browser_helper for consistency.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import paramiko
import threading
import time
from typing import Dict, Optional, Callable
import re


class SSHConnection:
    """Represents a single SSH connection to an access point."""
    
    # ANSI escape code pattern
    ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    
    def __init__(self, ap_id: str, host: str, username: str, password: str, port: int = 22):
        self.ap_id = ap_id
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        
        self.client: Optional[paramiko.SSHClient] = None
        self.shell: Optional[paramiko.Channel] = None
        self.connected = False
        self.output_buffer = ""
        self.automation_buffer = ""  # Separate buffer for automation that doesn't get cleared
        self.read_thread: Optional[threading.Thread] = None
        self.stop_reading = False
    
    @staticmethod
    def strip_ansi_codes(text: str) -> str:
        """Remove ANSI escape codes from text."""
        return SSHConnection.ANSI_ESCAPE.sub('', text)
        
    def connect(self) -> tuple[bool, str]:
        """
        Establish SSH connection.
        Returns: (success: bool, message: str)
        """
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect with timeout
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10,
                look_for_keys=False,
                allow_agent=False
            )
            
            # Get interactive shell
            self.shell = self.client.invoke_shell(width=120, height=40)
            self.shell.settimeout(0.1)  # Non-blocking reads
            
            self.connected = True
            
            # Start reading output in background
            self.stop_reading = False
            self.read_thread = threading.Thread(target=self._read_output, daemon=True)
            self.read_thread.start()
            
            # Start service mode detection
            threading.Thread(target=self._check_service_mode, daemon=True).start()
            
            return True, f"Connected to {self.host}"
            
        except paramiko.AuthenticationException:
            return False, "Authentication failed - check username/password"
        except paramiko.SSHException as e:
            return False, f"SSH connection failed: {str(e)}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    def _read_output(self):
        """Background thread to continuously read shell output."""
        while not self.stop_reading and self.shell and self.connected:
            try:
                if self.shell.recv_ready():
                    data = self.shell.recv(4096).decode('utf-8', errors='replace')
                    # Strip ANSI color codes
                    data = self.strip_ansi_codes(data)
                    self.output_buffer += data
                    self.automation_buffer += data  # Also add to automation buffer
                    # Keep automation buffer reasonable size (last 5000 chars)
                    if len(self.automation_buffer) > 5000:
                        self.automation_buffer = self.automation_buffer[-5000:]
            except:
                time.sleep(0.05)
            time.sleep(0.01)
    
    def _check_service_mode(self):
        """Check if we're in service mode after connection and auto-run status."""
        import re
        
        # Wait for initial connection output
        time.sleep(4)
        
        # Check automation buffer for service mode prompt
        output = self.get_automation_output(last_chars=1000)
        
        if 'servicemode>' in output.lower() or 'service mode' in output.lower():
            print(f"[SSH] Service mode detected for {self.host}, running status command...")
            
            # Send status command
            self.send_command("status")
            time.sleep(3)
            
            # Get status output
            status_output = self.get_automation_output(last_chars=2000)
            print(f"[SSH] Status output length: {len(status_output)} chars")
            print(f"[SSH] Status output preview: {status_output[:500]}")
            
            # Parse Java Version
            java_match = re.search(r'Java Version[:\s]+([^\n\r]+)', status_output, re.IGNORECASE)
            if java_match:
                java_version = java_match.group(1).strip()
                print(f"[SSH] Found Java Version: {java_version}")
                
                # Try to save to database if we can access it
                try:
                    from database_manager import DatabaseManager
                    db = DatabaseManager()
                    db.update_access_point(self.ap_id, {'java_version': java_version})
                    print(f"[SSH] Java Version saved to database for AP {self.ap_id}")
                except Exception as e:
                    print(f"[SSH] Could not save Java Version: {str(e)}")
            else:
                print(f"[SSH] Java Version not found in status output")
    
    def send_command(self, command: str):
        """Send command to the shell."""
        if not self.connected or not self.shell:
            return
        
        try:
            # Send command with newline
            self.shell.send(command + '\n')
        except Exception as e:
            print(f"Error sending command: {e}")
            self.connected = False
    
    def get_output(self) -> str:
        """Get and clear the output buffer."""
        output = self.output_buffer
        self.output_buffer = ""
        return output
    
    def peek_output(self, last_chars: int = 500) -> str:
        """Peek at recent output without clearing the buffer."""
        return self.output_buffer[-last_chars:] if len(self.output_buffer) > last_chars else self.output_buffer
    
    def get_automation_output(self, last_chars: int = 1000) -> str:
        """Get recent output from automation buffer (not cleared by terminal display)."""
        return self.automation_buffer[-last_chars:] if len(self.automation_buffer) > last_chars else self.automation_buffer
    
    def disconnect(self, preserve_buffers: bool = False):
        """Close the SSH connection.
        
        Args:
            preserve_buffers: If True, keeps output buffers for reconnection
        """
        self.connected = False
        self.stop_reading = True
        
        if self.shell:
            try:
                self.shell.close()
            except:
                pass
            self.shell = None
        
        if self.client:
            try:
                self.client.close()
            except:
                pass
            self.client = None
        
        # Clear buffers unless preserving for reconnect
        if not preserve_buffers:
            self.output_buffer = ""
            self.automation_buffer = ""


class SSHTerminalTab:
    """A single terminal tab in the SSH window."""
    
    def __init__(self, parent: ttk.Frame, connection: SSHConnection, on_close: Callable):
        self.parent = parent
        self.connection = connection
        self.on_close_callback = on_close
        self.is_reconnecting = False  # Flag to prevent [Connection closed] during reconnect
        
        self._build_ui()
        self._start_output_updater()
        
    def _build_ui(self):
        """Build the terminal UI."""
        # Terminal output area (scrollable text widget with dark theme)
        output_frame = tk.Frame(self.parent, bg="#1E1E1E")
        output_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(output_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Terminal text widget with dark terminal theme
        self.terminal_text = tk.Text(
            output_frame,
            wrap="word",
            font=("Consolas", 10),
            bg="#1E1E1E",
            fg="#D4D4D4",
            insertbackground="#D4D4D4",
            selectbackground="#264F78",
            relief="flat",
            yscrollcommand=scrollbar.set
        )
        self.terminal_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.terminal_text.yview)
        
        # Command input area
        input_frame = tk.Frame(self.parent, bg="#2D2D30")
        input_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        tk.Label(input_frame, text="$", font=("Consolas", 10, "bold"),
                bg="#2D2D30", fg="#4EC9B0").pack(side="left", padx=(5, 5))
        
        self.command_entry = tk.Entry(
            input_frame,
            font=("Consolas", 10),
            bg="#3C3C3C",
            fg="#D4D4D4",
            insertbackground="#D4D4D4",
            relief="flat",
            bd=0
        )
        self.command_entry.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 5))
        self.command_entry.bind("<Return>", self._on_command_enter)
        self.command_entry.focus()
        
        # Send button
        send_btn = tk.Button(
            input_frame,
            text="Send",
            command=self._send_command,
            bg="#0E639C",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5
        )
        send_btn.pack(side="left", padx=(0, 5))
        
        # Clear button
        clear_btn = tk.Button(
            input_frame,
            text="Clear",
            command=self._clear_terminal,
            bg="#6C757D",
            fg="white",
            font=("Segoe UI", 9),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5
        )
        clear_btn.pack(side="left")
        
    def _on_command_enter(self, event=None):
        """Handle Enter key press in command entry."""
        self._send_command()
        return "break"  # Prevent default behavior
    
    def _send_command(self):
        """Send command from entry to SSH connection."""
        command = self.command_entry.get().strip()
        if not command:
            return
        
        # Display command in terminal (echo)
        self.terminal_text.insert("end", f"$ {command}\n", "command")
        self.terminal_text.tag_config("command", foreground="#4EC9B0", font=("Consolas", 10, "bold"))
        self.terminal_text.see("end")
        
        # Send to SSH
        self.connection.send_command(command)
        
        # Clear entry
        self.command_entry.delete(0, "end")
    
    def _clear_terminal(self):
        """Clear the terminal output."""
        self.terminal_text.delete("1.0", "end")
    
    def _start_output_updater(self):
        """Start periodic update of terminal output from SSH connection."""
        self._update_output()
    
    def _update_output(self):
        """Update terminal with new output from SSH connection."""
        if not self.connection.connected:
            # Connection lost - but don't show message if reconnecting
            if not self.is_reconnecting:
                self.terminal_text.insert("end", "\n[Connection closed]\n", "error")
                self.terminal_text.tag_config("error", foreground="#F48771")
                self.terminal_text.see("end")
                return
            # If reconnecting, just wait and check again
            self.parent.after(100, self._update_output)
            return
        
        # Get new output
        output = self.connection.get_output()
        if output:
            self.terminal_text.insert("end", output)
            self.terminal_text.see("end")
        
        # Schedule next update (100ms)
        self.parent.after(100, self._update_output)
    
    def destroy(self):
        """Cleanup when tab is closed."""
        self.connection.disconnect()


class SSHWindow:
    """
    SSH Terminal Window with tab support for multiple connections.
    Can be used standalone or embedded in other windows.
    """
    
    def __init__(self, parent, title: str = "SSH Terminal"):
        self.parent = parent
        self.title = title
        self.tabs: Dict[str, SSHTerminalTab] = {}  # ap_id -> tab
        
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("900x650")
        self.window.configure(bg="#2D2D30")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.window.winfo_screenheight() // 2) - (650 // 2)
        self.window.geometry(f"900x650+{x}+{y}")
        
        self._build_ui()
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _build_ui(self):
        """Build the main SSH window UI."""
        # Header
        header = tk.Frame(self.window, bg="#2D2D30")
        header.pack(fill="x", padx=10, pady=(10, 5))
        
        tk.Label(header, text="SSH Terminal Manager", font=("Segoe UI", 14, "bold"),
                bg="#2D2D30", fg="#D4D4D4").pack(side="left")
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        
        # Style for tabs
        style = ttk.Style()
        style.configure("SSH.TNotebook", background="#2D2D30")
        style.configure("SSH.TNotebook.Tab", padding=[15, 8])
        
        self.notebook.configure(style="SSH.TNotebook")
    
    def add_connection(self, ap_id: str, host: str, username: str, password: str, port: int = 22) -> tuple[bool, str]:
        """
        Add a new SSH connection as a tab.
        Returns: (success: bool, message: str)
        """
        # Check if already connected
        if ap_id in self.tabs:
            # Switch to existing tab
            for i, tab_id in enumerate(self.notebook.tabs()):
                if self.notebook.tab(tab_id, "text") == ap_id:
                    self.notebook.select(i)
                    return True, f"Already connected to {ap_id}"
        
        # Create connection
        connection = SSHConnection(ap_id, host, username, password, port)
        success, message = connection.connect()
        
        if not success:
            return False, message
        
        # Create tab
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text=ap_id)
        
        # Create terminal tab
        terminal_tab = SSHTerminalTab(tab_frame, connection, lambda: self._close_tab(ap_id))
        self.tabs[ap_id] = terminal_tab
        
        # Switch to new tab
        self.notebook.select(tab_frame)
        
        return True, message
    
    def _close_tab(self, ap_id: str):
        """Close a specific tab."""
        if ap_id not in self.tabs:
            return
        
        # Find tab index
        for i, tab_id in enumerate(self.notebook.tabs()):
            if self.notebook.tab(tab_id, "text") == ap_id:
                # Disconnect and cleanup
                tab = self.tabs[ap_id]
                tab.destroy()
                
                # Remove tab
                self.notebook.forget(i)
                del self.tabs[ap_id]
                
                # Close window if no tabs left
                if len(self.tabs) == 0:
                    self.window.destroy()
                
                break
    
    def _on_close(self):
        """Handle window close - disconnect all tabs."""
        for ap_id in list(self.tabs.keys()):
            self._close_tab(ap_id)
        
        self.window.destroy()
    
    def show(self):
        """Show the window."""
        self.window.deiconify()
        self.window.lift()
        self.window.focus()


class SSHManager:
    """
    Manager for SSH windows and connections.
    Handles multiple SSH windows, each potentially with multiple tabs.
    """
    
    _windows: Dict[str, SSHWindow] = {}  # window_id -> SSHWindow
    
    @classmethod
    def open_ssh_connection(cls, parent, ap_id: str, host: str, username: str, password: str, 
                           port: int = 22, window_id: str = "default") -> tuple[bool, str]:
        """
        Open an SSH connection in a window.
        If window doesn't exist, creates it. Otherwise adds tab to existing window.
        
        Args:
            parent: Parent widget
            ap_id: Access point identifier
            host: SSH host address
            username: SSH username
            password: SSH password
            port: SSH port (default 22)
            window_id: Identifier for the SSH window (allows multiple windows)
        
        Returns:
            (success: bool, message: str)
        """
        # Get or create window
        if window_id not in cls._windows or not hasattr(cls._windows[window_id].window, 'winfo_exists') or not cls._windows[window_id].window.winfo_exists():
            window = SSHWindow(parent, title=f"SSH Terminal - {ap_id}")
            cls._windows[window_id] = window
        else:
            window = cls._windows[window_id]
            window.show()
        
        # Add connection to window
        return window.add_connection(ap_id, host, username, password, port)
    
    @classmethod
    def close_window(cls, window_id: str = "default"):
        """Close a specific SSH window."""
        if window_id in cls._windows:
            window = cls._windows[window_id]
            window._on_close()
            del cls._windows[window_id]
    
    @classmethod
    def close_all(cls):
        """Close all SSH windows."""
        for window_id in list(cls._windows.keys()):
            cls.close_window(window_id)


# Convenience function for simple use
def open_ssh_terminal(parent, ap_id: str, host: str, username: str, password: str, port: int = 22) -> tuple[bool, str]:
    """
    Convenience function to open an SSH terminal.
    Uses default window which allows multiple AP connections in tabs.
    """
    return SSHManager.open_ssh_connection(parent, ap_id, host, username, password, port)


if __name__ == "__main__":
    # Test the SSH terminal
    root = tk.Tk()
    root.withdraw()
    
    # Example usage
    success, message = open_ssh_terminal(
        root, 
        ap_id="TEST-AP-001",
        host="192.168.1.1",  # Replace with actual SSH host
        username="admin",
        password="password"
    )
    
    if success:
        print(f"Connected: {message}")
    else:
        messagebox.showerror("Connection Failed", message)
        root.destroy()
    
    root.mainloop()
