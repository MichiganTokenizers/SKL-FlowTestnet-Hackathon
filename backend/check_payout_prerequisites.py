#!/usr/bin/env python3
"""
Check if prerequisites are met for vault withdrawal and prize distribution.

This script verifies:
1. Vault deposit exists and is completed
2. League placements are recorded
3. No prior withdrawal or payout exists

Usage:
    python check_payout_prerequisites.py
"""

import sqlite3
import os
import json
import sys

# Configuration
DB_PATH = os.getenv('DATABASE_URL', os.path.join(os.path.dirname(__file__), 'keeper.db'))
LEAGUE_ID = "TEST_VAULT_001"

def get_db_connection():
    """Get database connection."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"❌ Failed to connect to database at {DB_PATH}")
        print(f"   Error: {str(e)}")
        sys.exit(1)

def check_vault_deposit(cursor):
    """Check if vault deposit exists and is completed."""
    print("\n" + "="*60)
    print("  Checking Vault Deposit")
    print("="*60)

    cursor.execute("""
        SELECT execution_id, status, result_data, created_at
        FROM AgentExecutions
        WHERE agent_type = 'vault_deposit'
        AND execution_id LIKE ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (f'vault_deposit_{LEAGUE_ID}%',))

    deposit = cursor.fetchone()

    if not deposit:
        print("❌ No vault deposit found for league")
        print(f"   League: {LEAGUE_ID}")
        print(f"   Action needed: Collect all fees to trigger automatic deposit")
        return False

    status = deposit['status']
    if status != 'completed':
        print(f"⚠️  Vault deposit exists but status is: {status}")
        print(f"   Execution ID: {deposit['execution_id']}")
        print(f"   Created: {deposit['created_at']}")
        return False

    # Parse amount from result_data
    result_data = json.loads(deposit['result_data']) if deposit['result_data'] else {}
    amount = result_data.get('amount', 0)
    tx_id = result_data.get('transaction_id', 'N/A')

    print("✅ Vault deposit completed")
    print(f"   Execution ID: {deposit['execution_id']}")
    print(f"   Amount: {amount} FLOW")
    print(f"   Transaction ID: {tx_id}")
    print(f"   Created: {deposit['created_at']}")
    return True

def check_vault_withdrawal(cursor):
    """Check if vault has already been withdrawn."""
    print("\n" + "="*60)
    print("  Checking Vault Withdrawal Status")
    print("="*60)

    cursor.execute("""
        SELECT execution_id, status, result_data, created_at
        FROM AgentExecutions
        WHERE agent_type = 'vault_withdrawal'
        AND execution_id LIKE ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (f'vault_withdrawal_{LEAGUE_ID}%',))

    withdrawal = cursor.fetchone()

    if not withdrawal:
        print("✅ No prior withdrawal found - ready to withdraw")
        return True

    status = withdrawal['status']
    print(f"⚠️  Vault already withdrawn!")
    print(f"   Status: {status}")
    print(f"   Execution ID: {withdrawal['execution_id']}")
    print(f"   Created: {withdrawal['created_at']}")

    if status == 'completed':
        result_data = json.loads(withdrawal['result_data']) if withdrawal['result_data'] else {}
        tx_id = result_data.get('transaction_id', 'N/A')
        print(f"   Transaction ID: {tx_id}")
        return False

    return False

def check_placements(cursor):
    """Check if league placements are recorded."""
    print("\n" + "="*60)
    print("  Checking League Placements")
    print("="*60)

    cursor.execute("""
        SELECT
            lp.placement_type,
            lp.roster_id,
            lp.final_rank,
            r.team_name,
            u.username,
            u.wallet_address
        FROM LeaguePlacements lp
        LEFT JOIN rosters r ON lp.roster_id = r.sleeper_roster_id
            AND lp.sleeper_league_id = r.sleeper_league_id
        LEFT JOIN Users u ON r.owner_id = u.sleeper_user_id
        WHERE lp.sleeper_league_id = ?
        ORDER BY lp.final_rank
    """, (LEAGUE_ID,))

    placements = cursor.fetchall()

    if not placements:
        print("❌ No placements found for league")
        print(f"   League: {LEAGUE_ID}")
        print(f"   Action needed: Insert records into LeaguePlacements table")
        print("\nExample SQL:")
        print("""
        INSERT INTO LeaguePlacements (sleeper_league_id, season_year, roster_id, placement_type, final_rank)
        VALUES
            ('TEST_VAULT_001', 2025, 'roster_1', '1st_place', 1),
            ('TEST_VAULT_001', 2025, 'roster_2', '2nd_place', 2),
            ('TEST_VAULT_001', 2025, 'roster_3', '3rd_place', 3),
            ('TEST_VAULT_001', 2025, 'roster_4', 'regular_season_winner', 4);
        """)
        return False

    print(f"✅ Found {len(placements)} placement(s)")
    print()

    required_placements = {'1st_place', '2nd_place', '3rd_place', 'regular_season_winner'}
    found_placements = {p['placement_type'] for p in placements}
    missing = required_placements - found_placements

    for placement in placements:
        team_name = placement['team_name'] or 'Unknown Team'
        username = placement['username'] or 'Unknown User'
        wallet = placement['wallet_address'] or 'No wallet'

        print(f"  {placement['placement_type']:25s} (Rank {placement['final_rank']})")
        print(f"    Team: {team_name}")
        print(f"    User: {username}")
        print(f"    Wallet: {wallet}")
        print()

    if missing:
        print(f"⚠️  Missing placements: {', '.join(missing)}")
        return False

    return True

def check_prior_payouts(cursor):
    """Check if payouts have already been executed."""
    print("="*60)
    print("  Checking Prior Payouts")
    print("="*60)

    cursor.execute("""
        SELECT payout_id, payout_status, total_prize_pool, payout_date
        FROM PayoutSchedules
        WHERE sleeper_league_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (LEAGUE_ID,))

    payout = cursor.fetchone()

    if not payout:
        print("✅ No prior payouts found - ready to execute")
        return True

    status = payout['payout_status']
    print(f"⚠️  Payout already exists!")
    print(f"   Status: {status}")
    print(f"   Payout ID: {payout['payout_id']}")
    print(f"   Total Pool: {payout['total_prize_pool']} FLOW")
    print(f"   Date: {payout['payout_date']}")

    if status == 'completed':
        print(f"   ❌ Cannot execute payouts - already completed")
        return False

    return True

def main():
    """Main check function."""
    print("\n" + "="*60)
    print("  Vault Withdrawal & Prize Distribution Prerequisites")
    print("="*60)
    print(f"\nLeague: {LEAGUE_ID}")
    print(f"Database: {DB_PATH}")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check all prerequisites
        deposit_ok = check_vault_deposit(cursor)
        withdrawal_ok = check_vault_withdrawal(cursor)
        placements_ok = check_placements(cursor)
        payouts_ok = check_prior_payouts(cursor)

        # Summary
        print("\n" + "="*60)
        print("  Summary")
        print("="*60)
        print()

        checks = [
            ("Vault deposit completed", deposit_ok),
            ("No prior withdrawal", withdrawal_ok),
            ("Placements recorded", placements_ok),
            ("No prior payouts", payouts_ok)
        ]

        all_ok = all(ok for _, ok in checks)

        for check_name, ok in checks:
            status = "✅" if ok else "❌"
            print(f"{status} {check_name}")

        print()
        print("="*60)

        if all_ok:
            print("✅ All prerequisites met!")
            print()
            print("Ready to execute:")
            print("  1. python test_payout_preview.py     (safe - preview only)")
            print("  2. python test_vault_payouts.py      (executes transactions)")
        else:
            print("❌ Prerequisites not met")
            print()
            print("Action items:")
            if not deposit_ok:
                print("  - Ensure all fees are collected to trigger vault deposit")
            if not withdrawal_ok:
                print("  - Vault already withdrawn, cannot withdraw again")
            if not placements_ok:
                print("  - Add placement records to LeaguePlacements table")
            if not payouts_ok:
                print("  - Payouts already executed, cannot execute again")

        sys.exit(0 if all_ok else 1)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Check interrupted by user.")
        sys.exit(1)