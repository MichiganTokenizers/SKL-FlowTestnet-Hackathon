#!/usr/bin/env python3
"""
Quick test script to preview payouts WITHOUT executing blockchain transactions.

This is safe to run repeatedly for testing without spending gas or sending real tokens.

Usage:
    python test_payout_preview.py
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:5000"
ADMIN_WALLET = "0xdf978465ee6dcf32"
LEAGUE_ID = "TEST_VAULT_001"

def main():
    print("=" * 60)
    print("  Payout Preview Test (Safe - No Blockchain Transactions)")
    print("=" * 60)
    print()

    # Login
    print("🔐 Logging in as admin...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"walletAddress": ADMIN_WALLET},
        timeout=10
    )

    if not login_response.ok:
        print(f"❌ Login request failed: {login_response.status_code}")
        sys.exit(1)

    login_data = login_response.json()
    if not login_data.get('success'):
        print(f"❌ Login failed: {login_data.get('error')}")
        sys.exit(1)

    session_token = login_data['sessionToken']
    print(f"✅ Logged in! Token: {session_token[:20]}...")
    print()

    # Preview payouts
    print(f"🔍 Previewing payouts for league: {LEAGUE_ID}")
    print()

    headers = {"Authorization": session_token}
    preview_response = requests.get(
        f"{BASE_URL}/admin/league/{LEAGUE_ID}/payouts/preview",
        headers=headers,
        timeout=10
    )

    if not preview_response.ok:
        print(f"❌ Preview request failed: {preview_response.status_code}")
        print(f"Response: {preview_response.text}")
        sys.exit(1)

    preview_data = preview_response.json()

    if not preview_data.get('success'):
        print(f"❌ Preview failed: {preview_data.get('error')}")
        sys.exit(1)

    # Display results
    print("✅ Preview loaded successfully!")
    print()

    total_pool = preview_data.get('total_prize_pool', 0)
    distributions = preview_data.get('distributions', [])

    print(f"💰 Total Prize Pool: {total_pool} FLOW")
    print(f"🏆 Number of Winners: {len(distributions)}")
    print()
    print("Distribution Breakdown:")
    print("=" * 60)

    for dist in distributions:
        placement = dist.get('placement_type', 'Unknown')
        username = dist.get('username', 'Unknown')
        wallet = dist.get('wallet_address', 'Unknown')
        amount = dist.get('amount', 0)
        percentage = dist.get('percentage', 0)

        print(f"\n{placement.upper().replace('_', ' ')}")
        print(f"  Username:   {username}")
        print(f"  Wallet:     {wallet}")
        print(f"  Amount:     {amount:.2f} FLOW ({percentage:.0f}%)")

    print()
    print("=" * 60)
    print()

    # Summary
    total_distributed = sum(d.get('amount', 0) for d in distributions)
    print(f"✅ Total to be distributed: {total_distributed:.2f} FLOW")

    if abs(total_distributed - total_pool) < 0.01:
        print("✅ Distribution amounts match prize pool")
    else:
        print(f"⚠️  Warning: Distribution total ({total_distributed}) doesn't match pool ({total_pool})")

    print()
    print("ℹ️  This was a preview only. No blockchain transactions were executed.")
    print("ℹ️  To execute payouts, run: python test_vault_payouts.py")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user.")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection failed. Is the backend server running?")
        print("   Start it with: python app.py")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)