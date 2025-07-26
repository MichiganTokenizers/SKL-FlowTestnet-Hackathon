import sqlite3
import json

# Sleeper API user data
sleeper_user_data = {
    "avatar": "87bebef5e389411628672fe2b15b24c8",
    "display_name": "LordTokenizer",
    "is_bot": False,
    "is_owner": True,
    "league_id": "1224829460549738496",
    "metadata": {
        "allow_pn": "on",
        "mention_pn": "on",
        "team_name": "Lord Tokenizer's serfs"
    },
    "settings": None,
    "user_id": "1224829004754718720",
    "wallet_address": "UQDwcjX6S1H3c5sAqYWIYTYJQ7yAW5znD3OEziNwiCOUnD5Q"
}

def insert_sleeper_user():
    try:
        # Connect to the database
        with sqlite3.connect('/var/data/keeper.db') as conn:
            cursor = conn.cursor()
            
            # Convert metadata to JSON string
            metadata_json = json.dumps(sleeper_user_data["metadata"]) if sleeper_user_data["metadata"] else None
            
            # Check if the user already exists
            cursor.execute('SELECT sleeper_user_id FROM users WHERE sleeper_user_id = ?', 
                          (sleeper_user_data["user_id"],))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # Update existing user
                cursor.execute('''
                    UPDATE users
                    SET display_name = ?,
                        avatar = ?,
                        metadata = ?,
                        wallet_address = ?,
                        updated_at = datetime("now")
                    WHERE sleeper_user_id = ?
                ''', (
                    sleeper_user_data["display_name"],
                    sleeper_user_data["avatar"],
                    metadata_json,
                    sleeper_user_data["wallet_address"],
                    sleeper_user_data["user_id"]
                ))
                print(f"User {sleeper_user_data['display_name']} updated successfully with wallet address")
            else:
                # Insert new user
                cursor.execute('''
                    INSERT INTO users (
                        sleeper_user_id,
                        display_name,
                        avatar,
                        metadata,
                        wallet_address,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, datetime("now"), datetime("now"))
                ''', (
                    sleeper_user_data["user_id"],
                    sleeper_user_data["display_name"],
                    sleeper_user_data["avatar"],
                    metadata_json,
                    sleeper_user_data["wallet_address"]
                ))
                print(f"User {sleeper_user_data['display_name']} inserted successfully")
            
            # Insert or update league information
            cursor.execute('SELECT sleeper_league_id FROM leagues WHERE sleeper_league_id = ?', 
                           (sleeper_user_data["league_id"],))
            existing_league = cursor.fetchone()
            
            if not existing_league:
                cursor.execute('''
                    INSERT INTO leagues (
                        sleeper_league_id,
                        sleeper_user_id,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, datetime("now"), datetime("now"))
                ''', (
                    sleeper_user_data["league_id"],
                    sleeper_user_data["user_id"]
                ))
                print(f"League {sleeper_user_data['league_id']} inserted successfully")
            
            conn.commit()
            print("Database operations completed successfully")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    insert_sleeper_user() 