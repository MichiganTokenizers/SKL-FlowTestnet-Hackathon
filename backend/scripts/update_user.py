import sqlite3

def update_database():
    try:
        # Connect to the database
        with sqlite3.connect('/var/data/keeper.db') as conn:
            cursor = conn.cursor()
            
            # Update the wallet_address for LordTokenizer
            cursor.execute('''
                UPDATE users 
                SET wallet_address = ?, updated_at = datetime("now")
                WHERE display_name = ?
            ''', ('0:f07235fa4b51f7739b00a9858861360943bc805b9ce70f7384ce23708823949c', 'LordTokenizer'))
            
            print(f"Updated {cursor.rowcount} user(s) with display_name 'LordTokenizer'")
            
            # Delete rows with null sleeper_id
            cursor.execute('DELETE FROM users WHERE sleeper_user_id IS NULL')
            print(f"Deleted {cursor.rowcount} rows with null sleeper_user_id")
            
            # Commit the changes
            conn.commit()
            print("Database updated successfully")
            
    except Exception as e:
        print(f"Error updating database: {str(e)}")

if __name__ == "__main__":
    update_database() 