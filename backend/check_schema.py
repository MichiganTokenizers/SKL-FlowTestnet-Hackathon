import sqlite3

try:
    conn = sqlite3.connect('supreme_keeper_league.db')
    cursor = conn.cursor()
    
    # Check rosters table schema
    cursor.execute('PRAGMA table_info(rosters)')
    rows = cursor.fetchall()
    
    print('Rosters table columns:')
    for row in rows:
        print(f'  {row[1]} ({row[2]})')
    
    # Check if points_for column exists
    has_points_for = any(row[1] == 'points_for' for row in rows)
    print(f'\nHas points_for column: {has_points_for}')
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
