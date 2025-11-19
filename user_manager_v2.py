"""
User Manager V2 - Database-backed authentication with audit logging

Features:
- SQLite database backend with encryption
- Role-based access (Admin/User)
- Comprehensive audit logging
- Track who created/modified users
- Activity logging
- Default admin account creation
"""

from typing import List, Dict, Optional
from database_manager import DatabaseManager
from pathlib import Path

class UserManager:
    """Manages users with authentication, role-based access, and audit logging."""
    
    ROLE_ADMIN = "Admin"
    ROLE_USER = "User"
    
    def __init__(self, db_file: str = None):
        """Initialize user manager with database backend."""
        if db_file is None:
            db_file = Path.home() / ".vera_database.db"
        self.db = DatabaseManager(str(db_file))
        self._ensure_default_admin()
        self._migrate_from_json()
    
    def _ensure_default_admin(self):
        """Ensure default admin user exists."""
        self.db.ensure_default_admin()
    
    def _migrate_from_json(self):
        """Migrate users from old JSON file to database if needed."""
        old_json_file = Path.home() / ".esl_ap_users.json"
        if not old_json_file.exists():
            return
        
        try:
            import json
            with open(old_json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                users = data.get('users', [])
            
            if not users:
                return
            
            # Check if migration already done
            existing_users = self.db.get_all_users()
            if len(existing_users) > 1:  # More than just default admin
                return
            
            print(f"Migrating {len(users)} users from JSON to database...")
            
            # Migrate users
            for user in users:
                username = user.get('username')
                # Skip if already exists
                if self.db.get_user(username):
                    continue
                
                # Decrypt password from old format if encrypted
                password = user.get('password', '')
                try:
                    # Try to decrypt with old key
                    from cryptography.fernet import Fernet
                    import base64
                    import hashlib
                    old_key_file = Path.home() / ".esl_ap_user_key"
                    if old_key_file.exists():
                        with open(old_key_file, 'rb') as f:
                            old_key = f.read()
                        old_cipher = Fernet(old_key)
                        try:
                            password = old_cipher.decrypt(password.encode()).decode()
                        except:
                            pass  # Password might not be encrypted
                except:
                    pass
                
                # Add user to database
                success, message = self.db.add_user(
                    username=username,
                    full_name=user.get('full_name', username),
                    password=password,
                    role=user.get('role', self.ROLE_USER),
                    created_by='migration'
                )
                
                if success:
                    print(f"  Migrated user: {username}")
                else:
                    print(f"  Failed to migrate {username}: {message}")
            
            # Backup old JSON file
            backup_file = old_json_file.with_suffix('.json.backup')
            old_json_file.rename(backup_file)
            print(f"Migration complete. Old file backed up to {backup_file}")
            
        except Exception as e:
            print(f"Error during user migration: {e}")
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate user and return user info if successful.
        Also logs the login event.
        """
        return self.db.authenticate_user(username, password)
    
    def find_by_username(self, username: str) -> Optional[Dict]:
        """Find user by username (with decrypted password)."""
        return self.db.get_user(username)
    
    def add_user(self, full_name: str, username: str, password: str, role: str,
                email: str = None, is_active: bool = True, created_by: str = None) -> tuple:
        """Add a new user with audit logging."""
        return self.db.add_user(username, full_name, password, role, email, created_by, is_active)
    
    def update_user(self, username: str, full_name: str = None, password: str = None, 
                   role: str = None, email: str = None, is_active: bool = None, 
                   updated_by: str = None) -> tuple:
        """Update user information with audit logging."""
        return self.db.update_user(username, full_name, password, role, email, is_active, updated_by)
    
    def delete_user(self, username: str, deleted_by: str = None) -> tuple:
        """Delete a user with audit logging."""
        return self.db.delete_user(username, deleted_by)
    
    def get_all_users(self) -> List[Dict]:
        """Get all users (without passwords for security)."""
        return self.db.get_all_users()
    
    def count(self) -> int:
        """Return total number of users."""
        return len(self.db.get_all_users())
    
    def is_admin(self, username: str) -> bool:
        """Check if user is an admin."""
        return self.db.is_admin(username)
    
    def log_activity(self, username: str, activity_type: str, description: str = None,
                    ap_id: str = None, success: bool = True, details: Dict = None):
        """Log a user activity."""
        self.db.log_user_activity(username, activity_type, description, ap_id, success, details)
    
    def get_user_audit_log(self, target_username: str = None, actor_username: str = None,
                          limit: int = 100) -> List[Dict]:
        """Get user audit log (who created/modified which users)."""
        return self.db.get_user_audit_log(target_username, actor_username, limit)
    
    def get_user_activity_log(self, username: str = None, activity_type: str = None,
                             limit: int = 100) -> List[Dict]:
        """Get user activity log (what users did in the system)."""
        return self.db.get_user_activity_log(username, activity_type, limit)


if __name__ == "__main__":
    # Test the user manager
    manager = UserManager()
    print(f"Total users: {manager.count()}")
    print("\nUsers:")
    for user in manager.get_all_users():
        print(f"  {user['full_name']} ({user['username']}) - {user['role']}")
    
    # Test audit log
    print("\nRecent audit events:")
    for event in manager.get_user_audit_log(limit=5):
        print(f"  {event['timestamp']}: {event['actor_username']} -> {event['action']} -> {event['target_username']}")
