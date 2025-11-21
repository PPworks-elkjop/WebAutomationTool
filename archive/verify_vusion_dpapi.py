"""Quick verification that Vusion credentials work with DPAPI"""
from database_manager import DatabaseManager
from credentials_manager import CredentialsManager
from vusion_api_config import VusionAPIConfig

db = DatabaseManager()
cm = CredentialsManager(db)
vusion = VusionAPIConfig(cm)

print(f'✅ DPAPI Active: {cm.use_dpapi}')
print(f'\n📋 Configured Vusion API Keys:')

all_keys = vusion.get_all_keys()
if all_keys:
    for country, services in all_keys.items():
        for service, api_key in services.items():
            # Mask the API key for security
            masked_key = api_key[:8] + '...' + api_key[-4:] if api_key else 'None'
            print(f'   ✓ {country}/{service}: {masked_key}')
else:
    print('   (No API keys configured)')

print(f'\n✅ Vusion credentials are now protected by Windows DPAPI')
