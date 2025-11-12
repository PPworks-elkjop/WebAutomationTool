"""
Test script for the new SQLite database system
"""

from credential_manager_v2 import CredentialManager
from database_manager import DatabaseManager

def test_database():
    print("Testing VERA SQLite Database System")
    print("=" * 60)
    print()
    
    # Initialize
    db = DatabaseManager()
    creds = CredentialManager()
    
    # Show stats
    stats = db.get_database_stats()
    print("Current Database Statistics:")
    print(f"  Total APs:       {stats['total_aps']}")
    print(f"  Online:          {stats['online_aps']}")
    print(f"  Offline:         {stats['offline_aps']}")
    print(f"  Total Events:    {stats['total_events']}")
    print(f"  Database:        {stats['database_file']}")
    print(f"  Encryption:      {stats['encryption']}")
    print()
    
    # Test adding an AP
    print("Testing: Add new AP...")
    test_ap = {
        'ap_id': 'TEST-AP-001',
        'store_id': 'TEST-STORE',
        'store_alias': 'Test Store',
        'retail_chain': 'Test Chain',
        'ip_address': '192.168.1.100',
        'type': 'VusionRail',
        'username_webui': 'admin',
        'password_webui': 'secret123',  # Will be encrypted
        'username_ssh': 'root',
        'password_ssh': 'sshpass456',   # Will be encrypted
        'su_password': 'supass789',      # Will be encrypted
        'notes': 'Test AP for validation'
    }
    
    success, msg = creds.add_credential(test_ap)
    print(f"  Result: {msg}")
    print()
    
    # Test retrieval
    print("Testing: Retrieve AP...")
    retrieved = creds.find_by_ap_id('TEST-AP-001')
    if retrieved:
        print(f"  ✓ Found AP: {retrieved['ap_id']}")
        print(f"    Store: {retrieved['store_id']}")
        print(f"    IP: {retrieved['ip_address']}")
        print(f"    Web Password (decrypted): {retrieved['password_webui']}")
        print(f"    SSH Password (decrypted): {retrieved['password_ssh']}")
        print()
    
    # Test history logging
    print("Testing: Add history event...")
    success = db.add_history_event(
        ap_id='TEST-AP-001',
        event_type='test',
        description='Test event for validation',
        user='test_user',
        success=True
    )
    print(f"  Result: {'✓ Added' if success else '✗ Failed'}")
    print()
    
    # Test status update
    print("Testing: Update AP status...")
    db.update_ap_status('TEST-AP-001', 'online', ping_time=15.5)
    updated = creds.find_by_ap_id('TEST-AP-001')
    print(f"  Status: {updated['status']}")
    print(f"  Last Ping: {updated['last_ping_time']}ms")
    print()
    
    # Test search
    print("Testing: Search functionality...")
    results = creds.search('TEST')
    print(f"  Found {len(results)} results for 'TEST'")
    print()
    
    # Test update
    print("Testing: Update AP...")
    success, msg = creds.update_credential('TEST-STORE', 'TEST-AP-001', {
        'notes': 'Updated test note',
        'ip_address': '192.168.1.101'
    })
    print(f"  Result: {msg}")
    print()
    
    # Show final stats
    stats = db.get_database_stats()
    print("Final Database Statistics:")
    print(f"  Total APs:       {stats['total_aps']}")
    print(f"  Total Events:    {stats['total_events']}")
    print()
    
    # Cleanup
    print("Cleanup: Removing test AP...")
    success, msg = creds.delete_credential('TEST-STORE', 'TEST-AP-001')
    print(f"  Result: {msg}")
    print()
    
    print("=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_database()
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
