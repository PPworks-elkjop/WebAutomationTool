"""
Migrate User Data to Database

This script migrates user data from the old JSON format to the new
SQLite database with proper encryption and audit logging.
"""

from pathlib import Path
from user_manager_v2 import UserManager

def main():
    """Migrate users from JSON to database."""
    print("=" * 60)
    print("User Migration to SQLite Database")
    print("=" * 60)
    
    # Initialize user manager (this will trigger automatic migration)
    user_manager = UserManager()
    
    # Show current users
    users = user_manager.get_all_users()
    print(f"\n✓ Total users in database: {len(users)}")
    
    print("\nUsers:")
    for user in users:
        print(f"  • {user['full_name']} ({user['username']}) - {user['role']}")
        if user.get('created_by'):
            print(f"    Created by: {user['created_by']}")
        if user.get('last_login'):
            print(f"    Last login: {user['last_login']}")
    
    # Show recent audit events
    print("\n" + "=" * 60)
    print("Recent Audit Events")
    print("=" * 60)
    
    audit_logs = user_manager.get_user_audit_log(limit=10)
    if audit_logs:
        for log in audit_logs:
            print(f"  {log['timestamp'][:19]}: {log['actor_username']} -> {log['action']} -> {log['target_username']}")
            if log.get('details'):
                print(f"    Details: {log['details']}")
    else:
        print("  No audit events yet")
    
    print("\n" + "=" * 60)
    print("Migration Complete!")
    print("=" * 60)
    print("\nOld JSON file has been backed up.")
    print("Users are now stored in the encrypted SQLite database.")
    print("\nDatabase location: ~/.vera_database.db")
    print("Encryption key: ~/.vera_encryption_key")
    print("\nAll user management actions are now logged for security auditing.")


if __name__ == "__main__":
    main()
