# Jira Integration - Implementation Summary

## Overview
Complete Jira integration for the ESL AP Helper Tool with secure credential storage, issue search, and comprehensive display of issues and comments.

## Components Created

### 1. Core Integration (`jira_integration.py`)
High-level interface for Jira operations throughout the application.

**Features:**
- Automatic credential initialization
- Consistent error handling with (success, result, message) tuples
- Generic operations: search_issues, get_issue, create_issue, add_comment, update_issue, get_projects
- Application-specific queries:
  - `search_ap_related_issues()` - Find issues mentioning AP MAC/name
  - `create_ap_support_ticket()` - Create formatted AP support tickets
  - `get_my_open_issues()` - Get user's assigned issues
  - `get_recent_issues()` - Get recently updated issues
  - `link_ap_to_issue()` - Add AP info as comment to existing issue

**JQL Syntax:** Uses `textfields ~` for broad text search across all Jira fields.

### 2. Database Layer (`jira_db_manager.py`)
Manages database operations for Jira data with ADF text extraction.

**Tables:**
- `jira_ap_links` - Main issue tracking (AP ID, Jira key, URL, summary, status, priority, etc.)
- `jira_comments` - Comment history with internal/public flag

**Key Functions:**
- `extract_text_from_adf()` - Converts Atlassian Document Format to plain text
- `store_issue()` - Store or update Jira issue
- `store_comments()` - Store comments with internal/public indicator
- `get_issues_for_ap()` - Get all issues for an AP
- `get_comments_for_issue()` - Get comments with optional internal filter
- `search_issues()` - Search with filters

**Indexes:** Optimized queries on ap_id, jira_key, status, updated_date, comment fields

### 3. User Interface (`jira_search_ui.py`)
Full-featured search and display window.

**Features:**
- **Search Jira** - Queries Jira API and caches results locally
- **View Cached** - Shows locally stored issues without API call
- **Split pane layout:**
  - Left: Issue list (key, summary, status, updated date)
  - Right: Tabbed details (Issue Details + Comments)
- **Comment display:**
  - 🟨 Yellow background = Internal notes (jsdPublic: false)
  - 🟩 Green background = Public/customer replies (jsdPublic: true)
- **Double-click** - Opens issue in default browser
- **Auto-loads** when AP ID provided
- **Status indicator** - Shows search progress and results

### 4. API Layer Updates
**Modified Files:**
- `jira_api.py` - Fixed endpoint to `/rest/api/3/search/jql`, removed debug output
- `admin_settings.py` - Fixed token masking to prevent save of placeholder
- `credentials_manager.py` - Added explicit UTF-8 encoding

**API Endpoint:** 
- GET `/rest/api/3/search/jql` (new migration-compliant endpoint)
- Fields requested: key, summary, status, issuetype, priority, created, updated, resolutiondate, creator, reporter, assignee, description, resolution, comment

### 5. Main Application Integration
**Modified:** `ap_support_ui.py`

Added "Search Jira Issues" button to AP Support window:
- Opens Jira search pre-filled with current AP ID
- Logs activity in user audit log
- Jira brand color (#0052CC)
- Positioned above "Open Another AP" button

## Usage

### From AP Support Window
1. Open any AP support window
2. Click "Search Jira Issues" button
3. Window opens pre-filled with AP ID
4. Click "Search Jira" to query API
5. Results cached in database
6. Click "View Cached" for offline access

### Standalone
```python
from jira_search_ui import open_jira_search
from database_manager import DatabaseManager

db = DatabaseManager('esl_ap_helper.db')
open_jira_search(parent_window, db, ap_id="203820")
```

### Programmatic API Use
```python
from jira_integration import JiraIntegration
from database_manager import DatabaseManager

db = DatabaseManager('esl_ap_helper.db')
jira = JiraIntegration(db)

# Search
success, results, msg = jira.search_ap_related_issues(ap_mac="AA:BB:CC:DD:EE:FF")

# Create ticket
success, issue_key, msg = jira.create_ap_support_ticket(
    ap_mac="AA:BB:CC:DD:EE:FF",
    ap_name="Store-AP-01",
    issue_description="AP not responding",
    project_key="SUPPORT"
)
```

## Database Schema

### jira_ap_links
```sql
- id (PK)
- ap_id (indexed)
- jira_key (indexed, unique with ap_id)
- jira_id
- jira_url
- summary
- issue_type
- status (indexed)
- priority
- resolution
- created_date
- updated_date (indexed)
- resolved_date
- creator
- reporter
- assignee
- description_preview (500 chars)
- comment_count
- last_synced
- created_at
- updated_at
```

### jira_comments
```sql
- id (PK)
- jira_link_id (FK, indexed)
- jira_comment_id (unique, indexed)
- author
- author_email
- comment_text (ADF extracted to plain text)
- is_internal (indexed, 0=public, 1=internal)
- created_date (indexed)
- updated_date
- created_at
```

## Security

- **Encrypted Credentials:** Jira API tokens stored encrypted using Fernet (AES-128-CBC + HMAC)
- **Token Masking:** Saved tokens displayed as ●●●●● in UI, never visible after save
- **SSL Verification:** Optional disable for corporate proxies with self-signed certificates
- **Audit Logging:** All Jira searches logged in user_activity_log

## Testing

### Test Scripts
1. `test_jira_search.py` - Command-line exploration of Jira API responses
2. `test_jira_ui.py` - Standalone UI test

### Run Tests
```bash
python test_jira_search.py  # Interactive API exploration
python test_jira_ui.py      # GUI test
```

## Configuration

### Required Settings (Admin Settings)
1. **Jira URL:** https://yourcompany.atlassian.net
2. **Username:** email@company.com
3. **API Token:** Generate from Atlassian Account Settings
4. **Verify SSL:** Uncheck for corporate proxies (shows warning)

### Credentials Storage
- Database: `esl_ap_helper.db` table `api_credentials`
- Encryption key: Stored in `system_config` table
- Service name: `'jira'`

## Known Limitations

1. **ADF Parsing:** Basic text extraction from Atlassian Document Format. Complex formatting (tables, code blocks, media) converted to plain text.
2. **Pagination:** Currently loads first 50 results. Add pagination for more results if needed.
3. **Real-time Sync:** Issues cached locally, requires manual refresh to get latest from Jira.
4. **Comment Filtering:** Shows all comments in UI. Could add toggle to hide internal notes.

## Future Enhancements

1. **Create Issues:** Add UI to create Jira tickets directly from AP Support window
2. **Link Issues:** Ability to link existing Jira issue to AP
3. **Status Updates:** Update Jira issue status from AP Support window
4. **Attachments:** Display/download issue attachments
5. **Watchers:** Show/manage issue watchers
6. **Real-time Sync:** Background process to keep issues updated
7. **Bulk Operations:** Update multiple issues at once
8. **Custom Fields:** Support for organization-specific Jira custom fields

## API Documentation

### Jira REST API v3
- Base: `https://[domain].atlassian.net/rest/api/3/`
- Search: `/search/jql` (GET with query parameters)
- Auth: HTTP Basic Auth (email + API token)
- Docs: https://developer.atlassian.com/cloud/jira/platform/rest/v3/

### JQL (Jira Query Language)
```jql
textfields ~ "203820" ORDER BY updated DESC
text ~ "AP-Name" AND status = Open
project = SUPPORT AND assignee = currentUser()
created >= -7d ORDER BY created DESC
```

## Troubleshooting

### "Jira not configured"
- Go to Admin Settings → Jira tab
- Enter credentials and click Save
- Click Test Connection to verify

### "SSL Certificate verification failed"
- Corporate proxy with self-signed certificate
- Uncheck "Verify SSL certificates" in Admin Settings
- Click Save and test again

### "No issues found" but they exist in Jira
- JQL syntax issue - verify query in Jira web UI
- Check if using `textfields ~` vs `text ~`
- Verify API token has permission to view issues

### "Could not connect to Jira: UnicodeEncodeError"
- Fixed in credentials_manager.py with explicit UTF-8 encoding
- Clear credentials and re-enter if still occurs

## Files Modified/Created

**New Files:**
- `jira_integration.py` (333 lines)
- `jira_db_manager.py` (396 lines)
- `jira_search_ui.py` (530 lines)
- `test_jira_search.py` (263 lines)
- `test_jira_ui.py` (21 lines)

**Modified Files:**
- `jira_api.py` (fixed endpoint, removed debug)
- `admin_settings.py` (fixed token masking)
- `credentials_manager.py` (UTF-8 encoding)
- `ap_support_ui.py` (added Search Jira button)

## Commit Message Template

```
feat: Add comprehensive Jira integration

- Secure credential storage with Fernet encryption
- Issue search with caching in SQLite
- ADF text extraction for descriptions and comments
- Internal/public comment distinction (jsdPublic flag)
- Full-featured search UI with split pane layout
- Integration with AP Support window
- Admin settings with SSL verification toggle
- Audit logging for all Jira operations

Tables: jira_ap_links, jira_comments
API: Jira REST API v3 (/rest/api/3/search/jql)
Auth: HTTP Basic Auth with API tokens
```

## Dependencies

**Required Python packages:**
- `requests` (HTTP client) - Already installed
- `cryptography` (Fernet encryption) - Already installed
- `tkinter` (GUI) - Built-in
- `sqlite3` (Database) - Built-in

**No additional installations needed!**
