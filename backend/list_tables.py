import sqlite3

def main():
    print("Checking tables in keeper.db...")
    conn = sqlite3.connect('keeper.db')
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("\nTables in database:")
    print("=" * 30)
    for table in tables:
        print(table[0])
    
    # Check if season_curr exists
    try:
        cursor.execute("SELECT COUNT(*) FROM season_curr")
        count = cursor.fetchone()[0]
        print(f"\nseason_curr table has {count} rows")
        
        if count > 0:
            cursor.execute("SELECT current_year, IsOffSeason FROM season_curr")
            data = cursor.fetchone()
            print(f"Year: {data[0]}, IsOffSeason: {data[1]}")
    except sqlite3.OperationalError as e:
        print(f"\nError accessing season_curr: {e}")
    
    conn.close()

if __name__ == "__main__":
    main() 