"""
VERA Database Migration Script
Migrates from JSON-based credential storage to SQLite database
"""

from credential_manager_v2 import CredentialManager
from database_manager import DatabaseManager
from pathlib import Path
import sys

def main():
    print("=" * 60)
    print("VERA Database Migration Tool")
    print("Migrating from JSON to SQLite with AES-256 encryption")
    print("=" * 60)
    print()
    
    # Check for old JSON file
    old_json = Path.home() / ".esl_ap_credentials.json"
    if not old_json.exists():
        print("✗ No JSON credentials file found at:")
        print(f"  {old_json}")
        print()
        print("Nothing to migrate. Starting fresh with SQLite database.")
        return
    
    print(f"✓ Found JSON credentials file: {old_json}")
    print()
    
    # Create database manager
    db = DatabaseManager()
    
    # Check if database already has data
    stats = db.get_database_stats()
    if stats['total_aps'] > 0:
        print(f"⚠ Database already contains {stats['total_aps']} Access Points")
        response = input("Do you want to migrate anyway? This will add/update entries. (y/n): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            return
    
    # Perform migration
    print("Starting migration...")
    print()
    
    success, message = db.migrate_from_json(str(old_json))
    
    if success:
        print(f"✓ {message}")
        print()
        
        # Show statistics
        stats = db.get_database_stats()
        print("Database Statistics:")
        print(f"  Total APs:       {stats['total_aps']}")
        print(f"  Online:          {stats['online_aps']}")
        print(f"  Offline:         {stats['offline_aps']}")
        print(f"  Database file:   {stats['database_file']}")
        print(f"  Encryption:      {stats['encryption']}")
        print()
        
        # Backup old JSON
        backup_path = old_json.with_suffix('.json.backup')
        if not backup_path.exists():
            old_json.rename(backup_path)
            print(f"✓ Old JSON file backed up to:")
            print(f"  {backup_path}")
        else:
            print(f"⚠ Backup already exists at: {backup_path}")
            print(f"  Original JSON file left at: {old_json}")
        
        print()
        print("=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Test the application to ensure everything works")
        print("2. Once confirmed, you can delete the backup JSON file")
        print("3. Update your application to use credential_manager_v2")
        
    else:
        print(f"✗ Migration failed: {message}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
