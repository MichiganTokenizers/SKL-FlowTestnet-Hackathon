#!/usr/bin/env python3
"""
Test script to verify the new commissioner logic based on Sleeper's is_owner field.
"""

import sqlite3
import os
import sys
from .sleeper_service import SleeperService

def test_commissioner_logic():
    """Test the new commissioner logic."""
    
    # Connect to the database
    db_path = '/var/data/keeper.db'
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        sleeper_service = SleeperService(conn)
        
        # Get all leagues from the database
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT sleeper_league_id FROM LeagueMetadata LIMIT 5")
        leagues = cursor.fetchall()
        
        if not leagues:
            print("No leagues found in database")
            return False
        
        print(f"Found {len(leagues)} leagues to test")
        
        for league_row in leagues:
            league_id = league_row['sleeper_league_id']
            print(f"\nTesting league: {league_id}")
            
            # Test the commissioner update function
            result = sleeper_service.update_commissioner_status_for_league(league_id)
            
            if result.get('success'):
                print(f"✅ Success: {result.get('message')}")
                
                # Check the results in the database
                cursor.execute("""
                    SELECT u.sleeper_user_id, u.display_name, ull.is_commissioner, ull.wallet_address
                    FROM UserLeagueLinks ull
                    JOIN users u ON ull.wallet_address = u.wallet_address
                    WHERE ull.sleeper_league_id = ? AND ull.is_commissioner = 1
                """, (league_id,))
                
                commissioners = cursor.fetchall()
                if commissioners:
                    print(f"   Commissioners found: {len(commissioners)}")
                    for comm in commissioners:
                        print(f"   - {comm['display_name']} (ID: {comm['sleeper_user_id']})")
                else:
                    print("   ⚠️  No commissioners found")
                    
            else:
                print(f"❌ Failed: {result.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("Testing new commissioner logic...")
    success = test_commissioner_logic()
    if success:
        print("\n✅ Test completed successfully")
    else:
        print("\n❌ Test failed")
        sys.exit(1) 