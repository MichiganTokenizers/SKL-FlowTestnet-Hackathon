import os
import sqlite3

print("Starting database recreation...")

# Delete existing db
if os.path.exists('keeper.db'):
    os.remove('keeper.db')
    print("Deleted existing keeper.db")

# Create new db
conn = sqlite3.connect('keeper.db')
cursor = conn.cursor()

# Create season_curr table
cursor.execute("""
CREATE TABLE season_curr (
    current_year INTEGER NOT NULL,
    IsOffSeason INTEGER NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Insert data
cursor.execute("INSERT INTO season_curr VALUES (2025, 1, datetime('now'))")

# Commit and close
conn.commit()
conn.close()

print("Database recreated with season_curr table")
print("Done!") 