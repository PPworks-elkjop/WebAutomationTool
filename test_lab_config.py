"""
Quick test to verify LAB country configuration
"""

from vusion_api_config import VusionAPIConfig

print("Testing LAB Country Configuration")
print("=" * 50)

config = VusionAPIConfig()

# Check if LAB is in countries
print(f"✓ LAB in COUNTRIES: {'LAB' in config.COUNTRIES}")

# Check if we can get the API key for LAB
api_key = config.get_api_key('LAB', 'vusion_pro')
if api_key:
    print(f"✓ LAB API key found: {api_key[:10]}...{api_key[-4:]}")
else:
    print("✗ No LAB API key found")

# Check SE key for comparison
se_key = config.get_api_key('SE', 'vusion_pro')
if se_key:
    print(f"✓ SE API key found: {se_key[:10]}...{se_key[-4:]}")
else:
    print("✗ No SE API key found")

print("\nAll configured keys:")
for item in config.list_configured_keys():
    print(f"  - {item['country']}: {item['service_name']}")

print("\n" + "=" * 50)
print("Now testing API call with LAB country code...")

from vusion_api_helper import VusionAPIHelper

helper = VusionAPIHelper()
success, data = helper.get_store_data('LAB', 'elkjop_se_lab.lab5')

if success:
    print(f"✓ Success! Store: {data.get('name', 'N/A')}")
    transmitters = data.get('transmitters', [])
    print(f"✓ Transmitters found: {len(transmitters)}")
    if transmitters:
        online = sum(1 for t in transmitters if t.get('connectivity', {}).get('status') == 'ONLINE')
        print(f"✓ Online: {online}, Offline: {len(transmitters) - online}")
else:
    print(f"✗ Failed: {data}")
