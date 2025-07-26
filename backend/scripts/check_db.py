import sqlite3

def check_database():
    try:
        # Connect to the database
        with sqlite3.connect('/var/data/keeper.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query the users table
            cursor.execute('SELECT sleeper_user_id, display_name, avatar, metadata, wallet_address FROM users')
            users = cursor.fetchall()
            
            # Print results
            print(f"Found {len(users)} users in the database:")
            for user in users:
                print(f"User ID: {user['sleeper_user_id']}")
                print(f"Display Name: {user['display_name']}")
                print(f"Avatar: {user['avatar']}")
                print(f"Metadata: {user['metadata']}")
                print(f"Wallet Address: {user['wallet_address']}")
                print("-" * 50)
                
            # Query the leagues table
            cursor.execute('SELECT sleeper_league_id, sleeper_user_id FROM leagues')
            leagues = cursor.fetchall()
            
            # Print results
            print(f"\nFound {len(leagues)} leagues in the database:")
            for league in leagues:
                print(f"League ID: {league['sleeper_league_id']}")
                print(f"Owner ID: {league['sleeper_user_id']}")
                print("-" * 50)
                
    except Exception as e:
        print(f"Error checking database: {str(e)}")

if __name__ == "__main__":
    check_database() 