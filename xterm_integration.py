"""
xterm.js terminal integration for Tkinter.
Provides a modern SSH terminal with full terminal emulation.
Opens in system browser to avoid threading issues.
"""
import tkinter as tk
import threading
import time
import webbrowser
from ssh_terminal_server import start_server


class XTermSSHTerminal:
    """xterm.js terminal in browser window."""
    
    def __init__(self, ap_id, ap_data):
        self.ap_id = ap_id
        self.ap_data = ap_data
        self.server_port = 5555
        
        # Build URL with connection parameters
        import urllib.parse
        params = {
            'ap_id': ap_id,
            'host': ap_data.get('ip_address', ''),
            'username': ap_data.get('ssh_username', 'esl'),
            'password': ap_data.get('ssh_password', ''),
            'port': '22'
        }
        query_string = urllib.parse.urlencode(params)
        self.url = f'http://127.0.0.1:{self.server_port}/?{query_string}'
        self.browser_opened = False
    
    def open_in_browser(self):
        """Open terminal in default browser."""
        if not self.browser_opened:
            webbrowser.open(self.url)
            self.browser_opened = True
            time.sleep(1)  # Give browser time to open


class XTermSSHPanel:
    """
    Replacement for the current SSH terminal implementation.
    Uses xterm.js for professional terminal emulation.
    """
    
    def __init__(self, parent, content_panel):
        self.parent = parent
        self.content_panel = content_panel
        self.terminals = {}  # ap_id -> XTermSSHTerminal
        self.server_started = False
        
    def show_ssh_terminal(self, ap_data):
        """Show xterm.js SSH terminal for an AP."""
        ap_id = ap_data.get('ap_id')
        
        # Clear content panel
        for widget in self.content_panel.winfo_children():
            widget.destroy()
        
        # Create header
        header_frame = tk.Frame(self.content_panel, bg="#2C3E50", height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title = tk.Label(
            header_frame,
            text=f"SSH Terminal - AP {ap_id}",
            font=('Segoe UI', 14, 'bold'),
            bg="#2C3E50",
            fg="white"
        )
        title.pack(side="left", padx=20, pady=15)
        
        # Connection info
        info_text = f"{ap_data.get('ssh_username', 'N/A')}@{ap_data.get('ip_address', 'N/A')}"
        info_label = tk.Label(
            header_frame,
            text=info_text,
            font=('Consolas', 10),
            bg="#2C3E50",
            fg="#95A5A6"
        )
        info_label.pack(side="left", padx=10, pady=15)
        
        # Disconnect button
        disconnect_btn = tk.Button(
            header_frame,
            text="Disconnect",
            command=lambda: self._disconnect_terminal(ap_id),
            bg="#DC3545",
            fg="white",
            font=('Segoe UI', 9, 'bold'),
            padx=15,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2"
        )
        disconnect_btn.pack(side="right", padx=20, pady=15)
        
        # Quick command buttons
        btn_frame = tk.Frame(self.content_panel, bg="#FFFFFF", height=80)
        btn_frame.pack(fill="x", padx=10, pady=5)
        btn_frame.pack_propagate(False)
        
        commands = [
            ("Exit Service", "exit_service", "#DC3545"),
            ("Start Service", "servicemode", "#FFC107"),
            ("Check DNS", "check_dns", "#6F42C1"),
            ("Disk Space", "df -h", "#17A2B8"),
            ("List Logs", "cd /opt/esl/accesspoint && ls -la *20*log* 2>/dev/null || echo 'No log files found'", "#28A745"),
            ("System Info", "uname -a && uptime", "#20C997"),
        ]
        
        for i, (text, cmd, color) in enumerate(commands):
            row = i // 3
            col = i % 3
            
            btn = tk.Button(
                btn_frame,
                text=text,
                command=lambda c=cmd, a=ap_data: self._quick_command(a, c),
                bg=color,
                fg="white",
                font=('Segoe UI', 8, 'bold'),
                padx=8,
                pady=4,
                relief=tk.FLAT,
                cursor="hand2",
                width=13
            )
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
        
        for i in range(3):
            btn_frame.grid_columnconfigure(i, weight=1)
        
        # Start server if needed
        if not self.server_started:
            def start_flask():
                start_server(host='127.0.0.1', port=5555, debug=False)
            
            threading.Thread(target=start_flask, daemon=True).start()
            time.sleep(2)
            self.server_started = True
        
        # Terminal info display
        terminal_frame = tk.Frame(self.content_panel, bg="#1e1e1e")
        terminal_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Instructions
        info_frame = tk.Frame(terminal_frame, bg="#2C3E50", padx=30, pady=30)
        info_frame.pack(expand=True)
        
        icon_label = tk.Label(
            info_frame,
            text="🖥️",
            font=('Segoe UI', 48),
            bg="#2C3E50",
            fg="white"
        )
        icon_label.pack(pady=10)
        
        title_label = tk.Label(
            info_frame,
            text="SSH Terminal Ready",
            font=('Segoe UI', 18, 'bold'),
            bg="#2C3E50",
            fg="white"
        )
        title_label.pack(pady=5)
        
        conn_label = tk.Label(
            info_frame,
            text=f"Connection: {ap_data.get('ssh_username', 'esl')}@{ap_data.get('ip_address', 'N/A')}",
            font=('Consolas', 12),
            bg="#2C3E50",
            fg="#95A5A6"
        )
        conn_label.pack(pady=5)
        
        status_label = tk.Label(
            info_frame,
            text="Terminal opened in browser window",
            font=('Segoe UI', 11),
            bg="#2C3E50",
            fg="#16825d"
        )
        status_label.pack(pady=10)
        
        hint_label = tk.Label(
            info_frame,
            text="Use quick command buttons above to send commands\nor type directly in the browser terminal window",
            font=('Segoe UI', 10),
            bg="#2C3E50",
            fg="#95A5A6",
            justify=tk.CENTER
        )
        hint_label.pack(pady=5)
        
        # Create or get terminal
        if ap_id not in self.terminals:
            terminal = XTermSSHTerminal(ap_id, ap_data)
            self.terminals[ap_id] = terminal
        else:
            terminal = self.terminals[ap_id]
        
        # Open terminal in browser and auto-connect
        def open_and_connect():
            terminal.open_in_browser()
            # Connection happens via JavaScript postMessage in the HTML
        
        threading.Thread(target=open_and_connect, daemon=True).start()
    
    def _quick_command(self, ap_data, command):
        """Execute a quick command in the terminal."""
        # Commands are sent via the browser terminal
        # Show message that command should be typed in browser
        from tkinter import messagebox
        
        if command == "exit_service":
            cmd_text = "Extended mode sequence:\nextended matex2010\nenableshell true\nexit\nexit"
        else:
            cmd_text = command
        
        messagebox.showinfo(
            "Quick Command",
            f"Execute this command in the browser terminal:\n\n{cmd_text}",
            parent=self.parent
        )
    
    def _disconnect_terminal(self, ap_id):
        """Disconnect SSH terminal."""
        from tkinter import messagebox
        messagebox.showinfo(
            "Disconnect",
            "Close the browser terminal window to disconnect.",
            parent=self.parent
        )
