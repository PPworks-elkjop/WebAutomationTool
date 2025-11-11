"""
User Manager - Authentication and user management for ESL AP Helper

Features:
- User authentication with encrypted passwords
- Role-based access (Admin/User)
- Default admin account creation
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from cryptography.fernet import Fernet
import base64
import hashlib

class UserManager:
    """Manages users with authentication and role-based access."""
    
    ROLE_ADMIN = "Admin"
    ROLE_USER = "User"
    
    def __init__(self, db_file: str = None):
        if db_file is None:
            db_file = Path.home() / ".esl_ap_users.json"
        self.db_file = Path(db_file)
        self.key_file = Path.home() / ".esl_ap_user_key"
        self.users = []
        self._cipher = self._get_cipher()
        self.load()
        self._ensure_default_admin()
    
    def _get_cipher(self):
        """Get or create encryption cipher."""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate a new key based on machine-specific info
            machine_id = str(Path.home())
            key = base64.urlsafe_b64encode(hashlib.sha256(machine_id.encode()).digest())
            with open(self.key_file, 'wb') as f:
                f.write(key)
        return Fernet(key)
    
    def _encrypt_password(self, password: str) -> str:
        """Encrypt a password."""
        if not password:
            return ''
        return self._cipher.encrypt(password.encode()).decode()
    
    def _decrypt_password(self, encrypted: str) -> str:
        """Decrypt a password."""
        if not encrypted:
            return ''
        try:
            return self._cipher.decrypt(encrypted.encode()).decode()
        except Exception:
            # If decryption fails, return as-is (for backward compatibility)
            return encrypted
    
    def _ensure_default_admin(self):
        """Ensure default admin user exists."""
        if not self.find_by_username("MasterBlaster"):
            default_admin = {
                'full_name': 'Elkjop Master',
                'username': 'MasterBlaster',
                'password': 'VinterMorker2025&',
                'role': self.ROLE_ADMIN,
                'created_at': datetime.now().isoformat(),
                'last_modified': datetime.now().isoformat()
            }
            self.users.append(default_admin)
            self.save()
            print("Default admin user created: MasterBlaster")
    
    def load(self):
        """Load users from database file and decrypt passwords."""
        if self.db_file.exists():
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    encrypted_users = data.get('users', [])
                    # Decrypt password fields
                    self.users = []
                    for user in encrypted_users:
                        decrypted_user = user.copy()
                        if 'password' in decrypted_user:
                            decrypted_user['password'] = self._decrypt_password(decrypted_user['password'])
                        self.users.append(decrypted_user)
                    return True
            except Exception as e:
                print(f"Error loading users: {e}")
                self.users = []
                return False
        else:
            self.users = []
            return True
    
    def save(self):
        """Save users to database file with encrypted passwords."""
        try:
            # Encrypt password fields before saving
            encrypted_users = []
            for user in self.users:
                encrypted_user = user.copy()
                if 'password' in encrypted_user:
                    encrypted_user['password'] = self._encrypt_password(encrypted_user['password'])
                encrypted_users.append(encrypted_user)
            
            data = {
                'users': encrypted_users,
                'last_modified': datetime.now().isoformat()
            }
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving users: {e}")
            return False
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user info if successful."""
        user = self.find_by_username(username)
        if user and user['password'] == password:
            # Return user info without password
            return {
                'full_name': user['full_name'],
                'username': user['username'],
                'role': user['role']
            }
        return None
    
    def find_by_username(self, username: str) -> Optional[Dict]:
        """Find user by username."""
        for user in self.users:
            if user['username'].lower() == username.lower():
                return user
        return None
    
    def add_user(self, full_name: str, username: str, password: str, role: str) -> tuple:
        """Add a new user."""
        # Check if username already exists
        if self.find_by_username(username):
            return False, f"Username '{username}' already exists"
        
        # Validate role
        if role not in [self.ROLE_ADMIN, self.ROLE_USER]:
            return False, f"Invalid role. Must be '{self.ROLE_ADMIN}' or '{self.ROLE_USER}'"
        
        # Create new user
        new_user = {
            'full_name': full_name,
            'username': username,
            'password': password,
            'role': role,
            'created_at': datetime.now().isoformat(),
            'last_modified': datetime.now().isoformat()
        }
        
        self.users.append(new_user)
        self.save()
        return True, f"User '{username}' added successfully"
    
    def update_user(self, username: str, full_name: str = None, password: str = None, role: str = None) -> tuple:
        """Update user information."""
        user = self.find_by_username(username)
        if not user:
            return False, f"User '{username}' not found"
        
        # Find user in list and update
        for i, u in enumerate(self.users):
            if u['username'].lower() == username.lower():
                if full_name is not None:
                    self.users[i]['full_name'] = full_name
                if password is not None:
                    self.users[i]['password'] = password
                if role is not None:
                    if role not in [self.ROLE_ADMIN, self.ROLE_USER]:
                        return False, f"Invalid role. Must be '{self.ROLE_ADMIN}' or '{self.ROLE_USER}'"
                    self.users[i]['role'] = role
                self.users[i]['last_modified'] = datetime.now().isoformat()
                break
        
        self.save()
        return True, f"User '{username}' updated successfully"
    
    def delete_user(self, username: str) -> tuple:
        """Delete a user."""
        # Prevent deleting the default admin
        if username.lower() == "masterblaster":
            return False, "Cannot delete the default admin user"
        
        user = self.find_by_username(username)
        if not user:
            return False, f"User '{username}' not found"
        
        self.users = [u for u in self.users if u['username'].lower() != username.lower()]
        self.save()
        return True, f"User '{username}' deleted successfully"
    
    def get_all_users(self) -> List[Dict]:
        """Get all users (without passwords for security)."""
        return [
            {
                'full_name': u['full_name'],
                'username': u['username'],
                'role': u['role'],
                'created_at': u.get('created_at', ''),
                'last_modified': u.get('last_modified', '')
            }
            for u in self.users
        ]
    
    def count(self) -> int:
        """Return total number of users."""
        return len(self.users)
    
    def is_admin(self, username: str) -> bool:
        """Check if user is an admin."""
        user = self.find_by_username(username)
        return user and user['role'] == self.ROLE_ADMIN


if __name__ == "__main__":
    # Test the user manager
    manager = UserManager()
    print(f"Total users: {manager.count()}")
    print("\nUsers:")
    for user in manager.get_all_users():
        print(f"  {user['full_name']} ({user['username']}) - {user['role']}")
