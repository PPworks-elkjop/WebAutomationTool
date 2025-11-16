"""
Quick test to verify Jira integration components work together
"""

import tkinter as tk
from database_manager import DatabaseManager
from jira_search_ui import open_jira_search


def main():
    """Test the Jira search UI."""
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    
    # Initialize database
    db_manager = DatabaseManager('esl_ap_helper.db')
    
    # Open Jira search window with a test AP ID
    open_jira_search(root, db_manager, ap_id="203820")
    
    root.mainloop()


if __name__ == '__main__':
    main()
