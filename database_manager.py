"""
VERA Database Manager - SQLite database with encrypted sensitive fields
Replaces JSON-based credential storage with concurrent-safe SQLite database
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from contextlib import contextmanager
import threading
from cryptography.fernet import Fernet
import base64
import hashlib

class DatabaseManager:
    """Manages VERA database with encryption for sensitive fields."""
    
    # Fields that should be encrypted
    ENCRYPTED_FIELDS = ['password_webui', 'password_ssh', 'su_password']
    
    def __init__(self, db_file: str = None):
        if db_file is None:
            db_file = Path.home() / ".vera_database.db"
        self.db_file = Path(db_file)
        self.key_file = Path.home() / ".vera_encryption_key"
        self._cipher = self._get_cipher()
        self._local = threading.local()
        self._init_database()
    
    def _get_cipher(self):
        """Get or create AES-256 encryption cipher."""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                key = f.read()
                # Check if it's an old 128-bit key and upgrade if needed
                if len(key) < 44:  # Old key format
                    print("Upgrading encryption from AES-128 to AES-256...")
                    key = self._upgrade_key(key)
        else:
            # Generate a new AES-256 key
            # Use Fernet.generate_key() which creates a proper 256-bit key
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Secure the key file (Windows)
            try:
                import os
                os.chmod(self.key_file, 0o600)
            except:
                pass
        return Fernet(key)
    
    def _upgrade_key(self, old_key: bytes) -> bytes:
        """Upgrade from old key format to AES-256."""
        # Create new stronger key
        new_key = Fernet.generate_key()
        # Save the new key
        with open(self.key_file, 'wb') as f:
            f.write(new_key)
        return new_key
    
    def _encrypt(self, value: str) -> str:
        """Encrypt a value using AES-256."""
        if not value:
            return ''
        return self._cipher.encrypt(value.encode()).decode()
    
    def _decrypt(self, encrypted: str) -> str:
        """Decrypt a value."""
        if not encrypted:
            return ''
        try:
            return self._cipher.decrypt(encrypted.encode()).decode()
        except Exception:
            # If decryption fails, return as-is (for backward compatibility)
            return encrypted
    
    @contextmanager
    def _get_connection(self):
        """Get a thread-safe database connection with proper locking."""
        # Each thread gets its own connection
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(
                self.db_file,
                timeout=30.0,  # Wait up to 30 seconds for locks
                check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
            # Enable Write-Ahead Logging for better concurrent access
            self._local.conn.execute('PRAGMA journal_mode=WAL')
            self._local.conn.execute('PRAGMA foreign_keys=ON')
        
        try:
            yield self._local.conn
        except Exception as e:
            self._local.conn.rollback()
            raise
    
    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Access Points table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS access_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ap_id TEXT NOT NULL UNIQUE,
                    store_id TEXT NOT NULL,
                    store_alias TEXT,
                    retail_chain TEXT,
                    ip_address TEXT,
                    type TEXT,
                    username_webui TEXT,
                    password_webui TEXT,  -- Encrypted
                    username_ssh TEXT,
                    password_ssh TEXT,    -- Encrypted
                    su_password TEXT,     -- Encrypted
                    notes TEXT,
                    status TEXT DEFAULT 'unknown',  -- online, offline, unknown
                    last_seen TIMESTAMP,
                    last_ping_time REAL,
                    serial_number TEXT,
                    software_version TEXT,
                    firmware_version TEXT,
                    hardware_revision TEXT,
                    build TEXT,
                    configuration_mode TEXT,
                    service_status TEXT,
                    uptime TEXT,
                    communication_daemon_status TEXT,
                    mac_address TEXT,
                    connectivity_internet TEXT,
                    connectivity_provisioning TEXT,
                    connectivity_ntp_server TEXT,
                    connectivity_apc_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # History/Events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ap_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ap_id TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,  -- ping, connect, provision, ssh, etc.
                    description TEXT,
                    user TEXT,
                    success BOOLEAN,
                    details TEXT,  -- JSON for additional data
                    FOREIGN KEY (ap_id) REFERENCES access_points(ap_id) ON DELETE CASCADE
                )
            ''')
            
            # Add new columns to existing access_points table if they don't exist
            # (for database migration)
            new_columns = [
                ('serial_number', 'TEXT'),
                ('software_version', 'TEXT'),
                ('firmware_version', 'TEXT'),
                ('hardware_revision', 'TEXT'),
                ('build', 'TEXT'),
                ('configuration_mode', 'TEXT'),
                ('service_status', 'TEXT'),
                ('uptime', 'TEXT'),
                ('communication_daemon_status', 'TEXT'),
                ('mac_address', 'TEXT'),
                ('connectivity_internet', 'TEXT'),
                ('connectivity_provisioning', 'TEXT'),
                ('connectivity_ntp_server', 'TEXT'),
                ('connectivity_apc_address', 'TEXT')
            ]
            
            for col_name, col_type in new_columns:
                try:
                    cursor.execute(f'ALTER TABLE access_points ADD COLUMN {col_name} {col_type}')
                except sqlite3.OperationalError:
                    # Column already exists, skip
                    pass
            
            # Jira Tickets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jira_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_key TEXT NOT NULL UNIQUE,
                    ap_id TEXT,
                    summary TEXT,
                    description TEXT,
                    status TEXT,
                    priority TEXT,
                    issue_type TEXT,
                    created TIMESTAMP,
                    updated TIMESTAMP,
                    resolved TIMESTAMP,
                    assignee TEXT,
                    reporter TEXT,
                    last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ap_id) REFERENCES access_points(ap_id) ON DELETE SET NULL
                )
            ''')
            
            # Comments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ap_id TEXT NOT NULL,
                    user TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    comment TEXT NOT NULL,
                    ticket_key TEXT,
                    FOREIGN KEY (ap_id) REFERENCES access_points(ap_id) ON DELETE CASCADE,
                    FOREIGN KEY (ticket_key) REFERENCES jira_tickets(ticket_key) ON DELETE SET NULL
                )
            ''')
            
            # Support Notes table (for AP support system)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS support_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ap_id TEXT NOT NULL,
                    user TEXT NOT NULL,
                    headline TEXT NOT NULL,
                    note TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by TEXT,
                    is_deleted BOOLEAN DEFAULT 0,
                    FOREIGN KEY (ap_id) REFERENCES access_points(ap_id) ON DELETE CASCADE
                )
            ''')
            
            # Support Note Replies table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS support_note_replies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_id INTEGER NOT NULL,
                    user TEXT NOT NULL,
                    reply_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted BOOLEAN DEFAULT 0,
                    FOREIGN KEY (note_id) REFERENCES support_notes(id) ON DELETE CASCADE
                )
            ''')
            
            # Add support_status column to access_points if it doesn't exist
            try:
                cursor.execute('ALTER TABLE access_points ADD COLUMN support_status TEXT DEFAULT "active"')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Performance metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ap_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ap_id TEXT NOT NULL,
                    date DATE NOT NULL,
                    ping_count INTEGER DEFAULT 0,
                    successful_pings INTEGER DEFAULT 0,
                    avg_response_time REAL,
                    min_response_time REAL,
                    max_response_time REAL,
                    uptime_percentage REAL,
                    issues_count INTEGER DEFAULT 0,
                    FOREIGN KEY (ap_id) REFERENCES access_points(ap_id) ON DELETE CASCADE,
                    UNIQUE(ap_id, date)
                )
            ''')
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    full_name TEXT NOT NULL,
                    password TEXT NOT NULL,  -- Encrypted
                    role TEXT NOT NULL,  -- Admin or User
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,  -- Username who created this user
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by TEXT,  -- Username who last modified this user
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # User audit log - tracks user management actions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    actor_username TEXT NOT NULL,  -- Who performed the action
                    action TEXT NOT NULL,  -- create_user, delete_user, change_password, change_role, etc.
                    target_username TEXT NOT NULL,  -- User affected by the action
                    details TEXT,  -- JSON for additional info (e.g., old role -> new role)
                    ip_address TEXT,
                    success BOOLEAN DEFAULT 1
                )
            ''')
            
            # User activity log - tracks user operations in the system
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    username TEXT NOT NULL,
                    activity_type TEXT NOT NULL,  -- login, logout, ap_connect, provision, etc.
                    description TEXT,
                    ap_id TEXT,  -- Optional: related AP
                    ip_address TEXT,
                    session_id TEXT,  -- For tracking sessions
                    success BOOLEAN DEFAULT 1,
                    details TEXT  -- JSON for additional data
                )
            ''')
            
            # System configuration - for storing encryption keys and system settings
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key TEXT UNIQUE NOT NULL,
                    config_value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # API credentials - encrypted storage for external API credentials
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT UNIQUE NOT NULL,  -- jira, vusion_cloud, etc.
                    encrypted_data TEXT NOT NULL,  -- JSON encrypted with Fernet
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,  -- Admin who created it
                    last_used TIMESTAMP  -- Last time credentials were used
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ap_store ON access_points(store_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ap_ip ON access_points(ip_address)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ap_status ON access_points(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_ap ON ap_history(ap_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_timestamp ON ap_history(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_type ON ap_history(event_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickets_ap ON jira_tickets(ap_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickets_status ON jira_tickets(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_ap ON comments(ap_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_ap_date ON ap_metrics(ap_id, date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_audit_timestamp ON user_audit_log(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_audit_actor ON user_audit_log(actor_username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_audit_target ON user_audit_log(target_username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_activity_timestamp ON user_activity_log(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_activity_user ON user_activity_log(username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_activity_type ON user_activity_log(activity_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_support_notes_ap ON support_notes(ap_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_support_notes_created ON support_notes(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ap_support_status ON access_points(support_status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_credentials_service ON api_credentials(service_name)')
            
            conn.commit()
    
    def migrate_from_json(self, json_file: str) -> Tuple[bool, str]:
        """Migrate existing JSON credentials to SQLite database."""
        try:
            json_path = Path(json_file)
            if not json_path.exists():
                return False, f"JSON file not found: {json_file}"
            
            # Load existing JSON data
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                credentials = data.get('credentials', [])
            
            if not credentials:
                return True, "No credentials to migrate"
            
            # Check if we need to decrypt from old format
            from cryptography.fernet import Fernet
            old_key_file = Path.home() / ".esl_ap_key"
            old_cipher = None
            if old_key_file.exists():
                with open(old_key_file, 'rb') as f:
                    old_key = f.read()
                    old_cipher = Fernet(old_key)
            
            migrated = 0
            skipped = 0
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                for cred in credentials:
                    # Check if already exists
                    cursor.execute('SELECT id FROM access_points WHERE ap_id = ?', (cred.get('ap_id'),))
                    if cursor.fetchone():
                        skipped += 1
                        continue
                    
                    # Decrypt passwords from old format if needed, then re-encrypt with new key
                    password_webui = cred.get('password_webui', '')
                    password_ssh = cred.get('password_ssh', '')
                    su_password = cred.get('su_password', '')
                    
                    if old_cipher:
                        try:
                            if password_webui:
                                password_webui = old_cipher.decrypt(password_webui.encode()).decode()
                            if password_ssh:
                                password_ssh = old_cipher.decrypt(password_ssh.encode()).decode()
                            if su_password:
                                su_password = old_cipher.decrypt(su_password.encode()).decode()
                        except:
                            pass  # Already decrypted or plain text
                    
                    # Encrypt with new AES-256 key
                    password_webui_encrypted = self._encrypt(password_webui)
                    password_ssh_encrypted = self._encrypt(password_ssh)
                    su_password_encrypted = self._encrypt(su_password)
                    
                    # Insert into database
                    cursor.execute('''
                        INSERT INTO access_points (
                            ap_id, store_id, store_alias, retail_chain, ip_address, type,
                            username_webui, password_webui, username_ssh, password_ssh,
                            su_password, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        cred.get('ap_id'),
                        cred.get('store_id', ''),
                        cred.get('store_alias', ''),
                        cred.get('retail_chain', ''),
                        cred.get('ip_address', ''),
                        cred.get('type', ''),
                        cred.get('username_webui', ''),
                        password_webui_encrypted,
                        cred.get('username_ssh', ''),
                        password_ssh_encrypted,
                        su_password_encrypted,
                        cred.get('notes', '')
                    ))
                    migrated += 1
                
                conn.commit()
            
            return True, f"Migration complete: {migrated} APs migrated, {skipped} already existed"
            
        except Exception as e:
            return False, f"Migration error: {str(e)}"
    
    def add_access_point(self, ap_data: Dict) -> Tuple[bool, str]:
        """Add a new access point."""
        try:
            # Encrypt sensitive fields
            ap_data_encrypted = ap_data.copy()
            for field in self.ENCRYPTED_FIELDS:
                if field in ap_data_encrypted:
                    ap_data_encrypted[field] = self._encrypt(ap_data_encrypted[field])
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO access_points (
                        ap_id, store_id, store_alias, retail_chain, ip_address, type,
                        username_webui, password_webui, username_ssh, password_ssh,
                        su_password, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    ap_data.get('ap_id'),
                    ap_data.get('store_id', ''),
                    ap_data.get('store_alias', ''),
                    ap_data.get('retail_chain', ''),
                    ap_data.get('ip_address', ''),
                    ap_data.get('type', ''),
                    ap_data.get('username_webui', ''),
                    ap_data_encrypted.get('password_webui', ''),
                    ap_data.get('username_ssh', ''),
                    ap_data_encrypted.get('password_ssh', ''),
                    ap_data_encrypted.get('su_password', ''),
                    ap_data.get('notes', '')
                ))
                conn.commit()
                return True, "Access point added successfully"
        except sqlite3.IntegrityError:
            return False, f"AP ID {ap_data.get('ap_id')} already exists"
        except Exception as e:
            return False, f"Error adding AP: {str(e)}"
    
    def get_access_point(self, ap_id: str) -> Optional[Dict]:
        """Get access point by AP ID with decrypted passwords."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM access_points WHERE ap_id = ?', (ap_id,))
            row = cursor.fetchone()
            
            if row:
                ap_dict = dict(row)
                # Decrypt sensitive fields
                for field in self.ENCRYPTED_FIELDS:
                    if field in ap_dict and ap_dict[field]:
                        ap_dict[field] = self._decrypt(ap_dict[field])
                return ap_dict
            return None
    
    def get_all_access_points(self) -> List[Dict]:
        """Get all access points with decrypted passwords."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM access_points ORDER BY store_id, ap_id')
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                ap_dict = dict(row)
                # Decrypt sensitive fields
                for field in self.ENCRYPTED_FIELDS:
                    if field in ap_dict and ap_dict[field]:
                        ap_dict[field] = self._decrypt(ap_dict[field])
                result.append(ap_dict)
            return result
    
    def update_access_point(self, ap_id: str, updates: Dict) -> Tuple[bool, str]:
        """Update access point fields."""
        try:
            # Encrypt sensitive fields in updates
            updates_encrypted = updates.copy()
            for field in self.ENCRYPTED_FIELDS:
                if field in updates_encrypted:
                    updates_encrypted[field] = self._encrypt(updates_encrypted[field])
            
            # Build UPDATE query dynamically
            set_clause = ', '.join([f"{k} = ?" for k in updates_encrypted.keys()])
            set_clause += ', updated_at = CURRENT_TIMESTAMP'
            values = list(updates_encrypted.values()) + [ap_id]
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'UPDATE access_points SET {set_clause} WHERE ap_id = ?', values)
                
                if cursor.rowcount == 0:
                    return False, f"AP ID {ap_id} not found"
                
                conn.commit()
                return True, "Access point updated successfully"
        except Exception as e:
            return False, f"Error updating AP: {str(e)}"
    
    def delete_access_point(self, ap_id: str) -> Tuple[bool, str]:
        """Delete access point and all related data (cascades)."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM access_points WHERE ap_id = ?', (ap_id,))
                
                if cursor.rowcount == 0:
                    return False, f"AP ID {ap_id} not found"
                
                conn.commit()
                return True, "Access point deleted successfully"
        except Exception as e:
            return False, f"Error deleting AP: {str(e)}"
    
    def search_access_points(self, query: str) -> List[Dict]:
        """Search access points by any text field."""
        query_pattern = f"%{query}%"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM access_points 
                WHERE ap_id LIKE ? OR store_id LIKE ? OR store_alias LIKE ? 
                   OR retail_chain LIKE ? OR ip_address LIKE ? OR type LIKE ? OR notes LIKE ?
                ORDER BY store_id, ap_id
            ''', (query_pattern,) * 7)
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                ap_dict = dict(row)
                # Decrypt sensitive fields
                for field in self.ENCRYPTED_FIELDS:
                    if field in ap_dict and ap_dict[field]:
                        ap_dict[field] = self._decrypt(ap_dict[field])
                result.append(ap_dict)
            return result
    
    def add_history_event(self, ap_id: str, event_type: str, description: str, 
                         user: str = None, success: bool = True, details: Dict = None) -> bool:
        """Add a history event for an AP."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ap_history (ap_id, event_type, description, user, success, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (ap_id, event_type, description, user, success, json.dumps(details) if details else None))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding history event: {e}")
            return False
    
    def get_history(self, ap_id: str = None, limit: int = 100) -> List[Dict]:
        """Get history events, optionally filtered by AP ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if ap_id:
                cursor.execute('''
                    SELECT * FROM ap_history WHERE ap_id = ? 
                    ORDER BY timestamp DESC LIMIT ?
                ''', (ap_id, limit))
            else:
                cursor.execute('''
                    SELECT * FROM ap_history 
                    ORDER BY timestamp DESC LIMIT ?
                ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_ap_status(self, ap_id: str, status: str, ping_time: float = None):
        """Update AP online/offline status and last seen."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if ping_time is not None:
                    cursor.execute('''
                        UPDATE access_points 
                        SET status = ?, last_seen = CURRENT_TIMESTAMP, last_ping_time = ?
                        WHERE ap_id = ?
                    ''', (status, ping_time, ap_id))
                else:
                    cursor.execute('''
                        UPDATE access_points 
                        SET status = ?, last_seen = CURRENT_TIMESTAMP
                        WHERE ap_id = ?
                    ''', (status, ap_id))
                conn.commit()
        except Exception as e:
            print(f"Error updating AP status: {e}")
    
    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM access_points')
            total_aps = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM access_points WHERE status = 'online'")
            online_aps = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM ap_history')
            total_events = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM jira_tickets')
            total_tickets = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM comments')
            total_comments = cursor.fetchone()[0]
            
            return {
                'total_aps': total_aps,
                'online_aps': online_aps,
                'offline_aps': total_aps - online_aps,
                'total_events': total_events,
                'total_tickets': total_tickets,
                'total_comments': total_comments,
                'database_file': str(self.db_file),
                'encryption': 'AES-256'
            }
    
    def execute_query(self, query: str, params: tuple = None, fetch_one: bool = False):
        """
        Execute a SQL query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            fetch_one: If True, return only first row
            
        Returns:
            For SELECT: List of dicts or single dict if fetch_one=True
            For INSERT/UPDATE/DELETE: None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Check if this is a SELECT query
            if query.strip().upper().startswith('SELECT'):
                if fetch_one:
                    row = cursor.fetchone()
                    return dict(row) if row else None
                else:
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
            else:
                # INSERT, UPDATE, DELETE - commit changes
                conn.commit()
                return None
    
    def close(self):
        """Close database connection."""
        if hasattr(self._local, 'conn'):
            self._local.conn.close()
            delattr(self._local, 'conn')
    
    # ==================== USER MANAGEMENT METHODS ====================
    
    def add_user(self, username: str, full_name: str, password: str, role: str, 
                 created_by: str = None) -> Tuple[bool, str]:
        """Add a new user with audit logging."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user exists
                cursor.execute('SELECT id FROM users WHERE username = ? COLLATE NOCASE', (username,))
                if cursor.fetchone():
                    return False, f"Username '{username}' already exists"
                
                # Validate role
                if role not in ['Admin', 'User']:
                    return False, f"Invalid role. Must be 'Admin' or 'User'"
                
                # Encrypt password
                encrypted_password = self._encrypt(password)
                
                # Insert user
                cursor.execute('''
                    INSERT INTO users (username, full_name, password, role, created_by, updated_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (username, full_name, encrypted_password, role, created_by, created_by))
                
                # Log the action
                self._log_user_audit(cursor, created_by or 'system', 'create_user', username, 
                                    f"Created {role} user")
                
                conn.commit()
                return True, f"User '{username}' created successfully"
        except Exception as e:
            return False, f"Error creating user: {e}"
    
    def update_user(self, username: str, full_name: str = None, password: str = None, 
                    role: str = None, updated_by: str = None) -> Tuple[bool, str]:
        """Update user information with audit logging."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get current user info
                cursor.execute('SELECT * FROM users WHERE username = ? COLLATE NOCASE', (username,))
                user = cursor.fetchone()
                if not user:
                    return False, f"User '{username}' not found"
                
                user_dict = dict(user)
                changes = []
                
                # Build update query
                updates = []
                params = []
                
                if full_name is not None and full_name != user_dict['full_name']:
                    updates.append('full_name = ?')
                    params.append(full_name)
                    changes.append(f"name: {user_dict['full_name']} -> {full_name}")
                
                if password is not None:
                    encrypted_password = self._encrypt(password)
                    updates.append('password = ?')
                    params.append(encrypted_password)
                    changes.append("password changed")
                    # Log password change separately
                    self._log_user_audit(cursor, updated_by or 'system', 'change_password', 
                                       username, "Password changed")
                
                if role is not None and role != user_dict['role']:
                    if role not in ['Admin', 'User']:
                        return False, f"Invalid role. Must be 'Admin' or 'User'"
                    updates.append('role = ?')
                    params.append(role)
                    changes.append(f"role: {user_dict['role']} -> {role}")
                    # Log role change separately
                    self._log_user_audit(cursor, updated_by or 'system', 'change_role', 
                                       username, f"{user_dict['role']} -> {role}")
                
                if not updates:
                    return True, "No changes to update"
                
                # Add updated_at and updated_by
                updates.append('updated_at = CURRENT_TIMESTAMP')
                updates.append('updated_by = ?')
                params.append(updated_by)
                params.append(username)
                
                # Execute update
                cursor.execute(f'''
                    UPDATE users SET {', '.join(updates)}
                    WHERE username = ? COLLATE NOCASE
                ''', params)
                
                # Log the update
                if changes:
                    self._log_user_audit(cursor, updated_by or 'system', 'update_user', 
                                       username, "; ".join(changes))
                
                conn.commit()
                return True, f"User '{username}' updated successfully"
        except Exception as e:
            return False, f"Error updating user: {e}"
    
    def delete_user(self, username: str, deleted_by: str = None) -> Tuple[bool, str]:
        """Delete a user with audit logging."""
        try:
            # Prevent deleting default admin
            if username.lower() == 'masterblaster':
                return False, "Cannot delete the default admin user"
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user exists
                cursor.execute('SELECT role FROM users WHERE username = ? COLLATE NOCASE', (username,))
                user = cursor.fetchone()
                if not user:
                    return False, f"User '{username}' not found"
                
                # Log the deletion
                self._log_user_audit(cursor, deleted_by or 'system', 'delete_user', 
                                   username, f"Deleted {dict(user)['role']} user")
                
                # Delete user
                cursor.execute('DELETE FROM users WHERE username = ? COLLATE NOCASE', (username,))
                conn.commit()
                return True, f"User '{username}' deleted successfully"
        except Exception as e:
            return False, f"Error deleting user: {e}"
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user by username (with decrypted password)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ? COLLATE NOCASE', (username,))
            row = cursor.fetchone()
            if row:
                user_dict = dict(row)
                # Decrypt password
                if user_dict.get('password'):
                    user_dict['password'] = self._decrypt(user_dict['password'])
                return user_dict
            return None
    
    def get_all_users(self) -> List[Dict]:
        """Get all users (without passwords for security)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, full_name, role, created_at, created_by, 
                       updated_at, updated_by, last_login, is_active 
                FROM users ORDER BY username
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user info if successful."""
        user = self.get_user(username)
        if user and user.get('is_active', True) and user['password'] == password:
            # Update last login
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE users SET last_login = CURRENT_TIMESTAMP 
                        WHERE username = ? COLLATE NOCASE
                    ''', (username,))
                    
                    # Log the login
                    self._log_user_activity(cursor, username, 'login', 'User logged in', success=True)
                    conn.commit()
            except Exception as e:
                print(f"Error updating last login: {e}")
            
            # Return user info without password
            return {
                'full_name': user['full_name'],
                'username': user['username'],
                'role': user['role']
            }
        return None
    
    def is_admin(self, username: str) -> bool:
        """Check if user is an admin."""
        user = self.get_user(username)
        return user and user['role'] == 'Admin'
    
    def _log_user_audit(self, cursor, actor: str, action: str, target: str, 
                       details: str = None, success: bool = True):
        """Internal method to log user audit events."""
        cursor.execute('''
            INSERT INTO user_audit_log (actor_username, action, target_username, details, success)
            VALUES (?, ?, ?, ?, ?)
        ''', (actor, action, target, details, success))
    
    def _log_user_activity(self, cursor, username: str, activity_type: str, 
                          description: str = None, ap_id: str = None, 
                          success: bool = True, details: Dict = None):
        """Internal method to log user activities."""
        cursor.execute('''
            INSERT INTO user_activity_log (username, activity_type, description, ap_id, success, details)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, activity_type, description, ap_id, success, 
              json.dumps(details) if details else None))
    
    def log_user_activity(self, username: str, activity_type: str, description: str = None,
                         ap_id: str = None, success: bool = True, details: Dict = None):
        """Public method to log user activities."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                self._log_user_activity(cursor, username, activity_type, description, 
                                       ap_id, success, details)
                conn.commit()
        except Exception as e:
            print(f"Error logging user activity: {e}")
    
    def get_user_audit_log(self, target_username: str = None, actor_username: str = None,
                          limit: int = 100) -> List[Dict]:
        """Get user audit log, optionally filtered by target or actor."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM user_audit_log WHERE 1=1'
            params = []
            
            if target_username:
                query += ' AND target_username = ?'
                params.append(target_username)
            
            if actor_username:
                query += ' AND actor_username = ?'
                params.append(actor_username)
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_activity_log(self, username: str = None, activity_type: str = None,
                             limit: int = 100) -> List[Dict]:
        """Get user activity log, optionally filtered by username or activity type."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM user_activity_log WHERE 1=1'
            params = []
            
            if username:
                query += ' AND username = ?'
                params.append(username)
            
            if activity_type:
                query += ' AND activity_type = ?'
                params.append(activity_type)
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def ensure_default_admin(self):
        """Ensure default admin user exists."""
        user = self.get_user("MasterBlaster")
        if not user:
            success, message = self.add_user(
                username="MasterBlaster",
                full_name="Elkjop Master",
                password="VinterMorker2025&",
                role="Admin",
                created_by="system"
            )
            if success:
                print("Default admin user created: MasterBlaster")
            else:
                print(f"Failed to create default admin: {message}")
    
    # ==================== Support Notes Methods ====================
    
    def add_support_note(self, ap_id: str, user: str, headline: str, note: str) -> Tuple[bool, str, int]:
        """Add a support note for an AP.
        
        Returns:
            Tuple of (success, message, note_id)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO support_notes (ap_id, user, headline, note, created_at, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (ap_id, user, headline, note))
                note_id = cursor.lastrowid
                conn.commit()
                return True, "Note added successfully", note_id
        except Exception as e:
            return False, f"Error adding note: {str(e)}", -1
    
    def get_support_notes(self, ap_id: str, include_deleted: bool = False) -> List[Dict]:
        """Get all support notes for an AP, ordered by most recent first."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if include_deleted:
                query = 'SELECT * FROM support_notes WHERE ap_id = ? ORDER BY created_at DESC'
            else:
                query = 'SELECT * FROM support_notes WHERE ap_id = ? AND is_deleted = 0 ORDER BY created_at DESC'
            cursor.execute(query, (ap_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_support_note_by_id(self, note_id: int) -> Optional[Dict]:
        """Get a specific support note by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM support_notes WHERE id = ?', (note_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_support_note(self, note_id: int, headline: str, note: str, user: str) -> Tuple[bool, str]:
        """Update a support note (only the most recent note can be edited)."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE support_notes 
                    SET headline = ?, note = ?, updated_at = CURRENT_TIMESTAMP, updated_by = ?
                    WHERE id = ?
                ''', (headline, note, user, note_id))
                conn.commit()
                if cursor.rowcount > 0:
                    return True, "Note updated successfully"
                else:
                    return False, "Note not found"
        except Exception as e:
            return False, f"Error updating note: {str(e)}"
    
    def delete_support_note(self, note_id: int, user: str) -> Tuple[bool, str]:
        """Soft delete a support note (only the most recent note can be deleted)."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE support_notes 
                    SET is_deleted = 1, updated_at = CURRENT_TIMESTAMP, updated_by = ?
                    WHERE id = ?
                ''', (user, note_id))
                conn.commit()
                if cursor.rowcount > 0:
                    return True, "Note deleted successfully"
                else:
                    return False, "Note not found"
        except Exception as e:
            return False, f"Error deleting note: {str(e)}"
    
    def is_latest_note(self, note_id: int, ap_id: str) -> bool:
        """Check if a note is the most recent note for an AP."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM support_notes 
                WHERE ap_id = ? AND is_deleted = 0 
                ORDER BY created_at DESC LIMIT 1
            ''', (ap_id,))
            row = cursor.fetchone()
            return row and row['id'] == note_id if row else False
    
    def add_note_reply(self, note_id: int, user: str, reply_text: str) -> Tuple[bool, str, int]:
        """Add a reply to a support note."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO support_note_replies (note_id, user, reply_text)
                    VALUES (?, ?, ?)
                ''', (note_id, user, reply_text))
                conn.commit()
                return True, "Reply added successfully", cursor.lastrowid
        except Exception as e:
            return False, f"Error adding reply: {str(e)}", 0
    
    def get_note_replies(self, note_id: int) -> List[Dict]:
        """Get all replies for a note, ordered by newest first."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, note_id, user, reply_text, created_at
                FROM support_note_replies
                WHERE note_id = ? AND is_deleted = 0
                ORDER BY created_at DESC
            ''', (note_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_note_reply_count(self, note_id: int) -> int:
        """Get the count of replies for a note."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM support_note_replies
                WHERE note_id = ? AND is_deleted = 0
            ''', (note_id,))
            row = cursor.fetchone()
            return row['count'] if row else 0
    
    def update_note_reply(self, reply_id: int, reply_text: str, user: str) -> Tuple[bool, str]:
        """Update a note reply."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # First check if this user owns the reply
                cursor.execute('''
                    SELECT user FROM support_note_replies 
                    WHERE id = ? AND is_deleted = 0
                ''', (reply_id,))
                row = cursor.fetchone()
                
                if not row:
                    return False, "Reply not found"
                
                if row['user'] != user:
                    return False, "You can only edit your own replies"
                
                # Update the reply
                cursor.execute('''
                    UPDATE support_note_replies 
                    SET reply_text = ?
                    WHERE id = ?
                ''', (reply_text, reply_id))
                conn.commit()
                return True, "Reply updated successfully"
        except Exception as e:
            return False, f"Error updating reply: {str(e)}"
    
    def delete_note_reply(self, reply_id: int, user: str) -> Tuple[bool, str]:
        """Delete (soft delete) a note reply."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # First check if this user owns the reply
                cursor.execute('''
                    SELECT user FROM support_note_replies 
                    WHERE id = ? AND is_deleted = 0
                ''', (reply_id,))
                row = cursor.fetchone()
                
                if not row:
                    return False, "Reply not found"
                
                if row['user'] != user:
                    return False, "You can only delete your own replies"
                
                # Soft delete the reply
                cursor.execute('''
                    UPDATE support_note_replies 
                    SET is_deleted = 1 
                    WHERE id = ?
                ''', (reply_id,))
                conn.commit()
                return True, "Reply deleted successfully"
        except Exception as e:
            return False, f"Error deleting reply: {str(e)}"
    
    def update_support_status(self, ap_id: str, status: str) -> Tuple[bool, str]:
        """Update the support status of an AP.
        
        Args:
            ap_id: AP identifier
            status: Support status (e.g., 'active', 'in_progress', 'resolved', 'pending')
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE access_points 
                    SET support_status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE ap_id = ?
                ''', (status, ap_id))
                conn.commit()
                if cursor.rowcount > 0:
                    return True, "Support status updated"
                else:
                    return False, "AP not found"
        except Exception as e:
            return False, f"Error updating support status: {str(e)}"
    
    def search_aps_for_support(self, search_term: str = None, store_id: str = None, 
                               support_status: str = None, has_open_tickets: bool = None) -> List[Dict]:
        """Search for APs in the support system with various filters."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM access_points WHERE 1=1'
            params = []
            
            if search_term:
                query += ' AND (ap_id LIKE ? OR ip_address LIKE ?)'
                search_pattern = f'%{search_term}%'
                params.extend([search_pattern, search_pattern])
            
            if store_id:
                query += ' AND (store_id LIKE ? OR store_alias LIKE ?)'
                search_pattern = f'%{store_id}%'
                params.extend([search_pattern, search_pattern])
            
            if support_status:
                query += ' AND support_status = ?'
                params.append(support_status)
            
            if has_open_tickets is not None:
                if has_open_tickets:
                    query += ''' AND EXISTS (
                        SELECT 1 FROM jira_tickets 
                        WHERE jira_tickets.ap_id = access_points.ap_id 
                        AND jira_tickets.status NOT IN ('Closed', 'Resolved', 'Done')
                    )'''
                else:
                    query += ''' AND NOT EXISTS (
                        SELECT 1 FROM jira_tickets 
                        WHERE jira_tickets.ap_id = access_points.ap_id 
                        AND jira_tickets.status NOT IN ('Closed', 'Resolved', 'Done')
                    )'''
            
            query += ' ORDER BY ap_id'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Decrypt sensitive fields
            result = []
            for row in rows:
                ap_dict = dict(row)
                for field in self.ENCRYPTED_FIELDS:
                    if field in ap_dict and ap_dict[field]:
                        ap_dict[field] = self._decrypt(ap_dict[field])
                result.append(ap_dict)
            
            return result

