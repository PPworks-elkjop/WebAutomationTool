"""Quick verification that Jira credentials work with DPAPI"""
from credentials_manager import CredentialsManager
from database_manager import DatabaseManager

db = DatabaseManager()
cm = CredentialsManager(db)
creds = cm.get_credentials('jira')

print(f'✅ DPAPI Active: {cm.use_dpapi}')
print(f'✅ Retrieved Jira URL: {creds.get("url", "Not found")}')
print(f'✅ Retrieved Username: {creds.get("username", "Not found")}')
print(f'✅ Has API Token: {"api_token" in creds}')
print(f'✅ Has SSL Settings: {"verify_ssl" in creds or "use_cert_pinning" in creds}')
