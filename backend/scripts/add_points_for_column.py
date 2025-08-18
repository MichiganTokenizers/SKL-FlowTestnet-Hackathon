#!/usr/bin/env python3
"""
Database migration script to add points_for column to rosters table.
This script adds the points_for column to store total points scored for each team.
"""

import sqlite3
import os
import sys

def add_points_for_column():
    """Add points_for column to rosters table if it doesn't exist."""
    
    # Get database path from environment or use default
    db_path = os.environ.get('KEEPER_DB_PATH', '/var/data/keeper.db')
    
    try:
        # Connect to the database
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Check if points_for column already exists
            cursor.execute("PRAGMA table_info(rosters)")
            columns = [column['name'] for column in cursor.fetchall()]
            
            if 'points_for' in columns:
                print("Column 'points_for' already exists in rosters table.")
                return True
            
            # Add the points_for column
            print("Adding points_for column to rosters table...")
            cursor.execute("ALTER TABLE rosters ADD COLUMN points_for REAL DEFAULT 0.0")
            
            # Verify the column was added
            cursor.execute("PRAGMA table_info(rosters)")
            columns_after = [column['name'] for column in cursor.fetchall()]
            
            if 'points_for' in columns_after:
                print("Successfully added points_for column to rosters table.")
                print("Column details:")
                cursor.execute("PRAGMA table_info(rosters)")
                for column in cursor.fetchall():
                    if column['name'] == 'points_for':
                        print(f"  - {column['name']}: {column['type']} (default: {column['dflt_value']})")
                return True
            else:
                print("Failed to add points_for column.")
                return False
                
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def main():
    """Main function to run the migration."""
    print("Starting database migration: Adding points_for column to rosters table")
    print("=" * 60)
    
    success = add_points_for_column()
    
    if success:
        print("\nMigration completed successfully!")
        print("The rosters table now includes a 'points_for' column for tracking total points scored.")
        print("\nNote: Existing rosters will have points_for set to 0.0 by default.")
        print("Points data will be populated when Sleeper data is refreshed.")
    else:
        print("\nMigration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 