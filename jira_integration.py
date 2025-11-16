"""
Jira Integration Module
High-level interface for Jira operations used throughout the application.
Provides common queries and result handling for various use cases.
"""

from typing import Dict, List, Optional, Tuple
from jira_api import JiraAPI
from credentials_manager import CredentialsManager
from database_manager import DatabaseManager


class JiraIntegration:
    """High-level Jira integration for application-wide use."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize Jira integration.
        
        Args:
            db_manager: Database manager instance for credential access
        """
        self.db_manager = db_manager
        self.credentials_manager = CredentialsManager(db_manager)
        self.jira_api = None
        self._initialized = False
    
    def _ensure_initialized(self) -> Tuple[bool, str]:
        """Ensure Jira API is initialized with credentials.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if self._initialized and self.jira_api:
            return True, "Already initialized"
        
        try:
            # Check if credentials exist
            credentials = self.credentials_manager.get_credentials('jira')
            if not credentials:
                return False, "Jira credentials not configured. Please configure in Admin Settings."
            
            # Initialize Jira API (pass CredentialsManager, not DatabaseManager)
            self.jira_api = JiraAPI(self.credentials_manager)
            success, message = self.jira_api.test_connection()
            
            if success:
                self._initialized = True
                return True, "Jira connected successfully"
            else:
                return False, f"Could not connect to Jira: {message}"
        
        except Exception as e:
            return False, f"Failed to initialize Jira: {str(e)}"
    
    def is_configured(self) -> bool:
        """Check if Jira credentials are configured.
        
        Returns:
            True if credentials exist, False otherwise
        """
        try:
            credentials = self.credentials_manager.get_credentials('jira')
            return credentials is not None
        except:
            return False
    
    def search_issues(self, jql: str, max_results: int = 50, 
                     fields: Optional[List[str]] = None) -> Tuple[bool, Optional[Dict], str]:
        """Search for Jira issues using JQL.
        
        Args:
            jql: JQL query string
            max_results: Maximum number of results to return
            fields: Optional list of fields to return
        
        Returns:
            Tuple of (success: bool, results: dict or None, message: str)
        """
        success, message = self._ensure_initialized()
        if not success:
            return False, None, message
        
        try:
            # jira_api.search_issues returns (success, results_dict, message)
            api_success, results, api_message = self.jira_api.search_issues(jql, max_results, fields)
            
            if not api_success:
                return False, None, api_message
            
            if results and 'issues' in results:
                issue_count = len(results['issues'])
                total = results.get('total', issue_count)
                return True, results, f"Found {issue_count} issues"
            else:
                return True, results, "No issues found"
        
        except Exception as e:
            return False, None, f"Search failed: {str(e)}"
    
    def get_issue(self, issue_key: str, 
                  fields: Optional[List[str]] = None) -> Tuple[bool, Optional[Dict], str]:
        """Get a specific Jira issue by key.
        
        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            fields: Optional list of fields to return
        
        Returns:
            Tuple of (success: bool, issue: dict or None, message: str)
        """
        success, message = self._ensure_initialized()
        if not success:
            return False, None, message
        
        try:
            issue = self.jira_api.get_issue(issue_key, fields)
            return True, issue, f"Retrieved issue {issue_key}"
        
        except Exception as e:
            return False, None, f"Failed to get issue: {str(e)}"
    
    def create_issue(self, project_key: str, summary: str, description: str,
                    issue_type: str = "Task", **additional_fields) -> Tuple[bool, Optional[str], str]:
        """Create a new Jira issue.
        
        Args:
            project_key: Project key (e.g., 'PROJ')
            summary: Issue summary/title
            description: Issue description
            issue_type: Issue type (default: 'Task')
            **additional_fields: Additional fields to set on the issue
        
        Returns:
            Tuple of (success: bool, issue_key: str or None, message: str)
        """
        success, message = self._ensure_initialized()
        if not success:
            return False, None, message
        
        try:
            result = self.jira_api.create_issue(
                project_key, summary, description, issue_type, **additional_fields
            )
            
            if result and 'key' in result:
                issue_key = result['key']
                return True, issue_key, f"Created issue {issue_key}"
            else:
                return False, None, "Issue created but no key returned"
        
        except Exception as e:
            return False, None, f"Failed to create issue: {str(e)}"
    
    def add_comment(self, issue_key: str, comment_text: str) -> Tuple[bool, str]:
        """Add a comment to a Jira issue.
        
        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            comment_text: Comment text
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        success, message = self._ensure_initialized()
        if not success:
            return False, message
        
        try:
            result = self.jira_api.add_comment(issue_key, comment_text)
            return True, f"Comment added to {issue_key}"
        
        except Exception as e:
            return False, f"Failed to add comment: {str(e)}"
    
    def update_issue(self, issue_key: str, **fields) -> Tuple[bool, str]:
        """Update a Jira issue.
        
        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            **fields: Fields to update
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        success, message = self._ensure_initialized()
        if not success:
            return False, message
        
        try:
            self.jira_api.update_issue(issue_key, fields)
            return True, f"Updated issue {issue_key}"
        
        except Exception as e:
            return False, f"Failed to update issue: {str(e)}"
    
    def get_projects(self) -> Tuple[bool, Optional[List[Dict]], str]:
        """Get list of all accessible Jira projects.
        
        Returns:
            Tuple of (success: bool, projects: list or None, message: str)
        """
        success, message = self._ensure_initialized()
        if not success:
            return False, None, message
        
        try:
            projects = self.jira_api.get_projects()
            
            if projects:
                return True, projects, f"Retrieved {len(projects)} projects"
            else:
                return True, [], "No projects found"
        
        except Exception as e:
            return False, None, f"Failed to get projects: {str(e)}"
    
    # Common query patterns for this application
    
    def search_ap_related_issues(self, ap_mac: Optional[str] = None, 
                                ap_name: Optional[str] = None,
                                max_results: int = 50) -> Tuple[bool, Optional[Dict], str]:
        """Search for issues related to a specific AP.
        
        Args:
            ap_mac: AP MAC address
            ap_name: AP name/hostname
            max_results: Maximum results to return
        
        Returns:
            Tuple of (success: bool, results: dict or None, message: str)
        """
        # Build JQL query for AP-related issues
        # Use 'textfields' instead of 'text' for broader search
        conditions = []
        
        if ap_mac:
            conditions.append(f'textfields ~ "{ap_mac}"')
        
        if ap_name:
            conditions.append(f'textfields ~ "{ap_name}"')
        
        if not conditions:
            return False, None, "Either AP MAC or AP name must be provided"
        
        jql = " OR ".join(conditions)
        jql += " ORDER BY updated DESC"
        
        return self.search_issues(jql, max_results)
    
    def create_ap_support_ticket(self, ap_mac: str, ap_name: str, 
                                 issue_description: str, project_key: str,
                                 priority: Optional[str] = None) -> Tuple[bool, Optional[str], str]:
        """Create a support ticket for an AP issue.
        
        Args:
            ap_mac: AP MAC address
            ap_name: AP name/hostname
            issue_description: Description of the issue
            project_key: Jira project key
            priority: Optional priority (e.g., 'High', 'Medium', 'Low')
        
        Returns:
            Tuple of (success: bool, issue_key: str or None, message: str)
        """
        summary = f"AP Support: {ap_name} ({ap_mac})"
        
        description = f"""*AP Information:*
* MAC Address: {ap_mac}
* AP Name: {ap_name}

*Issue Description:*
{issue_description}

_Created automatically from ESL AP Helper Tool_
"""
        
        additional_fields = {}
        if priority:
            additional_fields['priority'] = {'name': priority}
        
        return self.create_issue(
            project_key=project_key,
            summary=summary,
            description=description,
            issue_type="Task",
            **additional_fields
        )
    
    def get_my_open_issues(self, max_results: int = 50) -> Tuple[bool, Optional[Dict], str]:
        """Get open issues assigned to current user.
        
        Args:
            max_results: Maximum results to return
        
        Returns:
            Tuple of (success: bool, results: dict or None, message: str)
        """
        jql = "assignee = currentUser() AND resolution = Unresolved ORDER BY updated DESC"
        return self.search_issues(jql, max_results)
    
    def get_recent_issues(self, days: int = 7, max_results: int = 50) -> Tuple[bool, Optional[Dict], str]:
        """Get recently updated issues.
        
        Args:
            days: Number of days to look back
            max_results: Maximum results to return
        
        Returns:
            Tuple of (success: bool, results: dict or None, message: str)
        """
        jql = f"updated >= -{days}d ORDER BY updated DESC"
        return self.search_issues(jql, max_results)
    
    def link_ap_to_issue(self, issue_key: str, ap_mac: str, 
                        ap_name: str, notes: str = "") -> Tuple[bool, str]:
        """Add AP information as a comment to an existing issue.
        
        Args:
            issue_key: Jira issue key
            ap_mac: AP MAC address
            ap_name: AP name/hostname
            notes: Optional additional notes
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        comment = f"""*Related AP Information:*
* MAC Address: {ap_mac}
* AP Name: {ap_name}
"""
        
        if notes:
            comment += f"\n*Notes:*\n{notes}\n"
        
        comment += "\n_Added from ESL AP Helper Tool_"
        
        return self.add_comment(issue_key, comment)
