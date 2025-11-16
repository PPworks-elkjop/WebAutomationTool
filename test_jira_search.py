"""
Test script to explore Jira search results and available fields.
This will help us understand what data we get back and design the database schema.
"""

import json
from database_manager import DatabaseManager
from jira_integration import JiraIntegration


def print_separator(title):
    """Print a section separator."""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80 + "\n")


def explore_issue_fields(issue):
    """Explore all available fields in a single issue."""
    print("Available top-level keys in issue:")
    for key in issue.keys():
        print(f"  - {key}")
    
    print("\n" + "-"*80)
    print("FIELDS section contains:")
    if 'fields' in issue:
        fields = issue['fields']
        for field_key in sorted(fields.keys()):
            field_value = fields[field_key]
            # Show field name and type
            value_type = type(field_value).__name__
            
            # Show sample value (truncated if too long)
            if field_value is None:
                sample = "None"
            elif isinstance(field_value, (str, int, float, bool)):
                sample = str(field_value)[:100]
            elif isinstance(field_value, dict):
                sample = f"dict with keys: {list(field_value.keys())[:5]}"
            elif isinstance(field_value, list):
                sample = f"list with {len(field_value)} items"
            else:
                sample = f"{value_type} object"
            
            print(f"  {field_key:30} ({value_type:15}): {sample}")


def display_issue_summary(issue, jira_base_url):
    """Display a formatted summary of an issue."""
    key = issue.get('key', 'N/A')
    fields = issue.get('fields', {})
    
    # Common fields
    summary = fields.get('summary', 'N/A')
    status = fields.get('status', {}).get('name', 'N/A')
    issue_type = fields.get('issuetype', {}).get('name', 'N/A')
    priority = fields.get('priority', {}).get('name', 'N/A')
    
    # People
    creator = fields.get('creator', {}).get('displayName', 'N/A')
    assignee = fields.get('assignee')
    assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
    reporter = fields.get('reporter', {}).get('displayName', 'N/A')
    
    # Dates
    created = fields.get('created', 'N/A')
    updated = fields.get('updated', 'N/A')
    resolved = fields.get('resolutiondate', 'N/A')
    
    # Description
    description = fields.get('description')
    if description:
        if isinstance(description, dict):
            # Atlassian Document Format
            desc_text = "ADF format (complex structure)"
        else:
            desc_text = str(description)[:100]
    else:
        desc_text = "No description"
    
    # Resolution
    resolution = fields.get('resolution')
    resolution_name = resolution.get('name', 'N/A') if resolution else 'Unresolved'
    
    # Comments (internal notes and customer replies)
    comment_data = fields.get('comment', {})
    comments = comment_data.get('comments', []) if isinstance(comment_data, dict) else []
    comment_count = len(comments)
    total_comments = comment_data.get('total', comment_count) if isinstance(comment_data, dict) else comment_count
    
    # Build URL
    url = f"{jira_base_url}/browse/{key}"
    
    print(f"""
Issue Key:        {key}
URL:              {url}
Summary:          {summary}
Type:             {issue_type}
Status:           {status}
Priority:         {priority}
Resolution:       {resolution_name}

Created:          {created}
Updated:          {updated}
Resolved:         {resolved}

Creator:          {creator}
Reporter:         {reporter}
Assignee:         {assignee_name}

Description:      {desc_text}
Comments:         {comment_count} comment(s) (Total: {total_comments})
    """)
    
    # Show last few comments if available
    if comments:
        print("\n  Recent Comments:")
        for idx, comment in enumerate(comments[-3:], 1):  # Show last 3 comments
            comment_author = comment.get('author', {}).get('displayName', 'Unknown')
            comment_created = comment.get('created', 'N/A')
            comment_body = comment.get('body', '')
            
            # Extract text from comment body (could be ADF format)
            if isinstance(comment_body, dict):
                comment_text = "[ADF format comment]"
            elif isinstance(comment_body, str):
                comment_text = comment_body[:150] + ('...' if len(comment_body) > 150 else '')
            else:
                comment_text = str(comment_body)[:150]
            
            # Check if it's internal (restricted visibility)
            visibility = comment.get('jsdPublic', True)  # JSD public flag
            internal_marker = "[INTERNAL]" if not visibility else "[PUBLIC]"
            
            print(f"    {idx}. {internal_marker} {comment_author} ({comment_created[:10]})")
            print(f"       {comment_text}")
    print()


def main():
    """Main test function."""
    print_separator("JIRA SEARCH TEST")
    
    # Initialize
    print("Initializing Jira integration...")
    db_manager = DatabaseManager('esl_ap_helper.db')
    jira = JiraIntegration(db_manager)
    
    # Check if configured
    credentials = jira.credentials_manager.get_credentials('jira')
    
    if not credentials or not credentials.get('url'):
        print("\nJira is not configured. Please enter credentials for testing:")
        print("(These will be saved to the database)")
        
        url = input("\nJira URL (e.g., https://yourcompany.atlassian.net): ").strip()
        username = input("Username/Email: ").strip()
        api_token = input("API Token: ").strip()
        verify_ssl_input = input("Verify SSL certificates? (y/n, default=y): ").strip().lower()
        verify_ssl = verify_ssl_input != 'n'
        
        if not url or not username or not api_token:
            print("ERROR: All fields are required.")
            return
        
        # Save credentials
        print("\nSaving credentials...")
        credentials = {
            'url': url,
            'username': username,
            'api_token': api_token,
            'verify_ssl': verify_ssl
        }
        jira.credentials_manager.store_credentials('jira', credentials)
        print("Credentials saved successfully.")
        
        # Reinitialize to load new credentials
        jira = JiraIntegration(db_manager)
        credentials = jira.credentials_manager.get_credentials('jira')
    
    # Get Jira base URL for building links
    jira_base_url = credentials.get('url', '').rstrip('/') if credentials else ''
    
    print(f"\nJira URL: {jira_base_url}")
    
    # Get AP ID from user
    print()
    ap_id = input("Enter ESL AP ID to search for: ").strip()
    
    if not ap_id:
        print("No AP ID provided. Exiting.")
        return
    
    # Search for issues
    print_separator(f"SEARCHING FOR: {ap_id}")
    
    # Build JQL query (searching in all text fields)
    # Note: Using 'textfields' instead of 'text' for broader search
    jql = f'textfields ~ "{ap_id}" ORDER BY updated DESC'
    print(f"JQL Query: {jql}\n")
    
    success, results, message = jira.search_issues(jql, max_results=50)
    
    if not success:
        print(f"ERROR: {message}")
        return
    
    print(f"Result: {message}")
    
    if not results:
        print("No results returned.")
        return
    
    issues = results.get('issues', [])
    if not issues:
        print("No issues found in results.")
        return
    
    total = results.get('total', len(issues))
    is_last = results.get('isLast', True)
    
    print(f"\nFound {len(issues)} issues (isLast: {is_last})")
    
    if not issues:
        print("No issues found.")
        return
    
    # Explore first issue in detail
    print_separator("DETAILED FIELD EXPLORATION (First Issue)")
    explore_issue_fields(issues[0])
    
    # Show summary of all issues
    print_separator(f"SUMMARY OF ALL {len(issues)} ISSUES")
    
    for idx, issue in enumerate(issues, 1):
        print(f"\n--- Issue {idx} of {len(issues)} ---")
        display_issue_summary(issue, jira_base_url)
        print("-" * 80)
    
    # Show what we'd store in database
    print_separator("PROPOSED DATABASE SCHEMA")
    
    print("""
Based on the results, here's what we could store in the database:

TABLE: jira_ap_links
Columns:
  - id (INTEGER PRIMARY KEY AUTOINCREMENT)
  - ap_id (TEXT NOT NULL) - The ESL AP ID
  - jira_key (TEXT NOT NULL) - e.g., 'PROJ-123'
  - jira_id (TEXT NOT NULL) - Jira internal issue ID
  - jira_url (TEXT NOT NULL) - Full URL to the issue
  - summary (TEXT) - Issue summary/title
  - issue_type (TEXT) - e.g., 'Bug', 'Task', 'Story'
  - status (TEXT) - e.g., 'Open', 'In Progress', 'Closed'
  - priority (TEXT) - e.g., 'High', 'Medium', 'Low'
  - resolution (TEXT) - e.g., 'Done', 'Won't Fix', or NULL if unresolved
  - created_date (TEXT) - ISO format timestamp
  - updated_date (TEXT) - ISO format timestamp
  - resolved_date (TEXT) - ISO format timestamp or NULL
  - creator (TEXT) - Display name of creator
  - reporter (TEXT) - Display name of reporter
  - assignee (TEXT) - Display name of assignee or NULL
  - description_preview (TEXT) - First 500 chars of description
  - comment_count (INTEGER DEFAULT 0) - Total number of comments
  - last_synced (TEXT) - When we last pulled this data
  - created_at (TEXT DEFAULT CURRENT_TIMESTAMP)
  - updated_at (TEXT DEFAULT CURRENT_TIMESTAMP)

Indexes:
  - idx_jira_ap_links_ap_id ON jira_ap_links(ap_id)
  - idx_jira_ap_links_jira_key ON jira_ap_links(jira_key)
  - idx_jira_ap_links_status ON jira_ap_links(status)
  - idx_jira_ap_links_updated ON jira_ap_links(updated_date)

TABLE: jira_comments
Columns:
  - id (INTEGER PRIMARY KEY AUTOINCREMENT)
  - jira_link_id (INTEGER NOT NULL) - Foreign key to jira_ap_links.id
  - jira_comment_id (TEXT NOT NULL) - Jira internal comment ID
  - author (TEXT) - Comment author display name
  - author_email (TEXT) - Comment author email
  - comment_text (TEXT) - Extracted plain text from ADF format
  - is_internal (BOOLEAN DEFAULT 0) - 0=public/customer, 1=internal note
  - created_date (TEXT) - ISO format timestamp
  - updated_date (TEXT) - ISO format timestamp
  - created_at (TEXT DEFAULT CURRENT_TIMESTAMP)

Indexes:
  - idx_jira_comments_link_id ON jira_comments(jira_link_id)
  - idx_jira_comments_jira_id ON jira_comments(jira_comment_id)
  - idx_jira_comments_internal ON jira_comments(is_internal)
  - idx_jira_comments_created ON jira_comments(created_date)

Foreign Keys:
  - jira_comments.jira_link_id → jira_ap_links.id (ON DELETE CASCADE)
""")
    
    print("\nWould you like to see the raw JSON of the first issue? (y/n): ", end='')
    show_raw = input().strip().lower()
    
    if show_raw == 'y':
        print_separator("RAW JSON (First Issue)")
        print(json.dumps(issues[0], indent=2))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
