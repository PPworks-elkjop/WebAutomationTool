"""
Jira Integration Module - Handles all Jira API interactions
Provides methods to fetch issues, update issues, add comments, etc.
"""

import requests
from requests.auth import HTTPBasicAuth
import json
from typing import Optional, List, Dict


class JiraAPI:
    """Handles Jira API interactions with authentication."""
    
    def __init__(self, credentials_manager):
        """
        Initialize Jira API client.
        
        Args:
            credentials_manager: CredentialsManager instance for retrieving credentials
        """
        self.credentials_manager = credentials_manager
        self._base_url = None
        self._auth = None
        self._session = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize connection parameters from stored credentials."""
        credentials = self.credentials_manager.get_credentials('jira')
        
        if credentials:
            self._base_url = credentials.get('url', '').rstrip('/')
            username = credentials.get('username', '')
            api_token = credentials.get('api_token', '')
            verify_ssl = credentials.get('verify_ssl', True)  # Default to True for security
            
            if self._base_url and username and api_token:
                self._auth = HTTPBasicAuth(username, api_token)
                self._session = requests.Session()
                self._session.auth = self._auth
                self._session.headers.update({
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                })
                
                # Disable SSL verification if configured (for corporate proxies)
                if not verify_ssl:
                    self._session.verify = False
                    # Suppress only the single InsecureRequestWarning from urllib3
                    import urllib3
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def is_configured(self) -> bool:
        """Check if Jira credentials are configured."""
        return self._base_url is not None and self._auth is not None
    
    def test_connection(self) -> tuple[bool, str]:
        """
        Test the Jira connection.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_configured():
            return False, "Jira credentials not configured"
        
        # Debug output
        print(f"DEBUG - Testing connection to: {self._base_url}/rest/api/3/myself")
        print(f"DEBUG - Using username: {self._session.auth.username if self._session.auth else 'None'}")
        
        try:
            response = self._session.get(f"{self._base_url}/rest/api/3/myself", timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                return True, f"Connected as {user_data.get('displayName', 'Unknown')}"
            elif response.status_code == 401:
                return False, "Authentication failed - check credentials"
            else:
                return False, f"Connection failed: HTTP {response.status_code} - {response.text[:200]}"
                
        except requests.exceptions.Timeout:
            return False, f"Connection timeout - cannot reach {self._base_url}"
        except requests.exceptions.ConnectionError as e:
            return False, f"Cannot connect to Jira server at {self._base_url}. Error: {str(e)}"
        except requests.exceptions.SSLError as e:
            return False, f"SSL certificate error: {str(e)}"
        except Exception as e:
            return False, f"Error: {type(e).__name__}: {str(e)}"
    
    def search_issues(self, jql: str, max_results: int = 50, fields: Optional[List[str]] = None) -> tuple[bool, List[Dict], str]:
        """
        Search for issues using JQL.
        
        Args:
            jql: JQL query string
            max_results: Maximum number of results to return
            fields: List of fields to return (None = all fields)
            
        Returns:
            Tuple of (success: bool, issues: List[Dict], message: str)
        """
        if not self.is_configured():
            return False, [], "Jira not configured"
        
        try:
            # The /rest/api/3/search/jql endpoint uses GET with query parameters
            params = {
                'jql': jql,
                'maxResults': max_results
            }
            
            if fields:
                params['fields'] = ','.join(fields)
            else:
                # Request common fields by default (new API returns only IDs without this)
                # Include comment for internal notes and customer replies
                params['fields'] = 'key,summary,status,issuetype,priority,created,updated,resolutiondate,creator,reporter,assignee,description,resolution,comment'
            
            # Use GET to /rest/api/3/search/jql endpoint
            url = f"{self._base_url}/rest/api/3/search/jql"
            
            response = self._session.get(
                url,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                issues = data.get('issues', [])
                is_last = data.get('isLast', True)
                issue_count = len(issues)
                
                # Return the issues with a proper structure
                result = {
                    'issues': issues,
                    'total': issue_count,  # We don't get total from API, just the count
                    'isLast': is_last
                }
                return True, result, f"Found {issue_count} issue(s)"
            else:
                return False, {}, f"Search failed: HTTP {response.status_code}"
                
        except Exception as e:
            return False, [], f"Error: {str(e)}"
    
    def get_issue(self, issue_key: str, fields: Optional[List[str]] = None) -> tuple[bool, Optional[Dict], str]:
        """
        Get a specific issue by key.
        
        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            fields: List of fields to return (None = all fields)
            
        Returns:
            Tuple of (success: bool, issue: Optional[Dict], message: str)
        """
        if not self.is_configured():
            return False, None, "Jira not configured"
        
        try:
            params = {}
            if fields:
                params['fields'] = ','.join(fields)
            
            response = self._session.get(
                f"{self._base_url}/rest/api/3/issue/{issue_key}",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, response.json(), "Issue retrieved"
            elif response.status_code == 404:
                return False, None, "Issue not found"
            else:
                return False, None, f"Failed: HTTP {response.status_code}"
                
        except Exception as e:
            return False, None, f"Error: {str(e)}"
    
    def add_comment(self, issue_key: str, comment_text: str) -> tuple[bool, str]:
        """
        Add a comment to an issue.
        
        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            comment_text: Comment text to add
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_configured():
            return False, "Jira not configured"
        
        try:
            data = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": comment_text
                                }
                            ]
                        }
                    ]
                }
            }
            
            response = self._session.post(
                f"{self._base_url}/rest/api/3/issue/{issue_key}/comment",
                json=data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                return True, "Comment added successfully"
            else:
                return False, f"Failed to add comment: HTTP {response.status_code}"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def update_issue(self, issue_key: str, fields: Dict) -> tuple[bool, str]:
        """
        Update issue fields.
        
        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            fields: Dictionary of fields to update
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_configured():
            return False, "Jira not configured"
        
        try:
            data = {"fields": fields}
            
            response = self._session.put(
                f"{self._base_url}/rest/api/3/issue/{issue_key}",
                json=data,
                timeout=10
            )
            
            if response.status_code == 204:
                return True, "Issue updated successfully"
            else:
                return False, f"Failed to update: HTTP {response.status_code}"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def get_projects(self) -> tuple[bool, List[Dict], str]:
        """
        Get list of all projects.
        
        Returns:
            Tuple of (success: bool, projects: List[Dict], message: str)
        """
        if not self.is_configured():
            return False, [], "Jira not configured"
        
        try:
            response = self._session.get(
                f"{self._base_url}/rest/api/3/project",
                timeout=10
            )
            
            if response.status_code == 200:
                projects = response.json()
                return True, projects, f"Found {len(projects)} project(s)"
            else:
                return False, [], f"Failed: HTTP {response.status_code}"
                
        except Exception as e:
            return False, [], f"Error: {str(e)}"
    
    def create_issue(self, project_key: str, summary: str, description: str, 
                     issue_type: str = "Task") -> tuple[bool, Optional[str], str]:
        """
        Create a new issue.
        
        Args:
            project_key: Project key (e.g., 'PROJ')
            summary: Issue summary/title
            description: Issue description
            issue_type: Issue type (default: 'Task')
            
        Returns:
            Tuple of (success: bool, issue_key: Optional[str], message: str)
        """
        if not self.is_configured():
            return False, None, "Jira not configured"
        
        try:
            data = {
                "fields": {
                    "project": {
                        "key": project_key
                    },
                    "summary": summary,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": description
                                    }
                                ]
                            }
                        ]
                    },
                    "issuetype": {
                        "name": issue_type
                    }
                }
            }
            
            response = self._session.post(
                f"{self._base_url}/rest/api/3/issue",
                json=data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                issue_key = result.get('key')
                return True, issue_key, f"Issue {issue_key} created successfully"
            else:
                return False, None, f"Failed to create issue: HTTP {response.status_code}"
                
        except Exception as e:
            return False, None, f"Error: {str(e)}"
