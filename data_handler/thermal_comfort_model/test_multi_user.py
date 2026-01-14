"""Test script for multi-user context loading in comfort_calc.py."""
import sys
from pathlib import Path

# Fix imports
PKG_ROOT = Path(__file__).resolve().parent.parent
if str(PKG_ROOT) not in sys.path:
    sys.path.append(str(PKG_ROOT))

from thermal_comfort_model.comfort_calc import all_users_context, UserContext

def test_all_users_context():
    # Use the actual responses.csv for testing
    users = all_users_context()
    
    print(f"Found {len(users)} unique users.")
    for uid, ctx in users.items():
        print(f"UID: {uid}")
        print(f"  Activity: {ctx.activity}")
        print(f"  Task: {ctx.main_task}")
        print(f"  Clothing: {ctx.clothing_upper} / {ctx.clothing_lower}")
        print("-" * 20)

    if not users:
        print("Warning: No users found. Check if responses.csv exists and is valid.")
    else:
        print("Test PASSED: all_users_context successfully retrieved users.")

if __name__ == "__main__":
    test_all_users_context()
