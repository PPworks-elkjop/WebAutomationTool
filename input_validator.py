"""
Input Validation Helpers for WebAutomationTool
Centralized validation for all user inputs with security-focused checks.
"""

import re
import ipaddress
from typing import Tuple


class InputValidator:
    """Centralized input validation for all user inputs."""
    
    @staticmethod
    def ap_id(value: str) -> Tuple[bool, str]:
        """
        Validate AP ID format.
        
        Allowed formats:
        - Alphanumeric with dash, underscore, dot: AP-001, NSP25, CiG-09C
        - Pure numeric: 201265
        - Can include spaces for readability
        - Length: 1-50 characters
        
        Args:
            value: AP ID string to validate
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        
        Examples:
            >>> InputValidator.ap_id("AP-001")
            (True, "")
            >>> InputValidator.ap_id("201265")
            (True, "")
            >>> InputValidator.ap_id("NSP25")
            (True, "")
            >>> InputValidator.ap_id("Test AP 01")
            (True, "")
            >>> InputValidator.ap_id("")
            (False, "AP ID cannot be empty")
            >>> InputValidator.ap_id("AP@#$")
            (False, "AP ID contains invalid characters...")
        """
        if not value:
            return False, "AP ID cannot be empty"
        
        # Strip whitespace for length check
        value_stripped = value.strip()
        
        if len(value_stripped) > 50:
            return False, "AP ID too long (max 50 characters)"
        
        # Allow letters, numbers, dash, underscore, dot, space
        # This covers: AP-001, NSP25, CiG-09C, 201265, Test AP 01
        if not re.match(r'^[A-Za-z0-9\s._-]+$', value_stripped):
            return False, "AP ID contains invalid characters (use only letters, numbers, space, dash, underscore, dot)"
        
        # Prevent only spaces/dashes/dots
        if not re.search(r'[A-Za-z0-9]', value_stripped):
            return False, "AP ID must contain at least one letter or number"
        
        return True, ""
    
    @staticmethod
    def ip_address(value: str) -> Tuple[bool, str]:
        """
        Validate IP address format (IPv4 or IPv6).
        
        Uses Python's ipaddress module for robust validation.
        
        Args:
            value: IP address string to validate
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        
        Examples:
            >>> InputValidator.ip_address("192.168.1.1")
            (True, "")
            >>> InputValidator.ip_address("10.0.0.1")
            (True, "")
            >>> InputValidator.ip_address("2001:0db8:85a3::8a2e:0370:7334")
            (True, "")
            >>> InputValidator.ip_address("")
            (False, "IP address cannot be empty")
            >>> InputValidator.ip_address("999.999.999.999")
            (False, "Invalid IP address format")
        """
        if not value:
            return False, "IP address cannot be empty"
        
        value = value.strip()
        
        try:
            # This handles both IPv4 and IPv6
            ipaddress.ip_address(value)
            return True, ""
        except ValueError:
            return False, f"Invalid IP address format: {value}"
    
    @staticmethod
    def store_id(value: str) -> Tuple[bool, str]:
        """
        Validate store ID format.
        
        Allowed: alphanumeric, dash, underscore, dot
        Length: 1-50 characters
        
        Args:
            value: Store ID string to validate
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        
        Examples:
            >>> InputValidator.store_id("S001")
            (True, "")
            >>> InputValidator.store_id("elkjop_se_lab.lab5")
            (True, "")
            >>> InputValidator.store_id("")
            (False, "Store ID cannot be empty")
        """
        if not value:
            return False, "Store ID cannot be empty"
        
        value = value.strip()
        
        if len(value) > 50:
            return False, "Store ID too long (max 50 characters)"
        
        if not re.match(r'^[A-Za-z0-9._-]+$', value):
            return False, "Store ID contains invalid characters (use only letters, numbers, dash, underscore, dot)"
        
        return True, ""
    
    @staticmethod
    def store_alias(value: str) -> Tuple[bool, str]:
        """
        Validate store alias (display name).
        
        More permissive than store_id, allows spaces and more characters.
        Length: 0-100 characters (can be empty)
        
        Args:
            value: Store alias string to validate
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not value:
            return True, ""  # Can be empty
        
        value = value.strip()
        
        if len(value) > 100:
            return False, "Store alias too long (max 100 characters)"
        
        # Allow letters, numbers, spaces, and common punctuation
        if not re.match(r'^[A-Za-z0-9\s._\-,()&]+$', value):
            return False, "Store alias contains invalid characters"
        
        return True, ""
    
    @staticmethod
    def comment(value: str, max_length: int = 5000) -> Tuple[bool, str]:
        """
        Validate comment/note text with XSS prevention.
        
        Checks for:
        - Length limit (default 5000 characters)
        - Potentially dangerous script content
        
        Args:
            value: Comment text to validate
            max_length: Maximum allowed length (default 5000)
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not value:
            return True, ""  # Empty comments are allowed
        
        if len(value) > max_length:
            return False, f"Comment too long (max {max_length} characters)"
        
        # Basic XSS prevention - check for potentially dangerous content
        dangerous_patterns = [
            '<script', 'javascript:', 'onerror=', 'onload=', 
            '<iframe', 'onclick=', 'oninput=', 'onchange='
        ]
        value_lower = value.lower()
        
        for pattern in dangerous_patterns:
            if pattern in value_lower:
                return False, "Comment contains potentially dangerous content (script tags or event handlers not allowed)"
        
        return True, ""
    
    @staticmethod
    def username(value: str) -> Tuple[bool, str]:
        """
        Validate username format.
        
        Allowed: alphanumeric, underscore, dash
        Length: 3-50 characters
        
        Args:
            value: Username string to validate
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        
        Examples:
            >>> InputValidator.username("peterander")
            (True, "")
            >>> InputValidator.username("admin_user")
            (True, "")
            >>> InputValidator.username("ab")
            (False, "Username too short (min 3 characters)")
        """
        if not value:
            return False, "Username cannot be empty"
        
        value = value.strip()
        
        if len(value) < 3:
            return False, "Username too short (min 3 characters)"
        
        if len(value) > 50:
            return False, "Username too long (max 50 characters)"
        
        if not re.match(r'^[A-Za-z0-9_-]+$', value):
            return False, "Username can only contain letters, numbers, underscore, and dash"
        
        return True, ""
    
    @staticmethod
    def full_name(value: str) -> Tuple[bool, str]:
        """
        Validate full name format.
        
        Allows: letters, spaces, apostrophes, hyphens
        Length: 1-100 characters
        
        Args:
            value: Full name string to validate
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not value:
            return False, "Full name cannot be empty"
        
        value = value.strip()
        
        if len(value) > 100:
            return False, "Full name too long (max 100 characters)"
        
        # Allow letters, spaces, apostrophes, hyphens, dots (for names like "O'Brien" or "Mary-Jane" or "Dr. Smith")
        if not re.match(r"^[A-Za-zÀ-ÿ\s.'-]+$", value):
            return False, "Full name contains invalid characters"
        
        return True, ""
    
    @staticmethod
    def email(value: str) -> Tuple[bool, str]:
        """
        Validate email address format.
        
        Basic email validation using regex.
        Length: 0-100 characters (can be empty)
        
        Args:
            value: Email address string to validate
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not value:
            return True, ""  # Email is optional
        
        value = value.strip()
        
        if len(value) > 100:
            return False, "Email address too long (max 100 characters)"
        
        # Basic email regex (not RFC 5322 compliant, but good enough for most cases)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, value):
            return False, "Invalid email address format"
        
        return True, ""
    
    @staticmethod
    def url(value: str) -> Tuple[bool, str]:
        """
        Validate URL format.
        
        Must start with http:// or https://
        Length: 1-500 characters
        
        Args:
            value: URL string to validate
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not value:
            return False, "URL cannot be empty"
        
        value = value.strip()
        
        if len(value) > 500:
            return False, "URL too long (max 500 characters)"
        
        if not value.startswith('http://') and not value.startswith('https://'):
            return False, "URL must start with http:// or https://"
        
        # Basic URL validation
        url_pattern = r'^https?://[a-zA-Z0-9.-]+(:[0-9]+)?(/.*)?$'
        
        if not re.match(url_pattern, value):
            return False, "Invalid URL format"
        
        return True, ""
    
    @staticmethod
    def port(value: str) -> Tuple[bool, str]:
        """
        Validate port number.
        
        Must be integer between 1 and 65535.
        
        Args:
            value: Port number string to validate
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not value:
            return False, "Port number cannot be empty"
        
        try:
            port_num = int(value)
            
            if port_num < 1 or port_num > 65535:
                return False, "Port must be between 1 and 65535"
            
            return True, ""
        except ValueError:
            return False, "Port must be a valid number"
    
    @staticmethod
    def mac_address(value: str) -> Tuple[bool, str]:
        """
        Validate MAC address format.
        
        Accepts formats: XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX
        
        Args:
            value: MAC address string to validate
            
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        if not value:
            return True, ""  # MAC address is optional
        
        value = value.strip().upper()
        
        # Accept colon or hyphen separated format
        mac_pattern = r'^([0-9A-F]{2}[:-]){5}[0-9A-F]{2}$'
        
        if not re.match(mac_pattern, value):
            return False, "Invalid MAC address format (use XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX)"
        
        return True, ""


# Convenience functions for quick validation
def validate_ap_id(value: str) -> Tuple[bool, str]:
    """Quick access to AP ID validation."""
    return InputValidator.ap_id(value)


def validate_ip_address(value: str) -> Tuple[bool, str]:
    """Quick access to IP address validation."""
    return InputValidator.ip_address(value)


def validate_store_id(value: str) -> Tuple[bool, str]:
    """Quick access to Store ID validation."""
    return InputValidator.store_id(value)


if __name__ == "__main__":
    # Test the validators
    print("Testing Input Validators")
    print("=" * 50)
    
    # Test AP IDs
    test_aps = ["AP-001", "201265", "NSP25", "CiG-09C", "Test AP", "", "A"*60, "AP@#$"]
    print("\nAP ID Validation:")
    for ap in test_aps:
        valid, msg = InputValidator.ap_id(ap)
        status = "✓" if valid else "✗"
        print(f"  {status} '{ap}': {msg if msg else 'Valid'}")
    
    # Test IPs
    test_ips = ["192.168.1.1", "10.0.0.1", "999.999.999.999", "", "2001:0db8:85a3::8a2e:0370:7334"]
    print("\nIP Address Validation:")
    for ip in test_ips:
        valid, msg = InputValidator.ip_address(ip)
        status = "✓" if valid else "✗"
        print(f"  {status} '{ip}': {msg if msg else 'Valid'}")
    
    # Test usernames
    test_users = ["peterander", "admin_user", "ab", "user@name", "a"*60]
    print("\nUsername Validation:")
    for user in test_users:
        valid, msg = InputValidator.username(user)
        status = "✓" if valid else "✗"
        print(f"  {status} '{user}': {msg if msg else 'Valid'}")
    
    # Test emails
    test_emails = ["test@example.com", "user.name+tag@domain.co.uk", "invalid.email", "", "@domain.com"]
    print("\nEmail Validation:")
    for email in test_emails:
        valid, msg = InputValidator.email(email)
        status = "✓" if valid else "✗"
        print(f"  {status} '{email}': {msg if msg else 'Valid'}")
    
    print("\n" + "=" * 50)
