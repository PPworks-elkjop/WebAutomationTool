"""
Content Panel - Lower Right
Dynamic content area showing SSH terminal, browser status, Jira details, etc.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox


class ContentPanel:
    """Lower right panel - Dynamic content display."""
    
    def __init__(self, parent, db, current_user=None, log_callback=None, refresh_callback=None, ap_panel=None):
        self.parent = parent
        self.db = db
        self.current_user = current_user
        self.log_callback = log_callback
        self.refresh_callback = refresh_callback
        self.ap_panel = ap_panel  # Reference to AP panel for browser operations
        
        self.current_content_type = None
        self.current_data = None
        
        # Browser manager instance
        self.browser_manager = None
        self.browser_running = False
        self.browser_popout_window = None
        
        self._create_ui()
    
    def _create_ui(self):
        """Create content panel UI."""
        # Header
        self.header = tk.Frame(self.parent, bg="#6589B3", height=40)
        self.header.pack(fill=tk.X, side=tk.TOP)
        self.header.pack_propagate(False)
        
        self.header_label = tk.Label(self.header, text="Content View", font=('Segoe UI', 12, 'bold'),
                                     bg="#6589B3", fg="white")
        self.header_label.pack(side=tk.LEFT, padx=15, pady=8)
        
        self.popout_button = tk.Button(self.header, text="↗ Pop Out", command=self._popout,
                                       bg="#28A745", fg="white", font=('Segoe UI', 8),
                                       padx=10, pady=2, relief=tk.FLAT, cursor="hand2",
                                       activebackground="#218838")
        self.popout_button.pack(side=tk.RIGHT, padx=10)
        self.popout_button.pack_forget()  # Hidden by default
        
        # Import CustomNotebook
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from custom_notebook import CustomNotebook
        
        # Create tabbed interface
        self.notebook = CustomNotebook(self.parent, tab_font=('Segoe UI', 10), tab_height=32)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.ap_details_frame = tk.Frame(self.notebook.content_area, bg="#FFFFFF")
        self.notebook.add(self.ap_details_frame, text="AP Support Details")
        
        self.context_details_frame = tk.Frame(self.notebook.content_area, bg="#FFFFFF")
        self.notebook.add(self.context_details_frame, text="Context Details")
        
        # Show default placeholder in both
        self._show_placeholder_in_frame(self.ap_details_frame)
        self._show_placeholder_in_frame(self.context_details_frame)
    
    def _show_placeholder_in_frame(self, frame):
        """Show placeholder in a specific frame."""
        for widget in frame.winfo_children():
            widget.destroy()
        
        placeholder = tk.Frame(frame, bg="#FFFFFF")
        placeholder.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(placeholder, text="Select an item to view details",
                font=('Segoe UI', 14, 'bold'), bg="#FFFFFF", fg="#6C757D").pack(expand=True)
    
    def _clear_frame(self, frame):
        """Clear content from a specific frame, but preserve SSH terminal sessions."""
        for widget in frame.winfo_children():
            # Check if this widget is a preserved SSH terminal
            is_ssh_terminal = False
            if hasattr(self, 'current_ssh_sessions'):
                for ap_id, session in self.current_ssh_sessions.items():
                    if 'content_frame' in session and session['content_frame'] == widget:
                        # This is an active SSH terminal, just hide it instead of destroying
                        widget.pack_forget()
                        is_ssh_terminal = True
                        break
            
            if not is_ssh_terminal:
                widget.destroy()
    
    def show_ap_overview(self, ap_data):
        """Show all AP fields in a scrollable list in AP Support Details tab."""
        self._clear_frame(self.ap_details_frame)
        self.current_content_type = "ap_overview"
        self.current_data = ap_data
        
        self.header_label.config(text=f"AP {ap_data['ap_id']} - Details")
        self.popout_button.pack_forget()
        
        # Create scrollable canvas in AP details tab
        canvas = tk.Canvas(self.ap_details_frame, bg="#FFFFFF", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.ap_details_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#FFFFFF")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind mousewheel scrolling
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except:
                pass
        
        def _bind_mousewheel(event):
            canvas.bind("<MouseWheel>", _on_mousewheel)
        
        def _unbind_mousewheel(event):
            canvas.unbind("<MouseWheel>")
        
        canvas.bind("<Enter>", _bind_mousewheel)
        canvas.bind("<Leave>", _unbind_mousewheel)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Content inside scrollable frame
        content = tk.Frame(scrollable_frame, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Header with show passwords button
        header_frame = tk.Frame(content, bg="#FFFFFF")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(header_frame, text=f"All Fields - AP {ap_data['ap_id']}", font=('Segoe UI', 14, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(side=tk.LEFT)
        
        # Show/Hide passwords toggle
        self.show_passwords = tk.BooleanVar(value=False)
        self.password_widgets = []  # Store password labels for updating
        
        def toggle_passwords():
            show = self.show_passwords.get()
            toggle_btn.config(text="🔒 Hide Passwords" if show else "👁 Show Passwords",
                            bg="#DC3545" if show else "#28A745")
            # Update all password fields (Entry widgets)
            for pwd_entry, pwd_value in self.password_widgets:
                pwd_entry.config(state='normal')
                pwd_entry.delete(0, tk.END)
                if show:
                    display_value = pwd_value if pwd_value and pwd_value != 'N/A' else 'N/A'
                else:
                    display_value = '********' if pwd_value and pwd_value != 'N/A' else 'N/A'
                pwd_entry.insert(0, display_value)
                pwd_entry.config(state='readonly')
        
        toggle_btn = tk.Button(header_frame, text="👁 Show Passwords", 
                              command=lambda: [self.show_passwords.set(not self.show_passwords.get()), toggle_passwords()],
                              bg="#28A745", fg="white", font=('Segoe UI', 9, 'bold'),
                              padx=15, pady=5, relief=tk.FLAT, cursor="hand2")
        toggle_btn.pack(side=tk.RIGHT)
        
        # All fields from database (including password fields)
        all_fields = [
            ('AP ID', 'ap_id', False),
            ('Store ID', 'store_id', False),
            ('Store Alias', 'store_alias', False),
            ('Retail Chain', 'retail_chain', False),
            ('IP Address', 'ip_address', False),
            ('Type', 'type', False),
            ('MAC Address', 'mac_address', False),
            ('Serial Number', 'serial_number', False),
            ('Software Version', 'software_version', False),
            ('Firmware Version', 'firmware_version', False),
            ('Hardware Revision', 'hardware_revision', False),
            ('Build', 'build', False),
            ('Configuration Mode', 'configuration_mode', False),
            ('Service Status', 'service_status', False),
            ('Uptime', 'uptime', False),
            ('Communication Daemon Status', 'communication_daemon_status', False),
            ('Connectivity Internet', 'connectivity_internet', False),
            ('Connectivity Provisioning', 'connectivity_provisioning', False),
            ('Connectivity NTP Server', 'connectivity_ntp_server', False),
            ('Connectivity APC Address', 'connectivity_apc_address', False),
            ('Status', 'status', False),
            ('Last Seen', 'last_seen', False),
            ('Last Ping Time', 'last_ping_time', False),
            ('Username WebUI', 'username_webui', False),
            ('Password WebUI', 'password_webui', True),  # Password field
            ('Username SSH', 'username_ssh', False),
            ('Password SSH', 'password_ssh', True),  # Password field
            ('Notes', 'notes', False),
            ('Created At', 'created_at', False),
            ('Updated At', 'updated_at', False),
        ]
        
        for label, field, is_password in all_fields:
            value = ap_data.get(field, 'N/A')
            if is_password:
                # Create password row with hidden value initially
                value_label = self._create_info_row(content, label, '********' if value and value != 'N/A' else 'N/A')
                self.password_widgets.append((value_label, value))
            else:
                self._create_info_row(content, label, value)
        
        self._log(f"Showing all fields for AP {ap_data['ap_id']} - COMPLETE")
    
    def _connect_ssh(self, session):
        """Connect to AP via SSH in background thread."""
        import threading
        
        def connect():
            try:
                import paramiko
                import time
                
                ap_data = session['ap_data']
                terminal_text = session['terminal_text']
                
                ap_id = ap_data.get('ap_id')
                ip_address = ap_data.get('ip_address', '').strip()
                username = ap_data.get('username_ssh', '').strip()
                password = ap_data.get('password_ssh', '').strip()
                
                # Clean up IP address
                if ip_address.startswith('http'):
                    ip_address = ip_address.split('://')[1]
                if '@' in ip_address:
                    ip_address = ip_address.split('@')[1]
                
                # Validate credentials
                if not ip_address:
                    self.parent.after(0, lambda: terminal_text.insert(tk.END, "\n✗ Error: No IP address configured\n"))
                    self.parent.after(0, lambda: terminal_text.see(tk.END))
                    return
                
                if not username:
                    self.parent.after(0, lambda: terminal_text.insert(tk.END, "\n✗ Error: No SSH username configured\n"))
                    self.parent.after(0, lambda: terminal_text.see(tk.END))
                    return
                
                if not password:
                    self.parent.after(0, lambda: terminal_text.insert(tk.END, "\n✗ Error: No SSH password configured\n"))
                    self.parent.after(0, lambda: terminal_text.see(tk.END))
                    return
                
                def log_output(msg):
                    self.parent.after(0, lambda m=msg: terminal_text.insert(tk.END, m))
                    self.parent.after(0, lambda: terminal_text.see(tk.END))
                
                log_output(f"Connecting to {username}@{ip_address}...\n")
                
                # Create SSH client
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # Connect with timeout
                ssh_client.connect(
                    hostname=ip_address,
                    username=username,
                    password=password,
                    timeout=10,
                    look_for_keys=False,
                    allow_agent=False
                )
                
                log_output(f"✓ Connected to AP {ap_id}\n\n")
                
                # Start interactive shell
                shell_channel = ssh_client.invoke_shell(width=120, height=40)
                shell_channel.settimeout(0.1)
                
                session['ssh_client'] = ssh_client
                session['shell_channel'] = shell_channel
                session['connected'] = True
                
                # Start output reading thread
                def read_output():
                    """Read SSH output continuously."""
                    while session['connected']:
                        try:
                            if shell_channel.recv_ready():
                                output = shell_channel.recv(4096).decode('utf-8', errors='replace')
                                self.parent.after(0, lambda o=output: terminal_text.insert(tk.END, o))
                                self.parent.after(0, lambda: terminal_text.see(tk.END))
                            else:
                                time.sleep(0.05)
                        except Exception as e:
                            if session['connected']:
                                error_msg = f"\n✗ Output read error: {str(e)}\n"
                                self.parent.after(0, lambda m=error_msg: terminal_text.insert(tk.END, m))
                                self.parent.after(0, lambda: terminal_text.see(tk.END))
                            break
                
                output_thread = threading.Thread(target=read_output, daemon=True)
                output_thread.start()
                session['output_thread'] = output_thread
                
                # Enable command input
                self.parent.after(0, lambda: session['command_entry'].config(state='normal'))
                
            except paramiko.AuthenticationException:
                self.parent.after(0, lambda: terminal_text.insert(tk.END, "\n✗ Authentication failed - check username/password\n"))
                self.parent.after(0, lambda: terminal_text.see(tk.END))
            except paramiko.SSHException as e:
                self.parent.after(0, lambda: terminal_text.insert(tk.END, f"\n✗ SSH error: {str(e)}\n"))
                self.parent.after(0, lambda: terminal_text.see(tk.END))
            except Exception as e:
                self.parent.after(0, lambda: terminal_text.insert(tk.END, f"\n✗ Connection error: {str(e)}\n"))
                self.parent.after(0, lambda: terminal_text.see(tk.END))
        
        thread = threading.Thread(target=connect, daemon=True)
        thread.start()
    
    def _disconnect_ssh(self, session):
        """Disconnect SSH session."""
        try:
            session['connected'] = False
            
            if session['shell_channel']:
                session['shell_channel'].close()
            
            if session['ssh_client']:
                session['ssh_client'].close()
            
            terminal_text = session['terminal_text']
            terminal_text.insert(tk.END, "\n\n✓ Disconnected from SSH\n")
            terminal_text.see(tk.END)
            
            session['command_entry'].config(state='disabled')
            
            # Remove from active sessions
            if hasattr(self, 'current_ssh_sessions'):
                ap_id = session['ap_data'].get('ap_id')
                if ap_id in self.current_ssh_sessions:
                    del self.current_ssh_sessions[ap_id]
            
        except Exception as e:
            self._log(f"Error disconnecting SSH: {str(e)}")
    
    def restore_ssh_terminal(self, ap_id):
        """Restore an existing SSH terminal session to the display."""
        if not hasattr(self, 'current_ssh_sessions') or ap_id not in self.current_ssh_sessions:
            return
        
        session = self.current_ssh_sessions[ap_id]
        if not session.get('connected') or 'content_frame' not in session:
            return
        
        # Clear current content
        self._clear_frame(self.ap_details_frame)
        self.current_content_type = "ssh"
        self.current_data = session['ap_data']
        
        self.header_label.config(text=f"SSH Terminal - AP {ap_id}")
        self.popout_button.pack_forget()
        
        # Restore the saved frame
        content_frame = session['content_frame']
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Set focus to command entry
        if 'command_entry' in session:
            session['command_entry'].focus_set()
        
        self._log(f"Restored SSH terminal for AP {ap_id}")
    
    def ssh_execute_command(self, ap_data, command, action_name="command"):
        """Execute a command on the SSH terminal if it's active for this AP."""
        if not hasattr(self, 'current_ssh_sessions'):
            self.current_ssh_sessions = {}
        
        ap_id = ap_data.get('ap_id')
        if ap_id not in self.current_ssh_sessions:
            messagebox.showinfo("Not Connected", 
                              f"Please open SSH terminal for AP {ap_id} first",
                              parent=self.parent)
            return
        
        session = self.current_ssh_sessions[ap_id]
        
        if not session['connected'] or not session['shell_channel']:
            messagebox.showwarning("Not Connected", 
                                 f"SSH connection for AP {ap_id} is not active",
                                 parent=self.parent)
            return
        
        try:
            terminal_text = session['terminal_text']
            
            # Add visual separator and command label
            if action_name != "command":
                terminal_text.insert(tk.END, f"\n{'='*60}\n")
                terminal_text.insert(tk.END, f"# Action: {action_name}\n")
                terminal_text.insert(tk.END, f"{'='*60}\n")
            
            terminal_text.insert(tk.END, f"$ {command}\n")
            terminal_text.see(tk.END)
            
            session['shell_channel'].send(command + '\n')
            self._log(f"Executed SSH command '{action_name}' on AP {ap_id}")
        except Exception as e:
            messagebox.showerror("Command Error", 
                               f"Failed to execute command: {str(e)}",
                               parent=self.parent)
    
    def ssh_download_logs(self, ap_data, dest_folder):
        """Download log files from AP via SCP."""
        import threading
        
        if not hasattr(self, 'current_ssh_sessions'):
            self.current_ssh_sessions = {}
        
        ap_id = ap_data.get('ap_id')
        if ap_id not in self.current_ssh_sessions:
            messagebox.showinfo("Not Connected", 
                              f"Please open SSH terminal for AP {ap_id} first",
                              parent=self.parent)
            return
        
        session = self.current_ssh_sessions[ap_id]
        
        if not session['connected'] or not session['ssh_client']:
            messagebox.showwarning("Not Connected", 
                                 f"SSH connection for AP {ap_id} is not active",
                                 parent=self.parent)
            return
        
        def download():
            try:
                import paramiko
                import os
                
                terminal_text = session['terminal_text']
                
                def log_output(msg):
                    self.parent.after(0, lambda m=msg: terminal_text.insert(tk.END, m))
                    self.parent.after(0, lambda: terminal_text.see(tk.END))
                
                log_output("\n=== Downloading Log Files ===\n")
                
                # Create SCP client using existing SSH connection
                scp_client = paramiko.SFTPClient.from_transport(session['ssh_client'].get_transport())
                
                # Get list of files matching pattern
                remote_path = "/opt/esl/accesspoint"
                try:
                    files = scp_client.listdir(remote_path)
                    log_files = [f for f in files if '20' in f and 'log' in f.lower()]
                    
                    if not log_files:
                        log_output("No log files found to download\n")
                        return
                    
                    log_output(f"Found {len(log_files)} log file(s)\n\n")
                    
                    # Download each file
                    for filename in log_files:
                        remote_file = f"{remote_path}/{filename}"
                        local_file = os.path.join(dest_folder, filename)
                        
                        log_output(f"Downloading: {filename}...")
                        scp_client.get(remote_file, local_file)
                        log_output(" ✓\n")
                    
                    log_output(f"\n✓ All log files downloaded to {dest_folder}\n")
                    
                    def show_success():
                        messagebox.showinfo("Download Complete", 
                                          f"Downloaded {len(log_files)} log file(s) to {dest_folder}",
                                          parent=self.parent)
                    self.parent.after(0, show_success)
                    
                except Exception as e:
                    log_output(f"\n✗ Error: {str(e)}\n")
                finally:
                    scp_client.close()
                    
            except Exception as e:
                def show_error():
                    messagebox.showerror("Download Failed", 
                                       f"Failed to download logs: {str(e)}",
                                       parent=self.parent)
                self.parent.after(0, show_error)
        
        thread = threading.Thread(target=download, daemon=True)
        thread.start()
    
    def show_ssh_terminal(self, ap_data):
        """Show SSH terminal for AP with live connection."""
        ap_id = ap_data.get('ap_id')
        
        # Initialize session storage if needed
        if not hasattr(self, 'current_ssh_sessions'):
            self.current_ssh_sessions = {}
        
        # Check if session already exists and is connected
        if ap_id in self.current_ssh_sessions:
            existing_session = self.current_ssh_sessions[ap_id]
            if existing_session.get('connected'):
                # Session already exists and is connected, just show a message
                self._log(f"SSH terminal for AP {ap_id} is already open and connected")
                messagebox.showinfo("Already Connected", 
                                  f"SSH terminal for AP {ap_id} is already active in the lower right panel",
                                  parent=self.parent)
                return
        
        self._clear_frame(self.ap_details_frame)
        self.current_content_type = "ssh"
        self.current_data = ap_data
        
        self.header_label.config(text=f"SSH Terminal - AP {ap_id}")
        self.popout_button.pack_forget()
        
        content = tk.Frame(self.ap_details_frame, bg="#000000", padx=10, pady=10)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Create terminal output area
        terminal_frame = tk.Frame(content, bg="#000000")
        terminal_frame.pack(fill=tk.BOTH, expand=True)
        
        terminal_text = scrolledtext.ScrolledText(terminal_frame, font=('Consolas', 10),
                                                  bg="#000000", fg="#00FF00",
                                                  insertbackground="#00FF00",
                                                  wrap=tk.WORD)
        terminal_text.pack(fill=tk.BOTH, expand=True)
        
        # Create command input area
        input_frame = tk.Frame(content, bg="#1a1a1a", padx=5, pady=5)
        input_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Add label for clarity
        tk.Label(input_frame, text="Command:", bg="#1a1a1a", fg="#00FF00",
                font=('Consolas', 9)).pack(side=tk.LEFT, padx=(0, 5))
        
        # Create Entry without textvariable first, we'll get value directly
        command_entry = tk.Entry(input_frame,
                                font=('Consolas', 11), bg="#0a0a0a", fg="#00FF00",
                                insertbackground="#00FF00", relief=tk.SOLID, bd=1,
                                highlightthickness=2, highlightcolor="#00FF00",
                                highlightbackground="#333333")
        command_entry.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 5), ipady=3)
        
        # Store session info
        session = {
            'ap_data': ap_data,
            'terminal_text': terminal_text,
            'command_entry': command_entry,
            'ssh_client': None,
            'shell_channel': None,
            'connected': False,
            'output_thread': None,
            'content_frame': content  # Store frame reference to prevent destruction
        }
        
        # Store session by AP ID for quick command access
        self.current_ssh_sessions[ap_id] = session
        
        def send_command(event=None):
            """Send command to SSH session."""
            # Get command directly from Entry widget
            cmd = command_entry.get().strip()
            
            # Log that send was called
            self._log(f"SSH send_command called - cmd: '{cmd}', connected: {session.get('connected')}")
            
            if not session.get('connected') or not session.get('shell_channel'):
                if cmd:  # Only show message if user actually tried to send something
                    terminal_text.insert(tk.END, f"\n⚠ Not connected to SSH - please wait for connection\n")
                    terminal_text.insert(tk.END, f"   You typed: {cmd}\n")
                    terminal_text.see(tk.END)
                    command_entry.delete(0, tk.END)
                else:
                    terminal_text.insert(tk.END, "\n⚠ Not connected to SSH yet\n")
                    terminal_text.see(tk.END)
                return 'break'
            
            if cmd:
                try:
                    # Echo command in terminal
                    terminal_text.insert(tk.END, f"$ {cmd}\n")
                    terminal_text.see(tk.END)
                    
                    # Send to SSH
                    session['shell_channel'].send(cmd + '\n')
                    command_entry.delete(0, tk.END)
                    self._log(f"SSH command sent successfully: {cmd}")
                except Exception as e:
                    error_msg = f"\n✗ Error sending command: {str(e)}\n"
                    terminal_text.insert(tk.END, error_msg)
                    terminal_text.see(tk.END)
                    self._log(f"SSH command error: {str(e)}")
            else:
                terminal_text.insert(tk.END, "⚠ Please enter a command\n")
                terminal_text.see(tk.END)
            
            return 'break'
        
        command_entry.bind('<Return>', send_command)
        
        # Give focus to command entry so user can start typing immediately
        def set_focus():
            command_entry.focus_force()
            # Log to verify entry is enabled
            self._log(f"SSH command entry ready - state: {command_entry['state']}")
        
        # Set focus after a brief delay to ensure widget is fully rendered
        self.parent.after(100, set_focus)
        
        send_btn = tk.Button(input_frame, text="Send", command=send_command,
                           bg="#28A745", fg="white", font=('Segoe UI', 9, 'bold'),
                           padx=15, relief=tk.FLAT, cursor="hand2")
        send_btn.pack(side=tk.RIGHT)
        
        disconnect_btn = tk.Button(input_frame, text="Disconnect",
                                  command=lambda: self._disconnect_ssh(session),
                                  bg="#DC3545", fg="white", font=('Segoe UI', 9, 'bold'),
                                  padx=15, relief=tk.FLAT, cursor="hand2")
        disconnect_btn.pack(side=tk.RIGHT, padx=(0, 5))
        
        # Start SSH connection in background
        terminal_text.insert('1.0', f"SSH Terminal - AP {ap_id}\n")
        terminal_text.insert(tk.END, "Connecting...\n\n")
        
        self._log(f"Opening SSH terminal for AP {ap_id}")
        self._connect_ssh(session)
    
    def show_provisioning_actions(self, ap_data, ap_panel):
        """Show provisioning actions in content panel."""
        self._log(f"show_provisioning_actions called for AP {ap_data.get('ap_id')}")
        self._clear_frame(self.ap_details_frame)
        self.current_content_type = "provisioning"
        self.current_data = ap_data
        
        ap_id = ap_data.get('ap_id')
        self.header_label.config(text=f"Provisioning - AP {ap_id}")
        self.popout_button.pack_forget()
        self._log(f"Header and frame cleared")
        
        content = tk.Frame(self.ap_details_frame, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Header
        tk.Label(content, text="Provisioning Actions", font=('Segoe UI', 14, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(pady=(0, 20))
        
        # Action buttons
        actions = [
            ("Check Status", lambda: ap_panel._provisioning_action(ap_data, 'check')),
            ("Activate Provisioning", lambda: ap_panel._provisioning_action(ap_data, 'activate')),
            ("Deactivate Provisioning", lambda: ap_panel._provisioning_action(ap_data, 'deactivate'))
        ]
        
        self._log(f"Creating {len(actions)} provisioning action buttons")
        for text, command in actions:
            btn = tk.Button(content, text=text, command=command,
                     bg="#007BFF", fg="white", font=('Segoe UI', 10, 'bold'),
                     padx=20, pady=10, relief=tk.FLAT, cursor="hand2",
                     width=30)
            btn.pack(pady=8)
            self._log(f"Created button: {text}")
        
        # Back button
        tk.Button(content, text="← Back to Browser", 
                 command=lambda: self.show_browser_status(ap_id, ap_data),
                 bg="#6C757D", fg="white", font=('Segoe UI', 10, 'bold'),
                 padx=20, pady=10, relief=tk.FLAT, cursor="hand2",
                 width=30).pack(pady=(20, 0))
        
        self._log(f"Showing provisioning actions for AP {ap_id}")
    
    def show_ssh_actions(self, ap_data, ap_panel):
        """Show SSH actions in content panel."""
        self._clear_frame(self.ap_details_frame)
        self.current_content_type = "ssh_actions"
        self.current_data = ap_data
        
        ap_id = ap_data.get('ap_id')
        self.header_label.config(text=f"SSH - AP {ap_id}")
        self.popout_button.pack_forget()
        
        content = tk.Frame(self.ap_details_frame, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Header
        tk.Label(content, text="SSH Actions", font=('Segoe UI', 14, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(pady=(0, 20))
        
        # Action buttons
        actions = [
            ("Check Status", lambda: ap_panel._ssh_action(ap_data, 'check')),
            ("Activate SSH", lambda: ap_panel._ssh_action(ap_data, 'activate')),
            ("Deactivate SSH", lambda: ap_panel._ssh_action(ap_data, 'deactivate'))
        ]
        
        for text, command in actions:
            tk.Button(content, text=text, command=command,
                     bg="#6F42C1", fg="white", font=('Segoe UI', 10, 'bold'),
                     padx=20, pady=10, relief=tk.FLAT, cursor="hand2",
                     width=30).pack(pady=8)
        
        # Back button
        tk.Button(content, text="← Back to Browser", 
                 command=lambda: self.show_browser_status(ap_id, ap_data),
                 bg="#6C757D", fg="white", font=('Segoe UI', 10, 'bold'),
                 padx=20, pady=10, relief=tk.FLAT, cursor="hand2",
                 width=30).pack(pady=(20, 0))
        
        self._log(f"Showing SSH actions for AP {ap_id}")
    
    def show_browser_status(self, ap_id, ap_data=None):
        """Show browser connection status (browser runs in external Chrome window)."""
        # If ap_data not provided or doesn't have _data_collected, get it from ap_panel
        if not ap_data or '_data_collected' not in ap_data:
            if self.ap_panel and hasattr(self.ap_panel, 'ap_tabs') and ap_id in self.ap_panel.ap_tabs:
                ap_data = self.ap_panel.ap_tabs[ap_id]['ap_data']
                self._log(f"Retrieved ap_data from ap_panel for {ap_id}, data_collected={ap_data.get('_data_collected', False)}")
        
        self._clear_frame(self.ap_details_frame)
        self.current_content_type = "browser"
        self.current_data = ap_id
        
        self.header_label.config(text=f"Browser - AP {ap_id}")
        self.popout_button.pack_forget()  # No popout needed, browser is external
        
        # Create scrollable canvas for content
        canvas = tk.Canvas(self.ap_details_frame, bg="#FFFFFF", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.ap_details_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#FFFFFF")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind mousewheel
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except:
                pass
        
        canvas.bind("<Enter>", lambda e: canvas.bind("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind("<MouseWheel>"))
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        content = tk.Frame(scrollable_frame, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Add browser operations at top if we have ap_data
        if ap_data:
            self._add_browser_operations(content, ap_data)
        
        # Browser status box (moved under buttons)
        status_frame = tk.Frame(content, bg="#F8F9FA", relief=tk.SOLID, borderwidth=1)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        status_label = tk.Label(status_frame, 
                               text="● Browser Status: " + ("Running" if self.browser_running else "Not Running"),
                               font=('Segoe UI', 11, 'bold'),
                               bg="#F8F9FA", 
                               fg="#28A745" if self.browser_running else "#6C757D",
                               padx=20, pady=15)
        status_label.pack()
        
        # Info text box (moved to bottom)
        info_frame = tk.Frame(content, bg="#E7F3FF", relief=tk.SOLID, borderwidth=1)
        info_frame.pack(fill=tk.X, pady=20)
        
        info_text = ("The browser opens in a separate Chrome window.\n\n"
                    "Use the Browser tab controls in the AP panel (top-left)\n"
                    "to start the browser and connect to this AP.\n\n"
                    "The browser will automatically handle CATO warnings\n"
                    "and use the AP's stored credentials.")
        
        tk.Label(info_frame, text=info_text, font=('Segoe UI', 10),
                bg="#E7F3FF", fg="#004085", justify=tk.CENTER).pack(padx=20, pady=20)
        
        self._log(f"Showing browser status for AP {ap_id}")
    
    def show_notes(self, ap_id):
        """Show notes for AP."""
        self._clear_frame(self.context_details_frame)
        self.current_content_type = "notes"
        self.current_data = ap_id
        
        self.header_label.config(text=f"Notes - AP {ap_id}")
        self.popout_button.pack_forget()
        
        # Main container
        main_frame = tk.Frame(self.context_details_frame, bg="#FFFFFF", padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header with title and Add Note button
        header_frame = tk.Frame(main_frame, bg="#FFFFFF")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_frame, text="Notes", font=('Segoe UI', 11, 'bold'),
                bg="#FFFFFF", fg="#333333").pack(side=tk.LEFT)
        
        tk.Button(header_frame, text="Add Note", command=lambda: self._open_write_note_dialog(ap_id),
                 bg="#28A745", fg="white", cursor="hand2", padx=15, pady=6,
                 font=('Segoe UI', 9, 'bold'), relief=tk.FLAT, bd=0,
                 activebackground="#218838").pack(side=tk.RIGHT)
        
        # Separator line
        tk.Frame(main_frame, bg="#CCCCCC", height=1).pack(fill=tk.X, pady=(0, 10))
        
        # Notes list with scrollbar
        notes_list_frame = tk.Frame(main_frame, bg="#FFFFFF")
        notes_list_frame.pack(fill=tk.BOTH, expand=True)
        
        notes_canvas = tk.Canvas(notes_list_frame, bg="#FFFFFF", highlightthickness=0)
        notes_scrollbar = tk.Scrollbar(notes_list_frame, orient="vertical", command=notes_canvas.yview)
        notes_container = tk.Frame(notes_canvas, bg="#FFFFFF")
        
        def _update_scroll_region(event):
            notes_canvas.configure(scrollregion=notes_canvas.bbox("all"))
            canvas_width = notes_canvas.winfo_width()
            notes_canvas.itemconfig(notes_window, width=canvas_width)
        
        notes_container.bind("<Configure>", _update_scroll_region)
        notes_canvas.bind("<Configure>", _update_scroll_region)
        
        notes_window = notes_canvas.create_window((0, 0), window=notes_container, anchor="nw")
        notes_canvas.configure(yscrollcommand=notes_scrollbar.set)
        
        notes_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        notes_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            try:
                if notes_canvas.winfo_exists():
                    notes_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except:
                pass
        
        def _bind_mousewheel(event):
            notes_canvas.bind("<MouseWheel>", _on_mousewheel)
        
        def _unbind_mousewheel(event):
            notes_canvas.unbind("<MouseWheel>")
        
        notes_canvas.bind("<Enter>", _bind_mousewheel)
        notes_canvas.bind("<Leave>", _unbind_mousewheel)
        
        # Get notes from database
        notes = self.db.get_support_notes(ap_id)
        
        if notes:
            for note in notes:
                self._create_note_item(notes_container, note, ap_id)
        else:
            tk.Label(notes_container, text="No notes found for this AP",
                    font=('Segoe UI', 9, 'italic'), bg="#FFFFFF", fg="#888888").pack(pady=20)
        
        self._log(f"Showing notes for AP {ap_id}")
    
    def show_jira_details(self, ticket_data):
        """Show Jira ticket details."""
        self._clear_frame(self.context_details_frame)
        self.current_content_type = "jira"
        self.current_data = ticket_data
        
        ticket_key = ticket_data.get('key', 'Unknown')
        fields = ticket_data.get('fields', {})
        
        self.header_label.config(text=f"Jira Ticket - {ticket_key}")
        self.popout_button.pack_forget()
        
        # Scrollable content
        canvas = tk.Canvas(self.context_details_frame, bg="#FFFFFF", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.context_details_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#FFFFFF")
        
        def _update_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas_width = canvas.winfo_width()
            canvas.itemconfig(canvas_window, width=canvas_width)
        
        scrollable_frame.bind("<Configure>", _update_scroll_region)
        canvas.bind("<Configure>", _update_scroll_region)
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except:
                pass
        
        def _bind_mousewheel(event):
            canvas.bind("<MouseWheel>", _on_mousewheel)
        
        def _unbind_mousewheel(event):
            canvas.unbind("<MouseWheel>")
        
        canvas.bind("<Enter>", _bind_mousewheel)
        canvas.bind("<Leave>", _unbind_mousewheel)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        content = tk.Frame(scrollable_frame, bg="#FFFFFF", padx=20, pady=15)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Header with ticket key and status
        header_frame = tk.Frame(content, bg="#FFFFFF")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_frame, text=ticket_key, font=('Segoe UI', 16, 'bold'),
                bg="#FFFFFF", fg="#0066CC").pack(side=tk.LEFT)
        
        # Link icon to open in browser
        from credentials_manager import CredentialsManager
        creds_manager = CredentialsManager(self.db)
        jira_creds = creds_manager.get_credentials('jira')
        jira_url = jira_creds.get('url', '')
        
        if jira_url:
            link_btn = tk.Label(header_frame, text="🔗", font=('Segoe UI', 14),
                              bg="#FFFFFF", fg="#0066CC", cursor="hand2")
            link_btn.pack(side=tk.LEFT, padx=(5, 0))
            
            ticket_url = f"{jira_url.rstrip('/')}/browse/{ticket_key}"
            
            def open_in_browser(e=None):
                import webbrowser
                # Open in Edge
                edge_path = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
                try:
                    webbrowser.register('edge', None, webbrowser.BackgroundBrowser(edge_path))
                    webbrowser.get('edge').open(ticket_url)
                except:
                    # Fallback to default browser
                    webbrowser.open(ticket_url)
            
            link_btn.bind("<Button-1>", open_in_browser)
        
        # Status badge
        status = fields.get('status', {})
        status_name = status.get('name', 'Unknown') if isinstance(status, dict) else 'Unknown'
        status_color = "#28A745" if status_name.lower() in ['done', 'resolved', 'closed'] else "#007BFF"
        
        status_frame = tk.Frame(header_frame, bg=status_color, padx=8, pady=3)
        status_frame.pack(side=tk.LEFT, padx=(10, 0))
        tk.Label(status_frame, text=status_name, font=('Segoe UI', 8, 'bold'),
                bg=status_color, fg="white").pack()
        
        # Summary
        summary = fields.get('summary', 'No summary')
        summary_label = tk.Label(content, text=summary, font=('Segoe UI', 11),
                bg="#FFFFFF", fg="#333333", justify=tk.LEFT, anchor="w")
        summary_label.pack(fill=tk.X, anchor="w", pady=(0, 15))
        
        # Compact details table (2 columns)
        details_frame = tk.Frame(content, bg="#F8F9FA", relief=tk.SOLID, borderwidth=1)
        details_frame.pack(fill=tk.X, pady=(0, 15))
        
        issue_type = fields.get('issuetype', {})
        priority = fields.get('priority', {})
        assignee = fields.get('assignee', {})
        reporter = fields.get('reporter', {})
        
        details_data = [
            [('Type', issue_type.get('name', 'N/A') if isinstance(issue_type, dict) else 'N/A'),
             ('Priority', priority.get('name', 'N/A') if isinstance(priority, dict) else 'N/A')],
            [('Assignee', assignee.get('displayName', 'Unassigned') if isinstance(assignee, dict) else 'Unassigned'),
             ('Reporter', reporter.get('displayName', 'N/A') if isinstance(reporter, dict) else 'N/A')],
            [('Created', fields.get('created', 'N/A')[:10] if fields.get('created') else 'N/A'),
             ('Updated', fields.get('updated', 'N/A')[:10] if fields.get('updated') else 'N/A')]
        ]
        
        # Use grid layout for stable columns
        table_container = tk.Frame(details_frame, bg="#F8F9FA")
        table_container.pack(fill=tk.X, padx=10, pady=5)
        
        # Configure column weights to maintain structure
        table_container.grid_columnconfigure(0, weight=0, minsize=80)  # Label 1
        table_container.grid_columnconfigure(1, weight=1, minsize=150)  # Value 1
        table_container.grid_columnconfigure(2, weight=0, minsize=80)  # Label 2
        table_container.grid_columnconfigure(3, weight=1, minsize=150)  # Value 2
        
        for row_idx, row_data in enumerate(details_data):
            for col_idx, (label, value) in enumerate(row_data):
                col_offset = col_idx * 2
                
                # Label
                tk.Label(table_container, text=f"{label}:", font=('Segoe UI', 9, 'bold'),
                        bg="#F8F9FA", fg="#495057", anchor="w").grid(
                            row=row_idx, column=col_offset, sticky="w", padx=(0, 5), pady=3)
                
                # Value
                tk.Label(table_container, text=str(value), font=('Segoe UI', 9),
                        bg="#F8F9FA", fg="#212529", anchor="w").grid(
                            row=row_idx, column=col_offset+1, sticky="w", padx=(0, 20), pady=3)
        
        # Description with scrollable text
        tk.Label(content, text="Description:", font=('Segoe UI', 10, 'bold'),
                bg="#FFFFFF", fg="#495057").pack(anchor="w", pady=(5, 5))
        
        description = fields.get('description', 'No description available')
        if isinstance(description, dict):
            description = self._extract_adf_text(description)
        
        desc_frame = tk.Frame(content, bg="#F8F9FA", relief=tk.SOLID, borderwidth=1)
        desc_frame.pack(fill=tk.X, pady=(0, 15))
        
        desc_text = tk.Text(desc_frame, font=('Segoe UI', 9), wrap=tk.WORD,
                           bg="#F8F9FA", relief=tk.FLAT, padx=10, pady=8, bd=0)
        desc_text.pack(fill=tk.X)
        desc_text.insert('1.0', description)
        desc_text.config(state='disabled')
        
        # Auto-resize description to fit content
        desc_text.update_idletasks()
        line_count = int(desc_text.index('end-1c').split('.')[0])
        desc_text.config(height=line_count)
        
        # Comments/Replies section
        comments = fields.get('comment', {})
        if isinstance(comments, dict):
            comments_list = comments.get('comments', [])
            if comments_list:
                # Comments header
                tk.Label(content, text=f"Comments ({len(comments_list)}):", font=('Segoe UI', 10, 'bold'),
                        bg="#FFFFFF", fg="#495057").pack(anchor="w", pady=(5, 5))
                
                # Display each comment
                for comment in comments_list:
                    self._create_jira_comment(content, comment)
        
        self._log(f"Showing Jira ticket {ticket_key}")
    
    def _create_jira_comment(self, parent, comment):
        """Create a Jira comment display."""
        comment_frame = tk.Frame(parent, bg="#F0F0F0", relief=tk.SOLID, borderwidth=1)
        comment_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Comment header
        header_frame = tk.Frame(comment_frame, bg="#E9ECEF")
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        
        author = comment.get('author', {})
        author_name = author.get('displayName', 'Unknown') if isinstance(author, dict) else 'Unknown'
        created = comment.get('created', 'Unknown')[:16] if comment.get('created') else 'Unknown'
        
        tk.Label(header_frame, text=f"{author_name} • {created}", 
                font=('Segoe UI', 8), bg="#E9ECEF", fg="#495057").pack(side=tk.LEFT, padx=8, pady=4)
        
        # Comment body
        body = comment.get('body', '')
        if isinstance(body, dict):
            body = self._extract_adf_text(body)
        elif not body:
            body = 'No content'
        
        comment_text = tk.Text(comment_frame, font=('Segoe UI', 9), wrap=tk.WORD,
                              bg="#F0F0F0", relief=tk.FLAT, padx=8, pady=6, bd=0)
        comment_text.pack(fill=tk.X)
        comment_text.insert('1.0', body)
        comment_text.config(state='disabled')
        
        # Auto-resize comment to fit content
        comment_text.update_idletasks()
        line_count = int(comment_text.index('end-1c').split('.')[0])
        comment_text.config(height=line_count)
    
    def _extract_adf_text(self, adf_content):
        """Extract plain text from Atlassian Document Format."""
        if not isinstance(adf_content, dict):
            return str(adf_content)
        
        def extract(node):
            if isinstance(node, str):
                return node
            if not isinstance(node, dict):
                return ''
            
            text = ''
            if node.get('type') == 'text':
                text += node.get('text', '')
            
            if 'content' in node:
                for child in node['content']:
                    text += extract(child)
                    if child.get('type') in ['paragraph', 'heading']:
                        text += '\n\n'
            
            return text
        
        return extract(adf_content).strip()
    
    def show_vusion_details(self, vusion_data):
        """Show Vusion integration details."""
        self._clear_frame(self.context_details_frame)
        self.current_content_type = "vusion"
        self.current_data = vusion_data
        
        self.header_label.config(text="Vusion Integration Details")
        self.popout_button.pack_forget()
        
        content = tk.Frame(self.context_details_frame, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text="Vusion Integration", font=('Segoe UI', 16, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(anchor="w", pady=(0, 20))
        
        tk.Label(content, text="TODO: Display Vusion integration details",
                font=('Segoe UI', 10), bg="#FFFFFF", fg="#6C757D").pack(pady=20)
        
        self._log("Showing Vusion details")
    
    def show_add_note_form(self, ap_id, ap_data):
        """Show form to add a new note in Context Details."""
        self._clear_frame(self.context_details_frame)
        self.current_content_type = "add_note"
        self.current_data = ap_data
        
        self.header_label.config(text=f"Add Note - AP {ap_id}")
        self.popout_button.pack_forget()
        
        # Main content area
        content = tk.Frame(self.context_details_frame, bg="#FFFFFF", padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content, text="Write Note", font=("Segoe UI", 14, "bold"),
                bg="#FFFFFF").pack(anchor="w", pady=(0, 15))
        
        # Headline
        tk.Label(content, text="Headline:", font=("Segoe UI", 10, "bold"),
                bg="#FFFFFF").pack(anchor="w", pady=(0, 5))
        
        headline_entry = tk.Entry(content, font=("Segoe UI", 10), relief="flat",
                                 borderwidth=0, highlightthickness=1,
                                 highlightbackground="#CCCCCC",
                                 highlightcolor="#007BFF")
        headline_entry.pack(fill="x", ipady=6)
        headline_entry.focus_set()
        
        # Note content
        tk.Label(content, text="Note:", font=("Segoe UI", 10, "bold"),
                bg="#FFFFFF").pack(anchor="w", pady=(10, 5))
        
        text_widget = scrolledtext.ScrolledText(content, font=("Segoe UI", 10),
                                               wrap=tk.WORD, height=12, relief="flat",
                                               borderwidth=0, highlightthickness=1,
                                               highlightbackground="#CCCCCC",
                                               highlightcolor="#007BFF")
        text_widget.pack(fill="both", expand=True)
        
        # Button frame
        button_frame = tk.Frame(content, bg="#FFFFFF")
        button_frame.pack(fill="x", pady=(15, 0))
        
        def save_note():
            headline = headline_entry.get().strip()
            note_content = text_widget.get("1.0", tk.END).strip()
            
            if not headline or not note_content:
                messagebox.showwarning("Missing Data", "Both headline and content are required.",
                                     parent=self.parent)
                return
            
            username = self.current_user.get('username') if isinstance(self.current_user, dict) else self.current_user
            success, message, note_id = self.db.add_support_note(ap_id, username,
                                                                 headline, note_content)
            if success:
                self._log(f"Note added: {headline}", "success")
                # Refresh context panel to show new note
                if self.refresh_callback:
                    self.refresh_callback()
                # Clear the form
                self._clear_frame(self.context_details_frame)
                tk.Label(self.context_details_frame, text="Note saved successfully!",
                        font=('Segoe UI', 12), bg="#FFFFFF", fg="#28A745").pack(pady=50)
            else:
                messagebox.showerror("Error", f"Failed to save note: {message}", parent=self.parent)
        
        def cancel_note():
            self._clear_frame(self.context_details_frame)
            tk.Label(self.context_details_frame, text="Cancelled",
                    font=('Segoe UI', 12), bg="#FFFFFF", fg="#6C757D").pack(pady=50)
        
        # Save button
        tk.Button(button_frame, text="Save Note", command=save_note,
                 bg="#28A745", fg="white", cursor="hand2", padx=20, pady=8,
                 font=("Segoe UI", 10), relief=tk.FLAT, bd=0,
                 activebackground="#218838").pack(side=tk.LEFT, padx=(0, 5))
        
        # Cancel button
        tk.Button(button_frame, text="Cancel", command=cancel_note,
                 bg="#6C757D", fg="white", cursor="hand2", padx=20, pady=8,
                 font=("Segoe UI", 10), relief=tk.FLAT, bd=0,
                 activebackground="#5A6268").pack(side=tk.LEFT, padx=5)
        
        self._log(f"Opened add note form for AP {ap_id}")
    
    def show_note_details(self, note_data):
        """Show note with replies."""
        self.current_content_type = "note"
        self.current_data = note_data
        
        self.header_label.config(text=f"Note - {note_data.get('headline', 'Note')}")
        self.popout_button.pack_forget()
        
        # Get ap_id from note data or current AP
        ap_id = note_data.get('ap_id', None)
        
        # Call the full note window implementation
        self._open_note_window(note_data, ap_id)
        
        self._log(f"Showing note: {note_data.get('headline')}")
    
    def _add_browser_operations(self, parent, ap_data):
        """Add browser operations buttons below AP details."""
        # Check if browser is running AND data has been collected
        # Data is considered collected when we have navigated to status page
        data_collected = ap_data.get('_data_collected', False)
        buttons_enabled = self.browser_running and data_collected
        
        self._log(f"Adding browser operations for AP {ap_data.get('ap_id', 'unknown')} (browser_running={self.browser_running}, data_collected={data_collected})")
        
        # No separator at top anymore since this is at the top
        
        # Browser operations header
        ops_header = tk.Frame(parent, bg="#FFFFFF")
        ops_header.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(ops_header, text="🌐", font=('Segoe UI', 16),
                bg="#FFFFFF").pack(side=tk.LEFT, padx=(0, 8))
        
        tk.Label(ops_header, text="Browser Window", font=('Segoe UI', 11, 'bold'),
                bg="#FFFFFF", fg="#212529").pack(side=tk.LEFT)
        
        self._log("Browser operations: Header added")
        
        # Navigation group
        nav_frame = tk.Frame(parent, bg="#F8F9FA", padx=10, pady=10)
        nav_frame.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(nav_frame, text="Navigation", font=('Segoe UI', 9, 'bold'),
                bg="#F8F9FA", fg="#495057").pack(anchor="w", pady=(0, 6))
        
        nav_btn_frame = tk.Frame(nav_frame, bg="#F8F9FA")
        nav_btn_frame.pack(fill=tk.X)
        
        nav_operations = [
            ("📊 Status", lambda: self._browser_operation(ap_data, 'nav_status')),
            ("🔧 Provisioning", lambda: self._browser_operation(ap_data, 'provisioning')),
            ("💻 SSH", lambda: self._browser_operation(ap_data, 'ssh')),
        ]
        
        for i, (op_text, op_cmd) in enumerate(nav_operations):
            btn = tk.Button(nav_btn_frame, text=op_text, command=op_cmd,
                          bg="#007BFF", fg="white", font=('Segoe UI', 8),
                          padx=10, pady=4, relief=tk.FLAT, cursor="hand2",
                          borderwidth=0, state=tk.NORMAL if buttons_enabled else tk.DISABLED,
                          activebackground="#0069D9")
            btn.pack(side=tk.LEFT, padx=(0, 5) if i < len(nav_operations)-1 else 0)
            
            # Store reference
            if 'browser_ops_btns' not in ap_data:
                ap_data['browser_ops_btns'] = []
            ap_data['browser_ops_btns'].append(btn)
        
        self._log(f"Browser operations: Added {len(nav_operations)} navigation buttons")
        
        # Actions group
        action_frame = tk.Frame(parent, bg="#F8F9FA", padx=10, pady=10)
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(action_frame, text="Actions", font=('Segoe UI', 9, 'bold'),
                bg="#F8F9FA", fg="#495057").pack(anchor="w", pady=(0, 6))
        
        action_btn_frame = tk.Frame(action_frame, bg="#F8F9FA")
        action_btn_frame.pack(fill=tk.X)
        
        action_operations = [
            ("🔄 Refresh", lambda: self._browser_operation(ap_data, 'refresh')),
            ("📸 Screenshot", lambda: self._browser_operation(ap_data, 'screenshot')),
            ("📄 View Source", lambda: self._browser_operation(ap_data, 'view_source')),
        ]
        
        for i, (op_text, op_cmd) in enumerate(action_operations):
            btn = tk.Button(action_btn_frame, text=op_text, command=op_cmd,
                          bg="#6C757D", fg="white", font=('Segoe UI', 8),
                          padx=10, pady=4, relief=tk.FLAT, cursor="hand2",
                          borderwidth=0, state=tk.NORMAL if buttons_enabled else tk.DISABLED,
                          activebackground="#5A6268")
            btn.pack(side=tk.LEFT, padx=(0, 5) if i < len(action_operations)-1 else 0)
            
            # Store reference
            ap_data['browser_ops_btns'].append(btn)
        
        self._log(f"Browser operations: Added {len(action_operations)} action buttons - COMPLETE")
    
    def _browser_operation(self, ap_data, operation):
        """Handle browser operation button clicks - delegate to AP panel."""
        if self.ap_panel:
            self.ap_panel._browser_action(ap_data, operation)
        else:
            self._log(f"Error: AP panel reference not set, cannot execute {operation}")
    
    def _create_info_row(self, parent, label, value):
        """Create an information row with copyable text."""
        row = tk.Frame(parent, bg="#FFFFFF")
        row.pack(fill=tk.X, pady=3)
        
        tk.Label(row, text=f"{label}:", font=('Segoe UI', 10, 'bold'),
                bg="#FFFFFF", fg="#495057", width=30, anchor="w").pack(side=tk.LEFT)
        
        # Use Entry widget for copyable text
        value_entry = tk.Entry(row, font=('Segoe UI', 10),
                              bd=0, relief=tk.FLAT, highlightthickness=0,
                              readonlybackground="#FFFFFF", fg="#212529")
        value_entry.insert(0, str(value))
        value_entry.config(state='readonly')
        value_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(15, 0))
        
        return value_entry
    
    def _create_note_item(self, parent, note, ap_id):
        """Create a note item in 2-row format (date/user/replies, then headline)."""
        note_frame = tk.Frame(parent, bg="#FFFFFF", cursor="hand2")
        note_frame.pack(fill=tk.X, pady=3, padx=0)
        
        # Row 1: Date/Time, User (full name), and Reply count
        row1_frame = tk.Frame(note_frame, bg="#FFFFFF")
        row1_frame.pack(fill=tk.X, padx=0, pady=(5, 0))
        
        # Get user full name
        user_info = self.db.get_user(note['user'])
        display_name = user_info.get('full_name', note['user']) if user_info else note['user']
        
        tk.Label(row1_frame, text=f"{note['created_at']} - {display_name}",
                font=('Segoe UI', 8), fg="#888888", bg="#FFFFFF", anchor="w").pack(side=tk.LEFT)
        
        # Get reply count
        reply_count = self.db.get_note_reply_count(note['id'])
        if True:  # Always show reply count (even if 0)
            reply_frame = tk.Frame(row1_frame, bg="#FFFFFF")
            reply_frame.pack(side=tk.RIGHT, padx=5)
            
            # Forum icon (Unicode)
            icon_label = tk.Label(reply_frame, text="💬", font=('Segoe UI', 14),
                                 fg="#007BFF", bg="#FFFFFF", cursor="hand2")
            icon_label.pack(side=tk.LEFT, padx=(0, 3))
            
            # Reply count
            count_label = tk.Label(reply_frame, text=str(reply_count),
                                  font=('Segoe UI', 8), fg="#007BFF", bg="#FFFFFF",
                                  cursor="hand2")
            count_label.pack(side=tk.LEFT)
            
            # Tooltip
            def show_tooltip(event, widget):
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                label = tk.Label(tooltip, text="Replies", background="#FFFFE0", relief=tk.SOLID,
                               borderwidth=1, font=('Segoe UI', 9), padx=4, pady=2)
                label.pack()
                widget.tooltip_window = tooltip
            
            def hide_tooltip(event, widget):
                if hasattr(widget, 'tooltip_window'):
                    widget.tooltip_window.destroy()
                    del widget.tooltip_window
            
            for widget in [icon_label, count_label]:
                widget.bind("<Enter>", lambda e, w=widget: show_tooltip(e, w))
                widget.bind("<Leave>", lambda e, w=widget: hide_tooltip(e, w))
        
        # Row 2: Headline
        row2 = tk.Label(note_frame, text=note['headline'],
                       font=('Segoe UI', 9, 'bold'), bg="#FFFFFF", anchor="w", fg="#333333")
        row2.pack(fill=tk.X, padx=0, pady=(0, 5))
        
        # Separator line
        tk.Frame(note_frame, bg="#E0E0E0", height=1).pack(fill=tk.X, pady=(5, 0))
        
        # Bind click events to open note details
        for widget in [note_frame, row1_frame, row2]:
            widget.bind("<Button-1>", lambda e, n=note: self._open_note_window(n, ap_id))
            for child in widget.winfo_children():
                child.bind("<Button-1>", lambda e, n=note: self._open_note_window(n, ap_id))
    
    def _open_write_note_dialog(self, ap_id):
        """Open dialog to write a new note."""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Write Note")
        dialog.geometry("600x500")
        dialog.configure(bg="#FFFFFF")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        main_frame = tk.Frame(dialog, bg="#FFFFFF", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(main_frame, text="Write Note", font=("Segoe UI", 14, "bold"),
                bg="#FFFFFF").pack(anchor="w", pady=(0, 15))
        
        # Headline
        tk.Label(main_frame, text="Headline:", font=("Segoe UI", 10, "bold"),
                bg="#FFFFFF").pack(anchor="w", pady=(0, 5))
        
        headline_entry = tk.Entry(main_frame, font=("Segoe UI", 10), relief="flat",
                                 borderwidth=0, highlightthickness=1,
                                 highlightbackground="#CCCCCC",
                                 highlightcolor="#007BFF")
        headline_entry.pack(fill="x", ipady=6)
        headline_entry.focus_set()
        
        # Note content
        tk.Label(main_frame, text="Note:", font=("Segoe UI", 10, "bold"),
                bg="#FFFFFF").pack(anchor="w", pady=(10, 5))
        
        text_widget = scrolledtext.ScrolledText(main_frame, font=("Segoe UI", 10),
                                               wrap=tk.WORD, height=12, relief="flat",
                                               borderwidth=0, highlightthickness=1,
                                               highlightbackground="#CCCCCC",
                                               highlightcolor="#007BFF")
        text_widget.pack(fill="both", expand=True)
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg="#FFFFFF")
        button_frame.pack(fill="x", pady=(10, 0))
        
        def save_note():
            headline = headline_entry.get().strip()
            content = text_widget.get("1.0", tk.END).strip()
            
            if not headline or not content:
                messagebox.showwarning("Missing Data", "Both headline and content are required.",
                                     parent=dialog)
                return
            
            username = self.current_user.get('username') if isinstance(self.current_user, dict) else self.current_user
            success, message, note_id = self.db.add_support_note(ap_id, username,
                                                                 headline, content)
            if success:
                self._log(f"Note added: {headline}", "success")
                # Refresh notes display
                self.show_notes(ap_id)
                dialog.destroy()
            else:
                messagebox.showerror("Error", f"Failed to save note: {message}", parent=dialog)
        
        # Save button
        tk.Button(button_frame, text="Save Note", command=save_note,
                 bg="#28A745", fg="white", cursor="hand2", padx=20, pady=8,
                 font=("Segoe UI", 10), relief=tk.FLAT, bd=0,
                 activebackground="#218838").pack(side=tk.LEFT, padx=(0, 5))
        
        # Cancel button
        tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                 bg="#6C757D", fg="white", cursor="hand2", padx=20, pady=8,
                 font=("Segoe UI", 10), relief=tk.FLAT, bd=0,
                 activebackground="#5A6268").pack(side=tk.LEFT, padx=5)
    
    def _create_reply_display(self, parent_container, reply, username, note, ap_id):
        """Helper method to create a single reply display with edit functionality"""
        reply_box = tk.Frame(parent_container, bg="#FFFFFF")
        reply_box.pack(fill=tk.X, pady=(0, 15))
        
        # Reply header with edit button
        reply_header_frame = tk.Frame(reply_box, bg="#FFFFFF")
        reply_header_frame.pack(fill=tk.X, pady=(0, 5))
        
        reply_user = self.db.get_user(reply['user'])
        reply_display_name = reply_user.get('full_name', reply['user']) if reply_user else reply['user']
        
        tk.Label(reply_header_frame, text=f"{reply['created_at']} - {reply_display_name}",
                font=('Segoe UI', 8), fg="#888888", bg="#FFFFFF").pack(side=tk.LEFT)
        
        # Reply display label - fill width dynamically
        reply_display_label = tk.Label(reply_box, text=reply['reply_text'], font=('Segoe UI', 9),
                bg="#FFFFFF", fg="#333333", anchor="w", justify=tk.LEFT, wraplength=1)
        reply_display_label.pack(fill=tk.BOTH, expand=True)
        reply_display_label.bind("<Configure>", lambda e: reply_display_label.config(wraplength=e.width-4))
        
        # Divider after reply
        tk.Frame(parent_container, bg="#E0E0E0", height=1).pack(fill=tk.X, pady=(10, 0))
        
        # Reply edit frame (initially hidden)
        reply_edit_frame = tk.Frame(reply_box, bg="#FFFFFF")
        
        reply_edit_text = scrolledtext.ScrolledText(reply_edit_frame, font=("Segoe UI", 9),
                                                    wrap=tk.WORD, height=4, relief="flat",
                                                    borderwidth=0, highlightthickness=1,
                                                    highlightbackground="#CCCCCC",
                                                    highlightcolor="#007BFF")
        reply_edit_text.pack(fill="x", pady=(0, 10))
        reply_edit_text.insert("1.0", reply['reply_text'])
        
        reply_edit_buttons = tk.Frame(reply_edit_frame, bg="#FFFFFF")
        reply_edit_buttons.pack(fill="x")
        
        def toggle_reply_edit():
            if reply_display_label.winfo_viewable():
                reply_display_label.pack_forget()
                reply_edit_frame.pack(fill=tk.X, pady=(5, 0))
            else:
                reply_edit_frame.pack_forget()
                reply_display_label.pack(fill=tk.X)
        
        def save_reply_edit():
            new_reply_text = reply_edit_text.get("1.0", tk.END).strip()
            if not new_reply_text:
                messagebox.showwarning("Missing Reply", "Reply text is required.", parent=self.parent)
                return
            
            success, message = self.db.update_note_reply(reply['id'], new_reply_text, username)
            if success:
                self._log("Reply updated", "success")
                # Refresh the note window to show updated reply
                self._open_note_window(note, ap_id)
            else:
                messagebox.showerror("Error", f"Failed to update reply: {message}", parent=self.parent)
        
        def cancel_reply_edit():
            reply_edit_text.delete("1.0", tk.END)
            reply_edit_text.insert("1.0", reply['reply_text'])
            reply_edit_frame.pack_forget()
            reply_display_label.pack(fill=tk.X)
        
        # Edit and Delete buttons if user owns this reply
        if reply['user'] == username:
            def delete_reply_confirm():
                if messagebox.askyesno("Delete Reply",
                                      "Are you sure you want to delete this reply? This cannot be undone.",
                                      parent=self.parent):
                    success, message = self.db.delete_note_reply(reply['id'], username)
                    if success:
                        self._log("Reply deleted", "success")
                        # Refresh context panel to update reply count
                        if self.refresh_callback:
                            self.refresh_callback()
                        # Refresh the note window
                        self._open_note_window(note, ap_id)
                    else:
                        messagebox.showerror("Error", f"Failed to delete reply: {message}", parent=self.parent)
            
            delete_reply_btn = tk.Button(reply_header_frame, text="Delete",
                                         command=delete_reply_confirm,
                                         bg="#DC3545", fg="white", font=('Segoe UI', 8),
                                         relief=tk.FLAT, bd=0, cursor="hand2", padx=10, pady=2,
                                         activebackground="#C82333", width=8)
            delete_reply_btn.pack(side=tk.RIGHT, padx=(8, 0))
            
            edit_reply_btn = tk.Button(reply_header_frame, text="Edit", 
                                      command=toggle_reply_edit,
                                      bg="#007BFF", fg="white", font=('Segoe UI', 8),
                                      relief=tk.FLAT, bd=0, cursor="hand2", padx=10, pady=2,
                                      activebackground="#0056B3", width=8)
            edit_reply_btn.pack(side=tk.RIGHT, padx=(8, 0))
        
        tk.Button(reply_edit_buttons, text="Save", 
                 command=save_reply_edit,
                 bg="#28A745", fg="white", padx=15, pady=6, relief=tk.FLAT, bd=0,
                 cursor="hand2", font=("Segoe UI", 9),
                 activebackground="#218838").pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(reply_edit_buttons, text="Cancel",
                 command=cancel_reply_edit,
                 bg="#6C757D", fg="white", padx=15, pady=6, relief=tk.FLAT, bd=0,
                 cursor="hand2", font=("Segoe UI", 9),
                 activebackground="#5A6268").pack(side=tk.LEFT)

    def _open_note_window(self, note, ap_id):
        """Show note details with replies in Context Details tab."""
        self._clear_frame(self.context_details_frame)
        self._log(f"Opening note: {note['headline']}")
        
        # Top scrollable area for content
        scroll_container = tk.Frame(self.context_details_frame, bg="#FFFFFF")
        scroll_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(scroll_container, bg="#FFFFFF", highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        content = tk.Frame(canvas, bg="#FFFFFF")
        
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=content, anchor="nw", width=canvas.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Make canvas width dynamic
        def configure_canvas_width(event):
            canvas.itemconfig(canvas.find_withtag("all")[0], width=event.width)
        canvas.bind("<Configure>", configure_canvas_width)
        
        # Mousewheel scrolling
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except:
                pass
        
        def _bind_mousewheel(event):
            canvas.bind("<MouseWheel>", _on_mousewheel)
        
        def _unbind_mousewheel(event):
            canvas.unbind("<MouseWheel>")
        
        canvas.bind("<Enter>", _bind_mousewheel)
        canvas.bind("<Leave>", _unbind_mousewheel)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Content padding
        inner_content = tk.Frame(content, bg="#FFFFFF", padx=20, pady=15)
        inner_content.pack(fill=tk.BOTH, expand=True)
        
        # Bottom fixed area for input boxes (will be populated later)
        bottom_container = tk.Frame(self.context_details_frame, bg="#F8F9FA", relief=tk.RIDGE, borderwidth=1)
        # Don't pack yet - will be shown when needed
        
        # Check if user can edit this note
        username = self.current_user.get('username') if isinstance(self.current_user, dict) else self.current_user
        is_owner = note['user'] == username
        is_latest = self.db.is_latest_note(note['id'], ap_id)
        can_edit_note = is_owner and is_latest
        
        # Debug logging
        print(f"DEBUG: username={username}, note_user={note['user']}, is_owner={is_owner}, is_latest={is_latest}, can_edit={can_edit_note}")
        
        # Note metadata header
        metadata_frame = tk.Frame(inner_content, bg="#FFFFFF")
        metadata_frame.pack(fill=tk.X, pady=(0, 10))
        
        metadata_left = tk.Frame(metadata_frame, bg="#FFFFFF")
        metadata_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        user_info = self.db.get_user(note['user'])
        display_name = user_info.get('full_name', note['user']) if user_info else note['user']
        
        tk.Label(metadata_left, text=f"Created: {note['created_at']}",
                font=('Segoe UI', 9), bg="#FFFFFF", fg="#6C757D").pack(anchor="w", pady=2)
        tk.Label(metadata_left, text=f"By: {display_name}",
                font=('Segoe UI', 9), bg="#FFFFFF", fg="#6C757D").pack(anchor="w", pady=2)
        
        # Last edited line
        if note.get('updated_at') and note['updated_at'] != note['created_at']:
            updated_user = self.db.get_user(note.get('updated_by', ''))
            updated_name = updated_user.get('full_name', note.get('updated_by', 'unknown')) if updated_user else note.get('updated_by', 'unknown')
            tk.Label(metadata_left, text=f"Last edited: {note['updated_at']} by {updated_name}",
                    font=('Segoe UI', 8, 'italic'), bg="#FFFFFF", fg="#888888").pack(anchor="w", pady=2)
        
        # Buttons container on the right side of metadata
        metadata_right = tk.Frame(metadata_frame, bg="#FFFFFF")
        metadata_right.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Separator
        tk.Frame(inner_content, bg="#CCCCCC", height=1).pack(fill=tk.X, pady=10)
        
        # Display frames
        note_display_frame = tk.Frame(inner_content, bg="#FFFFFF")
        note_display_frame.pack(fill=tk.X)
        
        # Headline
        headline_label = tk.Label(note_display_frame, text=note['headline'], font=('Segoe UI', 16, 'bold'),
                bg="#FFFFFF", fg="#333333", anchor="w", justify=tk.LEFT, wraplength=1)
        headline_label.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        headline_label.bind("<Configure>", lambda e: headline_label.config(wraplength=e.width-4))
        
        # Note text - fill width dynamically
        note_text_label = tk.Label(note_display_frame, text=note['note'], font=('Segoe UI', 10),
                bg="#FFFFFF", fg="#333333", anchor="nw", justify=tk.LEFT, wraplength=1)
        note_text_label.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        note_text_label.bind("<Configure>", lambda e: note_text_label.config(wraplength=e.width-4))
        
        # Edit frame (initially hidden, will be shown in bottom_container)
        note_edit_frame = tk.Frame(bottom_container, bg="#F8F9FA")
        
        tk.Label(note_edit_frame, text="Headline:", font=("Segoe UI", 10, "bold"),
                bg="#FFFFFF").pack(anchor="w", pady=(0, 5))
        headline_entry = tk.Entry(note_edit_frame, font=("Segoe UI", 12, "bold"),
                                 relief="flat", borderwidth=0, highlightthickness=1,
                                 highlightbackground="#CCCCCC", highlightcolor="#007BFF")
        headline_entry.pack(fill="x", ipady=5, pady=(0, 10))
        headline_entry.insert(0, note['headline'])
        
        tk.Label(note_edit_frame, text="Note:", font=("Segoe UI", 10, "bold"),
                bg="#FFFFFF").pack(anchor="w", pady=(0, 5))
        note_text_edit = scrolledtext.ScrolledText(note_edit_frame, font=("Segoe UI", 10),
                                                    wrap=tk.WORD, height=10, relief="flat",
                                                    borderwidth=0, highlightthickness=1,
                                                    highlightbackground="#CCCCCC",
                                                    highlightcolor="#007BFF")
        note_text_edit.pack(fill="x")
        note_text_edit.insert("1.0", note['note'])
        
        # Edit buttons
        edit_buttons_frame = tk.Frame(note_edit_frame, bg="#FFFFFF")
        edit_buttons_frame.pack(fill="x", pady=(10, 0))
        
        def save_note_edit():
            new_headline = headline_entry.get().strip()
            new_text = note_text_edit.get("1.0", tk.END).strip()
            
            if not new_headline or not new_text:
                messagebox.showwarning("Missing Data", "Both headline and note are required.", parent=self.parent)
                return
            
            success, message = self.db.update_support_note(note['id'], new_headline, new_text, username)
            if success:
                self._log(f"Note updated: {new_headline}", "success")
                # Refresh the note view
                note['headline'] = new_headline
                note['note'] = new_text
                self._open_note_window(note, ap_id)
            else:
                messagebox.showerror("Error", f"Failed to update note: {message}", parent=self.parent)
        
        def cancel_note_edit():
            note_edit_frame.pack_forget()
            bottom_container.pack_forget()
            note_display_frame.pack(fill=tk.X)
        
        tk.Button(edit_buttons_frame, text="Save Changes", command=save_note_edit,
                 bg="#28A745", fg="white", padx=20, pady=8, relief=tk.FLAT, bd=0,
                 cursor="hand2", font=("Segoe UI", 10),
                 activebackground="#218838").pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(edit_buttons_frame, text="Cancel", command=cancel_note_edit,
                 bg="#6C757D", fg="white", padx=20, pady=8, relief=tk.FLAT, bd=0,
                 cursor="hand2", font=("Segoe UI", 10),
                 activebackground="#5A6268").pack(side=tk.LEFT)
        
        def toggle_note_edit():
            if note_display_frame.winfo_viewable():
                note_display_frame.pack_forget()
                # Show edit in bottom container
                bottom_container.pack(side=tk.BOTTOM, fill=tk.X, before=scroll_container)
                note_edit_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
            else:
                note_edit_frame.pack_forget()
                bottom_container.pack_forget()
                note_display_frame.pack(fill=tk.X)
        
        # Delete and Edit buttons for note (if owner) - in metadata_right
        if is_owner:
            def delete_note_confirm():
                if messagebox.askyesno("Delete Note", 
                                      "Are you sure you want to delete this note? This cannot be undone.",
                                      parent=self.parent):
                    success, message = self.db.delete_support_note(note['id'], username)
                    if success:
                        self._log("Note deleted", "success")
                        # Refresh context panel to remove deleted note from list
                        if self.refresh_callback:
                            self.refresh_callback()
                        self._clear_frame(self.context_details_frame)
                        # Show empty state
                        tk.Label(self.context_details_frame, text="Note deleted",
                                font=('Segoe UI', 12), bg="#FFFFFF", fg="#6C757D").pack(pady=50)
                    else:
                        messagebox.showerror("Error", f"Failed to delete note: {message}", parent=self.parent)
            
            delete_btn = tk.Button(metadata_right, text="Delete", command=delete_note_confirm,
                                  bg="#DC3545", fg="white", font=('Segoe UI', 9),
                                  relief=tk.FLAT, bd=0, cursor="hand2", padx=15, pady=4,
                                  activebackground="#C82333", width=8)
            delete_btn.pack(side=tk.RIGHT, padx=(8, 0))
            
            if can_edit_note:
                edit_btn = tk.Button(metadata_right, text="Edit", command=toggle_note_edit,
                                    bg="#007BFF", fg="white", font=('Segoe UI', 9),
                                    relief=tk.FLAT, bd=0, cursor="hand2", padx=15, pady=4,
                                    activebackground="#0056B3", width=8)
                edit_btn.pack(side=tk.RIGHT, padx=(8, 0))
        
        # Separator
        tk.Frame(inner_content, bg="#CCCCCC", height=1).pack(fill=tk.X, pady=10)
        
        # Reply button section (separate from Edit/Delete buttons)
        reply_button_frame = tk.Frame(inner_content, bg="#FFFFFF")
        reply_button_frame.pack(fill=tk.X, pady=(0, 10))
        
        def show_reply_input():
            bottom_container.pack(side=tk.BOTTOM, fill=tk.X, before=scroll_container)
            add_reply_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
            reply_text_widget.focus_set()
        
        show_reply_btn = tk.Button(reply_button_frame, text="Reply", command=show_reply_input,
                                   bg="#007BFF", fg="white", padx=15, pady=6,
                                   font=('Segoe UI', 9, 'bold'), relief=tk.FLAT, bd=0,
                                   cursor="hand2", activebackground="#0056B3")
        show_reply_btn.pack(side=tk.LEFT)
        
        # Another separator
        tk.Frame(inner_content, bg="#CCCCCC", height=1).pack(fill=tk.X, pady=10)
        
        # Add Reply section in bottom container
        add_reply_frame = tk.Frame(bottom_container, bg="#F8F9FA")
        
        tk.Label(add_reply_frame, text="Reply:", bg="#FFFFFF", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 5))
        reply_text_widget = scrolledtext.ScrolledText(add_reply_frame, height=4,
                                                      font=("Segoe UI", 10), wrap=tk.WORD,
                                                      relief="flat", borderwidth=0,
                                                      highlightthickness=1,
                                                      highlightbackground="#CCCCCC",
                                                      highlightcolor="#007BFF")
        reply_text_widget.pack(fill="x")
        
        # Reply buttons
        reply_btn_frame = tk.Frame(add_reply_frame, bg="#FFFFFF")
        reply_btn_frame.pack(fill="x", pady=(10, 0))
        
        def save_reply():
            reply_text = reply_text_widget.get("1.0", tk.END).strip()
            if not reply_text:
                messagebox.showwarning("Missing Reply", "Please enter a reply.", parent=self.parent)
                return
            
            username = self.current_user.get('username') if isinstance(self.current_user, dict) else self.current_user
            success, message, reply_id = self.db.add_note_reply(note['id'], username, reply_text)
            if success:
                self._log(f"Reply added to note: {note['headline']}", "success")
                # Refresh context panel to update reply count
                if self.refresh_callback:
                    self.refresh_callback()
                # Refresh note view
                self._open_note_window(note, ap_id)
            else:
                messagebox.showerror("Error", f"Failed to save reply: {message}", parent=self.parent)
        
        def hide_reply_input():
            add_reply_frame.pack_forget()
            bottom_container.pack_forget()
        
        tk.Button(reply_btn_frame, text="Save Reply", command=save_reply,
                 bg="#28A745", fg="white", padx=20, pady=8, relief=tk.FLAT, bd=0,
                 cursor="hand2", font=("Segoe UI", 10),
                 activebackground="#218838").pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(reply_btn_frame, text="Cancel", command=hide_reply_input,
                 bg="#6C757D", fg="white", padx=20, pady=8, relief=tk.FLAT, bd=0,
                 cursor="hand2", font=("Segoe UI", 10),
                 activebackground="#5A6268").pack(side=tk.LEFT, padx=5)
        
        # Replies section
        replies = self.db.get_note_replies(note['id'])
        if replies:
            # Replies header
            replies_header = tk.Frame(inner_content, bg="#FFFFFF")
            replies_header.pack(fill=tk.X, pady=(10, 10))
            
            tk.Label(replies_header, text="💬", font=('Segoe UI', 18),
                    bg="#FFFFFF", fg="#424242").pack(side=tk.LEFT, padx=(0, 5))
            tk.Label(replies_header, text=f"({len(replies)})",
                    font=('Segoe UI', 10, 'bold'), bg="#FFFFFF", fg="#424242").pack(side=tk.LEFT)
            
            # Display replies
            for reply in replies:
                self._create_reply_display(inner_content, reply, username, note, ap_id)
        else:
            tk.Label(inner_content, text="No replies yet",
                    font=('Segoe UI', 9, 'italic'), bg="#FFFFFF", fg="#6C757D").pack(pady=10)
    
    def _extract_xml_value(self, html_text, field_name):
        """Extract value from HTML table row. The data is in format:
        <tr><th>Field Name:</th><td>Value</td></tr>
        """
        import re
        # Create pattern to match the table row with the field name
        pattern = f"<th>{field_name}:</th>\\s*<td>([^<]*)</td>"
        match = re.search(pattern, html_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def start_browser(self):
        """Start the browser manager."""
        try:
            if self.browser_running:
                messagebox.showinfo("Browser", "Browser is already running", parent=self.parent)
                return False
            
            self._log("Starting browser...")
            
            # Import browser manager
            from browser_manager import BrowserManager
            
            # Initialize browser manager with callbacks
            self.browser_manager = BrowserManager(
                log_callback=self._log,
                progress_callback=lambda msg, pct: self._log(f"Browser: {msg} ({pct}%)"),
                extract_xml_callback=self._extract_xml_value,
                handle_cato_callback=self._handle_cato_warning
            )
            
            # Set db reference for data updates
            if hasattr(self, 'db'):
                self.browser_manager.db = self.db
            
            # Initialize the browser
            self.browser_manager.initialize_browser()
            
            self.browser_running = True
            self._log("✓ Browser started successfully")
            return True
            
        except Exception as e:
            self._log(f"Error starting browser: {str(e)}")
            messagebox.showerror("Error", f"Failed to start browser:\n{str(e)}", parent=self.parent)
            return False
    
    def stop_browser(self):
        """Stop the browser manager."""
        try:
            if not self.browser_running:
                return
            
            self._log("Stopping browser...")
            
            if self.browser_manager:
                self.browser_manager.close()
                self.browser_manager = None
            
            self.browser_running = False
            self._log("✓ Browser stopped")
            
        except Exception as e:
            self._log(f"Error stopping browser: {str(e)}")
            messagebox.showerror("Error", f"Failed to stop browser:\n{str(e)}", parent=self.parent)
    
    def open_ap_in_browser(self, ap_data):
        """Open a specific AP in the browser (runs in background thread)."""
        if not self.browser_running:
            self._log("Browser not running, starting it first...")
            if not self.start_browser():
                return False
        
        self._log(f"Opening AP {ap_data.get('ap_id')} in browser...")
        
        # Run in background thread to avoid locking the UI
        import threading
        
        def open_in_thread():
            try:
                # Open the AP using browser manager
                ap_list = [ap_data]
                result = self.browser_manager.open_multiple_aps(ap_list)
                
                # Minimize browser after opening to keep it in background
                try:
                    self.browser_manager.driver.minimize_window()
                except:
                    pass
                
                # Schedule UI update on main thread
                def update_ui():
                    if result.get('status') == 'success':
                        self._log(f"✓ Successfully opened AP {ap_data.get('ap_id')}")
                        # Mark data as collected so buttons can be enabled
                        ap_data['_data_collected'] = True
                        
                        # Also update the ap_data stored in ap_panel
                        if self.ap_panel and hasattr(self.ap_panel, 'ap_tabs'):
                            ap_id = ap_data.get('ap_id')
                            if ap_id in self.ap_panel.ap_tabs:
                                self.ap_panel.ap_tabs[ap_id]['ap_data']['_data_collected'] = True
                                self._log(f"Set _data_collected flag for AP {ap_id}")
                        
                        # Refresh the browser status view to update button states
                        if self.current_content_type == 'browser':
                            self.show_browser_status(ap_data.get('ap_id'), ap_data)
                        # Don't show success popup - just log it
                    else:
                        self._log(f"✗ Failed to open AP: {result.get('message')}")
                        messagebox.showerror("Error", 
                                           f"Failed to open AP:\n{result.get('message')}", 
                                           parent=self.parent)
                
                self.parent.after(0, update_ui)
                    
            except Exception as e:
                self._log(f"Error opening AP in browser: {str(e)}")
                def show_error():
                    messagebox.showerror("Error", 
                                       f"Failed to open AP in browser:\n{str(e)}", 
                                       parent=self.parent)
                self.parent.after(0, show_error)
        
        thread = threading.Thread(target=open_in_thread, daemon=True)
        thread.start()
        
        return True
    
    def _handle_cato_warning(self, driver):
        """Handle CATO Networks warning page."""
        try:
            import time
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            page_source = driver.page_source
            
            # Check if Cato Networks warning page is present
            has_warning = 'Warning - Restricted Website' in page_source
            has_ssl_error = 'Invalid SSL/TLS certificate' in page_source
            has_proceed_button = 'class="proceed prompt"' in page_source or 'onclick="onProceed()"' in page_source
            
            self._log(f"[CATO Check] Warning: {has_warning}, SSL Error: {has_ssl_error}, Proceed button: {has_proceed_button}")
            
            if (has_warning or has_ssl_error) and has_proceed_button:
                self._log("🚨 CATO Networks warning detected, clicking PROCEED...")
                
                # Find and click proceed button
                proceed_selectors = [
                    "button.proceed.prompt",
                    "button.proceed",
                    "button[class*='proceed']",
                    "//button[contains(text(), 'PROCEED')]",
                    "//button[contains(@class, 'proceed')]"
                ]
                
                proceed_btn = None
                for selector in proceed_selectors:
                    try:
                        if selector.startswith("//"):
                            proceed_btn = WebDriverWait(driver, 3).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        else:
                            proceed_btn = WebDriverWait(driver, 3).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                        self._log(f"✓ Found PROCEED button with: {selector}")
                        break
                    except:
                        continue
                
                if proceed_btn:
                    try:
                        proceed_btn.click()
                        self._log("✓ Clicked PROCEED button")
                    except:
                        driver.execute_script("arguments[0].click();", proceed_btn)
                        self._log("✓ Clicked PROCEED button (JavaScript)")
                    
                    # Wait 5 seconds then refresh
                    self._log("Waiting 5 seconds before refresh...")
                    time.sleep(5)
                    
                    try:
                        driver.refresh()
                        self._log("✓ Refreshed page after CATO click")
                        time.sleep(2)
                    except Exception as refresh_error:
                        # Refresh might timeout, but that's okay - page is loading
                        self._log(f"⚠ Refresh timeout (expected): {str(refresh_error)[:100]}")
                    
                    # Give page time to load after refresh
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        self._log("✓ Page loaded after CATO handling")
                    except:
                        # If wait times out, that's okay - we'll verify in Phase 3
                        self._log("⚠ Wait completed (page may still be loading)")
                    
                    return True
                else:
                    self._log("✗ Could not find PROCEED button")
                    return False
            
            return False
        except Exception as e:
            self._log(f"Error handling CATO warning: {str(e)}")
            return False
    
    def is_browser_running(self):
        """Check if browser is currently running."""
        return self.browser_running
    
    def _popout(self):
        """Pop out current content to separate window."""
        if self.current_content_type == "ssh":
            self._log(f"Popping out SSH terminal for AP {self.current_data}")
            messagebox.showinfo("Pop Out", "SSH terminal pop-out will be implemented")
        elif self.current_content_type == "browser":
            messagebox.showinfo("Browser", "Browser runs in external Chrome window", parent=self.parent)
    
    def _log(self, message, level="info"):
        """Log activity (thread-safe)."""
        if self.log_callback:
            import threading
            if threading.current_thread() is threading.main_thread():
                # We're on the main thread, log directly
                self.log_callback("Content Panel", message, level)
            else:
                # We're on a background thread, schedule on main thread
                self.parent.after(0, lambda: self.log_callback("Content Panel", message, level))
