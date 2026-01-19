"""Test script for multi-user context loading in comfort_calc.py."""
import sys
from pathlib import Path

# Fix imports
PKG_ROOT = Path(__file__).resolve().parent.parent
if str(PKG_ROOT) not in sys.path:
    sys.path.append(str(PKG_ROOT))

# Note: This might fail in CI if responses.csv is not present.
# We should ideally mock the file or ensure it exists.
from thermal_comfort_model.comfort_calc import all_users_context

def test_all_users_context():
    # Use the actual responses.csv for testing if it exists
    # In a real CI environment, we might want to mock this.
    try:
        users = all_users_context()
        # If it found users, great. If not, it should at least return a dict.
        assert isinstance(users, dict)
    except FileNotFoundError:
        # If file is missing, we skip or pass if it's expected in CI
        import pytest
        pytest.skip("responses.csv not found, skipping multi-user context test")
