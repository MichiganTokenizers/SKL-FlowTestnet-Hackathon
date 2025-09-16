import sys
import os

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the init_db function from app.py
from .app import init_db

def main():
    print("Resetting database...")
    init_db(force_create=True)
    print("Database reset complete!")

if __name__ == "__main__":
    main() 