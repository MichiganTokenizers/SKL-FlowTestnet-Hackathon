import sqlite3

def main():
    try:
        with sqlite3.connect('/var/data/keeper.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Check if players table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='players'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                print("Players table does not exist!")
                return
                
            # Count players
            cursor.execute("SELECT COUNT(*) as count FROM players")
            result = cursor.fetchone()
            print(f"Total players in database: {result['count']}")
            
            # Sample players
            cursor.execute("SELECT * FROM players LIMIT 10")
            players = cursor.fetchall()
            
            if not players:
                print("No players found in database.")
                return
                
            print("\nSample players:")
            print("=" * 50)
            
            for player in players:
                print(f"ID: {player['sleeper_player_id']}")
                print(f"Name: {player['name']}")
                print(f"Position: {player['position']}")
                print(f"Team: {player['team']}")
                print("-" * 30)
                
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 