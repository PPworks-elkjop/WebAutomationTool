"""Quick test of user manager."""
from user_manager_v2 import UserManager

print("Testing user manager...")
um = UserManager()
print(f"Total users: {um.count()}")

users = um.get_all_users()
for u in users:
    print(f"  {u['username']} ({u['full_name']}) - {u['role']}")

print("\nDone!")
