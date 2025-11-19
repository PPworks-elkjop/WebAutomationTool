"""
Flask-SocketIO server for xterm.js SSH terminal.
Handles WebSocket connections and bridges to SSH via Paramiko.
"""
import threading
import time
import paramiko
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ssh-terminal-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Store active SSH sessions
active_sessions = {}


class SSHSession:
    """Manages an SSH connection and shell channel."""
    
    def __init__(self, session_id, host, username, password, port=22):
        self.session_id = session_id
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.ssh_client = None
        self.shell_channel = None
        self.connected = False
        self.output_thread = None
        
    def connect(self):
        """Establish SSH connection."""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.ssh_client.connect(
                hostname=self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                timeout=10,
                look_for_keys=False,
                allow_agent=False
            )
            
            # Start interactive shell with proper terminal size
            self.shell_channel = self.ssh_client.invoke_shell(
                term='xterm-256color',
                width=120,
                height=40
            )
            self.shell_channel.settimeout(0.1)
            
            self.connected = True
            
            # Start output reading thread
            self.output_thread = threading.Thread(target=self._read_output, daemon=True)
            self.output_thread.start()
            
            # Check for service mode and auto-run status
            threading.Thread(target=self._check_service_mode, daemon=True).start()
            
            return True
            
        except Exception as e:
            socketio.emit('ssh_error', {'error': str(e)}, room=self.session_id)
            return False
    
    def _read_output(self):
        """Continuously read SSH output and send to client."""
        while self.connected and self.shell_channel:
            try:
                if self.shell_channel.recv_ready():
                    data = self.shell_channel.recv(8192).decode('utf-8', errors='replace')
                    socketio.emit('ssh_output', {'data': data}, room=self.session_id)
                else:
                    time.sleep(0.05)
            except Exception as e:
                if self.connected:
                    socketio.emit('ssh_error', {'error': f'Read error: {str(e)}'}, room=self.session_id)
                break
    
    def _check_service_mode(self):
        """Check if we're in service mode and auto-run status command."""
        time.sleep(4)  # Wait for initial output
        
        # Collect initial output to check for service mode
        collected = ""
        for _ in range(5):
            if self.shell_channel.recv_ready():
                try:
                    chunk = self.shell_channel.recv(4096).decode('utf-8', errors='replace')
                    collected += chunk
                except:
                    pass
            time.sleep(0.5)
        
        # Check for service mode prompt (case-insensitive)
        if 'servicemode>' in collected.lower() or 'service mode' in collected.lower():
            # Send status command
            self.send_input('status\n')
            time.sleep(3)
            
            # Collect status output
            status_output = ""
            for _ in range(10):
                if self.shell_channel.recv_ready():
                    try:
                        chunk = self.shell_channel.recv(4096).decode('utf-8', errors='replace')
                        status_output += chunk
                    except:
                        pass
                time.sleep(0.3)
            
            # Parse Java Version
            if status_output:
                import re
                java_match = re.search(r'Java Version[:\s]+([^\n\r]+)', status_output, re.IGNORECASE)
                if java_match:
                    java_version = java_match.group(1).strip()
                    socketio.emit('java_version', {'version': java_version}, room=self.session_id)
    
    def send_input(self, data):
        """Send input to SSH channel."""
        if self.connected and self.shell_channel:
            try:
                self.shell_channel.send(data)
            except Exception as e:
                socketio.emit('ssh_error', {'error': f'Send error: {str(e)}'}, room=self.session_id)
    
    def resize_terminal(self, cols, rows):
        """Resize the terminal."""
        if self.connected and self.shell_channel:
            try:
                self.shell_channel.resize_pty(width=cols, height=rows)
            except Exception as e:
                print(f"Resize error: {str(e)}")
    
    def disconnect(self):
        """Close SSH connection."""
        self.connected = False
        
        if self.shell_channel:
            try:
                self.shell_channel.close()
            except:
                pass
        
        if self.ssh_client:
            try:
                self.ssh_client.close()
            except:
                pass


@app.route('/')
def index():
    """Serve the xterm.js terminal page."""
    return render_template('ssh_terminal.html')


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    session_id = request.sid
    print(f"Client connected: {session_id}")
    emit('connected', {'session_id': session_id})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    session_id = request.sid
    print(f"Client disconnected: {session_id}")
    
    if session_id in active_sessions:
        active_sessions[session_id].disconnect()
        del active_sessions[session_id]


@socketio.on('start_ssh')
def handle_start_ssh(data):
    """Start SSH connection."""
    session_id = request.sid
    
    host = data.get('host')
    username = data.get('username')
    password = data.get('password')
    port = data.get('port', 22)
    
    if not all([host, username, password]):
        emit('ssh_error', {'error': 'Missing connection parameters'})
        return
    
    # Close existing session if any
    if session_id in active_sessions:
        active_sessions[session_id].disconnect()
    
    # Create new SSH session
    session = SSHSession(session_id, host, username, password, port)
    active_sessions[session_id] = session
    
    # Connect
    if session.connect():
        emit('ssh_connected', {'host': host})
    else:
        emit('ssh_error', {'error': 'Connection failed'})


@socketio.on('ssh_input')
def handle_ssh_input(data):
    """Handle input from terminal."""
    session_id = request.sid
    
    if session_id not in active_sessions:
        emit('ssh_error', {'error': 'No active SSH session'})
        return
    
    session = active_sessions[session_id]
    input_data = data.get('data', '')
    session.send_input(input_data)


@socketio.on('resize')
def handle_resize(data):
    """Handle terminal resize."""
    session_id = request.sid
    
    if session_id in active_sessions:
        cols = data.get('cols', 80)
        rows = data.get('rows', 24)
        active_sessions[session_id].resize_terminal(cols, rows)


@socketio.on('run_command')
def handle_run_command(data):
    """Run a quick command."""
    session_id = request.sid
    
    if session_id not in active_sessions:
        emit('ssh_error', {'error': 'No active SSH session'})
        return
    
    session = active_sessions[session_id]
    command = data.get('command', '')
    
    if command:
        session.send_input(command + '\n')


def start_server(host='127.0.0.1', port=5555, debug=False):
    """Start the Flask-SocketIO server."""
    print(f"Starting SSH terminal server on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    start_server(debug=True)
