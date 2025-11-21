"""
Migration Script: Old Fernet Encryption → Windows DPAPI Encryption

This script migrates credentials from the old Fernet-based encryption
to the new Windows DPAPI-based encryption.

Run this ONCE after upgrading to the new credentials_manager.py
"""

import os
import sys
import json
from cryptography.fernet import Fernet

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_manager import DatabaseManager
from credentials_manager import CredentialsManager


def migrate_credentials():
    """Migrate credentials from Fernet to DPAPI encryption."""
    
    print("\n" + "="*60)
    print("Credential Migration: Fernet → Windows DPAPI")
    print("="*60 + "\n")
    
    # Initialize database
    db = DatabaseManager()
    
    # Check if old encryption key exists
    result = db.execute_query(
        "SELECT config_value FROM system_config WHERE config_key = 'encryption_key'",
        fetch_one=True
    )
    
    if not result:
        print("✅ No old encryption key found. No migration needed.")
        print("   (Either already migrated or fresh install)")
        return
    
    old_encryption_key = result['config_value'].encode()
    print(f"🔍 Found old Fernet encryption key")
    
    # Get all stored credentials
    credentials_data = db.execute_query(
        "SELECT service_name, encrypted_data FROM api_credentials"
    )
    
    if not credentials_data:
        print("ℹ️  No credentials found to migrate.")
        # Clean up old key
        db.execute_query("DELETE FROM system_config WHERE config_key = 'encryption_key'")
        print("✅ Removed old encryption key")
        return
    
    print(f"📦 Found {len(credentials_data)} credential(s) to migrate:\n")
    
    # Decrypt with old Fernet encryption
    fernet = Fernet(old_encryption_key)
    decrypted_credentials = {}
    
    for row in credentials_data:
        service_name = row['service_name']
        encrypted_data = row['encrypted_data']
        
        try:
            # Decrypt using old Fernet key
            decrypted_bytes = fernet.decrypt(encrypted_data.encode('utf-8'))
            decrypted_json = decrypted_bytes.decode('utf-8')
            credentials_dict = json.loads(decrypted_json)
            decrypted_credentials[service_name] = credentials_dict
            print(f"   ✓ Decrypted: {service_name}")
        except Exception as e:
            print(f"   ✗ Failed to decrypt {service_name}: {e}")
    
    if not decrypted_credentials:
        print("\n❌ No credentials could be decrypted. Aborting migration.")
        return
    
    print(f"\n🔄 Re-encrypting with Windows DPAPI...\n")
    
    # Initialize new credentials manager (with DPAPI)
    cred_manager = CredentialsManager(db)
    
    if not cred_manager.use_dpapi:
        print("❌ ERROR: Windows DPAPI is not available!")
        print("   Migration cannot proceed without pywin32.")
        print("   Run: pip install pywin32")
        return
    
    # Re-encrypt and store with new DPAPI encryption
    for service_name, credentials_dict in decrypted_credentials.items():
        try:
            cred_manager.store_credentials(service_name, credentials_dict)
            print(f"   ✓ Re-encrypted: {service_name}")
        except Exception as e:
            print(f"   ✗ Failed to re-encrypt {service_name}: {e}")
    
    print(f"\n🧹 Cleaning up old encryption key...")
    
    # Remove the old Fernet encryption key
    db.execute_query("DELETE FROM system_config WHERE config_key = 'encryption_key'")
    
    print("\n" + "="*60)
    print("✅ Migration Complete!")
    print("="*60)
    print("\nYour credentials are now protected by Windows DPAPI.")
    print("They are tied to your Windows user account and cannot be")
    print("decrypted by other users or if the database is copied.")
    print("\n⚠️  IMPORTANT: If you change your Windows password, you may")
    print("   need to re-enter your credentials.\n")


if __name__ == "__main__":
    try:
        migrate_credentials()
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration cancelled by user.")
    except Exception as e:
        print(f"\n\n❌ Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
