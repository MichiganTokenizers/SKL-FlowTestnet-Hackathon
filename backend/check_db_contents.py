import sqlite3
import os

# Connect to the database
db_path = os.path.join(os.getcwd(), 'keeper.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check users table
cursor.execute('SELECT * FROM users')
users = cursor.fetchall()
print('Users table contents:')
for user in users:
    print(user)

# Check leagues table
cursor.execute('SELECT * FROM leagues')
leagues = cursor.fetchall()
print('\nLeagues table contents:')
for league in leagues:
    print(league)

# Check sessions table
cursor.execute('SELECT * FROM sessions')
sessions = cursor.fetchall()
print('\nSessions table contents:')
for session in sessions:
    print(session)

# Commit changes and close connection
conn.close()
print('Database contents check completed.') 