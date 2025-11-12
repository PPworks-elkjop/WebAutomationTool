# User Management Security Enhancements

## Overview
Complete overhaul of the user management system with security-first design and comprehensive audit logging.

## Key Security Improvements

### 1. **No Clear Text Password Display**
- **Before**: Passwords were shown in the user manager GUI in plain text
- **After**: Passwords are NEVER displayed in the GUI
  - Current password field removed from edit dialogs
  - Only new password entry when changing passwords
  - All password fields show asterisks by default
  - Optional "show password" toggle for new password entry only

### 2. **Role-Based Password Changes**
- **Users**: Can ONLY change their own password
- **Admins**: Can change any user's password
- **Protection**: Users attempting to change other passwords see "Access Denied" error
- **Audit**: All password changes are logged with who changed whose password

### 3. **Database-Backed with Encryption**
- **Storage**: Migrated from JSON files to SQLite database
- **Encryption**: AES-256 encryption for all passwords
- **Location**: `~/.vera_database.db` (same database as AP credentials)
- **Key Management**: Secure encryption key stored in `~/.vera_encryption_key`

### 4. **Comprehensive Audit Logging**

#### User Audit Log (`user_audit_log` table)
Tracks all user management actions:
- **create_user**: Who created which user
- **delete_user**: Who deleted which user  
- **change_password**: Who changed whose password
- **change_role**: Role changes (User ↔ Admin)
- **update_user**: Other profile updates

Each entry includes:
- Timestamp
- Actor (who performed the action)
- Action type
- Target (user affected)
- Details (description of changes)
- Success flag

#### User Activity Log (`user_activity_log` table)
Tracks all user actions in the system:
- **login**: User login events (automatically logged)
- **logout**: User logout events
- **ap_connect**: AP connection attempts
- **provision**: Provisioning operations
- **ssh_connect**: SSH connections
- **ping**: Ping operations
- And more...

Each entry includes:
- Timestamp
- Username
- Activity type
- Description
- Related AP ID (if applicable)
- Success flag
- Additional details (JSON)

### 5. **User Tracking Fields**
Every user record now includes:
- `created_by`: Username who created this user
- `created_at`: When user was created
- `updated_by`: Username who last modified this user
- `updated_at`: When user was last modified
- `last_login`: When user last logged in

## New Features

### Admin-Only Audit Log Viewer
- Accessible from User Manager: "View Audit Log" button
- Two tabs:
  1. **Audit Log**: User management actions
  2. **Activity Log**: User system actions
- Filtering by username/target
- Shows last 500 events
- Only visible to administrators

### Automatic Migration
- Old JSON user files automatically migrated to database
- Password encryption upgraded from AES-128 to AES-256
- Old files backed up to `.esl_ap_users.json.backup`
- Migration logged in audit log

### Default Admin Account
- Username: `MasterBlaster`
- Default password: `VinterMorker2025&`
- Cannot be deleted
- Automatically created if missing

## File Changes

### New Files Created
1. **user_manager_v2.py** - Database-backed user manager
2. **user_manager_gui_v2.py** - Secure GUI with audit viewer
3. **migrate_users_to_db.py** - Migration utility
4. **test_users.py** - Test script

### Updated Files
1. **database_manager.py**
   - Added `users` table
   - Added `user_audit_log` table
   - Added `user_activity_log` table
   - Added user management methods
   - Added audit logging methods

2. **login_dialog.py**
   - Import changed to `user_manager_v2`
   - Login events automatically logged

3. **esl_ap_helper_v2.py**
   - Import changed to `user_manager_gui_v2`

## Database Schema

### users table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    full_name TEXT NOT NULL,
    password TEXT NOT NULL,  -- Encrypted with AES-256
    role TEXT NOT NULL,      -- 'Admin' or 'User'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
)
```

### user_audit_log table
```sql
CREATE TABLE user_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actor_username TEXT NOT NULL,
    action TEXT NOT NULL,
    target_username TEXT NOT NULL,
    details TEXT,
    ip_address TEXT,
    success BOOLEAN DEFAULT 1
)
```

### user_activity_log table
```sql
CREATE TABLE user_activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    username TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    description TEXT,
    ap_id TEXT,
    ip_address TEXT,
    session_id TEXT,
    success BOOLEAN DEFAULT 1,
    details TEXT  -- JSON
)
```

## Usage Examples

### For Administrators
```python
from user_manager_v2 import UserManager

um = UserManager()

# Add a new user
success, msg = um.add_user(
    full_name="John Doe",
    username="johnd",
    password="SecurePass123!",
    role="User",
    created_by="admin_username"
)

# View audit log
audit_logs = um.get_user_audit_log(limit=50)
for log in audit_logs:
    print(f"{log['actor_username']} -> {log['action']} -> {log['target_username']}")

# View user activities
activities = um.get_user_activity_log(username="johnd", limit=50)
for activity in activities:
    print(f"{activity['username']}: {activity['activity_type']}")
```

### Logging User Activities
```python
# In your application code
um.log_activity(
    username="current_user",
    activity_type="ap_connect",
    description="Connected to AP via web interface",
    ap_id="123456",
    success=True
)
```

## Security Best Practices

1. **Password Requirements**
   - Minimum 8 characters
   - Enforced in GUI validation

2. **Access Control**
   - Users: Can only view/edit their own profile
   - Users: Can only change their own password
   - Admins: Full access to all user management
   - Admins: Can view all audit logs

3. **Audit Trail**
   - All sensitive actions are logged
   - Logs include who, what, when, and results
   - Logs cannot be deleted (only via direct database access)
   - Admin-only access to audit logs

4. **Database Security**
   - Encrypted passwords (AES-256)
   - Secure key storage
   - Thread-safe operations
   - Transaction-based updates

## Future Enhancements (Already Prepared)

The database schema is ready for:
- IP address logging (fields exist, need to capture from app)
- Session management (session_id field exists)
- User deactivation (is_active field exists)
- More granular activity types
- Extended details in JSON format

## Testing

Run the test script:
```bash
python test_users.py
```

Run the migration:
```bash
python migrate_users_to_db.py
```

Test the GUI:
```bash
python user_manager_gui_v2.py
```

## Migration Notes

- Old JSON user file: `~/.esl_ap_users.json`
- Backup created: `~/.esl_ap_users.json.backup`
- New database: `~/.vera_database.db` (shared with AP credentials)
- Migration is automatic on first run
- No data loss during migration

## Support

For issues or questions:
1. Check audit logs for error details
2. Verify database file exists and is readable
3. Check encryption key file exists
4. Review migration backup if needed

---

**Version**: 2.0  
**Date**: November 2025  
**Security Level**: Enhanced with comprehensive audit logging
