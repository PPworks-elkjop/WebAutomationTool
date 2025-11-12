"""
VERA Credential Manager V2 - SQLite-based with backward compatibility
Drop-in replacement for the JSON-based credential_manager.py

This wrapper provides the same API as the old CredentialManager but uses
the new SQLite database backend for better performance and concurrent access.
"""

from typing import List, Dict, Optional
from database_manager import DatabaseManager
from pathlib import Path
import pandas as pd
from datetime import datetime

class CredentialManager:
    """
    Credential Manager with SQLite backend.
    Maintains API compatibility with the old JSON-based version.
    """
    
    def __init__(self, db_file: str = None):
        self.db = DatabaseManager(db_file)
        self._auto_migrate()
    
    def _auto_migrate(self):
        """Automatically migrate from JSON if it exists and database is empty."""
        stats = self.db.get_database_stats()
        if stats['total_aps'] == 0:
            # Check for old JSON file
            old_json = Path.home() / ".esl_ap_credentials.json"
            if old_json.exists():
                print("Detected old JSON credentials file. Migrating to SQLite...")
                success, message = self.db.migrate_from_json(str(old_json))
                if success:
                    print(f"✓ {message}")
                    # Backup the old JSON file
                    backup_path = old_json.with_suffix('.json.backup')
                    old_json.rename(backup_path)
                    print(f"✓ Old JSON file backed up to: {backup_path}")
                else:
                    print(f"✗ Migration failed: {message}")
    
    def load(self):
        """Load credentials (no-op for backward compatibility)."""
        return True
    
    def save(self):
        """Save credentials (no-op for backward compatibility)."""
        return True
    
    def import_from_excel(self, excel_file: str) -> tuple:
        """Import credentials from Excel file."""
        try:
            df = pd.read_excel(excel_file)
            
            required_columns = [
                'Retail Chain', 'Store ID', 'Store Alias', 'AP ID', 'Type',
                'Username Web UI', 'Password Web UI', 'Username SSH',
                'Password SSH', 'SU Password', 'Notes'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return False, f"Missing columns: {', '.join(missing_columns)}"
            
            imported_count = 0
            updated_count = 0
            
            for _, row in df.iterrows():
                if pd.isna(row['AP ID']) or pd.isna(row['Password Web UI']) or pd.isna(row['Password SSH']):
                    continue
                
                ap_data = {
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
                }
                
                existing = self.find_by_ap_id(ap_data['ap_id'])
                if existing:
                    success, msg = self.db.update_access_point(ap_data['ap_id'], ap_data)
                    if success:
                        updated_count += 1
                else:
                    success, msg = self.db.add_access_point(ap_data)
                    if success:
                        imported_count += 1
            
            return True, f"Imported {imported_count} new, updated {updated_count} existing credentials"
            
        except Exception as e:
            return False, f"Error importing Excel: {str(e)}"
    
    def export_to_excel(self, excel_file: str) -> tuple:
        """Export credentials to Excel file."""
        try:
            aps = self.get_all()
            if not aps:
                return False, "No credentials to export"
            
            df_data = []
            for ap in aps:
                df_data.append({
                    'Retail Chain': ap.get('retail_chain', ''),
                    'Store ID': ap.get('store_id', ''),
                    'Store Alias': ap.get('store_alias', ''),
                    'AP ID': ap.get('ap_id', ''),
                    'IP Address': ap.get('ip_address', ''),
                    'Type': ap.get('type', ''),
                    'Username Web UI': ap.get('username_webui', ''),
                    'Password Web UI': ap.get('password_webui', ''),
                    'Username SSH': ap.get('username_ssh', ''),
                    'Password SSH': ap.get('password_ssh', ''),
                    'SU Password': ap.get('su_password', ''),
                    'Notes': ap.get('notes', '')
                })
            
            df = pd.DataFrame(df_data)
            df.to_excel(excel_file, index=False, engine='openpyxl')
            
            return True, f"Exported {len(aps)} credentials to {excel_file}"
            
        except Exception as e:
            return False, f"Error exporting Excel: {str(e)}"
    
    def add_credential(self, credential: Dict) -> tuple:
        """Add a new credential."""
        return self.db.add_access_point(credential)
    
    def update_credential(self, store_id: str, ap_id: str, updated_data: Dict) -> tuple:
        """Update an existing credential."""
        return self.db.update_access_point(ap_id, updated_data)
    
    def delete_credential(self, store_id: str, ap_id: str) -> tuple:
        """Delete a credential."""
        return self.db.delete_access_point(ap_id)
    
    def find_by_store_id(self, store_id: str) -> List[Dict]:
        """Find all credentials for a store."""
        all_aps = self.get_all()
        return [ap for ap in all_aps if ap.get('store_id', '').lower() == store_id.lower()]
    
    def find_by_ap_id(self, ap_id: str) -> Optional[Dict]:
        """Find credential by AP ID."""
        return self.db.get_access_point(ap_id)
    
    def find_by_store_and_ap(self, store_id: str, ap_id: str) -> Optional[Dict]:
        """Find credential by store ID and AP ID."""
        ap = self.db.get_access_point(ap_id)
        if ap and ap.get('store_id', '').lower() == store_id.lower():
            return ap
        return None
    
    def find_by_ip(self, ip_address: str) -> Optional[Dict]:
        """Find credential by IP address."""
        all_aps = self.get_all()
        for ap in all_aps:
            if ap.get('ip_address', '').lower() == ip_address.lower():
                return ap
        return None
    
    def search(self, query: str) -> List[Dict]:
        """Search credentials by any field."""
        return self.db.search_access_points(query)
    
    def get_all(self) -> List[Dict]:
        """Get all credentials."""
        return self.db.get_all_access_points()
    
    def count(self) -> int:
        """Get total number of credentials."""
        return len(self.get_all())
