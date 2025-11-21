"""
Error Sanitization Utility
Sanitizes error messages before displaying to users to prevent information disclosure.
"""

import re
import traceback
from typing import Tuple


class ErrorSanitizer:
    """Sanitizes error messages to prevent sensitive information disclosure."""
    
    # Patterns to redact from error messages
    SENSITIVE_PATTERNS = [
        # File paths (Windows and Unix)
        (r'[A-Za-z]:\\[\w\\\.\-]+', '[PATH]'),
        (r'/[\w/\.\-]+/[\w/\.\-]+', '[PATH]'),
        (r'C:\\Users\\[\w]+', '[USER_PATH]'),
        
        # API endpoints and URLs
        (r'https?://[\w\.\-]+/[\w/\-]+', '[API_ENDPOINT]'),
        
        # IP addresses
        (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP_ADDRESS]'),
        
        # API keys/tokens (common patterns)
        (r'[A-Za-z0-9]{32,}', '[TOKEN]'),
        
        # Database connection strings
        (r'(?:password|pwd|token|key)[\s]*=[\s]*[^\s;]+', 'password=[REDACTED]'),
        
        # Email addresses
        (r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '[EMAIL]'),
        
        # SQL statements
        (r'(?i)SELECT .+ FROM', 'SELECT [QUERY] FROM'),
        (r'(?i)INSERT INTO', 'INSERT [QUERY]'),
        (r'(?i)UPDATE .+ SET', 'UPDATE [QUERY] SET'),
        (r'(?i)DELETE FROM', 'DELETE [QUERY]'),
    ]
    
    # Generic error messages for common exception types
    GENERIC_MESSAGES = {
        'ConnectionError': 'Unable to connect to the service. Please check your network connection.',
        'TimeoutError': 'The operation timed out. Please try again.',
        'PermissionError': 'Access denied. You may not have permission to perform this operation.',
        'FileNotFoundError': 'Required file not found. The application may need to be reinstalled.',
        'KeyError': 'Invalid data structure. This may indicate corrupted data.',
        'ValueError': 'Invalid data received. Please check your input.',
        'TypeError': 'Internal data type error. Please report this issue.',
        'AttributeError': 'Internal configuration error. Please report this issue.',
        'ImportError': 'Required component not found. The application may need to be reinstalled.',
        'ModuleNotFoundError': 'Required module missing. Please check installation.',
    }
    
    @staticmethod
    def sanitize_error(error: Exception, user_friendly: bool = True) -> str:
        """
        Sanitize an error message for display to users.
        
        Args:
            error: The exception to sanitize
            user_friendly: If True, return generic message for common errors
            
        Returns:
            Sanitized error message safe for user display
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # For common errors, return generic user-friendly message
        if user_friendly and error_type in ErrorSanitizer.GENERIC_MESSAGES:
            return ErrorSanitizer.GENERIC_MESSAGES[error_type]
        
        # Sanitize the error message
        sanitized = error_message
        
        for pattern, replacement in ErrorSanitizer.SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized)
        
        # If message is empty or very short after sanitization, use generic
        if len(sanitized.strip()) < 5:
            return "An error occurred. Please try again or contact support."
        
        return f"{error_type}: {sanitized}"
    
    @staticmethod
    def get_safe_error_message(error: Exception, 
                               context: str = "",
                               show_type: bool = False) -> str:
        """
        Get a safe, user-friendly error message.
        
        Args:
            error: The exception
            context: Context about what was being done (e.g., "searching Jira")
            show_type: Whether to include exception type
            
        Returns:
            Safe error message for user display
        """
        error_type = type(error).__name__
        
        # Check for known error types with friendly messages
        if error_type in ErrorSanitizer.GENERIC_MESSAGES:
            message = ErrorSanitizer.GENERIC_MESSAGES[error_type]
        else:
            # Sanitize the error message
            message = ErrorSanitizer.sanitize_error(error, user_friendly=False)
        
        # Add context if provided
        if context:
            message = f"Error {context}: {message}"
        
        return message
    
    @staticmethod
    def log_full_error(error: Exception, context: str = ""):
        """
        Log the full error with stack trace (for debugging).
        Use this for logging while showing sanitized version to user.
        
        Args:
            error: The exception
            context: Context about what was being done
        """
        print(f"\n{'='*60}")
        print(f"ERROR LOG - {context}")
        print(f"{'='*60}")
        print(f"Exception Type: {type(error).__name__}")
        print(f"Exception Message: {str(error)}")
        print(f"\nFull Traceback:")
        traceback.print_exc()
        print(f"{'='*60}\n")
    
    @staticmethod
    def handle_error(error: Exception, 
                    context: str = "",
                    log_full: bool = True) -> Tuple[str, str]:
        """
        Handle an error by logging full details and returning safe message.
        
        Args:
            error: The exception
            context: Context about what was being done
            log_full: Whether to log full error details
            
        Returns:
            Tuple of (safe_message, title) for display
        """
        if log_full:
            ErrorSanitizer.log_full_error(error, context)
        
        safe_message = ErrorSanitizer.get_safe_error_message(error, context)
        
        # Generate appropriate title
        error_type = type(error).__name__
        if 'Connection' in error_type or 'Timeout' in error_type:
            title = "Connection Error"
        elif 'Permission' in error_type or 'Access' in error_type:
            title = "Access Denied"
        elif 'File' in error_type:
            title = "File Error"
        else:
            title = "Error"
        
        return safe_message, title


# Convenience functions for common use cases
def sanitize_error_for_user(error: Exception) -> str:
    """Quick function to sanitize error for user display."""
    return ErrorSanitizer.sanitize_error(error, user_friendly=True)


def handle_and_log_error(error: Exception, context: str = "") -> Tuple[str, str]:
    """Quick function to handle error with logging."""
    return ErrorSanitizer.handle_error(error, context, log_full=True)
