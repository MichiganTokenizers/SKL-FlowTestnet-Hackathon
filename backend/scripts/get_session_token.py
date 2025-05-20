import sqlite3

def get_session_token():
    try:
        # Connect to the database
        with sqlite3.connect('backend/keeper.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get the most recent session token
            cursor.execute('SELECT wallet_address, session_token FROM sessions LIMIT 1')
            session = cursor.fetchone()
            
            if not session:
                print("No sessions found in the database.")
                return
            
            print(f"Found session token for wallet: {session['wallet_address']}")
            print(f"Session token: {session['session_token']}")
            print("\nYou can use this token for testing the API endpoints.")
    
    except Exception as e:
        print(f"Error retrieving session token: {str(e)}")

if __name__ == "__main__":
    get_session_token() 