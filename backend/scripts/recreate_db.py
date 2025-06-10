import os
import sqlite3

def recreate_database():
    """Delete and recreate the keeper.db database with proper schema"""
    db_path = 'keeper.db'
    
    # Delete the existing database if it exists
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Deleted existing {db_path}")
        except Exception as e:
            print(f"Error deleting {db_path}: {e}")
            return False
    
    # Create new database and tables
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create all tables
        cursor.execute('''CREATE TABLE IF NOT EXISTS sessions
                          (wallet_address TEXT PRIMARY KEY, session_token TEXT)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS leagues
                          (sleeper_league_id TEXT,
                           sleeper_user_id TEXT,
                           name TEXT,
                           season TEXT,
                           status TEXT,
                           settings TEXT,
                           created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                           updated_at DATETIME)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                          (sleeper_user_id TEXT UNIQUE,
                           username TEXT,
                           display_name TEXT,
                           avatar TEXT,
                           wallet_address TEXT UNIQUE,
                           metadata TEXT,
                           created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                           updated_at DATETIME)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS players
                          (sleeper_player_id TEXT UNIQUE,
                           name TEXT,
                           position TEXT,
                           team TEXT,
                           created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                           updated_at DATETIME)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS rosters
                          (sleeper_roster_id TEXT,
                           league_id TEXT,
                           owner_id TEXT,
                           players TEXT,
                           settings TEXT,
                           metadata TEXT,
                           created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                           updated_at DATETIME)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS contracts
                          (player_id TEXT,
                           team_id TEXT,
                           sleeper_league_id TEXT,
                           draft_amount REAL,
                           contract_year INTEGER,
                           duration INTEGER,
                           is_active BOOLEAN DEFAULT 1,
                           created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                           updated_at DATETIME,
                           UNIQUE (player_id, team_id, contract_year, sleeper_league_id),
                           FOREIGN KEY (sleeper_league_id) REFERENCES LeagueMetadata(sleeper_league_id) ON DELETE CASCADE
                           )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS transactions
                          (sleeper_transaction_id TEXT UNIQUE,
                           league_id INTEGER,
                           type TEXT,
                           status TEXT,
                           data TEXT,
                           created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                           updated_at DATETIME)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS traded_picks
                          (league_id INTEGER,
                           draft_id TEXT,
                           round INTEGER,
                           roster_id TEXT,
                           previous_owner_id TEXT,
                           current_owner_id TEXT,
                           created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                           updated_at DATETIME)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS drafts
                          (sleeper_draft_id TEXT UNIQUE,
                           league_id INTEGER,
                           status TEXT,
                           start_time DATETIME,
                           data TEXT,
                           created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                           updated_at DATETIME)''')
        
        # Create the season_curr table
        cursor.execute('''CREATE TABLE IF NOT EXISTS season_curr
                          (current_year INTEGER NOT NULL,
                           IsOffSeason INTEGER NOT NULL,
                           updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        
        # Insert default season data
        cursor.execute('''INSERT INTO season_curr (current_year, IsOffSeason)
                          VALUES (2025, 1)''')
        
        conn.commit()
        print(f"Successfully created {db_path} with all tables")
        
        # Verify tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("\nCreated tables:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Verify season_curr data
        cursor.execute("SELECT current_year, IsOffSeason FROM season_curr")
        season_data = cursor.fetchone()
        print(f"\nSeason settings: Year={season_data[0]}, IsOffSeason={season_data[1]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error creating database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    recreate_database() 