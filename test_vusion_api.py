"""
Test script for Vusion API Configuration
Run this to verify the setup works correctly.
"""

from vusion_api_config import VusionAPIConfig
from vusion_api_helper import VusionAPIHelper

def test_config():
    """Test basic configuration."""
    print("=" * 60)
    print("Testing Vusion API Configuration")
    print("=" * 60)
    
    config = VusionAPIConfig()
    
    # Test 1: Build store ID
    print("\n[Test 1] Building Store IDs")
    print("-" * 60)
    
    test_cases = [
        ('FI', 'gigantti', '4010'),
        ('NO', 'elkjop', '1234'),
        ('SE', 'elgiganten', '5678'),
    ]
    
    for country, chain, store_num in test_cases:
        store_id = config.build_store_id(country, chain, store_num)
        print(f"  {country}/{chain}/{store_num} → {store_id}")
    
    # Test 2: Build URLs
    print("\n[Test 2] Building Endpoint URLs")
    print("-" * 60)
    
    url = config.get_endpoint_url('vusion_pro', 'stores', storeId='gigantti_fi.4010')
    print(f"  Stores endpoint: {url}")
    
    url = config.get_endpoint_url('vusion_pro', 'labels', storeId='elkjop_no.1234')
    print(f"  Labels endpoint: {url}")
    
    url = config.get_endpoint_url('vusion_pro', 'gateways', storeId='elgiganten_se.5678')
    print(f"  Gateways endpoint: {url}")
    
    # Test 3: List configured keys
    print("\n[Test 3] Configured API Keys")
    print("-" * 60)
    
    keys = config.list_configured_keys()
    
    if keys:
        for key_info in keys:
            print(f"  ✓ {key_info['country']} - {key_info['service_name']}")
    else:
        print("  No API keys configured yet.")
        print("  Use 'Manage Vusion API Keys' in the dashboard to add keys.")
    
    return config


def test_helper():
    """Test API helper with actual requests (requires configured keys)."""
    print("\n" + "=" * 60)
    print("Testing Vusion API Helper")
    print("=" * 60)
    
    config = VusionAPIConfig()
    keys = config.list_configured_keys()
    
    if not keys:
        print("\n⚠️  No API keys configured. Skipping API tests.")
        print("   Configure keys using 'Manage Vusion API Keys' first.")
        return
    
    helper = VusionAPIHelper(config)
    
    # Test connection for each configured key
    print("\n[Test 4] Testing API Connections")
    print("-" * 60)
    
    for key_info in keys:
        country = key_info['country']
        service = key_info['service'].split('_')[0]  # Get service key
        
        # Find service key
        for svc_key in ['vusion_pro', 'vusion_cloud', 'vusion_retail']:
            if config.SERVICES[svc_key]['name'] == key_info['service_name']:
                service = svc_key
                break
        
        print(f"\n  Testing {country}/{service}...")
        success, message = helper.test_connection(country, service)
        
        if success:
            print(f"    ✓ {message}")
        else:
            print(f"    ✗ {message}")


def test_gui():
    """Test GUI configuration dialog."""
    print("\n" + "=" * 60)
    print("Testing Vusion API Configuration GUI")
    print("=" * 60)
    
    print("\nLaunching GUI...")
    print("Use the GUI to:")
    print("  1. Add API keys for your countries")
    print("  2. Test connections")
    print("  3. Query stores")
    print("\nClose the window when done.")
    
    try:
        from vusion_config_dialog import VusionAPIConfigDialog
        dialog = VusionAPIConfigDialog()
        dialog.show()
        print("\n✓ GUI test complete")
    except Exception as e:
        print(f"\n✗ GUI test failed: {e}")


def main():
    """Run all tests."""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         Vusion API Configuration Test Suite              ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    # Test configuration
    config = test_config()
    
    # Test helper
    test_helper()
    
    # Test GUI
    print("\n\nWould you like to test the GUI? (y/n): ", end='')
    try:
        response = input().strip().lower()
        if response == 'y':
            test_gui()
        else:
            print("Skipping GUI test.")
    except KeyboardInterrupt:
        print("\nTest interrupted.")
    
    print("\n" + "=" * 60)
    print("All tests complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Open VERA dashboard")
    print("  2. Go to Admin → Manage Vusion API Keys")
    print("  3. Add API keys for your countries")
    print("  4. Test connections")
    print("  5. Start querying stores!")
    print("")


if __name__ == '__main__':
    main()
