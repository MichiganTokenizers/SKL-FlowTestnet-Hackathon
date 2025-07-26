import sqlite3
import os

# Connect to the database
db_path = '/var/data/keeper.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Alter the leagues table to add new columns if they don't exist
try:
    cursor.execute('ALTER TABLE leagues ADD COLUMN name TEXT')
    print('Added name column to leagues table')
except sqlite3.OperationalError as e:
    print('Column name already exists or error: ', str(e))

try:
    cursor.execute('ALTER TABLE leagues ADD COLUMN season TEXT')
    print('Added season column to leagues table')
except sqlite3.OperationalError as e:
    print('Column season already exists or error: ', str(e))

try:
    cursor.execute('ALTER TABLE leagues ADD COLUMN status TEXT')
    print('Added status column to leagues table')
except sqlite3.OperationalError as e:
    print('Column status already exists or error: ', str(e))

try:
    cursor.execute('ALTER TABLE leagues ADD COLUMN settings TEXT')
    print('Added settings column to leagues table')
except sqlite3.OperationalError as e:
    print('Column settings already exists or error: ', str(e))

# Commit changes and close connection
conn.commit()
conn.close()
print('Database schema updated successfully.') 