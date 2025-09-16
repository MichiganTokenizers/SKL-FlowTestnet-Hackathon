#!/usr/bin/env python3
"""
Migration script to add players_updated_at column to season_curr table.
This enables time-based throttling of player data updates separate from general season updates.
"""

import sqlite3
import os

def add_players_updated_at():
    """Add players_updated_at column to season_curr table."""
    db_path = os.path.join(os.path.dirname(__file__), 'keeper.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(season_curr)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'players_updated_at' in columns:
            print("Column 'players_updated_at' already exists in season_curr table")
            return True
        
        # Add the new column
        cursor.execute('''
            ALTER TABLE season_curr 
            ADD COLUMN players_updated_at DATETIME
        ''')
        
        conn.commit()
        print("Successfully added 'players_updated_at' column to season_curr table")
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = add_players_updated_at()
    if success:
        print("Migration completed successfully")
    else:
        print("Migration failed")
