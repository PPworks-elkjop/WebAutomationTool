"""
Credentials Manager - Secure storage and retrieval of API credentials
Handles encryption/decryption of sensitive data for various integrations.
"""

from cryptography.fernet import Fernet
import base64
import hashlib
import os
import json


class CredentialsManager:
    """Manages secure storage and retrieval of API credentials."""
    
    def __init__(self, db_manager):
        """
        Initialize the credentials manager.
        
        Args:
            db_manager: Database manager instance for storing encrypted credentials
        """
        self.db = db_manager
        self._encryption_key = None
        self._ensure_encryption_key()
    
    def _ensure_encryption_key(self):
        """Ensure encryption key exists, create if needed."""
        # Check if encryption key exists in database
        result = self.db.execute_query(
            "SELECT config_value FROM system_config WHERE config_key = 'encryption_key'",
            fetch_one=True
        )
        
        if result:
            self._encryption_key = result['config_value'].encode()
        else:
            # Generate new encryption key
            key = Fernet.generate_key()
            self._encryption_key = key
            
            # Store in database
            self.db.execute_query(
                "INSERT INTO system_config (config_key, config_value) VALUES (?, ?)",
                ('encryption_key', key.decode())
            )
    
    def _encrypt(self, data: str) -> str:
        """Encrypt data using Fernet encryption."""
        if not data:
            return ""
        
        fernet = Fernet(self._encryption_key)
        encrypted = fernet.encrypt(data.encode('utf-8'))
        return encrypted.decode('utf-8')
    
    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt data using Fernet encryption."""
        if not encrypted_data:
            return ""
        
        try:
            fernet = Fernet(self._encryption_key)
            decrypted = fernet.decrypt(encrypted_data.encode('utf-8'))
            return decrypted.decode('utf-8')
        except Exception as e:
            print(f"Decryption error: {e}")
            return ""
    
    def store_credentials(self, service: str, credentials: dict):
        """
        Store encrypted credentials for a service.
        
        Args:
            service: Service name (e.g., 'jira', 'vusion_cloud')
            credentials: Dictionary with credential fields
        """
        # Encrypt the entire credentials dictionary as JSON
        credentials_json = json.dumps(credentials)
        encrypted = self._encrypt(credentials_json)
        
        # Check if credentials already exist
        existing = self.db.execute_query(
            "SELECT id FROM api_credentials WHERE service_name = ?",
            (service,),
            fetch_one=True
        )
        
        if existing:
            # Update existing
            self.db.execute_query(
                """UPDATE api_credentials 
                   SET encrypted_data = ?, updated_at = CURRENT_TIMESTAMP 
                   WHERE service_name = ?""",
                (encrypted, service)
            )
        else:
            # Insert new
            self.db.execute_query(
                """INSERT INTO api_credentials (service_name, encrypted_data) 
                   VALUES (?, ?)""",
                (service, encrypted)
            )
    
    def get_credentials(self, service: str) -> dict:
        """
        Retrieve and decrypt credentials for a service.
        
        Args:
            service: Service name (e.g., 'jira', 'vusion_cloud')
            
        Returns:
            Dictionary with credential fields, or empty dict if not found
        """
        result = self.db.execute_query(
            "SELECT encrypted_data FROM api_credentials WHERE service_name = ?",
            (service,),
            fetch_one=True
        )
        
        if result and result['encrypted_data']:
            decrypted_json = self._decrypt(result['encrypted_data'])
            if decrypted_json:
                return json.loads(decrypted_json)
        
        return {}
    
    def delete_credentials(self, service: str):
        """
        Delete credentials for a service.
        
        Args:
            service: Service name to delete
        """
        self.db.execute_query(
            "DELETE FROM api_credentials WHERE service_name = ?",
            (service,)
        )
    
    def get_all_services(self) -> list:
        """
        Get list of all services with stored credentials.
        
        Returns:
            List of service names
        """
        results = self.db.execute_query(
            "SELECT service_name, updated_at FROM api_credentials ORDER BY service_name"
        )
        return results if results else []
    
    def test_credentials(self, service: str) -> tuple[bool, str]:
        """
        Test if credentials exist and are valid.
        
        Args:
            service: Service name to test
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        credentials = self.get_credentials(service)
        
        if not credentials:
            return False, f"No credentials found for {service}"
        
        # Check if required fields are present based on service
        if service == 'jira':
            required = ['url', 'username', 'api_token']
            missing = [field for field in required if field not in credentials or not credentials[field]]
            if missing:
                return False, f"Missing required fields: {', '.join(missing)}"
        
        elif service == 'vusion_cloud':
            required = ['url', 'api_key']
            missing = [field for field in required if field not in credentials or not credentials[field]]
            if missing:
                return False, f"Missing required fields: {', '.join(missing)}"
        
        return True, "Credentials found"
