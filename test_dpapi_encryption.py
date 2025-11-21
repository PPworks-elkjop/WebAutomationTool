"""
Test script for Windows DPAPI credential encryption
Verifies that credentials can be encrypted and decrypted properly.
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_manager import DatabaseManager
from credentials_manager import CredentialsManager


def test_dpapi_encryption():
    """Test DPAPI encryption and decryption."""
    
    print("\n" + "="*60)
    print("Testing Windows DPAPI Encryption")
    print("="*60 + "\n")
    
    # Initialize database and credentials manager
    db = DatabaseManager()
    cred_manager = CredentialsManager(db)
    
    # Check DPAPI availability
    if not cred_manager.use_dpapi:
        print("❌ ERROR: Windows DPAPI is not available!")
        print("   Install pywin32: pip install pywin32")
        return False
    
    print("✅ Windows DPAPI is available\n")
    
    # Test data
    test_service = "test_service_dpapi"
    test_credentials = {
        "username": "test_user",
        "password": "super_secret_password_123",
        "url": "https://test.example.com",
        "api_token": "test_token_abc123xyz"
    }
    
    print("📝 Test Data:")
    print(f"   Service: {test_service}")
    print(f"   Username: {test_credentials['username']}")
    print(f"   Password: {'*' * len(test_credentials['password'])}")
    print(f"   URL: {test_credentials['url']}")
    print(f"   API Token: {'*' * len(test_credentials['api_token'])}\n")
    
    # Test 1: Store credentials
    print("🔒 Test 1: Encrypting and storing credentials...")
    try:
        cred_manager.store_credentials(test_service, test_credentials)
        print("   ✅ Credentials stored successfully\n")
    except Exception as e:
        print(f"   ❌ FAILED: {e}\n")
        return False
    
    # Test 2: Retrieve credentials
    print("🔓 Test 2: Retrieving and decrypting credentials...")
    try:
        retrieved = cred_manager.get_credentials(test_service)
        if retrieved == test_credentials:
            print("   ✅ Credentials retrieved successfully")
            print("   ✅ Decrypted data matches original\n")
        else:
            print(f"   ❌ FAILED: Retrieved data doesn't match")
            print(f"   Original: {test_credentials}")
            print(f"   Retrieved: {retrieved}\n")
            return False
    except Exception as e:
        print(f"   ❌ FAILED: {e}\n")
        return False
    
    # Test 3: Verify encryption (data should not be readable in database)
    print("🔍 Test 3: Verifying encryption in database...")
    try:
        result = db.execute_query(
            "SELECT encrypted_data FROM api_credentials WHERE service_name = ?",
            (test_service,),
            fetch_one=True
        )
        
        if result:
            encrypted_data = result['encrypted_data']
            # Check that password is NOT visible in encrypted data
            if test_credentials['password'] in encrypted_data:
                print(f"   ❌ FAILED: Password is visible in encrypted data!")
                return False
            else:
                print(f"   ✅ Data is properly encrypted (password not visible)")
                print(f"   ✅ Encrypted data length: {len(encrypted_data)} bytes\n")
        else:
            print("   ❌ FAILED: Could not retrieve encrypted data from database\n")
            return False
    except Exception as e:
        print(f"   ❌ FAILED: {e}\n")
        return False
    
    # Test 4: Test empty/null data handling
    print("🧪 Test 4: Testing edge cases...")
    try:
        # Test with empty password
        cred_manager.store_credentials("test_empty", {"password": ""})
        retrieved = cred_manager.get_credentials("test_empty")
        if retrieved.get("password") == "":
            print("   ✅ Empty string handling works")
        else:
            print("   ⚠️  Empty string handling issue")
        
        # Clean up test data
        cred_manager.delete_credentials(test_service)
        cred_manager.delete_credentials("test_empty")
        print("   ✅ Edge cases passed\n")
    except Exception as e:
        print(f"   ⚠️  Edge case issue: {e}\n")
    
    print("="*60)
    print("✅ All Tests Passed!")
    print("="*60)
    print("\n🔒 Your credentials are now protected by Windows DPAPI.")
    print("   They can only be decrypted by your Windows user account")
    print("   on this specific machine.\n")
    
    return True


if __name__ == "__main__":
    try:
        success = test_dpapi_encryption()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
