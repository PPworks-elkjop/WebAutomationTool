"""
Debug script to see actual transmitters data from API response
"""

import json
from vusion_api_config import VusionAPIConfig
from vusion_api_helper import VusionAPIHelper

print("=" * 80)
print("Debug: View Transmitters Data Structure")
print("=" * 80)
print()

config = VusionAPIConfig()
helper = VusionAPIHelper(config)

store_id = 'elkjop_se_lab.lab5'

print(f"Querying store: {store_id}")
print()

# Get raw store data
success, data = helper.make_request(
    country='SE',
    service='vusion_pro',
    endpoint='stores',
    method='GET',
    storeId=store_id
)

if success:
    print("✓ Request successful")
    print()
    
    # Check if transmitters field exists
    print("Checking for 'transmitters' field:")
    if 'transmitters' in data:
        transmitters = data['transmitters']
        print(f"  ✓ 'transmitters' field found")
        print(f"  Type: {type(transmitters)}")
        print(f"  Length: {len(transmitters) if isinstance(transmitters, (list, dict)) else 'N/A'}")
        print()
        
        if isinstance(transmitters, list):
            print(f"  Transmitters is a list with {len(transmitters)} items")
            
            if transmitters:
                print()
                print("  First transmitter:")
                print(json.dumps(transmitters[0], indent=4))
                print()
                
                # Show all transmitter IDs
                print("  All transmitter IDs:")
                for idx, t in enumerate(transmitters, 1):
                    t_id = t.get('id', 'NO ID')
                    conn = t.get('connectivity', {})
                    status = conn.get('status', 'UNKNOWN')
                    print(f"    {idx}. ID: {t_id}, Status: {status}")
            else:
                print("  ⚠️ Transmitters list is empty")
        elif isinstance(transmitters, dict):
            print(f"  Transmitters is a dict")
            print(json.dumps(transmitters, indent=4))
        else:
            print(f"  Transmitters value: {transmitters}")
    else:
        print("  ✗ 'transmitters' field NOT found in response")
        print()
        print("  Available top-level fields:")
        for key in data.keys():
            value = data[key]
            if isinstance(value, (list, dict)):
                size = len(value)
                print(f"    - {key} ({type(value).__name__}, {size} items)")
            else:
                print(f"    - {key} ({type(value).__name__})")
    
    print()
    print("-" * 80)
    print("FULL RESPONSE:")
    print("-" * 80)
    print(json.dumps(data, indent=2))
    
else:
    print(f"✗ Error: {data}")

print()
