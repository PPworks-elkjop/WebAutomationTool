"""
Debug script to check Vusion API configuration and test connection
"""

import sys
import traceback

print("=" * 80)
print("Vusion API Debug")
print("=" * 80)
print()

# Step 1: Check if modules can be imported
print("Step 1: Checking imports...")
try:
    from vusion_api_config import VusionAPIConfig
    print("  ✓ vusion_api_config imported")
except Exception as e:
    print(f"  ✗ Failed to import vusion_api_config: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    from vusion_api_helper import VusionAPIHelper
    print("  ✓ vusion_api_helper imported")
except Exception as e:
    print(f"  ✗ Failed to import vusion_api_helper: {e}")
    traceback.print_exc()
    sys.exit(1)

print()

# Step 2: Initialize config
print("Step 2: Initializing configuration...")
try:
    config = VusionAPIConfig()
    print(f"  ✓ Config initialized")
    print(f"  Config file: {config.config_file}")
    print(f"  Config file exists: {config.config_file.exists()}")
    print(f"  Key file: {config.key_file}")
    print(f"  Key file exists: {config.key_file.exists()}")
except Exception as e:
    print(f"  ✗ Failed to initialize config: {e}")
    traceback.print_exc()
    sys.exit(1)

print()

# Step 3: Check for API key
print("Step 3: Checking for API key...")
try:
    api_key = config.get_api_key('SE', 'vusion_pro')
    if api_key:
        masked = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "[short key]"
        print(f"  ✓ API key found: {masked}")
    else:
        print("  ✗ No API key configured for SE/vusion_pro")
        print()
        print("  To configure, run:")
        print("    python configure_vusion_se_lab.py")
        print()
        print("  Or in Python:")
        print("    from vusion_api_config import VusionAPIConfig")
        print("    config = VusionAPIConfig()")
        print("    config.set_api_key('SE', 'vusion_pro', 'YOUR-KEY-HERE')")
        sys.exit(1)
except Exception as e:
    print(f"  ✗ Error checking API key: {e}")
    traceback.print_exc()
    sys.exit(1)

print()

# Step 4: Build store ID and URL
print("Step 4: Building request details...")
try:
    store_id = config.build_store_id('SE', 'elkjop', 'lab5')
    print(f"  Store ID: {store_id}")
    
    url = config.get_endpoint_url('vusion_pro', 'stores', storeId=store_id)
    print(f"  URL: {url}")
    
    headers = config.get_request_headers('SE', 'vusion_pro')
    print(f"  Headers: {list(headers.keys())}")
except Exception as e:
    print(f"  ✗ Error building request: {e}")
    traceback.print_exc()
    sys.exit(1)

print()

# Step 5: Make actual API request
print("Step 5: Making API request...")
try:
    helper = VusionAPIHelper(config)
    
    success, data = helper.make_request(
        country='SE',
        service='vusion_pro',
        endpoint='stores',
        method='GET',
        storeId=store_id
    )
    
    if success:
        print(f"  ✓ Request successful!")
        print()
        print(f"  Store ID: {data.get('id', 'N/A')}")
        print(f"  Store Name: {data.get('name', 'N/A')}")
        print(f"  Status: {data.get('status', 'N/A')}")
        
        if 'gateways' in data:
            gateways = data['gateways']
            if isinstance(gateways, list):
                print(f"  Gateways: {len(gateways)}")
                for gw in gateways[:3]:
                    print(f"    - {gw.get('id')}: {'🟢 Online' if gw.get('online') else '🔴 Offline'}")
        
        print()
        print("=" * 80)
        print("✓ SUCCESS - API is working!")
        print("=" * 80)
    else:
        print(f"  ✗ Request failed: {data}")
        print()
        print("=" * 80)
        print("✗ FAILED - Check error message above")
        print("=" * 80)
        
except Exception as e:
    print(f"  ✗ Error making request: {e}")
    traceback.print_exc()
    sys.exit(1)

print()
