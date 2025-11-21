"""
Fix Type field - Remove hyphen and last 4 digits
Example: "VusionRail-1234" -> "VusionRail"
"""

from database_manager import DatabaseManager
import re

def fix_type_fields():
    print("Fixing Type field - Removing hyphens and trailing digits")
    print("=" * 60)
    print()
    
    db = DatabaseManager()
    
    # Get all APs
    all_aps = db.get_all_access_points()
    print(f"Found {len(all_aps)} Access Points")
    print()
    
    updated_count = 0
    pattern = re.compile(r'-\d{4}$')  # Match hyphen followed by 4 digits at end
    
    for ap in all_aps:
        ap_id = ap['ap_id']
        current_type = ap.get('type', '')
        
        if not current_type:
            continue
        
        # Check if type ends with -#### pattern
        if pattern.search(current_type):
            # Remove the hyphen and 4 digits
            new_type = pattern.sub('', current_type)
            
            print(f"Updating {ap_id}: '{current_type}' -> '{new_type}'")
            
            # Update in database
            success, msg = db.update_access_point(ap_id, {'type': new_type})
            if success:
                updated_count += 1
            else:
                print(f"  ✗ Failed: {msg}")
    
    print()
    print("=" * 60)
    print(f"Updated {updated_count} Access Points")
    print("=" * 60)

if __name__ == "__main__":
    try:
        fix_type_fields()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
