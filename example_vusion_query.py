"""
Quick example showing how to build store ID for elkjop_se_lab.lab5
and make a request to Vusion Manager Pro API.
"""

from vusion_api_config import VusionAPIConfig
from vusion_api_helper import VusionAPIHelper

# Initialize
config = VusionAPIConfig()
helper = VusionAPIHelper(config)

# Method 1: Using the helper's build_store_id function
# This uses the pattern defined in STORE_PATTERNS
store_id = config.build_store_id('SE', 'elkjop', 'lab5')
print(f"Built store ID: {store_id}")
# Output: elkjop_se_lab.lab5

# Method 2: Direct store ID (if you already know it)
store_id_direct = 'elkjop_se_lab.lab5'

# Make the request
print(f"\nQuerying store: {store_id_direct}")
success, data = helper.make_request(
    country='SE',
    service='vusion_pro',
    endpoint='stores',
    method='GET',
    storeId=store_id_direct
)

if success:
    print("\n✓ Success!")
    print(f"Store name: {data.get('name')}")
    print(f"Store status: {data.get('status')}")
    
    # Check for gateways/APs
    if 'gateways' in data:
        gateways = data['gateways']
        print(f"\nGateways found: {len(gateways) if isinstance(gateways, list) else 'N/A'}")
        
        if isinstance(gateways, list):
            for gw in gateways:
                gw_id = gw.get('id', 'N/A')
                online = gw.get('online', False)
                status = "🟢 ONLINE" if online else "🔴 OFFLINE"
                print(f"  {gw_id}: {status}")
else:
    print(f"\n❌ Error: {data}")
