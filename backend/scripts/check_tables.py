import sqlite3

def main():
    try:
        # Connect to the database
        with sqlite3.connect('/var/data/keeper.db') as conn:
            cursor = conn.cursor()
            
            # Get list of all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = cursor.fetchall()
            
            if not tables:
                print("No tables found in the database.")
                return
            
            print("\nTables in keeper.db:")
            print("=" * 40)
            for table in tables:
                print(table[0])
                
            # Try to verify season_curr specifically
            try:
                cursor.execute("SELECT * FROM season_curr LIMIT 1")
                data = cursor.fetchone()
                if data:
                    print("\nseason_curr table data:")
                    print(f"Year: {data[0]}, IsOffSeason: {data[1]}")
                else:
                    print("\nseason_curr table exists but has no data.")
            except sqlite3.OperationalError:
                print("\nCould not query season_curr table: table does not exist")
                
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 