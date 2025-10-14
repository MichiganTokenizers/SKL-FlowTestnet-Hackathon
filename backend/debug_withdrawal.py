#!/usr/bin/env python3
"""Debug script to test withdrawal endpoint directly."""

import requests
import json

BACKEND_URL = "http://localhost:5000"
ADMIN_WALLET = "0xdf978465ee6dcf32"
LEAGUE_ID = "TEST_VAULT_001"

print("=" * 60)
print("  Debug Withdrawal Endpoint")
print("=" * 60)

# Step 1: Login
print("\n1. Logging in as admin...")
login_response = requests.post(
    f"{BACKEND_URL}/auth/login",
    json={"walletAddress": ADMIN_WALLET}
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    print(f"Response: {login_response.text}")
    exit(1)

login_data = login_response.json()
print(f"Login response: {json.dumps(login_data, indent=2)}")

if 'token' in login_data:
    token = login_data['token']
elif 'sessionToken' in login_data:
    token = login_data['sessionToken']
elif 'session_token' in login_data:
    token = login_data['session_token']
else:
    print(f"❌ No token in response")
    exit(1)

print(f"✅ Logged in! Token: {token[:20]}...")

# Step 2: Call withdrawal endpoint with full error details
print(f"\n2. Calling withdrawal endpoint for league: {LEAGUE_ID}")
headers = {'Authorization': f'Bearer {token}'}

try:
    withdrawal_response = requests.post(
        f"{BACKEND_URL}/admin/league/{LEAGUE_ID}/vault/withdraw",
        headers=headers
    )

    print(f"\n📊 Response Status: {withdrawal_response.status_code}")
    print(f"📊 Response Headers: {dict(withdrawal_response.headers)}")
    print(f"\n📄 Response Body:")
    print(json.dumps(withdrawal_response.json(), indent=2))

except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Response text: {withdrawal_response.text}")