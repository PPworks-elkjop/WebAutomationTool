"""
Migration Script: Vusion Fernet Encryption → Windows DPAPI Encryption

This script migrates Vusion API keys from the old Fernet-based file storage
to the new Windows DPAPI-based database storage.

Run this ONCE after upgrading to the new vusion_api_config.py
"""

import os
import sys
import json
from pathlib import Path
from cryptography.fernet import Fernet

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_manager import DatabaseManager
from credentials_manager import CredentialsManager
from vusion_api_config import VusionAPIConfig


def migrate_vusion_credentials():
    """Migrate Vusion API keys from Fernet file storage to DPAPI database storage."""
    
    print("\n" + "="*60)
    print("Vusion Migration: Fernet Files → Windows DPAPI Database")
    print("="*60 + "\n")
    
    # Check if old files exist
    old_config_file = Path.home() / ".vera_vusion_config.json"
    old_key_file = Path.home() / ".vera_vusion_key"
    
    if not old_config_file.exists():
        print("✅ No old Vusion config file found.")
        print("   Either already migrated or fresh install.\n")
        return
    
    if not old_key_file.exists():
        print("⚠️  Config file found but no encryption key file.")
        print("   Cannot decrypt without key. Aborting.\n")
        return
    
    print(f"🔍 Found old Vusion configuration:")
    print(f"   Config: {old_config_file}")
    print(f"   Key:    {old_key_file}\n")
    
    # Load old encryption key
    try:
        with open(old_key_file, 'rb') as f:
            old_key = f.read()
        fernet = Fernet(old_key)
        print(f"✓ Loaded old Fernet encryption key\n")
    except Exception as e:
        print(f"❌ Failed to load encryption key: {e}\n")
        return
    
    # Load old config file
    try:
        with open(old_config_file, 'r') as f:
            old_config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load config file: {e}\n")
        return
    
    # Extract API keys
    api_keys = old_config.get('api_keys', {})
    
    if not api_keys:
        print("ℹ️  No API keys found in old configuration.\n")
        # Still clean up old files
        cleanup_old_files(old_config_file, old_key_file)
        return
    
    # Count total keys
    total_keys = sum(len(services) for services in api_keys.values())
    print(f"📦 Found {total_keys} API key(s) to migrate:\n")
    
    # Decrypt old keys
    decrypted_keys = {}
    for country, services in api_keys.items():
        decrypted_keys[country] = {}
        for service, encrypted_key in services.items():
            try:
                decrypted = fernet.decrypt(encrypted_key.encode()).decode()
                decrypted_keys[country][service] = decrypted
                print(f"   ✓ Decrypted: {country}/{service}")
            except Exception as e:
                print(f"   ✗ Failed to decrypt {country}/{service}: {e}")
    
    if not decrypted_keys or all(not services for services in decrypted_keys.values()):
        print("\n❌ No keys could be decrypted. Aborting migration.\n")
        return
    
    print(f"\n🔄 Re-encrypting with Windows DPAPI...\n")
    
    # Initialize new system (with DPAPI)
    db = DatabaseManager()
    cred_manager = CredentialsManager(db)
    
    if not cred_manager.use_dpapi:
        print("❌ ERROR: Windows DPAPI is not available!")
        print("   Migration cannot proceed without pywin32.")
        print("   Run: pip install pywin32\n")
        return
    
    vusion_config = VusionAPIConfig(cred_manager)
    
    # Re-encrypt and store with new DPAPI encryption
    migrated_count = 0
    for country, services in decrypted_keys.items():
        for service, api_key in services.items():
            try:
                vusion_config.set_api_key(country, service, api_key)
                print(f"   ✓ Re-encrypted: {country}/{service}")
                migrated_count += 1
            except Exception as e:
                print(f"   ✗ Failed to re-encrypt {country}/{service}: {e}")
    
    print(f"\n🧹 Cleaning up old files...")
    cleanup_old_files(old_config_file, old_key_file)
    
    print("\n" + "="*60)
    print("✅ Migration Complete!")
    print("="*60)
    print(f"\nMigrated {migrated_count} API key(s) to Windows DPAPI.")
    print("Your Vusion API keys are now protected by Windows DPAPI.")
    print("They are tied to your Windows user account and cannot be")
    print("decrypted by other users or if the database is copied.")
    print("\n⚠️  IMPORTANT: If you change your Windows password, you may")
    print("   need to re-enter your API keys.\n")


def cleanup_old_files(config_file, key_file):
    """Backup and remove old Vusion configuration files."""
    backup_dir = Path.home() / ".webautomation" / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Backup config file
    if config_file.exists():
        backup_config = backup_dir / f"vera_vusion_config_{timestamp}.json.bak"
        try:
            import shutil
            shutil.copy2(config_file, backup_config)
            config_file.unlink()
            print(f"   ✓ Removed old config file (backed up to {backup_config})")
        except Exception as e:
            print(f"   ⚠️  Could not remove config file: {e}")
    
    # Backup key file
    if key_file.exists():
        backup_key = backup_dir / f"vera_vusion_key_{timestamp}.bak"
        try:
            import shutil
            shutil.copy2(key_file, backup_key)
            key_file.unlink()
            print(f"   ✓ Removed old key file (backed up to {backup_key})")
        except Exception as e:
            print(f"   ⚠️  Could not remove key file: {e}")


if __name__ == "__main__":
    try:
        migrate_vusion_credentials()
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration cancelled by user.")
    except Exception as e:
        print(f"\n\n❌ Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
