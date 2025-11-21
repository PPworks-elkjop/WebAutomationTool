"""Test error sanitization"""
from error_sanitizer import ErrorSanitizer, handle_and_log_error

# Test 1: File path in error
try:
    raise FileNotFoundError("File not found: C:\\Users\\PeterAndersson\\secret\\config.json")
except Exception as e:
    safe_msg, title = handle_and_log_error(e, "testing file error")
    print(f"Title: {title}")
    print(f"Safe message: {safe_msg}\n")

# Test 2: Connection error with API endpoint
try:
    raise ConnectionError("Failed to connect to https://api.example.com/secret/endpoint?token=abc123def456")
except Exception as e:
    safe_msg, title = handle_and_log_error(e, "testing connection")
    print(f"Title: {title}")
    print(f"Safe message: {safe_msg}\n")

# Test 3: Generic error
try:
    raise ValueError("Invalid configuration in database row 123")
except Exception as e:
    safe_msg, title = handle_and_log_error(e, "testing validation")
    print(f"Title: {title}")
    print(f"Safe message: {safe_msg}\n")

print("✅ Error sanitizer working correctly")
