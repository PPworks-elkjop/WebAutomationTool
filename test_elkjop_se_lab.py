"""
Test Script for Vusion Manager Pro API - Elkjop SE Lab
Tests the GET stores endpoint specifically for elkjop_se_lab store.
"""

import sys
import json
from vusion_api_config import VusionAPIConfig
from vusion_api_helper import VusionAPIHelper


def configure_api_key():
    """Helper to configure API key for SE/vusion_pro."""
    print("=" * 80)
    print("API Key Configuration for Elkjop SE Lab")
    print("=" * 80)
    print()
    print("Please enter your Vusion Manager Pro API key for Sweden (SE):")
    print("(This will be encrypted and stored securely)")
    print()
    
    api_key = input("API Key: ").strip()
    
    if not api_key:
        print("❌ No API key entered. Exiting.")
        return False
    
    config = VusionAPIConfig()
    
    try:
        config.set_api_key('SE', 'vusion_pro', api_key)
        print()
        print("✓ API key saved successfully!")
        print(f"  Location: {config.config_file}")
        print()
        return True
    except Exception as e:
        print(f"❌ Error saving API key: {e}")
        return False


def test_elkjop_se_lab():
    """Test connection to elkjop_se_lab store."""
    print("=" * 80)
    print("Vusion Manager Pro API - Elkjop SE Lab Test")
    print("=" * 80)
    print()
    
    # Initialize configuration and helper
    config = VusionAPIConfig()
    helper = VusionAPIHelper(config)
    
    # Test parameters
    country = 'SE'
    service = 'vusion_pro'
    store_id = 'elkjop_se_lab.lab5'  # Lab environment store ID
    
    print(f"Configuration:")
    print(f"  Country: {country}")
    print(f"  Service: Vusion Manager Pro")
    print(f"  Store ID: {store_id}")
    print()
    
    # Check if API key is configured
    api_key = config.get_api_key(country, service)
    if not api_key:
        print("❌ No API key configured for SE/vusion_pro!")
        print()
        print("Would you like to configure it now? (y/n): ", end='')
        
        try:
            response = input().strip().lower()
            if response == 'y':
                print()
                if configure_api_key():
                    # Reload the config
                    config = VusionAPIConfig()
                    helper = VusionAPIHelper(config)
                    api_key = config.get_api_key(country, service)
                else:
                    return False
            else:
                print("Please configure the API key first.")
                return False
        except KeyboardInterrupt:
            print("\nCancelled.")
            return False
    
    # Mask the API key for display
    if len(api_key) > 12:
        masked_key = f"{api_key[:8]}...{api_key[-4:]}"
    else:
        masked_key = "[key too short to display safely]"
    
    print(f"✓ API key configured")
    print(f"  Key (masked): {masked_key}")
    print()
    
    # Step 1: Test basic connectivity
    print("-" * 80)
    print("Step 1: Testing API connectivity...")
    print("-" * 80)
    
    success, message = helper.test_connection(country, service)
    
    if success:
        print(f"✓ {message}")
    else:
        print(f"❌ {message}")
        return False
    
    print()
    
    # Step 2: Build request
    print("-" * 80)
    print("Step 2: Building request...")
    print("-" * 80)
    
    try:
        url = config.get_endpoint_url(service, 'stores', storeId=store_id)
        print(f"Request URL: {url}")
        
        headers = config.get_request_headers(country, service)
        print(f"Headers:")
        for key, value in headers.items():
            if key == 'Ocp-Apim-Subscription-Key':
                print(f"  {key}: {masked_key}")
            else:
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"❌ Error building request: {e}")
        return False
    
    print()
    
    # Step 3: Query store information
    print("-" * 80)
    print("Step 3: Querying store information...")
    print("-" * 80)
    
    success, data = helper.make_request(
        country=country,
        service=service,
        endpoint='stores',
        method='GET',
        storeId=store_id
    )
    
    if not success:
        print(f"❌ Request failed: {data}")
        print()
        print("Possible issues:")
        print("  - Store ID 'elkjop_se_lab' might not exist")
        print("  - API key might not have access to this store")
        print("  - Network connectivity issue")
        print()
        print("Try checking if there's a different store ID format needed.")
        return False
    
    print("✓ Request successful!")
    print()
    
    # Step 4: Display store information
    print("-" * 80)
    print("Step 4: Store Information")
    print("-" * 80)
    print()
    
    # Basic store info
    print("Basic Information:")
    basic_fields = ['id', 'name', 'status', 'storeType', 'timeZone', 'country']
    for field in basic_fields:
        value = data.get(field, 'N/A')
        print(f"  {field.capitalize()}: {value}")
    
    print()
    
    # Gateway/AP information (this is what we need for AP Panel)
    print("Gateway/AP Status (Key for AP Panel integration):")
    
    if 'gateways' in data:
        gateways = data['gateways']
        
        if isinstance(gateways, list):
            print(f"  Total Gateways: {len(gateways)}")
            print()
            
            if gateways:
                print("  Gateway Details:")
                for idx, gw in enumerate(gateways, 1):
                    gw_id = gw.get('id', 'N/A')
                    gw_name = gw.get('name', 'N/A')
                    gw_status = gw.get('status', 'N/A')
                    gw_online = gw.get('online', 'N/A')
                    gw_ip = gw.get('ipAddress', 'N/A')
                    
                    online_indicator = "🟢" if gw_online else "🔴"
                    print(f"    {idx}. {online_indicator} {gw_id}")
                    print(f"       Name: {gw_name}")
                    print(f"       Status: {gw_status}")
                    print(f"       Online: {gw_online}")
                    print(f"       IP: {gw_ip}")
                    print()
            else:
                print("  No gateways found in store.")
        elif isinstance(gateways, dict):
            print(f"  Gateways info (dict): {gateways}")
        else:
            print(f"  Gateways: {gateways}")
    else:
        print("  ⚠ No 'gateways' field in response")
        print("  The store data might not include gateway information in the main store endpoint.")
        print("  We may need to use the separate /stores/{storeId}/gateways endpoint.")
    
    print()
    
    # Additional useful information
    if 'address' in data:
        print("Address:")
        addr = data['address']
        if isinstance(addr, dict):
            for key, value in addr.items():
                print(f"  {key}: {value}")
        else:
            print(f"  {addr}")
        print()
    
    # Full JSON response
    print("-" * 80)
    print("Full Response Data (for reference):")
    print("-" * 80)
    print(json.dumps(data, indent=2))
    print()
    
    print("=" * 80)
    print("✓ Test completed successfully!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Verify gateway/AP information is available")
    print("  2. Integrate into AP Panel to show online/offline status")
    print("  3. Map AP IP addresses to Vusion gateway data")
    print()
    
    return True


def test_gateways_endpoint():
    """Test the dedicated gateways endpoint."""
    print()
    print("=" * 80)
    print("Testing Dedicated Gateways Endpoint")
    print("=" * 80)
    print()
    
    config = VusionAPIConfig()
    helper = VusionAPIHelper(config)
    
    country = 'SE'
    service = 'vusion_pro'
    store_id = 'elkjop_se_lab'
    
    print(f"Querying: GET /stores/{store_id}/gateways")
    print()
    
    try:
        url = config.get_endpoint_url(service, 'gateways', storeId=store_id)
        print(f"URL: {url}")
        print()
        
        success, data = helper.make_request(
            country=country,
            service=service,
            endpoint='gateways',
            method='GET',
            storeId=store_id
        )
        
        if success:
            print("✓ Gateway endpoint query successful!")
            print()
            print(json.dumps(data, indent=2))
            print()
            
            # Try to extract gateway list
            if isinstance(data, list):
                print(f"Found {len(data)} gateways:")
                for gw in data:
                    gw_id = gw.get('id', 'N/A')
                    online = gw.get('online', 'N/A')
                    status = "🟢 ONLINE" if online else "🔴 OFFLINE"
                    print(f"  - {gw_id}: {status}")
            elif isinstance(data, dict) and 'gateways' in data:
                gateways = data['gateways']
                print(f"Found {len(gateways)} gateways:")
                for gw in gateways:
                    gw_id = gw.get('id', 'N/A')
                    online = gw.get('online', 'N/A')
                    status = "🟢 ONLINE" if online else "🔴 OFFLINE"
                    print(f"  - {gw_id}: {status}")
        else:
            print(f"⚠ Gateway endpoint query failed: {data}")
            print("This endpoint might not be available or might be included in the main store data.")
    
    except Exception as e:
        print(f"⚠ Error: {e}")
    
    print()


if __name__ == '__main__':
    print()
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║     Vusion Manager Pro API Test - Elkjop SE Lab                          ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Run main test
    success = test_elkjop_se_lab()
    
    # If successful, try the gateways endpoint
    if success:
        try:
            test_gateways_endpoint()
        except Exception as e:
            print(f"⚠ Gateway endpoint test skipped: {e}")
    
    print()
    if success:
        print("✓ All tests completed successfully!")
        print()
        print("The API is working and ready to integrate into the AP Panel.")
    else:
        print("❌ Tests failed. Please check configuration and try again.")
    
    print()
    input("Press Enter to exit...")
