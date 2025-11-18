"""
Jira Database Manager - Handles database operations for Jira integration
Extends the main DatabaseManager with Jira-specific tables and operations
"""

from database_manager import DatabaseManager
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json


def extract_text_from_adf(adf_content) -> str:
    """
    Extract plain text from Atlassian Document Format (ADF).
    
    Args:
        adf_content: ADF content (dict or string)
        
    Returns:
        Plain text extracted from the ADF structure
    """
    if isinstance(adf_content, str):
        return adf_content
    
    if not isinstance(adf_content, dict):
        return str(adf_content)
    
    text_parts = []
    
    def extract_from_node(node):
        """Recursively extract text from ADF nodes."""
        if isinstance(node, str):
            text_parts.append(node)
            return
        
        if not isinstance(node, dict):
            return
        
        # Handle text nodes
        if node.get('type') == 'text':
            text_parts.append(node.get('text', ''))
        
        # Handle hard breaks
        elif node.get('type') == 'hardBreak':
            text_parts.append('\n')
        
        # Recursively process content
        if 'content' in node and isinstance(node['content'], list):
            for child in node['content']:
                extract_from_node(child)
        
        # Add paragraph breaks
        if node.get('type') == 'paragraph' and text_parts and text_parts[-1] != '\n\n':
            text_parts.append('\n\n')
    
    extract_from_node(adf_content)
    
    # Clean up the result
    result = ''.join(text_parts).strip()
    # Remove excessive newlines
    while '\n\n\n' in result:
        result = result.replace('\n\n\n', '\n\n')
    
    return result


class JiraDBManager:
    """Manages Jira-specific database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize with existing DatabaseManager instance."""
        self.db = db_manager
        self._init_jira_tables()
    
    def _init_jira_tables(self):
        """Initialize Jira-specific tables."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            # Jira AP Links table - main issue tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jira_ap_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ap_id TEXT NOT NULL,
                    jira_key TEXT NOT NULL,
                    jira_id TEXT NOT NULL,
                    jira_url TEXT NOT NULL,
                    summary TEXT,
                    issue_type TEXT,
                    status TEXT,
                    priority TEXT,
                    resolution TEXT,
                    created_date TEXT,
                    updated_date TEXT,
                    resolved_date TEXT,
                    creator TEXT,
                    reporter TEXT,
                    assignee TEXT,
                    description_preview TEXT,
                    comment_count INTEGER DEFAULT 0,
                    last_synced TEXT DEFAULT CURRENT_TIMESTAMP,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ap_id, jira_key)
                )
            ''')
            
            # Jira Comments table - internal notes and customer replies
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jira_comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    jira_link_id INTEGER NOT NULL,
                    jira_comment_id TEXT NOT NULL UNIQUE,
                    author TEXT,
                    author_email TEXT,
                    comment_text TEXT,
                    is_internal BOOLEAN DEFAULT 0,
                    created_date TEXT,
                    updated_date TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (jira_link_id) REFERENCES jira_ap_links(id) ON DELETE CASCADE
                )
            ''')
            
            # Create indexes for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_jira_ap_links_ap_id 
                ON jira_ap_links(ap_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_jira_ap_links_jira_key 
                ON jira_ap_links(jira_key)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_jira_ap_links_status 
                ON jira_ap_links(status)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_jira_ap_links_updated 
                ON jira_ap_links(updated_date)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_jira_comments_link_id 
                ON jira_comments(jira_link_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_jira_comments_jira_id 
                ON jira_comments(jira_comment_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_jira_comments_internal 
                ON jira_comments(is_internal)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_jira_comments_created 
                ON jira_comments(created_date)
            ''')
            
            conn.commit()
    
    def store_issue(self, ap_id: str, issue: Dict, jira_base_url: str) -> int:
        """
        Store or update a Jira issue.
        
        Args:
            ap_id: AP ID this issue relates to
            issue: Issue data from Jira API
            jira_base_url: Base URL for constructing issue URLs
            
        Returns:
            Database ID of the stored issue
        """
        fields = issue.get('fields', {})
        
        # Extract basic info
        jira_key = issue.get('key', '')
        jira_id = issue.get('id', '')
        jira_url = f"{jira_base_url}/browse/{jira_key}"
        
        # Extract fields
        summary = fields.get('summary', '')
        issue_type = fields.get('issuetype', {}).get('name', '')
        status = fields.get('status', {}).get('name', '')
        priority = fields.get('priority', {}).get('name', '')
        resolution = fields.get('resolution', {}).get('name') if fields.get('resolution') else None
        
        # Dates
        created_date = fields.get('created', '')
        updated_date = fields.get('updated', '')
        resolved_date = fields.get('resolutiondate')
        
        # People
        creator = fields.get('creator', {}).get('displayName', '')
        reporter = fields.get('reporter', {}).get('displayName', '')
        assignee_obj = fields.get('assignee')
        assignee = assignee_obj.get('displayName', '') if assignee_obj else None
        
        # Description
        description = fields.get('description')
        description_preview = extract_text_from_adf(description)[:500] if description else ''
        
        # Comment count
        comment_data = fields.get('comment', {})
        comment_count = comment_data.get('total', 0) if isinstance(comment_data, dict) else 0
        
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert or replace
            cursor.execute('''
                INSERT OR REPLACE INTO jira_ap_links (
                    ap_id, jira_key, jira_id, jira_url, summary, issue_type,
                    status, priority, resolution, created_date, updated_date,
                    resolved_date, creator, reporter, assignee, description_preview,
                    comment_count, last_synced, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                         CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (
                ap_id, jira_key, jira_id, jira_url, summary, issue_type,
                status, priority, resolution, created_date, updated_date,
                resolved_date, creator, reporter, assignee, description_preview,
                comment_count
            ))
            
            # Get the ID
            cursor.execute('''
                SELECT id FROM jira_ap_links WHERE ap_id = ? AND jira_key = ?
            ''', (ap_id, jira_key))
            
            row = cursor.fetchone()
            link_id = row[0] if row else cursor.lastrowid
            
            conn.commit()
            return link_id
    
    def store_comments(self, jira_link_id: int, comments: List[Dict]):
        """
        Store comments for a Jira issue.
        
        Args:
            jira_link_id: Database ID of the jira_ap_links record
            comments: List of comment data from Jira API
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            for comment in comments:
                jira_comment_id = comment.get('id', '')
                author = comment.get('author', {}).get('displayName', '')
                author_email = comment.get('author', {}).get('emailAddress', '')
                
                # Extract text from ADF body
                body = comment.get('body')
                comment_text = extract_text_from_adf(body)
                
                # Check if internal (jsdPublic: false means internal only)
                is_internal = not comment.get('jsdPublic', True)
                
                created_date = comment.get('created', '')
                updated_date = comment.get('updated', '')
                
                cursor.execute('''
                    INSERT OR REPLACE INTO jira_comments (
                        jira_link_id, jira_comment_id, author, author_email,
                        comment_text, is_internal, created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    jira_link_id, jira_comment_id, author, author_email,
                    comment_text, is_internal, created_date, updated_date
                ))
            
            conn.commit()
    
    def get_issues_for_ap(self, ap_id: str) -> List[Dict]:
        """
        Get all Jira issues for an AP.
        Returns unique issues (deduplicated by jira_key).
        
        Args:
            ap_id: AP ID to search for
            
        Returns:
            List of unique issue dictionaries
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            # Get unique issues by jira_key, preferring the most recent entry
            cursor.execute('''
                SELECT * FROM jira_ap_links 
                WHERE id IN (
                    SELECT MAX(id) FROM jira_ap_links 
                    WHERE ap_id = ?
                    GROUP BY jira_key
                )
                ORDER BY updated_date DESC
            ''', (ap_id,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_comments_for_issue(self, jira_link_id: int, include_internal: bool = True) -> List[Dict]:
        """
        Get comments for a Jira issue.
        
        Args:
            jira_link_id: Database ID of the jira_ap_links record
            include_internal: Whether to include internal comments
            
        Returns:
            List of comment dictionaries
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            if include_internal:
                cursor.execute('''
                    SELECT * FROM jira_comments 
                    WHERE jira_link_id = ? 
                    ORDER BY created_date ASC
                ''', (jira_link_id,))
            else:
                cursor.execute('''
                    SELECT * FROM jira_comments 
                    WHERE jira_link_id = ? AND is_internal = 0
                    ORDER BY created_date ASC
                ''', (jira_link_id,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def search_issues(self, search_term: str = None, status: str = None, 
                     limit: int = 100) -> List[Dict]:
        """
        Search Jira issues with optional filters.
        Returns unique issues (deduplicated by jira_key).
        
        Args:
            search_term: Search in AP ID, summary, or Jira key
            status: Filter by status
            limit: Maximum number of results
            
        Returns:
            List of unique issue dictionaries
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            # Use DISTINCT on jira_key and get the most recent entry for each
            query = '''
                SELECT * FROM jira_ap_links 
                WHERE id IN (
                    SELECT MAX(id) FROM jira_ap_links 
                    WHERE 1=1
            '''
            params = []
            
            if search_term:
                query += ''' AND (ap_id LIKE ? OR summary LIKE ? OR jira_key LIKE ?)'''
                search_pattern = f'%{search_term}%'
                params.extend([search_pattern, search_pattern, search_pattern])
            
            if status:
                query += ' AND status = ?'
                params.append(status)
            
            query += ' GROUP BY jira_key) ORDER BY updated_date DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
