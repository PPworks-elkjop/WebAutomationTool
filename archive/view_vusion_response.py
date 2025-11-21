"""
View full Vusion API response to understand data structure
"""

import json
from vusion_api_config import VusionAPIConfig
from vusion_api_helper import VusionAPIHelper

print("=" * 80)
print("Vusion API - Full Response Data")
print("=" * 80)
print()

config = VusionAPIConfig()
helper = VusionAPIHelper(config)

store_id = 'elkjop_se_lab.lab5'

print(f"Querying store: {store_id}")
print()

success, data = helper.make_request(
    country='SE',
    service='vusion_pro',
    endpoint='stores',
    method='GET',
    storeId=store_id
)

if success:
    print("=" * 80)
    print("FULL JSON RESPONSE:")
    print("=" * 80)
    print(json.dumps(data, indent=2))
    print()
    print("=" * 80)
    print("KEY FIELDS FOR AP PANEL:")
    print("=" * 80)
    
    # Check what we need for AP Panel integration
    print(f"\nStore Information:")
    print(f"  ID: {data.get('id', 'N/A')}")
    print(f"  Name: {data.get('name', 'N/A')}")
    
    if 'status' in data and isinstance(data['status'], dict):
        operational = data['status'].get('operational', 'N/A')
        installation = data['status'].get('installation', 'N/A')
        print(f"  Operational Status: {operational}")
        print(f"  Installation Status: {installation}")
    
    # Look for gateway/AP information
    print(f"\nGateway/AP Data:")
    
    # Check various possible locations for gateway data
    if 'gateways' in data:
        print(f"  'gateways' field found: {type(data['gateways'])}")
        gateways = data['gateways']
        if isinstance(gateways, list):
            print(f"  Number of gateways: {len(gateways)}")
            if gateways:
                print(f"\n  First gateway example:")
                print(json.dumps(gateways[0], indent=4))
        else:
            print(f"  Gateway data: {gateways}")
    else:
        print("  ⚠ No 'gateways' field in main store response")
    
    if 'transmitters' in data:
        print(f"  'transmitters' field found: {type(data['transmitters'])}")
    
    if 'accessPoints' in data:
        print(f"  'accessPoints' field found: {type(data['accessPoints'])}")
    
    print()
    print("=" * 80)
    print("ALL TOP-LEVEL FIELDS:")
    print("=" * 80)
    for key in data.keys():
        value_type = type(data[key]).__name__
        if isinstance(data[key], (list, dict)):
            size = len(data[key])
            print(f"  {key} ({value_type}): {size} items")
        else:
            print(f"  {key} ({value_type}): {data[key]}")
    
    print()
else:
    print(f"✗ Error: {data}")
