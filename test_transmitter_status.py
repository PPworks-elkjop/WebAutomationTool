"""
Test transmitter (AP) status functions
"""

from vusion_api_helper import VusionAPIHelper

print("=" * 80)
print("Vusion Transmitter Status Test")
print("=" * 80)
print()

helper = VusionAPIHelper()

# Test parameters
country = 'SE'
store_id = 'elkjop_se_lab.lab5'
test_transmitter_id = '201265'

print(f"Store ID: {store_id}")
print()

# Test 1: Get all transmitters
print("-" * 80)
print("Test 1: Get all transmitters")
print("-" * 80)

success, transmitters = helper.get_transmitter_status(country, store_id)

if success:
    print(f"✓ Found {len(transmitters)} transmitters")
    print()
    
    for idx, t in enumerate(transmitters, 1):
        t_id = t.get('id', 'N/A')
        connectivity = t.get('connectivity', {})
        status = connectivity.get('status', 'UNKNOWN')
        
        # Status indicator
        if status == 'ONLINE':
            indicator = "🟢"
        elif status == 'OFFLINE':
            indicator = "🔴"
        else:
            indicator = "⚠️"
        
        print(f"  {idx}. {indicator} Transmitter {t_id}: {status}")
        
        # Show additional info if available
        if 'name' in t:
            print(f"     Name: {t.get('name')}")
        if 'ipAddress' in connectivity:
            print(f"     IP: {connectivity.get('ipAddress')}")
        if 'lastSeen' in connectivity:
            print(f"     Last Seen: {connectivity.get('lastSeen')}")
        print()
else:
    print(f"✗ Error: {transmitters}")

print()

# Test 2: Get specific transmitter
print("-" * 80)
print(f"Test 2: Get specific transmitter ({test_transmitter_id})")
print("-" * 80)

success, transmitter = helper.get_transmitter_status(country, store_id, test_transmitter_id)

if success:
    if transmitter:
        print(f"✓ Transmitter found")
        print()
        
        import json
        print(json.dumps(transmitter, indent=2))
    else:
        print(f"⚠️ Transmitter {test_transmitter_id} not found")
else:
    print(f"✗ Error: {transmitter}")

print()

# Test 3: Quick online check
print("-" * 80)
print(f"Test 3: Quick online check ({test_transmitter_id})")
print("-" * 80)

success, online = helper.check_transmitter_online(country, store_id, test_transmitter_id)

if success:
    if online is True:
        print(f"✓ 🟢 Transmitter {test_transmitter_id} is ONLINE")
    elif online is False:
        print(f"✓ 🔴 Transmitter {test_transmitter_id} is OFFLINE")
    else:
        print(f"⚠️ Transmitter {test_transmitter_id} not found")
else:
    print(f"✗ Error checking status")

print()

# Test 4: Simulate AP Panel use case
print("-" * 80)
print("Test 4: AP Panel Integration Simulation")
print("-" * 80)
print()
print("Simulating how this will work in the AP Panel:")
print()

# Simulate having an AP with ID from your system
ap_id = test_transmitter_id

print(f"User searched for AP: {ap_id}")
print("Checking Vusion status...")
print()

success, online = helper.check_transmitter_online(country, store_id, ap_id)

if success and online is not None:
    status_text = "ONLINE" if online else "OFFLINE"
    icon = "🟢" if online else "🔴"
    
    print(f"  AP Panel Display:")
    print(f"  ┌─────────────────────────────────┐")
    print(f"  │ AP: {ap_id}                    │")
    print(f"  │ Vusion Status: {icon} {status_text:7} │")
    print(f"  └─────────────────────────────────┘")
else:
    print(f"  AP Panel Display:")
    print(f"  ┌─────────────────────────────────┐")
    print(f"  │ AP: {ap_id}                    │")
    print(f"  │ Vusion Status: ⚠️ Unknown     │")
    print(f"  └─────────────────────────────────┘")

print()
print("=" * 80)
print("✓ Transmitter tests complete!")
print("=" * 80)
print()
print("Ready to integrate into AP Panel!")
print()
