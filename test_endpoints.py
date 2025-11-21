"""
Test different endpoints to find where transmitters data comes from
"""

import urllib.request
import json
from vusion_api_config import VusionAPIConfig

config = VusionAPIConfig()
store_id = 'elkjop_se_lab.lab5'
headers = config.get_request_headers('SE', 'vusion_pro')

base_url = 'https://api-eu.vusion.io/vusion-pro/v1'

endpoints_to_test = [
    f'/stores/{store_id}',
    f'/stores/{store_id}/transmitters',
    f'/stores/{store_id}/devices',
    f'/stores/{store_id}/accesspoints',
    f'/stores/{store_id}?include=transmitters',
    f'/stores/{store_id}?expand=transmitters',
    f'/transmitters?storeId={store_id}',
]

print("=" * 80)
print("Testing Vusion API Endpoints for Transmitters")
print("=" * 80)
print()

for endpoint in endpoints_to_test:
    url = base_url + endpoint
    print(f"Testing: {endpoint}")
    print(f"  URL: {url}")
    
    try:
        req = urllib.request.Request(url, headers=headers)
        req.get_method = lambda: 'GET'
        
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.getcode()
            data = json.loads(response.read().decode('utf-8'))
            
            print(f"  ✓ Status: {status}")
            
            # Check if transmitters data is present
            if isinstance(data, dict):
                if 'transmitters' in data:
                    trans = data['transmitters']
                    if isinstance(trans, list):
                        print(f"  ✓ FOUND: transmitters list with {len(trans)} items")
                        if trans:
                            print(f"  ✓ First transmitter ID: {trans[0].get('id', 'N/A')}")
                    else:
                        print(f"  ✓ FOUND: transmitters field (type: {type(trans).__name__})")
                else:
                    print(f"  Available fields: {', '.join(list(data.keys())[:10])}")
            elif isinstance(data, list):
                print(f"  Response is a list with {len(data)} items")
                if data:
                    print(f"  First item type: {type(data[0]).__name__}")
                    if isinstance(data[0], dict) and 'id' in data[0]:
                        print(f"  ✓ FOUND: List of items, first ID: {data[0].get('id')}")
            
            print()
    
    except urllib.error.HTTPError as e:
        print(f"  ✗ HTTP Error {e.code}: {e.reason}")
        print()
    except Exception as e:
        print(f"  ✗ Error: {e}")
        print()

print("=" * 80)
print("Test complete")
print("=" * 80)
