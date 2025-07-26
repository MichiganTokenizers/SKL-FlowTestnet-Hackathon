import sqlite3

def main():
    conn = None
    try:
        conn = sqlite3.connect('/var/data/keeper.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("Checking contents of the 'contracts' table...")
        cursor.execute("SELECT player_id, team_id, draft_amount, contract_year, duration, is_active FROM contracts")
        contracts = cursor.fetchall()
        
        if not contracts:
            print("The 'contracts' table is empty.")
            return
            
        print(f"Found {len(contracts)} contracts:")
        for contract in contracts:
            print(f"  Player ID: {contract['player_id']}, Team ID: {contract['team_id']}, "
                  f"Draft Amount: ${contract['draft_amount']}, Year: {contract['contract_year']}, "
                  f"Duration: {contract['duration']} yrs, Active: {contract['is_active']}")
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main() 