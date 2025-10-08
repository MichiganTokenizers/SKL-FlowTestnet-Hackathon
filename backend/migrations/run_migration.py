#!/usr/bin/env python3
"""
Run database migrations for SKL Admin Dashboard
"""
import sqlite3
import os
import sys

def run_migration(db_path, migration_file):
    """Execute a SQL migration file"""
    print(f"Running migration: {migration_file}")

    # Read migration file
    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Execute each statement separately (SQLite doesn't support multiple statements in executescript well with ALTER)
        statements = migration_sql.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                    print(f"✓ Executed: {statement[:60]}...")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print(f"⊘ Skipped (already exists): {statement[:60]}...")
                    else:
                        print(f"✗ Error: {e}")
                        print(f"   Statement: {statement}")
                        raise

        conn.commit()
        print(f"\n✅ Migration completed successfully!")

        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'Admin%' OR name LIKE '%Vault%' OR name LIKE '%Payout%' OR name LIKE 'FeeSchedules' OR name LIKE 'AgentExecutions'")
        tables = cursor.fetchall()
        print(f"\nCreated tables: {', '.join([t[0] for t in tables])}")

        # Verify admin user
        cursor.execute("SELECT wallet_address, role FROM AdminUsers")
        admins = cursor.fetchall()
        print(f"\nAdmin users: {admins}")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    # Determine database path
    db_path = os.getenv('DATABASE_URL', 'backend/keeper.db')
    if not os.path.exists(db_path):
        # Try alternative path
        db_path = 'keeper.db'

    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        sys.exit(1)

    print(f"Database: {db_path}")

    # Run migration
    migration_file = os.path.join(os.path.dirname(__file__), '001_add_admin_tables.sql')
    run_migration(db_path, migration_file)
