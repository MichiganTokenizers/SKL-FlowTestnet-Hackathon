#!/usr/bin/env python3
"""
Quick viewer for TEST_VAULT_001 league status.

Shows:
- Vault deposit status
- Withdrawal status
- Placements
- Payout status

Usage:
    python view_league_status.py
"""

import sqlite3
import os
import json
import sys
from datetime import datetime

DB_PATH = os.getenv('DATABASE_URL', os.path.join(os.path.dirname(__file__), 'keeper.db'))
LEAGUE_ID = "TEST_VAULT_001"

def get_connection():
    """Get database connection."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"❌ Database connection failed: {str(e)}")
        sys.exit(1)

def format_timestamp(ts):
    """Format timestamp for display."""
    if not ts:
        return "N/A"
    try:
        dt = datetime.fromisoformat(ts.replace(' ', 'T'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return ts

def main():
    """Display league status."""
    print("\n" + "="*70)
    print(f"  {LEAGUE_ID} - League Status")
    print("="*70)
    print()

    conn = get_connection()
    cursor = conn.cursor()

    # Vault Deposit
    print("💰 VAULT DEPOSIT")
    print("-"*70)
    cursor.execute("""
        SELECT execution_id, status, result_data, created_at
        FROM AgentExecutions
        WHERE agent_type = 'vault_deposit'
        AND execution_id LIKE ?
        ORDER BY created_at DESC LIMIT 1
    """, (f'vault_deposit_{LEAGUE_ID}%',))

    deposit = cursor.fetchone()
    if deposit:
        data = json.loads(deposit['result_data']) if deposit['result_data'] else {}
        amount = data.get('amount', 0)
        tx_id = data.get('transaction_id', 'N/A')
        status_icon = "✅" if deposit['status'] == 'completed' else "⚠️"

        print(f"{status_icon} Status: {deposit['status']}")
        print(f"   Amount: {amount} FLOW")
        print(f"   TX ID: {tx_id}")
        print(f"   Date: {format_timestamp(deposit['created_at'])}")
    else:
        print("❌ No vault deposit found")
    print()

    # Vault Withdrawal
    print("🏦 VAULT WITHDRAWAL")
    print("-"*70)
    cursor.execute("""
        SELECT execution_id, status, result_data, created_at
        FROM AgentExecutions
        WHERE agent_type = 'vault_withdrawal'
        AND execution_id LIKE ?
        ORDER BY created_at DESC LIMIT 1
    """, (f'vault_withdrawal_{LEAGUE_ID}%',))

    withdrawal = cursor.fetchone()
    if withdrawal:
        data = json.loads(withdrawal['result_data']) if withdrawal['result_data'] else {}
        amount = data.get('withdrawal_amount', 0)
        tx_id = data.get('transaction_id', 'N/A')
        status_icon = "✅" if withdrawal['status'] == 'completed' else "⚠️"

        print(f"{status_icon} Status: {withdrawal['status']}")
        print(f"   Amount: {amount} FLOW")
        print(f"   TX ID: {tx_id}")
        print(f"   Date: {format_timestamp(withdrawal['created_at'])}")
    else:
        print("✅ No withdrawal yet (ready to withdraw)")
    print()

    # Placements
    print("🏆 PLACEMENTS")
    print("-"*70)
    cursor.execute("""
        SELECT
            lp.placement_type,
            lp.final_rank,
            lp.roster_id,
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
    if placements:
        for p in placements:
            print(f"#{p['final_rank']} {p['placement_type'].upper().replace('_', ' ')}")
            print(f"   Team: {p['team_name'] or 'Unknown'}")
            print(f"   User: {p['username'] or 'Unknown'}")
            print(f"   Wallet: {p['wallet_address'] or 'N/A'}")
            print()
    else:
        print("❌ No placements recorded")
        print()

    # Payout Status
    print("💸 PAYOUT STATUS")
    print("-"*70)
    cursor.execute("""
        SELECT payout_id, payout_status, total_prize_pool, payout_date, created_at
        FROM PayoutSchedules
        WHERE sleeper_league_id = ?
        ORDER BY created_at DESC LIMIT 1
    """, (LEAGUE_ID,))

    payout = cursor.fetchone()
    if payout:
        status_icon = "✅" if payout['payout_status'] == 'completed' else "⚠️"
        print(f"{status_icon} Status: {payout['payout_status']}")
        print(f"   Payout ID: {payout['payout_id']}")
        print(f"   Total Pool: {payout['total_prize_pool']} FLOW")
        print(f"   Date: {format_timestamp(payout['payout_date'])}")
        print()

        # Show distributions
        cursor.execute("""
            SELECT
                pd.wallet_address,
                pd.payout_type,
                pd.amount,
                pd.percentage,
                pd.status,
                pd.transaction_id,
                u.username
            FROM PayoutDistributions pd
            LEFT JOIN Users u ON pd.wallet_address = u.wallet_address
            WHERE pd.payout_id = ?
            ORDER BY pd.amount DESC
        """, (payout['payout_id'],))

        distributions = cursor.fetchall()
        if distributions:
            print("   Distributions:")
            for d in distributions:
                status_icon = "✅" if d['status'] == 'completed' else "⚠️"
                print(f"   {status_icon} {d['username'] or 'Unknown'}: {d['amount']:.2f} FLOW ({d['percentage']*100:.0f}%)")
                print(f"      Type: {d['payout_type']}")
                if d['transaction_id']:
                    print(f"      TX: {d['transaction_id']}")
    else:
        print("✅ No payouts yet (ready to execute)")

    print()
    print("="*70)

    # Summary status
    print("\n📊 SUMMARY")
    print("-"*70)

    ready_to_withdraw = (
        deposit and deposit['status'] == 'completed' and
        not withdrawal
    )

    ready_to_payout = (
        withdrawal and withdrawal['status'] == 'completed' and
        len(placements) == 4 and
        not payout
    )

    if ready_to_withdraw:
        print("✅ Ready to withdraw from vault")
        print("   Run: python test_vault_payouts.py")
    elif ready_to_payout:
        print("✅ Ready to execute payouts")
        print("   Run: python test_vault_payouts.py")
    elif payout and payout['payout_status'] == 'completed':
        print("✅ All operations completed!")
        print("   League processing finished")
    else:
        print("⚠️  Not ready - check prerequisites")
        print("   Run: python check_payout_prerequisites.py")

    print()

    conn.close()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)