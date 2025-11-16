"""Quick script to check what APs are in the database."""
from database_manager import DatabaseManager

db = DatabaseManager('esl_ap_helper.db')
aps = db.search_access_points('')

print(f'Found {len(aps)} APs in database:')
for ap in aps[:20]:
    print(f"  - {ap['ap_id']} (Store: {ap.get('store_id', 'N/A')}, Status: {ap.get('current_status', 'N/A')})")

if len(aps) == 0:
    print("\nNo APs found. Please add APs using the main application first.")
