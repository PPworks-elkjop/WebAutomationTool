"""
Batch SSH Operations Tool - Execute SSH commands on multiple APs
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Dict
import paramiko
import socket
import time
import concurrent.futures
from batch_operations_base import BatchOperationWindow
from database_manager import DatabaseManager


class BatchSSHWindow(BatchOperationWindow):
    """Window for batch SSH operations on multiple APs."""
    
    def __init__(self, parent, current_user, db_manager: DatabaseManager):
        """Initialize batch SSH operations window."""
        self.ssh_command = ""
        self.ssh_timeout = 30
        self.max_parallel = 10
        
        super().__init__(parent, "Batch SSH Operations", current_user, db_manager)
    
    def _create_operation_controls(self):
        """Create SSH operation-specific controls."""
        # Predefined commands
        preset_frame = ttk.LabelFrame(self.operation_frame, text="Quick Commands", padding=10)
        preset_frame.pack(fill=tk.X, pady=(0, 10))
        
        quick_commands = [
            ("Show Uptime", "uptime"),
            ("Show IP Configuration", "ifconfig"),
            ("Show Running Processes", "ps aux"),
            ("Show Disk Usage", "df -h"),
            ("Show Memory Info", "free -m"),
            ("Check SSH Service", "systemctl status ssh"),
            ("Restart Network", "systemctl restart networking"),
        ]
        
        preset_buttons = ttk.Frame(preset_frame)
        preset_buttons.pack(fill=tk.X)
        
        for idx, (label, cmd) in enumerate(quick_commands):
            btn = ttk.Button(
                preset_buttons,
                text=label,
                command=lambda c=cmd: self._insert_command(c),
                width=20
            )
            btn.grid(row=idx // 3, column=idx % 3, padx=5, pady=5, sticky=tk.W)
        
        # Custom command
        command_frame = ttk.LabelFrame(self.operation_frame, text="SSH Command", padding=10)
        command_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        ttk.Label(command_frame, text="Command to execute:").pack(anchor=tk.W, pady=(0, 5))
        
        # Command entry with scrollbar
        cmd_container = ttk.Frame(command_frame)
        cmd_container.pack(fill=tk.BOTH, expand=True)
        
        self.command_text = scrolledtext.ScrolledText(
            cmd_container,
            height=5,
            width=80,
            wrap=tk.WORD,
            font=('Consolas', 10)
        )
        self.command_text.pack(fill=tk.BOTH, expand=True)
        
        # Help text
        help_label = ttk.Label(
            command_frame,
            text="⚠ Commands will be executed with current user privileges. "
                 "Be careful with destructive commands!",
            foreground="orange",
            wraplength=1000,
            font=('Segoe UI', 9)
        )
        help_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Settings
        settings_frame = ttk.Frame(self.operation_frame)
        settings_frame.pack(fill=tk.X)
        
        ttk.Label(settings_frame, text="Timeout (seconds):").pack(side=tk.LEFT, padx=(0, 10))
        
        self.timeout_var = tk.IntVar(value=30)
        timeout_spin = ttk.Spinbox(settings_frame, from_=10, to=300, width=10,
                                   textvariable=self.timeout_var)
        timeout_spin.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(settings_frame, text="Max Parallel:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.parallel_var = tk.IntVar(value=10)
        parallel_spin = ttk.Spinbox(settings_frame, from_=1, to=20, width=10,
                                    textvariable=self.parallel_var)
        parallel_spin.pack(side=tk.LEFT)
    
    def _insert_command(self, command: str):
        """Insert a predefined command into the text box."""
        self.command_text.delete('1.0', tk.END)
        self.command_text.insert('1.0', command)
    
    def _get_operation_description(self) -> str:
        """Get operation description for confirmation dialog."""
        command = self.command_text.get('1.0', tk.END).strip()
        
        if not command:
            return "No command specified"
        
        return f"Execute SSH command on all marked APs:\n\n{command}\n\n" \
               f"Timeout: {self.timeout_var.get()}s, Max Parallel: {self.parallel_var.get()}"
    
    def _confirm_and_execute(self):
        """Override to validate command before execution."""
        command = self.command_text.get('1.0', tk.END).strip()
        
        if not command:
            messagebox.showwarning("No Command", 
                                 "Please enter a command to execute",
                                 parent=self.window)
            return
        
        # Check for dangerous commands
        dangerous_keywords = ['rm -rf', 'dd if=', 'mkfs', 'format', '> /dev/', 'shutdown', 'halt']
        if any(keyword in command.lower() for keyword in dangerous_keywords):
            if not messagebox.askyesno(
                "Dangerous Command Detected",
                f"The command contains potentially dangerous keywords.\n\n"
                f"Command: {command}\n\n"
                f"Are you absolutely sure you want to execute this?",
                parent=self.window,
                icon='warning'
            ):
                return
        
        super()._confirm_and_execute()
    
    def _get_operation_params(self) -> dict:
        """Read tkinter variables in main thread."""
        return {
            'ssh_command': self.command_text.get('1.0', tk.END).strip(),
            'ssh_timeout': self.timeout_var.get(),
            'max_parallel': self.parallel_var.get()
        }
    
    def _run_operation(self, operation_params: dict = None):
        """Run batch SSH operation with parallel execution."""
        # Use parameters passed from main thread
        self.ssh_command = operation_params.get('ssh_command', '')
        self.ssh_timeout = operation_params.get('ssh_timeout', 30)
        self.max_parallel = operation_params.get('max_parallel', 10)
        
        total = len(self.selected_aps)
        completed = 0
        
        # Use ThreadPoolExecutor for parallel SSH connections
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
            # Submit all SSH tasks
            future_to_ap = {
                executor.submit(self._execute_ssh_command, ap): ap 
                for ap in self.selected_aps
            }
            
            # Process completed tasks as they finish
            for future in concurrent.futures.as_completed(future_to_ap):
                if not self.operation_running:
                    self.operation_queue.put(('log', 'Operation stopped by user', 'warning'))
                    break
                
                ap = future_to_ap[future]
                ap_id = ap['ap_id']
                
                try:
                    success, result = future.result()
                    
                    # Update status
                    status = 'Success' if success else 'Failed'
                    tag = 'success' if success else 'error'
                    
                    # Truncate long output for status column
                    display_result = result[:100] + '...' if len(result) > 100 else result
                    
                    self.operation_queue.put(('status', ap_id, status, display_result))
                    self.operation_queue.put(('log', f"{ap_id}: {result}", tag))
                    
                except Exception as e:
                    self.operation_queue.put(('status', ap_id, 'Failed', f'Error: {str(e)}'))
                    self.operation_queue.put(('log', f"{ap_id}: Error - {str(e)}", 'error'))
                
                # Update progress
                completed += 1
                progress = (completed / total) * 100
                self.operation_queue.put(('progress', progress, f"Processed {completed} of {total}"))
        
        # Operation complete
        self.operation_queue.put(('complete', None, None))
    
    def _execute_ssh_command(self, ap: Dict) -> tuple[bool, str]:
        """
        Execute SSH command on a single AP.
        
        Returns:
            tuple: (success, output/error_message)
        """
        ip = ap.get('ip_address', '')
        username = ap.get('ssh_username', ap.get('username', 'admin'))
        password = ap.get('ssh_password', ap.get('password', ''))
        port = ap.get('ssh_port', 22)
        
        if not ip:
            return False, "No IP address"
        
        if not password:
            return False, "No SSH password configured"
        
        ssh_client = None
        
        try:
            # Create SSH client
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect
            ssh_client.connect(
                hostname=ip,
                port=port,
                username=username,
                password=password,
                timeout=self.ssh_timeout,
                allow_agent=False,
                look_for_keys=False
            )
            
            # Execute command
            stdin, stdout, stderr = ssh_client.exec_command(
                self.ssh_command,
                timeout=self.ssh_timeout
            )
            
            # Get output
            output = stdout.read().decode('utf-8', errors='ignore').strip()
            error = stderr.read().decode('utf-8', errors='ignore').strip()
            
            # Get exit status
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                if output:
                    return True, output
                else:
                    return True, "Command executed successfully (no output)"
            else:
                return False, f"Exit code {exit_status}: {error if error else 'Command failed'}"
        
        except paramiko.AuthenticationException:
            return False, "Authentication failed"
        
        except paramiko.SSHException as e:
            return False, f"SSH error: {str(e)[:50]}"
        
        except socket.timeout:
            return False, "Connection timeout"
        
        except socket.error as e:
            return False, f"Network error: {str(e)[:50]}"
        
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
        
        finally:
            if ssh_client:
                try:
                    ssh_client.close()
                except:
                    pass


class SSHOutputViewerDialog:
    """Dialog to view detailed SSH output for a specific AP."""
    
    def __init__(self, parent, ap_id: str, command: str, output: str):
        """
        Initialize SSH output viewer.
        
        Args:
            parent: Parent window
            ap_id: AP identifier
            command: Command that was executed
            output: Command output
        """
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"SSH Output - {ap_id}")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400)
        y = (self.dialog.winfo_screenheight() // 2) - (300)
        self.dialog.geometry(f"800x600+{x}+{y}")
        
        # Header
        header_frame = ttk.Frame(self.dialog)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(header_frame, text=f"AP: {ap_id}", 
                 font=('Segoe UI', 12, 'bold')).pack(anchor=tk.W)
        ttk.Label(header_frame, text=f"Command: {command}", 
                 font=('Consolas', 10)).pack(anchor=tk.W, pady=(5, 0))
        
        # Output
        output_frame = ttk.LabelFrame(self.dialog, text="Output", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            font=('Consolas', 9)
        )
        output_text.pack(fill=tk.BOTH, expand=True)
        output_text.insert('1.0', output)
        output_text.config(state='disabled')
        
        # Close button
        ttk.Button(self.dialog, text="Close", 
                  command=self.dialog.destroy).pack(pady=(0, 10))


def main():
    """Test the batch SSH window."""
    root = tk.Tk()
    root.withdraw()
    
    from database_manager import DatabaseManager
    db = DatabaseManager()
    
    window = BatchSSHWindow(None, "test_user", db)
    window.window.mainloop()


if __name__ == '__main__':
    main()
