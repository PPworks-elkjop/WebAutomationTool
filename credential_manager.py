"""
ESL AP Credential Manager - Database for storing and managing AP credentials
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
from cryptography.fernet import Fernet
import base64
import hashlib

class CredentialManager:
    """Manages ESL AP credentials with import/export and search capabilities."""
    
    # Password fields that should be encrypted
    PASSWORD_FIELDS = ['password_webui', 'password_ssh', 'su_password']
    
    def __init__(self, db_file: str = None):
        if db_file is None:
            db_file = Path.home() / ".esl_ap_credentials.json"
        self.db_file = Path(db_file)
        self.key_file = Path.home() / ".esl_ap_key"
        self.credentials = []
        self._cipher = self._get_cipher()
        self.load()
    
    def _get_cipher(self):
        """Get or create encryption cipher."""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate a new key based on machine-specific info
            # This makes it machine-specific but doesn't require user input
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
    
    def load(self):
        """Load credentials from database file and decrypt passwords."""
        if self.db_file.exists():
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    encrypted_creds = data.get('credentials', [])
                    # Decrypt password fields
                    self.credentials = []
                    for cred in encrypted_creds:
                        decrypted_cred = cred.copy()
                        for field in self.PASSWORD_FIELDS:
                            if field in decrypted_cred:
                                decrypted_cred[field] = self._decrypt_password(decrypted_cred[field])
                        self.credentials.append(decrypted_cred)
                    return True
            except Exception as e:
                print(f"Error loading credentials: {e}")
                self.credentials = []
                return False
        else:
            self.credentials = []
            return True
    
    def save(self):
        """Save credentials to database file with encrypted passwords."""
        try:
            # Encrypt password fields before saving
            encrypted_creds = []
            for cred in self.credentials:
                encrypted_cred = cred.copy()
                for field in self.PASSWORD_FIELDS:
                    if field in encrypted_cred:
                        encrypted_cred[field] = self._encrypt_password(encrypted_cred[field])
                encrypted_creds.append(encrypted_cred)
            
            data = {
                'credentials': encrypted_creds,
                'last_modified': datetime.now().isoformat()
            }
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving credentials: {e}")
            return False
    
    def import_from_excel(self, excel_file: str) -> tuple:
        """Import credentials from Excel file."""
        try:
            df = pd.read_excel(excel_file)
            
            # Expected columns (IP Address is optional, will be handled if present)
            required_columns = [
                'Retail Chain', 'Store ID', 'Store Alias', 'AP ID', 'Type',
                'Username Web UI', 'Password Web UI', 'Username SSH',
                'Password SSH', 'SU Password', 'Notes'
            ]
            
            # Check if all required columns exist
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return False, f"Missing columns: {', '.join(missing_columns)}"
            
            # Import data
            imported_count = 0
            updated_count = 0
            
            for _, row in df.iterrows():
                # Skip empty rows - only AP ID, web password, and SSH password are mandatory
                if pd.isna(row['AP ID']) or pd.isna(row['Password Web UI']) or pd.isna(row['Password SSH']):
                    continue
                credential = {
                    'retail_chain': str(row['Retail Chain']) if not pd.isna(row['Retail Chain']) else '',
                    'store_id': str(row['Store ID']),
                    'store_alias': str(row['Store Alias']) if not pd.isna(row['Store Alias']) else '',
                    'ap_id': str(row['AP ID']),
                    'ip_address': str(row['IP Address']) if 'IP Address' in df.columns and not pd.isna(row['IP Address']) else '',
                    'type': str(row['Type']) if not pd.isna(row['Type']) else '',
                    'username_webui': str(row['Username Web UI']) if not pd.isna(row['Username Web UI']) else '',
                    'password_webui': str(row['Password Web UI']) if not pd.isna(row['Password Web UI']) else '',
                    'username_ssh': str(row['Username SSH']) if not pd.isna(row['Username SSH']) else '',
                    'password_ssh': str(row['Password SSH']) if not pd.isna(row['Password SSH']) else '',
                    'su_password': str(row['SU Password']) if not pd.isna(row['SU Password']) else '',
                    'notes': str(row['Notes']) if not pd.isna(row['Notes']) else '',
                    'last_modified': datetime.now().isoformat()
                }
                
                # Check if credential already exists (by ap_id only, since store_id might be empty)
                existing = self.find_by_ap_id(credential['ap_id'])
                if existing:
                    # Update existing - find the exact one to update
                    for i, cred in enumerate(self.credentials):
                        if cred['ap_id'] == credential['ap_id']:
                            self.credentials[i] = credential
                            updated_count += 1
                            break
                else:
                    # Add new
                    self.credentials.append(credential)
                    imported_count += 1
            
            self.save()
            return True, f"Imported {imported_count} new, updated {updated_count} existing credentials"
            
        except Exception as e:
            return False, f"Error importing Excel: {str(e)}"
    
    def export_to_excel(self, excel_file: str) -> tuple:
        """Export credentials to Excel file."""
        try:
            if not self.credentials:
                return False, "No credentials to export"
            
            # Convert to DataFrame
            df_data = []
            for cred in self.credentials:
                df_data.append({
                    'Retail Chain': cred.get('retail_chain', ''),
                    'Store ID': cred.get('store_id', ''),
                    'Store Alias': cred.get('store_alias', ''),
                    'AP ID': cred.get('ap_id', ''),
                    'IP Address': cred.get('ip_address', ''),
                    'Type': cred.get('type', ''),
                    'Username Web UI': cred.get('username_webui', ''),
                    'Password Web UI': cred.get('password_webui', ''),
                    'Username SSH': cred.get('username_ssh', ''),
                    'Password SSH': cred.get('password_ssh', ''),
                    'SU Password': cred.get('su_password', ''),
                    'Notes': cred.get('notes', '')
                })
            
            df = pd.DataFrame(df_data)
            df.to_excel(excel_file, index=False, engine='openpyxl')
            
            return True, f"Exported {len(self.credentials)} credentials to {excel_file}"
            
        except Exception as e:
            return False, f"Error exporting Excel: {str(e)}"
    
    def add_credential(self, credential: Dict) -> tuple:
        """Add a new credential."""
        try:
            # Validate required fields
            if not credential.get('store_id') or not credential.get('ap_id'):
                return False, "Store ID and AP ID are required"
            
            # Check if already exists
            existing = self.find_by_store_and_ap(credential['store_id'], credential['ap_id'])
            if existing:
                return False, f"Credential already exists for Store {credential['store_id']}, AP {credential['ap_id']}"
            
            credential['last_modified'] = datetime.now().isoformat()
            self.credentials.append(credential)
            self.save()
            return True, "Credential added successfully"
            
        except Exception as e:
            return False, f"Error adding credential: {str(e)}"
    
    def update_credential(self, store_id: str, ap_id: str, updated_data: Dict) -> tuple:
        """Update an existing credential."""
        try:
            for i, cred in enumerate(self.credentials):
                if cred['store_id'] == store_id and cred['ap_id'] == ap_id:
                    updated_data['last_modified'] = datetime.now().isoformat()
                    self.credentials[i] = updated_data
                    self.save()
                    return True, "Credential updated successfully"
            
            return False, f"Credential not found for Store {store_id}, AP {ap_id}"
            
        except Exception as e:
            return False, f"Error updating credential: {str(e)}"
    
    def delete_credential(self, store_id: str, ap_id: str) -> tuple:
        """Delete a credential."""
        try:
            for i, cred in enumerate(self.credentials):
                if cred['store_id'] == store_id and cred['ap_id'] == ap_id:
                    self.credentials.pop(i)
                    self.save()
                    return True, "Credential deleted successfully"
            
            return False, f"Credential not found for Store {store_id}, AP {ap_id}"
            
        except Exception as e:
            return False, f"Error deleting credential: {str(e)}"
    
    def find_by_store_id(self, store_id: str) -> List[Dict]:
        """Find all credentials for a store."""
        return [cred for cred in self.credentials if cred['store_id'].lower() == store_id.lower()]
    
    def find_by_ap_id(self, ap_id: str) -> Optional[Dict]:
        """Find credential by AP ID."""
        for cred in self.credentials:
            if cred['ap_id'].lower() == ap_id.lower():
                return cred
        return None
    
    def find_by_store_and_ap(self, store_id: str, ap_id: str) -> Optional[Dict]:
        """Find credential by store ID and AP ID."""
        for cred in self.credentials:
            if cred['store_id'].lower() == store_id.lower() and cred['ap_id'].lower() == ap_id.lower():
                return cred
        return None
    
    def search(self, query: str) -> List[Dict]:
        """Search credentials by any field."""
        query = query.lower()
        results = []
        
        for cred in self.credentials:
            # Search in all string fields
            if (query in cred.get('retail_chain', '').lower() or
                query in cred.get('store_id', '').lower() or
                query in cred.get('store_alias', '').lower() or
                query in cred.get('ap_id', '').lower() or
                query in cred.get('ip_address', '').lower() or
                query in cred.get('type', '').lower() or
                query in cred.get('notes', '').lower()):
                results.append(cred)
        
        return results
    
    def get_all(self) -> List[Dict]:
        """Get all credentials."""
        return self.credentials.copy()
    
    def count(self) -> int:
        """Get total number of credentials."""
        return len(self.credentials)
