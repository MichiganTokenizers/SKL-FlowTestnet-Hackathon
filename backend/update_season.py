import sqlite3
import argparse
from datetime import datetime

def update_season(year=None, is_offseason=None):
    """
    Update the current season information in the season_curr table.
    
    Args:
        year: The season year to set (defaults to current year if None)
        is_offseason: Boolean indicating if it's off-season (1) or in-season (0)
    """
    if year is None:
        year = datetime.now().year
    
    try:
        with sqlite3.connect('keeper.db') as conn:
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='season_curr'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create table if it doesn't exist
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS season_curr (
                        current_year INTEGER NOT NULL,
                        IsOffSeason INTEGER NOT NULL,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            
            # Check if we need to update is_offseason
            if is_offseason is not None:
                # Convert to integer (1 for True, 0 for False)
                is_offseason_int = 1 if is_offseason else 0
                
                # Delete all rows and insert new values
                cursor.execute("DELETE FROM season_curr")
                cursor.execute('''
                    INSERT INTO season_curr (current_year, IsOffSeason, updated_at)
                    VALUES (?, ?, datetime("now"))
                ''', (year, is_offseason_int))
                
                conn.commit()
                print(f"Season updated: Year = {year}, IsOffSeason = {is_offseason_int}")
            else:
                # Just show current settings
                cursor.execute("SELECT current_year, IsOffSeason, updated_at FROM season_curr LIMIT 1")
                data = cursor.fetchone()
                
                if data:
                    print(f"Current season settings:")
                    print(f"Year: {data[0]}")
                    print(f"IsOffSeason: {data[1]} ({'Off-Season' if data[1] == 1 else 'In-Season'})")
                    print(f"Last Updated: {data[2]}")
                else:
                    print("No season data found. Run with --year and --offseason to set.")
    
    except Exception as e:
        print(f"Error updating season data: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update season information in the keeper.db database')
    parser.add_argument('--year', type=int, help='The season year (e.g., 2025)')
    parser.add_argument('--offseason', type=int, choices=[0, 1], 
                        help='Whether it is off-season (1) or in-season (0)')
    
    args = parser.parse_args()
    
    if args.year is None and args.offseason is None:
        # Just display current settings if no arguments
        update_season()
    else:
        # Update with provided arguments
        update_season(year=args.year, is_offseason=args.offseason) 