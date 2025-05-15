import sqlite3
import json

def main():
    try:
        # Connect to the database
        with sqlite3.connect('keeper.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Check tables exist
            tables = [
                "users", "leagues", "rosters", "players", 
                "transactions", "traded_picks", "drafts"
            ]
            
            print("Database Table Counts:")
            print("=" * 40)
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    result = cursor.fetchone()
                    if result:
                        print(f"{table}: {result['count']} records")
                    else:
                        print(f"{table}: Error getting count")
                except sqlite3.OperationalError as e:
                    print(f"{table}: {str(e)}")
            
            # Sample data from players table
            print("\nSample Players:")
            print("=" * 40)
            try:
                cursor.execute("SELECT * FROM players LIMIT 5")
                players = cursor.fetchall()
                for player in players:
                    print(f"ID: {player['sleeper_player_id']}")
                    print(f"Name: {player['name']}")
                    print(f"Position: {player['position']}")
                    print(f"Team: {player['team']}")
                    print("-" * 30)
            except sqlite3.OperationalError as e:
                print(f"Players query error: {str(e)}")
            
            # Check roster players
            print("\nRoster Player IDs:")
            print("=" * 40)
            try:
                cursor.execute("SELECT players FROM rosters LIMIT 3")
                rosters = cursor.fetchall()
                for i, roster in enumerate(rosters):
                    print(f"Roster #{i+1}:")
                    if roster['players']:
                        try:
                            players_list = json.loads(roster['players'])
                            print(f"  Player count: {len(players_list) if isinstance(players_list, list) else 'Not a list'}")
                            print(f"  First few players: {str(players_list)[:100]}...")
                        except json.JSONDecodeError:
                            print(f"  JSON decode error: {roster['players'][:50]}...")
                    else:
                        print("  No players")
                    print("-" * 30)
            except sqlite3.OperationalError as e:
                print(f"Rosters query error: {str(e)}")
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")

if __name__ == "__main__":
    main() 