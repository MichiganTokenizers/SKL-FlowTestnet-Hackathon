#!/usr/bin/env python3
"""
Test script for vault withdrawal and prize distribution endpoints.

This script tests the complete flow:
1. Login as admin
2. Withdraw funds from IncrementFi vault
3. Preview prize distributions
4. Execute prize distributions to winners

Usage:
    python test_vault_payouts.py
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:5000"
ADMIN_WALLET = "0xdf978465ee6dcf32"
LEAGUE_ID = "TEST_VAULT_001"

def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_success(text):
    """Print success message."""
    print(f"✅ {text}")

def print_error(text):
    """Print error message."""
    print(f"❌ {text}")

def print_info(text):
    """Print info message."""
    print(f"ℹ️  {text}")

def login_as_admin():
    """Login as admin and return session token."""
    print_header("STEP 1: Admin Login")
    print_info(f"Logging in with admin wallet: {ADMIN_WALLET}")

    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"walletAddress": ADMIN_WALLET},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if not data.get('success'):
            print_error(f"Login failed: {data.get('error', 'Unknown error')}")
            return None

        session_token = data.get('sessionToken')
        print_success(f"Logged in successfully!")
        print_info(f"Session token: {session_token[:20]}...")
        return session_token

    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        return None
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return None

def withdraw_from_vault(session_token):
    """Withdraw funds from IncrementFi vault."""
    print_header("STEP 2: Withdraw from Vault")
    print_info(f"Withdrawing from IncrementFi for league: {LEAGUE_ID}")

    headers = {
        "Authorization": f"Bearer {session_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/admin/league/{LEAGUE_ID}/vault/withdraw",
            headers=headers,
            timeout=120  # Longer timeout for blockchain transaction
        )

        # Try to get response body even on error
        try:
            data = response.json()
            print_info(f"Response: {json.dumps(data, indent=2)}")
        except:
            print_info(f"Response status: {response.status_code}")
            print_info(f"Response text: {response.text}")
            data = {}

        response.raise_for_status()

        if data.get('success'):
            print_success("Vault withdrawal successful!")
            print_info(f"Amount withdrawn: {data.get('withdrawal_amount')} FLOW")
            print_info(f"Transaction ID: {data.get('transaction_id')}")
            print_info(f"Execution ID: {data.get('execution_id')}")
            print_info(f"View on Flow Testnet: https://testnet.flowscan.org/transaction/{data.get('transaction_id')}")
            return data
        else:
            print_error(f"Withdrawal failed: {data.get('error')}")
            return None

    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        return None
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return None

def preview_payouts(session_token):
    """Preview prize distributions."""
    print_header("STEP 3: Preview Prize Distributions")
    print_info(f"Loading payout preview for league: {LEAGUE_ID}")

    headers = {
        "Authorization": f"Bearer {session_token}"
    }

    try:
        response = requests.get(
            f"{BASE_URL}/admin/league/{LEAGUE_ID}/payouts/preview",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if data.get('success'):
            print_success("Preview loaded successfully!")
            total_pool = data.get('total_prize_pool', 0)
            distributions = data.get('distributions', [])

            print_info(f"Total prize pool: {total_pool} FLOW")
            print_info(f"Number of winners: {len(distributions)}")
            print("\nDistribution breakdown:")
            print("-" * 60)

            for dist in distributions:
                placement = dist.get('placement_type', 'Unknown')
                username = dist.get('username', 'Unknown')
                wallet = dist.get('wallet_address', 'Unknown')
                amount = dist.get('amount', 0)
                percentage = dist.get('percentage', 0)

                print(f"  {placement:25s} | {username:15s}")
                print(f"    Wallet: {wallet}")
                print(f"    Amount: {amount} FLOW ({percentage}%)")
                print("-" * 60)

            return data
        else:
            print_error(f"Preview failed: {data.get('error')}")
            return None

    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        return None
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return None

def execute_payouts(session_token):
    """Execute prize distributions to winners."""
    print_header("STEP 4: Execute Prize Distributions")
    print_error("⚠️  WARNING: This will execute REAL blockchain transactions!")
    print_info("This will send FLOW tokens to winner wallets on Flow Testnet.")

    # Confirmation prompt (disabled for automated testing)
    # confirmation = input("\nType 'YES' to continue with payout execution: ")
    # if confirmation.strip().upper() != 'YES':
    #     print_info("Execution cancelled by user.")
    #     return None
    print_info("Auto-confirming payout execution for automated test...")

    print_info(f"Executing payouts for league: {LEAGUE_ID}")

    headers = {
        "Authorization": f"Bearer {session_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/admin/league/{LEAGUE_ID}/payouts/execute",
            headers=headers,
            timeout=120  # Longer timeout for blockchain transaction
        )
        response.raise_for_status()
        data = response.json()

        print_info(f"Response: {json.dumps(data, indent=2)}")

        if data.get('success'):
            print_success("Prize distribution executed successfully!")
            total = data.get('total_distributed', 0)
            tx_id = data.get('transaction_id')
            payout_id = data.get('payout_id')
            distributions = data.get('distributions', [])

            print_info(f"Total distributed: {total} FLOW")
            print_info(f"Transaction ID: {tx_id}")
            print_info(f"Payout ID: {payout_id}")
            print_info(f"View on Flow Testnet: https://testnet.flowscan.org/transaction/{tx_id}")

            print("\nPayments sent:")
            print("-" * 60)
            for dist in distributions:
                username = dist.get('username', 'Unknown')
                amount = dist.get('amount', 0)
                placement = dist.get('placement_type', 'Unknown')
                print(f"  {username:15s} | {amount:8.2f} FLOW | {placement}")
            print("-" * 60)

            return data
        else:
            print_error(f"Execution failed: {data.get('error')}")
            return None

    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        return None
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return None

def main():
    """Main test flow."""
    print_header("Vault Withdrawal & Prize Distribution Test")
    print_info(f"Testing league: {LEAGUE_ID}")
    print_info(f"Admin wallet: {ADMIN_WALLET}")
    print_info(f"Backend URL: {BASE_URL}")

    # Step 1: Login
    session_token = login_as_admin()
    if not session_token:
        print_error("Failed to login. Exiting.")
        sys.exit(1)

    # Step 2: Withdraw from vault
    withdrawal_result = withdraw_from_vault(session_token)
    if not withdrawal_result:
        print_error("Failed to withdraw from vault. Exiting.")
        sys.exit(1)

    # Step 3: Preview payouts
    preview_result = preview_payouts(session_token)
    if not preview_result:
        print_error("Failed to preview payouts. Exiting.")
        sys.exit(1)

    # Step 4: Execute payouts
    execution_result = execute_payouts(session_token)
    if not execution_result:
        print_error("Failed to execute payouts. Exiting.")
        sys.exit(1)

    # Success!
    print_header("All Operations Completed Successfully! 🎉")
    print_success("Vault withdrawal completed")
    print_success("Prize distributions executed")
    print_info("Check the Flow Testnet explorer to verify transactions")
    print_info("Check the database tables:")
    print_info("  - AgentExecutions: vault_withdrawal record")
    print_info("  - PayoutSchedules: payout schedule record")
    print_info("  - PayoutDistributions: individual distribution records")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user. Exiting.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error in main: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)