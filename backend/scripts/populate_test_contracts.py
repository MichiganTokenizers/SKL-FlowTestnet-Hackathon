import sqlite3
import json

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    try:
        # Path relative to the workspace root where the script is executed from
        conn = sqlite3.connect('backend/keeper.db')
        conn.row_factory = sqlite3.Row
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON;")
        print("Database connection successful. Foreign keys ON.")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def find_player_id(conn, player_name):
    """Finds the sleeper_player_id for a given player name."""
    cursor = conn.cursor()
    cursor.execute("SELECT sleeper_player_id FROM players WHERE name = ?", (player_name,))
    player = cursor.fetchone()
    if player:
        return player['sleeper_player_id']
    else:
        print(f"Player '{player_name}' not found.")
        return None

def find_league_id(conn, league_name):
    """Finds the sleeper_league_id for a given league name."""
    cursor = conn.cursor()
    cursor.execute("SELECT sleeper_league_id FROM LeagueMetadata WHERE name = ?", (league_name,))
    league = cursor.fetchone()
    if league:
        return league['sleeper_league_id']
    else:
        print(f"League '{league_name}' not found.")
        return None

def find_user_id(conn, username):
    """Finds the sleeper_user_id for a given username or display_name."""
    cursor = conn.cursor()
    # Check both username and display_name
    cursor.execute("SELECT sleeper_user_id FROM Users WHERE username = ? OR display_name = ?", (username, username))
    user = cursor.fetchone()
    if user:
        return user['sleeper_user_id']
    else:
        print(f"User '{username}' not found.")
        return None

def find_roster_id(conn, owner_sleeper_id, league_sleeper_id):
    """Finds the sleeper_roster_id for a given owner and league."""
    cursor = conn.cursor()
    cursor.execute("SELECT sleeper_roster_id FROM rosters WHERE owner_id = ? AND sleeper_league_id = ?", 
                   (owner_sleeper_id, league_sleeper_id))
    roster = cursor.fetchone()
    if roster:
        return roster['sleeper_roster_id']
    else:
        print(f"Roster not found for owner_id '{owner_sleeper_id}' in league_id '{league_sleeper_id}'.")
        return None

def insert_contract(conn, player_id, team_id, draft_amount, contract_year, duration, is_active):
    """Inserts a new contract into the contracts table."""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO contracts (player_id, team_id, draft_amount, contract_year, duration, is_active, updated_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (player_id, team_id, draft_amount, contract_year, duration, is_active))
        conn.commit()
        print(f"Contract inserted for player_id {player_id} on team_id {team_id}.")
    except sqlite3.IntegrityError as e:
        print(f"Could not insert contract for player {player_id} on team {team_id}. IntegrityError: {e}")
        print("This could be due to a duplicate entry (player_id, team_id may need to be unique for active contracts depending on schema details not fully specified here) or a non-existent player_id/team_id if foreign keys are not set up on these columns directly but rather on the tables they reference.")
    except sqlite3.Error as e:
        print(f"Error inserting contract for player_id {player_id} on team_id {team_id}: {e}")
        conn.rollback()

def main():
    conn = get_db_connection()
    if not conn:
        return

    league_name = "SKL - test league" # As per user request
    team_owner_username = "LordTokenizer" # As per user request

    # Player contract details
    contracts_to_add = [
        {"player_name": "Jayden Daniels", "draft_amount": 24, "contract_year": 2024, "duration": 3, "is_active": 1},
        {"player_name": "Caleb Williams", "draft_amount": 19, "contract_year": 2024, "duration": 4, "is_active": 1}
    ]

    # 1. Find League ID
    skl_league_id = find_league_id(conn, league_name)
    if not skl_league_id:
        conn.close()
        return

    # 2. Find User ID for LordTokenizer
    lord_tokenizer_user_id = find_user_id(conn, team_owner_username)
    if not lord_tokenizer_user_id:
        conn.close()
        return
        
    # 3. Find Roster ID for LordTokenizer in SKL - test league
    # Note: The 'contracts' table uses 'team_id' which corresponds to 'sleeper_roster_id' from the 'rosters' table
    target_team_id = find_roster_id(conn, lord_tokenizer_user_id, skl_league_id)
    if not target_team_id:
        print(f"Could not find roster_id for {team_owner_username} in league {league_name}.")
        conn.close()
        return
    
    print(f"Target league: {league_name} (ID: {skl_league_id})")
    print(f"Target owner: {team_owner_username} (User ID: {lord_tokenizer_user_id})")
    print(f"Target team (roster_id): {target_team_id}")

    for contract_details in contracts_to_add:
        player_name = contract_details["player_name"]
        print(f"\nProcessing contract for: {player_name}")
        
        # 4. Find Player ID
        player_id = find_player_id(conn, player_name)
        if not player_id:
            print(f"Skipping contract for {player_name} as player_id could not be found.")
            continue

        print(f"Found player_id for {player_name}: {player_id}")
        
        # 5. Insert contract
        insert_contract(conn, 
                        player_id, 
                        target_team_id, 
                        contract_details["draft_amount"],
                        contract_details["contract_year"],
                        contract_details["duration"],
                        contract_details["is_active"])

    conn.close()
    print("\nScript finished.")

if __name__ == "__main__":
    main() 