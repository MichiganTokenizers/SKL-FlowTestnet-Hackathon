import sqlite3
import json

def main():
    try:
        with sqlite3.connect('/var/data/keeper.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Check if leagues table exists

                
            # Count leagues
            cursor.execute("SELECT COUNT(*) as count FROM leagues")
            result = cursor.fetchone()
            print(f"Total leagues in database: {result['count']}")
            
            # Get league data
            cursor.execute("""
                SELECT sleeper_league_id, sleeper_user_id, name, season, status, settings
                FROM leagues
            """)
            leagues = cursor.fetchall()
            
            if not leagues:
                print("No leagues found in database.")
                return
                
            print("\nLeague details:")
            print("=" * 50)
            
            for league in leagues:
                print(f"ID: {league['sleeper_league_id']}")
                print(f"Sleeper User ID: {league['sleeper_user_id']}")
                print(f"Name: {league['name']}")
                print(f"Season: {league['season']}")
                print(f"Status: {league['status']}")
                
                # Parse settings if available
                if league['settings']:
                    try:
                        settings = json.loads(league['settings'])
                        print("Settings:")
                        for key, value in settings.items():
                            if isinstance(value, dict) or isinstance(value, list):
                                print(f"  {key}: (complex object)")
                            else:
                                print(f"  {key}: {value}")
                    except json.JSONDecodeError:
                        print(f"Settings (unable to parse): {league['settings'][:100]}...")
                else:
                    print("Settings: None")
                
                print("-" * 50)
                
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 