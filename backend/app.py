from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
import sqlite3, math
import os
import secrets
import requests # Added import for requests
from sleeper_service import SleeperService
import json
import time # Added for potential sleep, though might not be used in final global conn version
from functools import wraps # Import wraps
import logging # Add logging import
from typing import Any
from utils import get_escalated_contract_costs # Changed to direct import

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Environment variables loaded from .env file")
except ImportError:
    print("python-dotenv not installed. Using system environment variables only.")

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create Flask app instance at the top
app = Flask(__name__)

# Production configuration
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
app.config['ENV'] = os.getenv('FLASK_ENV', 'production')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6')

print(f"Flask configured - Environment: {app.config['ENV']}, Debug: {app.config['DEBUG']}")

# --- TEMPORARY DEBUGGING: Global DB Connection ---
# DO NOT USE IN PRODUCTION
_global_db_conn = None

def get_global_db_connection():
    global _global_db_conn
    if _global_db_conn is None:
        print("DEBUG_GLOBAL_CONN: Initializing global database connection...")
        try:
            # Use environment variable for database path
            db_path = os.getenv('DATABASE_URL', '/var/data/keeper.db')
            print(f"DEBUG_GLOBAL_CONN: Connecting to database at: {db_path}")
            _global_db_conn = sqlite3.connect(db_path, check_same_thread=False)
            _global_db_conn.row_factory = sqlite3.Row
            # Attempt to set WAL mode on this global connection too
            cursor = _global_db_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            current_journal_mode = cursor.execute("PRAGMA journal_mode;").fetchone()
            print(f"DEBUG_GLOBAL_CONN: Journal mode set to: {current_journal_mode[0] if current_journal_mode else 'Unknown'}")
            cursor.execute("PRAGMA foreign_keys = ON;") # Enforce foreign key constraints
            print("DEBUG_GLOBAL_CONN: Foreign keys ON.")
            _global_db_conn.commit() # Commit pragma changes
            print("DEBUG_GLOBAL_CONN: Global database connection initialized successfully.")
        except sqlite3.Error as e:
            print(f"DEBUG_GLOBAL_CONN: Failed to initialize global connection or set WAL mode: {e}")
            # If connection failed, _global_db_conn will remain None or be a broken object.
            # Handle this gracefully or let it raise further up.
            raise
    return _global_db_conn
# --- END TEMPORARY DEBUGGING ---

# Initialize SleeperService
# sleeper_service = SleeperService() # Old instantiation
db_conn = get_global_db_connection()  # Get the global connection
# NOTE: SleeperService class will need significant updates to align with the new database schema 
# (LeagueMetadata, UserLeagueLinks, rosters.sleeper_league_id, etc.) for data insertion and querying.
sleeper_service = SleeperService(db_connection=db_conn) # Pass it to the service

@app.route('/')
def root():
    """Root endpoint for health checks."""
    return jsonify({'status': 'ok', 'message': 'Supreme Keeper League Backend is running'}), 200

@app.before_request
def log_cors_headers():
    print(f"Request method: {request.method}, URL: {request.url}")
    if request.method == "OPTIONS":
        print("Handling OPTIONS preflight request")
        response = app.make_response('')
        # Allow both development and production origins
        origin = request.headers.get('Origin', '')
        if origin in ['http://localhost:5173', 'https://supremekeeperleague.com']:
            response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response, 200

@app.errorhandler(Exception)
def handle_exception(e):
    print(f"Unhandled exception: {str(e)}")
    import traceback
    traceback.print_exc()
    response = jsonify({'success': False, 'error': f'Server error: {str(e)}'})
    response.status_code = 500
    # Allow both development and production origins
    origin = request.headers.get('Origin', '')
    if origin in ['http://localhost:5173', 'https://supremekeeperleague.com']:
        response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

@app.after_request
def add_cors_headers(response):
    # Allow both development and production origins
    origin = request.headers.get('Origin', '')
    if origin in ['http://localhost:5173', 'https://supremekeeperleague.com']:
        response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    print(f"Response headers after modification: {response.headers}")
    return response

# Initialize the database
def init_db():
    try:
        conn = get_global_db_connection() # Use global connection
        cursor = conn.cursor()
        
        # Enable WAL mode is handled by get_global_db_connection() now
        # So, no specific PRAGMA call here unless to re-verify or if get_global_db_connection fails.

        # TEMPORARY: Add missing points_for column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE rosters ADD COLUMN points_for REAL DEFAULT 0.0")
            print("Added missing points_for column to rosters table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("points_for column already exists - no action needed")
            else:
                print(f"Error adding points_for column: {e}")

        # Check if tables exist and create them if they don't
        print("Checking existing tables and creating missing ones...")
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS sessions
                          (wallet_address TEXT PRIMARY KEY, session_token TEXT)''')
        
        # Create LeagueMetadata first as UserLeagueLinks will reference it
        cursor.execute('''CREATE TABLE IF NOT EXISTS LeagueMetadata (
                            sleeper_league_id TEXT PRIMARY KEY,
                            name TEXT,
                            season TEXT,
                            status TEXT, 
                            settings TEXT, -- Stores JSON settings from Sleeper
                            scoring_settings TEXT, -- Stores JSON scoring settings from Sleeper
                            roster_positions TEXT, -- Stores JSON of roster positions from Sleeper
                            previous_league_id TEXT, -- Sleeper specific
                            league_creation_time INTEGER, -- epoch time
                            display_order INTEGER,
                            company_id TEXT,
                            bracket_id TEXT,
                            avatar TEXT, -- URL to league avatar
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME
                            )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS LeagueFees (
                            sleeper_league_id TEXT NOT NULL,
                            season_year INTEGER NOT NULL,
                            fee_amount REAL,
                            fee_currency TEXT DEFAULT 'FLOW', -- e.g., 'FLOW', 'USDF'
                            notes TEXT,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME,
                            PRIMARY KEY (sleeper_league_id, season_year),
                            FOREIGN KEY (sleeper_league_id) REFERENCES LeagueMetadata(sleeper_league_id) ON DELETE CASCADE
                            )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS UserLeagueLinks (
                            wallet_address TEXT,
                            sleeper_league_id TEXT,
                            is_commissioner INTEGER DEFAULT 0,
                            fee_paid_amount REAL DEFAULT 0.0,
                            fee_payment_status TEXT DEFAULT 'unpaid', -- e.g., 'unpaid', 'paid', 'partially_paid', 'waived',
                            updated_at DATETIME,
                            PRIMARY KEY (wallet_address, sleeper_league_id),
                            FOREIGN KEY (wallet_address) REFERENCES Users(wallet_address) ON DELETE CASCADE,
                            FOREIGN KEY (sleeper_league_id) REFERENCES LeagueMetadata(sleeper_league_id) ON DELETE CASCADE
                            )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS LeaguePayments (
                            sleeper_league_id TEXT NOT NULL,
                            season_year INTEGER NOT NULL,
                            wallet_address TEXT NOT NULL, -- Wallet of the payer
                            amount REAL NOT NULL,
                            currency TEXT NOT NULL,
                            transaction_id TEXT UNIQUE NOT NULL, -- Each payment has a unique Flow transaction ID
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- To determine most recent
                            FOREIGN KEY (sleeper_league_id) REFERENCES LeagueMetadata(sleeper_league_id) ON DELETE CASCADE,
                            FOREIGN KEY (wallet_address) REFERENCES Users(wallet_address) ON DELETE CASCADE
                            )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS Users (
                            wallet_address TEXT PRIMARY KEY,
                            sleeper_user_id TEXT UNIQUE,
                            username TEXT,
                            display_name TEXT,
                            avatar TEXT,
                            metadata TEXT,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME
                            )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS players
                          (sleeper_player_id TEXT UNIQUE,
                           name TEXT,
                           position TEXT,
                           team TEXT,
                           created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                           updated_at DATETIME)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS rosters
                          (sleeper_roster_id TEXT,
                           sleeper_league_id TEXT,
                           owner_id TEXT, -- Sleeper user ID of the roster owner
                           team_name TEXT, -- Actual team name, sourced by sleeper_service
                           players TEXT, -- JSON list of player_ids on main roster
                           metadata TEXT, -- JSON of roster metadata (e.g., custom team name from Sleeper)
                           reserve TEXT, -- JSON list of player_ids on reserve
                           wins INTEGER DEFAULT 0,
                           losses INTEGER DEFAULT 0,
                           ties INTEGER DEFAULT 0,
                           points_for REAL DEFAULT 0.0,
                           created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                           updated_at DATETIME,
                           PRIMARY KEY (sleeper_roster_id, sleeper_league_id),
                           FOREIGN KEY (sleeper_league_id) REFERENCES LeagueMetadata(sleeper_league_id) ON DELETE CASCADE
                           )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS contracts
                          (rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                           player_id TEXT,
                           team_id TEXT,
                           sleeper_league_id TEXT, -- Added
                           draft_amount REAL,
                           contract_year INTEGER,
                           duration INTEGER,
                           is_active BOOLEAN DEFAULT 1,
                           created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                           updated_at DATETIME,
                           UNIQUE (player_id, team_id, contract_year, sleeper_league_id), -- Updated
                           FOREIGN KEY (sleeper_league_id) REFERENCES LeagueMetadata(sleeper_league_id) ON DELETE CASCADE -- Added
                           )''') 
        cursor.execute('''CREATE TABLE IF NOT EXISTS penalties
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           contract_id INTEGER,
                           penalty_year INTEGER,
                           penalty_amount REAL,
                           created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                           updated_at DATETIME,
                           FOREIGN KEY (contract_id) REFERENCES contracts(rowid) ON DELETE CASCADE 
                           )''') # Now contracts has explicit rowid, so this FK will work
        cursor.execute('''CREATE TABLE IF NOT EXISTS transactions
                          (sleeper_transaction_id TEXT UNIQUE,
                           league_id INTEGER,
                           type TEXT,
                           status TEXT,
                           data TEXT,
                           created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                           updated_at DATETIME)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS drafts
                          (sleeper_draft_id TEXT UNIQUE,
                           league_id TEXT, -- Changed from INTEGER
                           season TEXT, -- Added for easier lookup of drafts for a specific season
                           status TEXT,
                           start_time DATETIME,
                           data TEXT,
                           created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                           updated_at DATETIME)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS season_curr
                          (current_year TEXT,
                           IsOffSeason INTEGER,
                           updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')

        # Create trade-related tables
        cursor.execute('''CREATE TABLE IF NOT EXISTS trades (
                            trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            sleeper_league_id TEXT NOT NULL,
                            initiator_team_id TEXT NOT NULL,
                            recipient_team_id TEXT NOT NULL,
                            trade_status TEXT DEFAULT 'pending', -- pending, approved, rejected, completed
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME,
                            commissioner_notes TEXT,
                            FOREIGN KEY (sleeper_league_id) REFERENCES LeagueMetadata(sleeper_league_id) ON DELETE CASCADE,
                            FOREIGN KEY (initiator_team_id) REFERENCES rosters(sleeper_roster_id),
                            FOREIGN KEY (recipient_team_id) REFERENCES rosters(sleeper_roster_id)
                            )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS trade_items (
                            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            trade_id INTEGER NOT NULL,
                            from_team_id TEXT NOT NULL,
                            to_team_id TEXT NOT NULL,
                            budget_amount REAL NOT NULL, -- Dollar amount being traded
                            season_year INTEGER NOT NULL, -- Which future year (e.g., 2026, 2027, 2028, 2029)
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE,
                            FOREIGN KEY (from_team_id) REFERENCES rosters(sleeper_roster_id),
                            FOREIGN KEY (to_team_id) REFERENCES rosters(sleeper_roster_id)
                            )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS trade_approvals (
                            approval_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            trade_id INTEGER NOT NULL,
                            approver_type TEXT NOT NULL, -- 'commissioner'
                            approver_id TEXT NOT NULL, -- sleeper_user_id of commissioner
                            approval_status TEXT NOT NULL, -- 'approved', 'rejected', 'pending'
                            approval_notes TEXT,
                            approved_at DATETIME,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (trade_id) REFERENCES trades(trade_id) ON DELETE CASCADE
                            )''')

        # Create the vw_contractByYear view
        # This view calculates the escalated cost for each year of every contract
        cursor.execute('''
            CREATE VIEW IF NOT EXISTS vw_contractByYear AS
            WITH RECURSIVE ContractYearCosts (
                original_contract_rowid, 
                player_id,
                team_id,                 
                sleeper_league_id, -- Added
                contract_start_season,   
                contract_duration,       
                year_number_in_contract, 
                cost_for_season          
            ) AS (
                SELECT
                    c.rowid,
                    c.player_id,
                    c.team_id,
                    c.sleeper_league_id, -- Added
                    c.contract_year,
                    c.duration,
                    1, 
                    c.draft_amount 
                FROM
                    contracts c
                UNION ALL
                SELECT
                    cyc.original_contract_rowid,
                    cyc.player_id,
                    cyc.team_id,
                    cyc.sleeper_league_id, -- Added
                    cyc.contract_start_season,
                    cyc.contract_duration,
                    cyc.year_number_in_contract + 1,
                    CAST( (cyc.cost_for_season * 1.1) + 0.9999999999 AS INTEGER)
                FROM
                    ContractYearCosts cyc
                WHERE
                    cyc.year_number_in_contract < cyc.contract_duration
            )
            SELECT
                cyc.original_contract_rowid,
                cyc.player_id,
                p.name AS player_name, 
                cyc.team_id,
                cyc.sleeper_league_id, -- Added
                cyc.contract_start_season,
                cyc.contract_duration,
                cyc.year_number_in_contract,
                (cyc.contract_start_season + cyc.year_number_in_contract - 1) AS season_for_this_year_of_contract, 
                cyc.cost_for_season
            FROM
                ContractYearCosts cyc
            JOIN
                players p ON cyc.player_id = p.sleeper_player_id 
            ORDER BY
                cyc.player_id,
                cyc.team_id,
                cyc.contract_start_season,
                cyc.year_number_in_contract;
        ''')
        print("View vw_contractByYear creation/check executed.")

        conn.commit() 
        print("Database initialized successfully via global connection")
    except Exception as e:
        print(f"Failed to initialize database (global conn): {str(e)}")
        # Potentially close and None out _global_db_conn if init fails badly
        global _global_db_conn
        if _global_db_conn:
            try:
                _global_db_conn.close()
            except: # nosec
                pass
        _global_db_conn = None
        raise

print("DEBUG: Database initialization skipped. Proceeding to define routes and helpers...")



def get_current_season():
    """Fetches the current season year and off-season status from the local season_curr table."""
    try:
        conn = get_global_db_connection()
        cursor = conn.cursor()
        # Ensure we fetch from rowid=1 as per INSERT OR REPLACE logic in sleeper_service
        cursor.execute("SELECT current_year, IsOffSeason FROM season_curr WHERE rowid = 1 LIMIT 1")
        season_info_db = cursor.fetchone()

        if season_info_db and season_info_db["current_year"] is not None and season_info_db["IsOffSeason"] is not None:
            year_db = int(season_info_db["current_year"])
            is_offseason_db = bool(season_info_db["IsOffSeason"])
            app.logger.info(f"get_current_season: Retrieved season info from DB: Year={year_db}, IsOffseason={is_offseason_db}")
            return {"current_year": year_db, "is_offseason": is_offseason_db}
        else:
            app.logger.error("get_current_season: CRITICAL - No valid season information found in season_curr table. Using hardcoded defaults.")
            return {"current_year": 2025, "is_offseason": True} # Fallback to hardcoded defaults

    except sqlite3.Error as e:
        app.logger.error(f"get_current_season: Database error when fetching from season_curr: {e}. Using hardcoded defaults.")
        return {"current_year": 2025, "is_offseason": True} # Fallback for DB errors
    except Exception as e:
        app.logger.error(f"get_current_season: Unexpected error: {e}. Using hardcoded defaults.")
        return {"current_year": 2025, "is_offseason": True} # General fallback



def get_current_user():
    """Retrieve the current user.
    Tries Flask session first, then Authorization header token.
    """
    wallet_address = session.get('wallet_address') 
    
    if wallet_address:
        print(f"DEBUG: get_current_user - Found wallet_address in Flask session: {wallet_address}")
    else:
        print(f"DEBUG: get_current_user - No wallet_address in Flask session. Checking Authorization header.")
        auth_header = request.headers.get('Authorization')
        if auth_header:
            # Frontend sends token directly as per App.jsx: headers: { 'Authorization': token }
            # If it could be "Bearer <token>", add splitting logic here.
            session_token_from_header = auth_header 

            if session_token_from_header:
                print(f"DEBUG: get_current_user - Found token in Authorization header: {session_token_from_header[:10]}...")
                conn_header_check = get_global_db_connection()
                cursor_header_check = conn_header_check.cursor()
                cursor_header_check.execute("SELECT wallet_address FROM sessions WHERE session_token = ?", (session_token_from_header,))
                session_db_data = cursor_header_check.fetchone()
                if session_db_data:
                    wallet_address = session_db_data['wallet_address']
                    print(f"DEBUG: get_current_user - Wallet address from DB via header token: {wallet_address}")
                    # Optionally, set Flask session here for this request if desired, though it might be set by /login already for cookie-based sessions.
                    # session['wallet_address'] = wallet_address 
                else:
                    print(f"DEBUG: get_current_user - Header token invalid or expired. No session found in DB for token {session_token_from_header[:10]}...")
            else:
                print(f"DEBUG: get_current_user - Authorization header present but no token value.")
        else:
            print(f"DEBUG: get_current_user - No Authorization header found.")

    if not wallet_address:
        print(f"DEBUG: get_current_user - Still no wallet_address after all checks. Cannot authenticate.")
        return None
    
    # Proceed to fetch user details from Users table with the determined wallet_address
    conn = get_global_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE wallet_address = ?", (wallet_address,))
    user = cursor.fetchone()

    if not user:
        print(f"DEBUG: get_current_user - User not found in DB for wallet_address: {wallet_address}. This is unusual if wallet_address was validated. Clearing Flask session if it was the source.") 
        if session.get('wallet_address') == wallet_address: # Only pop if this wallet_address came from Flask session
            session.pop('wallet_address', None) 
        return None
        
    print(f"DEBUG: get_current_user - User authenticated and found in DB: {dict(user) if user else 'None'}") 
    return dict(user) if user else None


@app.route('/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    try:
        print("Received /auth/login request")
        print(f"Request headers: {request.headers}")
        print(f"Request data: {request.get_data(as_text=True)}")

        data = request.get_json()
        if data is None:
            print("Failed to parse JSON from request")
            return jsonify({'success': False, 'error': 'Invalid JSON payload'}), 400

        wallet_address = data.get('walletAddress')

        if not wallet_address:
            print("Missing walletAddress")
            return jsonify({'success': False, 'error': 'Missing walletAddress'}), 400

        session_token = secrets.token_urlsafe(32)
        print(f"Generated session token: {session_token}")

        conn = get_global_db_connection() # Use global connection
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT wallet_address, sleeper_user_id FROM Users WHERE wallet_address = ?', (wallet_address,))
        user = cursor.fetchone()
        is_new_user = not user

        if is_new_user:
            # Create new user
            cursor.execute('''
                INSERT INTO Users (
                    wallet_address,
                    created_at
                ) VALUES (?, datetime("now"))''',
                (wallet_address,)
            )
            print("Created new user")
            # Also create a session for the new user
            cursor.execute('''
                INSERT OR REPLACE INTO sessions (
                    wallet_address,
                    session_token
                ) VALUES (?, ?)''',
                (wallet_address, session_token)
            )
            conn.commit()
            session['wallet_address'] = wallet_address # Set Flask session
            print(f"DEBUG: Flask session set for new user: {wallet_address}")

        else:
            # For existing users, check if they have a Sleeper user ID
            if user['sleeper_user_id']:
                print(f"Existing user with Sleeper ID detected, triggering full Sleeper data pull via /auth/login path")
                full_data_response = sleeper_service.fetch_all_data(wallet_address)
                if not full_data_response['success']:
                    print(f"Failed to fetch full Sleeper data in /auth/login: {full_data_response.get('error', 'Unknown error')}")
                    # Don't return error here, just log it. The user can still log in
            else:
                print(f"Existing user without Sleeper ID detected: {wallet_address}")
            
            # Create or update session
            cursor.execute('''
                INSERT OR REPLACE INTO sessions (
                    wallet_address,
                    session_token
                ) VALUES (?, ?)''',
                (wallet_address, session_token)
            )
            conn.commit()
            session['wallet_address'] = wallet_address # Set Flask session
            print(f"DEBUG: Flask session set for existing user: {wallet_address}")
            print("Successfully created/updated session in DB and Flask session")

        return jsonify({
            'success': True,
            'sessionToken': session_token,
            'isNewUser': is_new_user,
            'hasSleeperId': not is_new_user and user['sleeper_user_id'] is not None
        })

    except Exception as e:
        print(f"Error in /auth/login: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

# Auth verify route
@app.route('/auth/verify', methods=['GET'])
def verify():
    session_token = request.headers.get('Authorization')
    if not session_token:
        return jsonify({'success': False, 'error': 'No session token'}), 401

    conn = get_global_db_connection() # Use global connection
    cursor = conn.cursor()
    session_data = cursor.execute('SELECT wallet_address FROM sessions WHERE session_token = ?', (session_token,)).fetchone()
    if not session_data:
        return jsonify({'success': False, 'error': 'Invalid session'}), 401

    return jsonify({'success': True, 'walletAddress': session_data['wallet_address']})

# Leagues route
@app.route('/leagues', methods=['GET'])
def get_leagues():
    """Fetches all leagues present in the LeagueMetadata table."""
    # This endpoint is public and shows all leagues in the system.
    # For user-specific leagues, use /league/local.
    try:
        conn = get_global_db_connection()
        cursor = conn.cursor()
        
        # Fetch all leagues from LeagueMetadata
        cursor.execute('''
            SELECT sleeper_league_id, name, season, status, avatar, settings
            FROM LeagueMetadata 
            ORDER BY name, season DESC
        ''')
        leagues_data = cursor.fetchall()
        
        leagues_list = []
        for row in leagues_data:
            settings_json = json.loads(row['settings']) if row['settings'] else {}
            leagues_list.append({
                'league_id': row['sleeper_league_id'],
                'name': row['name'],
                'season': row['season'],
                'status': row['status'],
                'avatar': row['avatar'],
                'total_rosters': settings_json.get('total_rosters'),
                # Add other publicly relevant league details here
            })
            
        print(f"DEBUG: /leagues - Fetched {len(leagues_list)} leagues from LeagueMetadata.")
        return jsonify({'success': True, 'leagues': leagues_list}), 200

    except sqlite3.Error as e:
        print(f"ERROR: /leagues - Database error: {str(e)}")
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        print(f"ERROR: /leagues - Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}), 500

# Logout route
@app.route('/logout')
def logout():
    session.pop('wallet_address', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('initiate_login'))

# Decorator for protected routes
def login_required(f):
    @wraps(f) # Ensure to use @wraps(f) from functools
    def wrap(*args, **kwargs):
        current_user = get_current_user()
        if not current_user:
            print(f"DEBUG: login_required - Denying access to {f.__name__} because get_current_user returned None.") 
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs) 
    return wrap

# League page route
@app.route('/league/local')
def get_league_data_local():
    """Fetches league data for the authenticated user from the local database."""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'User not authenticated'}), 401

    wallet_address = user['wallet_address']
    print(f"DEBUG: /league/local - Authenticated user wallet_address: {wallet_address}")

    try:
        conn = get_global_db_connection()
        cursor = conn.cursor()

        # Get user's sleeper_user_id and display_name from Users table
        print(f"DEBUG: /league/local - Querying Users table for wallet_address: {wallet_address}")
        cursor.execute('SELECT sleeper_user_id, username, display_name FROM Users WHERE wallet_address = ?', (wallet_address,))
        user_data = cursor.fetchone()
            
        if not user_data or not user_data['sleeper_user_id']:
            print(f"DEBUG: /league/local - No sleeper_user_id found for wallet_address: {wallet_address}. User might not have associated Sleeper account yet.")
            return jsonify({'success': True, 'leagues': [], 'user_info': {'wallet_address': wallet_address, 'sleeper_user_id': None, 'display_name': 'N/A'}}), 200

        sleeper_user_id = user_data['sleeper_user_id']
        display_name = user_data['display_name'] or user_data['username'] # Fallback to username if display_name is None

        print(f"DEBUG: /league/local - User info: sleeper_user_id={sleeper_user_id}, display_name={display_name}")

        # Fetch leagues associated with the user through UserLeagueLinks and join with LeagueMetadata
        cursor.execute('''
            SELECT lm.sleeper_league_id, lm.name, lm.season, lm.status, lm.settings, lm.avatar
            FROM UserLeagueLinks ull
            JOIN LeagueMetadata lm ON ull.sleeper_league_id = lm.sleeper_league_id
            WHERE ull.wallet_address = ?
        ''', (wallet_address,))
        leagues_data = cursor.fetchall()

        leagues_list = []
        if leagues_data:
            for row in leagues_data:
                leagues_list.append({
                    'league_id': row['sleeper_league_id'],
                    'name': row['name'],
                    'season': row['season'],
                    'status': row['status'],
                    'avatar': row['avatar'], # Added avatar
                    'total_rosters': json.loads(row['settings']).get('total_rosters') if row['settings'] else None, # Example: extracting from settings
                    # Add other relevant league details from LeagueMetadata as needed
                })
            print(f"DEBUG: /league/local - Found {len(leagues_list)} leagues for wallet_address {wallet_address}.")
        else:
            print(f"DEBUG: /league/local - No leagues found for wallet_address {wallet_address} in UserLeagueLinks.")

        return jsonify({
            'success': True, 
            'leagues': leagues_list, 
            'user_info': {
                'wallet_address': wallet_address,
                'sleeper_user_id': sleeper_user_id,
                'display_name': display_name
            }
        }), 200

    except sqlite3.Error as e:
        print(f"ERROR: /league/local - Database error: {str(e)}")
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        print(f"ERROR: /league/local - Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}), 500

# Waive player route

# League connection route
@app.route('/league/connect', methods=['POST'])
def connect_league():
    # NOTE: This function appears to use an undefined KeeperDB class and logic 
    # that needs to be updated to align with the new database schema (LeagueMetadata, UserLeagueLinks)
    # and use the global db connection or SleeperService for database operations.
    data = request.get_json()
    league_id = data.get('league_id')
    wallet_address = data.get('walletAddress')
    
    if not league_id or not wallet_address:
        return jsonify({'error': 'Missing leagueId or walletAddress'}), 400
    
    # Save league connection
    db = KeeperDB()
    db.connect_league(wallet_address, league_id)
    
    # Trigger full data pull for the league
    sleeper_service.fetch_all_data(wallet_address)
    
    return jsonify({'message': 'League connected successfully'}), 200

# Sleeper integration routes

# League teams route
@app.route('/league/teams')
def get_league_teams():
    session_token = request.headers.get('Authorization')
    if not session_token:
        return jsonify({'success': False, 'error': 'No session token'}), 401
    
    try:
        db = KeeperDB()
        with get_global_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get user from session
            cursor.execute('SELECT wallet_address FROM sessions WHERE session_token = ?', (session_token,))
            session_data = cursor.fetchone()
            if not session_data:
                return jsonify({'success': False, 'error': 'Invalid session'}), 401
            
            wallet_address = session_data[0]
            
            # Get team data from local database
            team_data = db.get_team_data(wallet_address)
            
            if not team_data:
                return jsonify({'success': False, 'error': 'No team data found'}), 404
            
            return jsonify({'success': True, 'teams': team_data})
    except Exception as e:
        print(f"Error in /league/teams: {str(e)}")
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/sleeper/import', methods=['POST'])
def import_sleeper_data():
    session_token = request.headers.get('Authorization')
    if not session_token:
        return jsonify({'success': False, 'error': 'No session token'}), 401
    
    try:
        db = KeeperDB()
        with get_global_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get user from session
            cursor.execute('SELECT wallet_address FROM sessions WHERE session_token = ?', (session_token,))
            session_data = cursor.fetchone()
            if not session_data:
                return jsonify({'success': False, 'error': 'Invalid session'}), 401
            
            wallet_address = session_data[0]
            
            # Check if local data exists
            league_data = db.get_league_data(wallet_address)
            
            if league_data:
                return jsonify({'success': True, 'message': 'Local data already exists', 'league': league_data})
            
            # If no local data, trigger full data pull
            sleeper_service.fetch_all_data(wallet_address)
            
            return jsonify({'success': True, 'message': 'Data imported successfully'})
    except Exception as e:
        print(f"Error in /sleeper/import: {str(e)}")
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/sleeper/fetchAll', methods=['POST'])
def fetch_all_data_route():
    session_token = request.headers.get('Authorization')
    if not session_token:
        return jsonify({'success': False, 'error': 'No session token'}), 401
    
    try:
        # REMOVE THIS LOGGING LINE
        # app.logger.info(f"Accessed /sleeper/fetchAll route. Method: {request.method}")
        print(f"DEBUG: /sleeper/fetchAll called, method: {request.method}")
        print(f"DEBUG: Headers: {request.headers}")
        
        conn = get_global_db_connection() # Use global connection
        cursor = conn.cursor()
            
        cursor.execute('SELECT wallet_address FROM sessions WHERE session_token = ?', (session_token,))
        session_data = cursor.fetchone()
        if not session_data:
            print("DEBUG: Invalid session token in /sleeper/fetchAll")
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
            
        wallet_address = session_data[0]
        print(f"DEBUG: Wallet address in /sleeper/fetchAll: {wallet_address}")
            
        # Verify sleeper_user_id BEFORE calling sleeper_service
        cursor.execute("SELECT sleeper_user_id FROM Users WHERE wallet_address = ?", (wallet_address,))
        user_check = cursor.fetchone()
        print(f"DEBUG: Pre-service call user check in /sleeper/fetchAll for {wallet_address}: {dict(user_check) if user_check else 'No user found'}")

        print("DEBUG: Calling sleeper_service.fetch_all_data() in /sleeper/fetchAll")
        result = sleeper_service.fetch_all_data(wallet_address)
        print(f"DEBUG: Result from fetch_all_data in /sleeper/fetchAll: {result}")
            
        if not result.get('success'):
            error_message = result.get('error', 'Unknown error during data fetch')
            print(f"DEBUG: fetch_all_data failed in /sleeper/fetchAll: {error_message}")
            status_code = 400 # Bad Request, as the user needs association
            if "No Sleeper user ID associated" in error_message:
                status_code = 404 # Or 404 if we consider the sleeper user itself not found for this wallet
            return jsonify({'success': False, 'error': error_message}), status_code
            
        print("DEBUG: /sleeper/fetchAll successful")
        conn.commit() # Commit changes if fetch_all_data was successful
        return jsonify({'success': True, 'message': 'Full data pull triggered successfully'})
    except Exception as e:
        print(f"ERROR in /sleeper/fetchAll: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

# League local data route
@app.route('/league/standings/local', methods=['GET'])
@login_required
def get_league_standings_local():
    """Fetches league standings for a specific league_id, ensuring the user is part of it."""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'User not authenticated'}), 401

    wallet_address = user['wallet_address']
    league_id_from_request = request.args.get('league_id')

    if not league_id_from_request:
        return jsonify({'success': False, 'error': 'Missing league_id parameter'}), 400

    print(f"DEBUG: /league/standings/local - User: {wallet_address}, Requested League ID: {league_id_from_request}")

    try:
        conn = get_global_db_connection()
        cursor = conn.cursor()

        # Verify the user is linked to this league_id in UserLeagueLinks
        cursor.execute("SELECT 1 FROM UserLeagueLinks WHERE wallet_address = ? AND sleeper_league_id = ?", 
                       (wallet_address, league_id_from_request))
        if not cursor.fetchone():
            print(f"DEBUG: /league/standings/local - User {wallet_address} is not authorized or not linked to league {league_id_from_request}.")
            # Check if the league even exists to give a more specific error
            cursor.execute("SELECT 1 FROM LeagueMetadata WHERE sleeper_league_id = ?", (league_id_from_request,))
            if not cursor.fetchone():
                 return jsonify({'success': False, 'error': f'League with ID {league_id_from_request} not found.'}), 404
            return jsonify({'success': False, 'error': 'User not authorized for this league or league link does not exist.'}), 403

        # Fetch league metadata for context (e.g., league name)
        cursor.execute("SELECT name, season FROM LeagueMetadata WHERE sleeper_league_id = ?", (league_id_from_request,))
        league_meta = cursor.fetchone()
        if not league_meta:
            # This case should ideally be caught by the UserLeagueLinks check if foreign keys are enforced
            print(f"ERROR: /league/standings/local - LeagueMetadata not found for {league_id_from_request} even after UserLeagueLinks check.")
            return jsonify({'success': False, 'error': f'League metadata not found for ID {league_id_from_request}.'}), 404
        
        league_name = league_meta['name']
        league_season = league_meta['season']
        print(f"DEBUG: /league/standings/local - Verified user is part of league: {league_name} ({league_id_from_request})")

        # Fetch rosters and join with Users to get display_name for roster owners
        cursor.execute('''
            SELECT 
                r.sleeper_roster_id,
                r.owner_id, -- This is sleeper_user_id
                r.team_name as roster_team_name, -- Directly select the new team_name column
                COALESCE(u.display_name, u.username, r.owner_id) as owner_display_name, -- Use display_name, fallback to username, then owner_id
                u.avatar as owner_avatar,
                r.players, -- JSON string of player_ids
                r.wins,
                r.losses,
                r.ties,
                r.points_for
            FROM rosters r
            LEFT JOIN Users u ON r.owner_id = u.sleeper_user_id -- Join with Users table
            WHERE r.sleeper_league_id = ?
        ''', (league_id_from_request,))
        rosters_data = cursor.fetchall()

        simplified_roster_info = []
        for row in rosters_data:
            # Use the directly fetched team_name, fallback to owner_display_name if it's null/empty
            team_name_to_display = row['roster_team_name'] if row['roster_team_name'] else row['owner_display_name']

            simplified_roster_info.append({
                'roster_id': row['sleeper_roster_id'],
                'owner_id': row['owner_id'],
                'owner_display_name': row['owner_display_name'],
                'owner_avatar': row['owner_avatar'],
                'team_name': team_name_to_display, # Use the determined team name
                'player_count': len(json.loads(row['players'])) if row['players'] else 0,
                'wins': row['wins'],
                'losses': row['losses'],
                'ties': row['ties'],
                'points_for': row['points_for'] or 0.0
            })
        
        # Sorting is removed as statistical ranking is no longer the primary purpose.
        # If a specific order is desired (e.g., by owner name), it can be added here.

        print(f"DEBUG: /league/standings/local - Successfully fetched {len(simplified_roster_info)} simplified roster details for league {league_id_from_request}.")
        return jsonify({
            'success': True, 
            'league_id': league_id_from_request,
            'league_name': league_name,
            'league_season': league_season,
            'standings': simplified_roster_info # Renamed variable, but keeping key as 'standings' for now to minimize frontend breaking changes
        })

    except sqlite3.Error as e:
        print(f"ERROR: /league/standings/local - Database error for league {league_id_from_request}: {str(e)}")
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        print(f"ERROR: /league/standings/local - Unexpected error for league {league_id_from_request}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}), 500

# Sleeper user search endpoint
@app.route('/sleeper/search', methods=['GET'])
def search_sleeper_user():
    session_token = request.headers.get('Authorization')
    if not session_token:
        return jsonify({'success': False, 'error': 'No session token'}), 401
    
    try:
        # Verify session
        with get_global_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT wallet_address FROM sessions WHERE session_token = ?', (session_token,))
            session_data = cursor.fetchone()
            
            if not session_data:
                return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        # Get username from query params
        username = request.args.get('username')
        if not username:
            return jsonify({'success': False, 'error': 'No username provided'}), 400
        
        # Search for user
        user = sleeper_service.get_user(username)
        if not user:
            return jsonify({'success': False, 'error': f'User "{username}" not found'}), 404
        
        # Get user's leagues
        leagues = sleeper_service.get_user_leagues(user['user_id'])
        
        # Return user and leagues
        return jsonify({
            'success': True,
            'user': user,
            'leagues': leagues
        })
    except Exception as e:
        print(f"Error in /sleeper/search: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

# Check if wallet address needs association with Sleeper
@app.route('/auth/check_association', methods=['GET'])
def check_association():
    session_token = request.headers.get('Authorization')
    if not session_token:
        return jsonify({'success': False, 'error': 'No session token'}), 401
    
    try:
        # Verify session and get wallet address
        conn = get_global_db_connection() # Use global connection
        cursor = conn.cursor()
        cursor.execute('SELECT wallet_address FROM sessions WHERE session_token = ?', (session_token,))
        session_data = cursor.fetchone()
        
        if not session_data:
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        wallet_address = session_data['wallet_address']
        
        # Check if wallet address is already associated with a Sleeper account
        cursor.execute('SELECT sleeper_user_id FROM Users WHERE wallet_address = ?', (wallet_address,))
        user_data = cursor.fetchone()
        
        needs_association = not user_data or not user_data['sleeper_user_id']
        
        return jsonify({
            'success': True,
            'wallet_address': wallet_address,
            'needs_association': needs_association
        })
            
    except Exception as e:
        print(f"Error in /auth/check_association: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

# Complete Sleeper association
@app.route('/auth/complete_association', methods=['POST'])
def complete_sleeper_association():
    session_token = request.headers.get('Authorization')
    if not session_token:
        return jsonify({'success': False, 'error': 'No session token provided'}), 401

    try:
        print("DEBUG: /auth/complete_association called")
        conn = get_global_db_connection() # Use global connection
        cursor = conn.cursor()

        # Verify session and get wallet_address
        cursor.execute('SELECT wallet_address FROM sessions WHERE session_token = ?', (session_token,))
        session_data = cursor.fetchone()
        if not session_data:
            print("DEBUG: Invalid session token in /auth/complete_association")
            return jsonify({'success': False, 'error': 'Invalid session token'}), 401
        wallet_address = session_data['wallet_address']
        print(f"DEBUG: wallet_address: {wallet_address}")

        data = request.get_json()
        if not data or 'sleeperUsername' not in data:
            print("DEBUG: Missing sleeperUsername in /auth/complete_association")
            return jsonify({'success': False, 'error': 'Missing sleeperUsername in request body'}), 400
        
        sleeper_username = data['sleeperUsername']
        print(f"DEBUG: sleeper_username: {sleeper_username}")

        # Get Sleeper user details from Sleeper API
        sleeper_user_data = sleeper_service.get_user(sleeper_username)
        print(f"DEBUG: sleeper_user_data from service: {sleeper_user_data}")
        if not sleeper_user_data:
            print(f"DEBUG: Sleeper username '{sleeper_username}' not found by service")
            return jsonify({'success': False, 'error': f'Sleeper username "{sleeper_username}" not found'}), 404

        sleeper_user_id = sleeper_user_data.get('user_id')
        display_name = sleeper_user_data.get('display_name', sleeper_username) # Fallback to username if display_name is null
        avatar = sleeper_user_data.get('avatar')
        print(f"DEBUG: Extracted sleeper_user_id: {sleeper_user_id}, display_name: {display_name}, avatar: {avatar}")

        if not sleeper_user_id: # This also catches empty strings
            print(f"DEBUG: sleeper_user_id is null or empty after extraction for {sleeper_username}")
            return jsonify({'success': False, 'error': 'Could not retrieve user_id from Sleeper for the given username'}), 500

        # Step 1: Check if a user record already exists for this sleeper_user_id (regardless of wallet_address)
        cursor.execute('SELECT wallet_address FROM Users WHERE sleeper_user_id = ?', (sleeper_user_id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            existing_wallet = existing_user['wallet_address']
            if existing_wallet and existing_wallet != wallet_address:
                # Another wallet already owns this sleeper_user_id - this shouldn't happen in normal flow
                print(f"ERROR: sleeper_user_id {sleeper_user_id} is already associated with wallet {existing_wallet}. Cannot associate with {wallet_address}")
                return jsonify({'success': False, 'error': 'This Sleeper account is already associated with another wallet'}), 409
            elif existing_wallet == wallet_address:
                # User already has this association - just update other fields
                print(f"DEBUG: User already associated. Updating existing record for wallet_address: {wallet_address}")
                cursor.execute('''
                    UPDATE Users 
                    SET username = ?, display_name = ?, avatar = ?, updated_at = datetime('now')
                    WHERE wallet_address = ? AND sleeper_user_id = ?
                ''', (sleeper_username, display_name, avatar, wallet_address, sleeper_user_id))
                update_rowcount = cursor.rowcount
                print(f"DEBUG: UPDATE existing user for wallet_address {wallet_address} rowcount: {update_rowcount}")
            else:
                # Record exists but has NULL wallet_address (imported by SleeperService)
                # Update it to set the wallet_address
                print(f"DEBUG: Found existing user record with NULL wallet_address. Updating to set wallet_address: {wallet_address}")
                cursor.execute('''
                    UPDATE Users 
                    SET wallet_address = ?, username = ?, display_name = ?, avatar = ?, updated_at = datetime('now')
                    WHERE sleeper_user_id = ? AND wallet_address IS NULL
                ''', (wallet_address, sleeper_username, display_name, avatar, sleeper_user_id))
                update_rowcount = cursor.rowcount
                print(f"DEBUG: UPDATE existing NULL wallet user for sleeper_user_id {sleeper_user_id} rowcount: {update_rowcount}")
        else:
            # No existing record for this sleeper_user_id - create new one
            print(f"DEBUG: No existing user record found. Creating new user record for wallet_address: {wallet_address}")
            cursor.execute('''
                INSERT INTO Users (wallet_address, sleeper_user_id, username, display_name, avatar, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            ''', (wallet_address, sleeper_user_id, sleeper_username, display_name, avatar))
            update_rowcount = cursor.rowcount
            print(f"DEBUG: INSERT new user for wallet_address {wallet_address} rowcount: {update_rowcount}")

        # Verify the operation was successful
        if update_rowcount == 0:
            print(f"ERROR: Failed to create/update user record for wallet_address: {wallet_address}, sleeper_user_id: {sleeper_user_id}")
            return jsonify({'success': False, 'error': 'Failed to create/update user record'}), 500

        # The original Step 2 (cleanup) is now Step 1 (pre-emptive cleanup).

        conn.commit()
        print(f"DEBUG: conn.commit() executed for wallet_address: {wallet_address}")

        # Verify directly from DB after commit
        cursor.execute("SELECT sleeper_user_id, username, display_name FROM Users WHERE wallet_address = ?", (wallet_address,))
        updated_user_check = cursor.fetchone()
        print(f"DEBUG: DB check after commit for {wallet_address}: {dict(updated_user_check) if updated_user_check else 'No user found'}")

        # Optionally, trigger fetch_all_data here, or let the frontend do it via onAssociationSuccess callback
        # For simplicity and immediate feedback, triggering here can be good.
        print(f"DEBUG: Calling internal sleeper_service.fetch_all_data for {wallet_address}")
        fetch_result = sleeper_service.fetch_all_data(wallet_address)
        print(f"DEBUG: Internal fetch_all_data result: {fetch_result}")
        
        if fetch_result.get('success'):
            # NEW LOGIC: Set commissioner status based on Sleeper's is_owner field
            cursor.execute("SELECT sleeper_league_id FROM UserLeagueLinks WHERE wallet_address = ?", (wallet_address,))
            user_leagues = cursor.fetchall()
            for league_row in user_leagues:
                current_league_id = league_row['sleeper_league_id']
                # Get this user's sleeper_user_id
                cursor.execute("SELECT sleeper_user_id FROM users WHERE wallet_address = ?", (wallet_address,))
                user_data = cursor.fetchone()
                if not user_data or not user_data['sleeper_user_id']:
                    print(f"DEBUG: No sleeper_user_id found for wallet {wallet_address}")
                    continue
                sleeper_user_id = user_data['sleeper_user_id']
                # Get all users from Sleeper API for this league
                league_users = sleeper_service.get_league_users(current_league_id)
                if not league_users:
                    print(f"DEBUG: Could not fetch users from Sleeper API for league {current_league_id}")
                    continue
                # Find this user in the Sleeper API response
                sleeper_user = next((u for u in league_users if u.get('user_id') == sleeper_user_id), None)
                is_owner = sleeper_user.get('is_owner', False) if sleeper_user else False
                print(f"DEBUG: User {wallet_address} (sleeper_user_id: {sleeper_user_id}) is_owner in Sleeper: {is_owner}")
                cursor.execute("""
                    UPDATE UserLeagueLinks 
                    SET is_commissioner = ?, updated_at = datetime('now')
                    WHERE wallet_address = ? AND sleeper_league_id = ?
                """, (1 if is_owner else 0, wallet_address, current_league_id))
            conn.commit()
            print(f"DEBUG: conn.commit() executed for wallet_address: {wallet_address} (after successful fetch_all_data and commissioner check)")
        elif fetch_result.get('error'): # Make sure to check if 'error' key exists
            # Log this error, but the association itself was successful.
            # The client will attempt another fetch via onAssociationSuccess anyway.
            print(f"Warning: Post-association data fetch failed for {wallet_address}: {fetch_result.get('error')}")
            # Consider if a rollback is needed if fetch_all_data could leave partial data on error.
            # For now, the user association is committed, but data fetch might be incomplete.
        else:
            # Handle cases where 'success' is not true and 'error' is not present, if any.
            print(f"Warning: Post-association data fetch returned an unexpected result for {wallet_address}: {fetch_result}")

        print(f"DEBUG: /auth/complete_association successful for {wallet_address}")
        return jsonify({'success': True, 'message': 'Sleeper account associated successfully'}), 200

    except sqlite3.Error as sqle:
        print(f"SQLite error in /auth/complete_association: {str(sqle)}")
        import traceback
        traceback.print_exc()
        # conn.rollback() # Not needed as with statement handles commit/rollback on exception
        return jsonify({'success': False, 'error': f'Database error: {str(sqle)}'}), 500
    except Exception as e:
        print(f"Error in /auth/complete_association: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

# Get users in a specific league
@app.route('/sleeper/league/<league_id>/users', methods=['GET'])
def get_league_users(league_id):
    session_token = request.headers.get('Authorization')
    if not session_token:
        return jsonify({'success': False, 'error': 'No session token'}), 401
    
    try:
        # Verify session
        with get_global_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT wallet_address FROM sessions WHERE session_token = ?', (session_token,))
            session_data = cursor.fetchone()
            
            if not session_data:
                return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        # Get users from the Sleeper API
        users = sleeper_service.get_league_users(league_id)
        
        if not users:
            return jsonify({'success': False, 'error': f'No users found for league {league_id}'}), 404
        
        # Return the users
        return jsonify({
            'success': True,
            'league_id': league_id,
            'users': users
        })
        
    except Exception as e:
        print(f"Error in /sleeper/league/{league_id}/users: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

# Season settings endpoints
@app.route('/season/settings', methods=['GET'])
def get_season_settings():
    session_token = request.headers.get('Authorization')
    if not session_token:
        return jsonify({'success': False, 'error': 'No session token'}), 401
    
    try:
        # Verify session
        with get_global_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT wallet_address FROM sessions WHERE session_token = ?', (session_token,))
            session_data = cursor.fetchone()
            
            if not session_data:
                return jsonify({'success': False, 'error': 'Invalid session'}), 401
            
            # Get season settings
            cursor.execute('SELECT current_year, IsOffSeason, updated_at FROM season_curr LIMIT 1')
            season_data = cursor.fetchone()
            
            if not season_data:
                return jsonify({
                    'success': False,
                    'error': 'No season settings found'
                }), 404
            
            return jsonify({
                'success': True,
                'season': {
                    'year': season_data['current_year'],
                    'is_offseason': season_data['IsOffSeason'] == 1,
                    'updated_at': season_data['updated_at']
                }
            })
    except Exception as e:
        print(f"Error in /season/settings: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500


@app.route('/api/user/roster', methods=['GET'])
@login_required
def get_user_roster_for_league():
    """Fetches the roster_id for the authenticated user in a specific league."""
    user = get_current_user()
    # @login_required should ensure user is not None, but double check for safety
    if not user or not user.get('sleeper_user_id'):
        return jsonify({'success': False, 'error': 'User not authenticated or sleeper_user_id missing'}), 401

    sleeper_user_id = user['sleeper_user_id']
    league_id = request.args.get('league_id')

    if not league_id:
        return jsonify({'success': False, 'error': 'Missing league_id parameter'}), 400

    try:
        conn = get_global_db_connection()
        cursor = conn.cursor()

        # First, verify the user is actually part of this league via UserLeagueLinks
        # This is an important authorization check.
        cursor.execute("""
            SELECT 1 FROM UserLeagueLinks 
            WHERE wallet_address = ? AND sleeper_league_id = ?
        """, (user['wallet_address'], league_id))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'User not authorized for this league or league link does not exist.'}), 403

        # Fetch the roster_id from the rosters table
        cursor.execute("""
            SELECT sleeper_roster_id 
            FROM rosters 
            WHERE owner_id = ? AND sleeper_league_id = ?
        """, (sleeper_user_id, league_id))
        roster_data = cursor.fetchone()

        if roster_data and roster_data['sleeper_roster_id']:
            return jsonify({'success': True, 'roster_id': roster_data['sleeper_roster_id']}), 200
        else:
            # This means the user is in the league, but no roster was found for them.
            # This could be a data integrity issue or the user might not have a roster in that specific league (e.g., co-manager not primary owner listed in rosters.owner_id)
            # PLANNING.md suggests rosters.owner_id is the sleeper user ID of the team owner.
            return jsonify({'success': False, 'error': 'No roster found for this user in the specified league.'}), 404

    except sqlite3.Error as e:
        print(f"ERROR: /api/user/roster - Database error: {str(e)}")
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        print(f"ERROR: /api/user/roster - Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}), 500

def _get_player_current_year_cost(player_id: str, team_id: str, sleeper_league_id: str, current_season_year: int, db_conn: sqlite3.Connection) -> float:
    """
    Determines the current season's contract cost for a player on a specific team in a specific league.
    Uses vw_contractByYear first, then falls back to the contracts table for Year 1 costs.
    """
    cursor = db_conn.cursor()
    cost = 0.0

    # Attempt 1: Check vw_contractByYear
    try:
        cursor.execute("""
            SELECT cost_for_season
            FROM vw_contractByYear
            WHERE player_id = ? 
              AND team_id = ? 
              AND sleeper_league_id = ? 
              AND (contract_start_season + year_number_in_contract - 1) = ?
        """, (player_id, team_id, sleeper_league_id, current_season_year))
        row = cursor.fetchone()
        if row and row['cost_for_season'] is not None:
            cost = float(row['cost_for_season'])
            return cost
    except Exception as e:
        # Log this error, as an issue with the view or query would be problematic
        app.logger.error(f"Error querying vw_contractByYear for player {player_id}, team {team_id}, year {current_season_year}: {e}")

    # Attempt 2: Check contracts table directly (primarily for Year 1 costs if not caught by view, or for 1-year contracts)
    # This is important for players newly drafted and assigned a 1-year default contract by SleeperService.
    try:
        cursor.execute("""
            SELECT draft_amount
            FROM contracts
            WHERE player_id = ?
              AND team_id = ?
              AND sleeper_league_id = ? 
              AND contract_year = ? 
              AND is_active = 1
        """, (player_id, team_id, sleeper_league_id, current_season_year))
        row = cursor.fetchone()
        if row and row['draft_amount'] is not None:
            cost = float(row['draft_amount'])
            return cost
    except Exception as e:
        app.logger.error(f"Error querying contracts table for player {player_id}, team {team_id}, year {current_season_year}: {e}")
        
    return cost # Defaults to 0.0 if no cost found

@app.route('/team/<team_id>', methods=['GET'])
@login_required
def get_team_details(team_id):
    """Fetches detailed information for a specific team (roster).
       Expects league_id as a query parameter.
    """
    current_user_details = get_current_user()
    if not current_user_details:
        return jsonify({'success': False, 'error': 'User not authenticated'}), 401

    league_id_from_query = request.args.get('league_id')
    if not league_id_from_query:
        return jsonify({'success': False, 'error': 'Missing league_id query parameter'}), 400

    # team_id is the sleeper_roster_id
    try:
        conn = get_global_db_connection()
        cursor = conn.cursor()

        # 1. Fetch basic roster details (including owner_id and league_id)
        cursor.execute("""
            SELECT r.sleeper_roster_id, r.sleeper_league_id, r.owner_id, r.players as player_ids_json, 
                   r.reserve as reserve_ids_json, 
                   r.team_name as roster_db_team_name, -- Select the new team_name column
                   COALESCE(u.display_name, u.username) as manager_name, u.username as sleeper_username
            FROM rosters r
            LEFT JOIN Users u ON r.owner_id = u.sleeper_user_id
            WHERE r.sleeper_roster_id = ? AND r.sleeper_league_id = ?
        """, (team_id, league_id_from_query))
        roster_info = cursor.fetchone()

        if not roster_info:
            return jsonify({'success': False, 'error': 'Team (roster) not found'}), 404

        # Fetch League Name for league_context
        cursor.execute("SELECT name FROM LeagueMetadata WHERE sleeper_league_id = ?", (roster_info['sleeper_league_id'],))
        league_metadata_row = cursor.fetchone()
        league_name_for_context = league_metadata_row['name'] if league_metadata_row else 'Unknown League'

        # Verify that the current user is part of the league this team belongs to.
        cursor.execute("""SELECT 1 FROM UserLeagueLinks WHERE wallet_address = ? AND sleeper_league_id = ?""",
                       (current_user_details['wallet_address'], roster_info['sleeper_league_id']))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'User not authorized to view this team (not part of the league)'}), 403

        # Prioritize the team_name from the rosters table. Fallback to manager's name.
        team_name_to_display = roster_info['roster_db_team_name'] if roster_info['roster_db_team_name'] else roster_info['manager_name']

        # <<< CORRECTED LOGIC FOR all_player_ids_on_roster >>>
        main_player_ids = json.loads(roster_info['player_ids_json']) if roster_info['player_ids_json'] else []
        reserve_player_ids = json.loads(roster_info['reserve_ids_json']) if roster_info['reserve_ids_json'] else []
        # MODIFICATION: Use only main_player_ids as per user request for this view
        all_player_ids_on_roster = main_player_ids
        app.logger.info(f"DEBUG_TEAM_DETAILS: Using main_player_ids for all_player_ids_on_roster: {all_player_ids_on_roster}")

        current_season_data = get_current_season()
        current_processing_year = int(current_season_data['current_year']) if current_season_data and current_season_data.get('current_year') else 0
        is_offseason = current_season_data['is_offseason']
        
        # print(f"DEBUG_TEAM_DETAILS_FULL: current_season_data = {current_season_data}")
        # print(f"DEBUG_TEAM_DETAILS_FULL: current_processing_year = {current_processing_year}")
        # print(f"DEBUG_TEAM_DETAILS_FULL: is_offseason = {is_offseason}")
        # print(f"DEBUG_TEAM_DETAILS_FULL: Roster's league_id = {roster_info['sleeper_league_id']}")

        # Determine if the contract setting period is active for this league
        is_contract_setting_period_active = False
        auction_acquisitions = {} 
        
        # print(f"DEBUG_TEAM_DETAILS: Initial is_contract_setting_period_active: {is_contract_setting_period_active}")
        # print(f"DEBUG_TEAM_DETAILS: Initial auction_acquisitions: {auction_acquisitions}")

        if is_offseason and current_processing_year > 0:
            cursor.execute("""
                SELECT data 
                FROM drafts 
                WHERE league_id = ? AND season = ? AND status = ? 
                ORDER BY start_time DESC LIMIT 1
            """, (roster_info['sleeper_league_id'], str(current_processing_year), "complete"))
            draft_record = cursor.fetchone()
            # print(f"DEBUG_TEAM_DETAILS: Draft record for league {roster_info['sleeper_league_id']} season {current_processing_year}: {draft_record}")
            
            if draft_record and draft_record['data']:
                try:
                    draft_picks_data = json.loads(draft_record['data'])
                    # print(f"DEBUG_TEAM_DETAILS: Parsed draft_picks_data: {draft_picks_data}")
                    if isinstance(draft_picks_data, list):
                        is_contract_setting_period_active = True 
                        for pick in draft_picks_data:
                            player_id = pick.get('player_id')
                            metadata = pick.get('metadata', {})
                            amount_str = metadata.get('amount')
                            # print(f"DEBUG_TEAM_DETAILS: Draft pick processing - player_id: {player_id}, amount_str: {amount_str}")
                            if player_id and amount_str is not None:
                                try:
                                    auction_acquisitions[str(player_id)] = int(amount_str)
                                except ValueError:
                                    app.logger.warning(f"DEBUG_TEAM_DETAILS_FULL: Warning: Could not convert auction amount '{amount_str}' to int for player {player_id}")
                    else:
                        # print(f"DEBUG_TEAM_DETAILS: draft_picks_data is not a list. Type: {type(draft_picks_data)}")
                        pass # draft_picks_data is not a list, no action needed here
                except json.JSONDecodeError:
                    app.logger.warning(f"DEBUG_TEAM_DETAILS_FULL: Warning: Could not parse draft data JSON for league {roster_info['sleeper_league_id']} season {current_processing_year}")
        
        # print(f"DEBUG_TEAM_DETAILS: Final is_contract_setting_period_active: {is_contract_setting_period_active}")
        # print(f"DEBUG_TEAM_DETAILS: Final auction_acquisitions: {auction_acquisitions}")

        # <<< START NEW LOGIC FOR LEAGUE SPENDING RANKS >>>
        team_position_spending_ranks = {}
        current_league_id_for_ranks = roster_info['sleeper_league_id']

        if current_league_id_for_ranks and current_processing_year > 0:
            try:
                # 1. Get all rosters for the current league
                cursor.execute("SELECT sleeper_roster_id, players FROM rosters WHERE sleeper_league_id = ?", (current_league_id_for_ranks,))
                all_league_rosters_raw = cursor.fetchall()

                if not all_league_rosters_raw:
                    app.logger.warning(f"No rosters found for league {current_league_id_for_ranks} when calculating spending ranks.")
                else:
                    # Collect all unique player IDs from all rosters in the league first
                    all_player_ids_in_league_set = set()
                    for r_raw_temp in all_league_rosters_raw:
                        p_ids_temp = json.loads(r_raw_temp['players']) if r_raw_temp['players'] else []
                        for p_id_item in p_ids_temp:
                            all_player_ids_in_league_set.add(p_id_item)
                    
                    player_positions_map = {}
                    if all_player_ids_in_league_set:
                        placeholders_for_player_pos = ', '.join('?' * len(all_player_ids_in_league_set))
                        cursor.execute(f"SELECT sleeper_player_id, position FROM players WHERE sleeper_player_id IN ({placeholders_for_player_pos})", tuple(all_player_ids_in_league_set))
                        for row_pos_map in cursor.fetchall():
                            player_positions_map[row_pos_map['sleeper_player_id']] = row_pos_map['position']

                    league_spending_by_pos_for_ranking = {} 
                    
                    for roster_raw_in_league in all_league_rosters_raw:
                        current_roster_id_in_league = roster_raw_in_league['sleeper_roster_id']
                        player_ids_json_in_league = roster_raw_in_league['players']
                        player_ids_in_league = json.loads(player_ids_json_in_league) if player_ids_json_in_league else []
                        
                        team_spending_this_iteration = {}

                        for p_id_str in player_ids_in_league:
                            position = player_positions_map.get(p_id_str)
                            
                            if not position:
                                app.logger.debug(f"Skipping player {p_id_str} on roster {current_roster_id_in_league}: no position found in pre-fetched map.")
                                continue 
                            
                            if position not in team_spending_this_iteration:
                                 team_spending_this_iteration[position] = 0.0

                            cost = _get_player_current_year_cost(p_id_str, current_roster_id_in_league, current_league_id_for_ranks, current_processing_year, conn)
                            if cost > 0:
                                team_spending_this_iteration[position] += cost
                        
                        for pos, total_amount in team_spending_this_iteration.items():
                            if pos not in league_spending_by_pos_for_ranking:
                                league_spending_by_pos_for_ranking[pos] = []
                            league_spending_by_pos_for_ranking[pos].append({'team_id': current_roster_id_in_league, 'amount': total_amount})

                    # 3. Rank teams within each position
                    for position, spending_list_for_pos in league_spending_by_pos_for_ranking.items():
                        sorted_spending = sorted(spending_list_for_pos, key=lambda x: x['amount'], reverse=True)
                        
                        rank_for_viewed_team = -1 
                        # Find the rank of the team whose page is being viewed (team_id)
                        for i, team_spend_info in enumerate(sorted_spending):
                            if team_spend_info['team_id'] == team_id: # team_id is the sleeper_roster_id of the team page being viewed
                                rank_for_viewed_team = i + 1
                                break
                        
                        # Only include rank if the viewed team has spending (and thus a rank) in this position
                        if rank_for_viewed_team != -1:
                            team_position_spending_ranks[position] = {
                                'rank': rank_for_viewed_team,
                                'total_teams': len(sorted_spending) 
                            }
            except Exception as e:
                app.logger.error(f"Error calculating league spending ranks for team {team_id}, league {current_league_id_for_ranks}: {e}")
                # team_position_spending_ranks will remain empty or partially filled; frontend should handle this
        # <<< END NEW LOGIC FOR LEAGUE SPENDING RANKS >>>

        # Calculate Future Yearly Total Ranks
        future_yearly_total_ranks = {}
        if current_league_id_for_ranks and current_processing_year > 0:
            try:
                # Get all rosters for the current league (re-fetch or reuse if already fetched and suitable)
                cursor.execute("SELECT sleeper_roster_id FROM rosters WHERE sleeper_league_id = ?", (current_league_id_for_ranks,))
                all_roster_ids_in_league = [row['sleeper_roster_id'] for row in cursor.fetchall()]

                if all_roster_ids_in_league:
                    seasons_to_rank = [current_processing_year + i for i in range(1, 4)] # For next 3 future years

                    # Dictionary to store total spending for each team for each future year
                    # { year1: [{\'team_id\': X, \'total_cost\': Y}, ...], year2: [...] }
                    league_spending_by_future_year = {year: [] for year in seasons_to_rank}

                    for r_id_in_league in all_roster_ids_in_league:
                        for year_to_rank in seasons_to_rank:
                            # Sum costs for this team for this specific future year from vw_contractByYear
                            cursor.execute("""
                                SELECT SUM(v.cost_for_season) as total_future_cost
                                FROM vw_contractByYear v
                                JOIN contracts c ON v.original_contract_rowid = c.rowid 
                                WHERE v.team_id = ? AND v.sleeper_league_id = ? AND v.contract_start_season + v.year_number_in_contract -1 = ? AND c.is_active = 1
                            """, (r_id_in_league, current_league_id_for_ranks, year_to_rank))
                            result = cursor.fetchone()
                            total_cost_for_year = result['total_future_cost'] if result and result['total_future_cost'] is not None else 0.0
                            league_spending_by_future_year[year_to_rank].append({'team_id': r_id_in_league, 'total_cost': total_cost_for_year})
                    
                    # Rank teams for each future year based on their total spending
                    for year_val, spending_data_for_year in league_spending_by_future_year.items():
                        sorted_teams_for_year = sorted(spending_data_for_year, key=lambda x: x['total_cost'], reverse=True)
                        
                        rank_for_viewed_team_future = -1
                        # Find the rank of the team whose page is being viewed (team_id)
                        for i, team_spend_future_info in enumerate(sorted_teams_for_year):
                            if team_spend_future_info['team_id'] == team_id:
                                rank_for_viewed_team_future = i + 1
                                break
                        
                        # Store the rank if the viewed team has spending (and thus a rank) for this future year
                        if rank_for_viewed_team_future != -1:
                             future_yearly_total_ranks[str(year_val)] = {
                                 'rank': rank_for_viewed_team_future,
                                 'total_teams': len(sorted_teams_for_year)
                             }

            except Exception as e:
                 app.logger.error(f"Error calculating future yearly total ranks for team {team_id}, league {current_league_id_for_ranks}: {e}")

        # Initialize grouped_players once, correctly, before it might be used or populated.
        grouped_players = {pos: [] for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DEF', 'Unknown']}

        # Initialize team_yearly_totals. This should be done regardless of player count initially.
        team_yearly_totals = {year: 0.0 for year in range(current_processing_year, current_processing_year + 4)}

        # The if block that previously redefined all_player_ids_on_roster is now removed.
        # We proceed directly to processing if all_player_ids_on_roster (which now correctly includes reserve) has players.
        
        # player_details = [] # This seems unused, consider removing if truly not needed later.
        if all_player_ids_on_roster: # This check now uses the comprehensive list of players
            placeholders = ', '.join('?' * len(all_player_ids_on_roster))
            # Query players table for names, positions, teams
            app.logger.info(f"DEBUG_TEAM_DETAILS: Querying players table for IDs: {all_player_ids_on_roster}")
            cursor.execute(f"""
                SELECT p.sleeper_player_id, p.name, p.position, p.team
                FROM players p
                WHERE p.sleeper_player_id IN ({placeholders})
            """, tuple(all_player_ids_on_roster))
            team_players_details_list = cursor.fetchall()
            team_players_details = {row['sleeper_player_id']: dict(row) for row in team_players_details_list}
            app.logger.info(f"DEBUG_TEAM_DETAILS: Fetched team_players_details map: {team_players_details}")

            # Prepare a dictionary to hold contract details for each player for faster lookup
            contracts_info = {}
            if all_player_ids_on_roster: # Ensure there are players before querying contracts
                cursor.execute(f"""
                        SELECT player_id, draft_amount, contract_year, duration, is_active, rowid as contract_rowid
                        FROM contracts 
                        WHERE player_id IN ({placeholders}) 
                        AND team_id = ? 
                        AND sleeper_league_id = ?
                """, tuple(all_player_ids_on_roster) + (team_id, roster_info['sleeper_league_id']))
                
                for contract_row in cursor.fetchall():
                        contracts_info[contract_row['player_id']] = dict(contract_row)
            
            # DO NOT RE-INITIALIZE grouped_players here. It's done above.
            # grouped_players = {'QB': [], 'RB': [], 'WR': [], 'TE': [], 'K': [], 'DEF': [], 'Unknown': []} 
            
            # team_yearly_totals is already initialized before this block based on players or lack thereof.
            # However, it's populated inside the loop if players exist and have contracts.
            # Let's ensure it's initialized if not already done in the 'else' for no players.
            if not team_yearly_totals: # Should have been caught by the else, but as a safeguard
                 team_yearly_totals = {year: 0.0 for year in range(current_processing_year, current_processing_year + 4)}

            for p_id in all_player_ids_on_roster: # Iterate in a defined order if necessary, or use original list order
                p_data = team_players_details.get(p_id)
                if not p_data:
                    app.logger.warning(f"DEBUG_TEAM_DETAILS_LOOP: Player data for ID {p_id} not found in team_players_details map. SKIPPING THIS PLAYER.")
                    continue

                player_contract_info = contracts_info.get(p_id)
                app.logger.info(f"DEBUG_TEAM_DETAILS_LOOP Player ID: {p_id} ({p_data.get('name', 'N/A')})")
                app.logger.info(f"  Raw player_contract_info from DB: {player_contract_info}")

                # Default values
                draft_amount_for_calc = 0
                contract_duration_for_calc = 0
                contract_start_year_for_calc = 0
                is_active_for_calc = False
                contract_status = "Free Agent" # Default status
                years_remaining_display = "N/A"
                projected_costs = [] # Default empty list

                if player_contract_info:
                    draft_amount_for_calc = player_contract_info.get('draft_amount', 0)
                    # Ensure duration and contract_year are treated as int, defaulting to 0 if None/missing
                    db_duration = player_contract_info.get('duration')
                    contract_duration_for_calc = int(db_duration) if db_duration is not None else 0
                    
                    db_contract_year = player_contract_info.get('contract_year')
                    contract_start_year_for_calc = int(db_contract_year) if db_contract_year is not None else 0
                    
                    is_active_for_calc = bool(player_contract_info.get('is_active', False))
                    app.logger.info(f"  Derived from contract_info: is_active_for_calc={is_active_for_calc}, duration_for_calc={contract_duration_for_calc}, start_year_for_calc={contract_start_year_for_calc}, draft_amount_for_calc={draft_amount_for_calc}")


                    if is_active_for_calc:
                        contract_status = "Active Contract"
                        
                        # CRITICAL: Ensure contract_duration_for_calc and contract_start_year_for_calc are positive for calculations
                        if contract_duration_for_calc > 0 and contract_start_year_for_calc > 0:
                            contract_end_year = contract_start_year_for_calc + contract_duration_for_calc - 1
                            years_left = contract_end_year - current_processing_year + 1
                            
                            if years_left <= 0: 
                                years_remaining_display = "Expires " + str(contract_end_year) if contract_end_year >= current_processing_year else "Expired"
                            else: 
                                years_remaining_display = str(years_left)
                            
                            # Also ensure draft_amount is floatable for get_escalated_contract_costs
                            current_draft_amount = float(draft_amount_for_calc if draft_amount_for_calc is not None else 0.0)

                            projected_costs = get_escalated_contract_costs(
                                draft_amount=current_draft_amount, 
                                duration=int(contract_duration_for_calc), 
                                contract_start_year=int(contract_start_year_for_calc)
                            )
                            app.logger.info(f"  Player {p_id} calculated projected_costs: {projected_costs}")
                            
                            for cost_info in projected_costs:
                                cost_year = cost_info['year']
                                cost_value = cost_info['cost']
                                if current_processing_year <= cost_year < current_processing_year + 4:
                                    team_yearly_totals[cost_year] += cost_value
                        else:
                            app.logger.warning(f"  Player {p_id} has active contract but duration ({contract_duration_for_calc}) or start_year ({contract_start_year_for_calc}) is invalid (zero or None). Costs/Years not calculated.")
                            years_remaining_display = "Error" # Indicate data issue for frontend
                            projected_costs = [] # Ensure it's empty
                    else: 
                        contract_status = "Inactive Contract" # Contract exists but is_active = 0
                        years_remaining_display = "N/A" # Inactive contracts don't have remaining years in this context
                        projected_costs = []
                else: # No player_contract_info at all
                    app.logger.info(f"  No player_contract_info found for player {p_id}. Defaulting to Free Agent status.")
                    # contract_status remains "Free Agent", years_remaining_display "N/A", projected_costs empty

                app.logger.info(f"  Before auction override: status='{contract_status}', yrs_rem='{years_remaining_display}', projected_costs_count={len(projected_costs)}")
                
                # Override status for auction acquisitions during contract setting period
                is_auction_acquisition = p_id in auction_acquisitions
                # Refined logic: Only set to "Pending Contract Setting" if it's an auction acquisition,
                # contract setting period is active, AND (no contract exists OR the existing one is specifically the 1-year default that needs setting)
                # A player with an already set multi-year contract (even if is_active=0 briefly before season start) should not revert to pending.
                # The key is often that a 1-year, $X contract is created by sleeper_service for new draftees.
                
                # If it's an auction acquisition, and the period is active...
                if is_auction_acquisition and is_contract_setting_period_active:
                    # Check if the existing contract (if any) looks like the default 1-year placeholder
                    # OR if no contract exists yet for this player on this team for this year.
                    is_default_placeholder = False
                    if player_contract_info:
                        # A common placeholder is duration=1 and contract_year = current_processing_year
                        if contract_duration_for_calc == 1 and contract_start_year_for_calc == current_processing_year:
                           is_default_placeholder = True 
                    
                    if not player_contract_info or is_default_placeholder:
                        contract_status = "Pending Contract Setting"
                        # Only use auction amount if player has an active contract
                        if player_contract_info and is_active_for_calc:
                            draft_amount_for_calc = auction_acquisitions.get(p_id, 0)
                        else:
                            draft_amount_for_calc = 0  # Free agents show $0 regardless of auction history
                        years_remaining_display = "Set Duration" 
                        projected_costs = [] # Clear any prior projected costs
                        app.logger.info(f"  Player {p_id} is an auction acquisition in setting period. Status OVERRIDDEN to 'Pending Contract Setting'. Placeholder contract was: {is_default_placeholder}")
                    # else:
                        # It's an auction acquisition in setting period, but already has a non-placeholder contract (e.g., user set it, then page reloaded)
                        # In this case, we want to keep showing the set contract details but still allow edits.
                        # The contract_status will be "Active Contract" (if is_active_for_calc was true)
                        # The frontend handles editability based on 'Pending Contract Setting' OR (is_contract_setting_period_active AND is_auction_acquisition)
                        # So, the main loop's 'Active Contract' status is fine, frontend can still show dropdowns.
                        # We might need to explicitly set 'years_remaining_display' to 'Set Duration' if we want the dropdown visible.
                        # For now, let existing calculated years_remaining_display and projected_costs stand if a contract has been set.
                        # The key is the frontend check: player.contract_status === 'Pending Contract Setting' || (teamData.is_contract_setting_period_active && teamData.auction_acquisitions_for_team && teamData.auction_acquisitions_for_team[player.id] !== undefined)

                # Ensure free agents always show $0 regardless of auction history
                if not player_contract_info:
                    draft_amount_for_calc = 0
                    contract_status = "Free Agent"

                app.logger.info(f"  FINAL for player {p_id} ({p_data.get('name', 'N/A')}):")
                app.logger.info(f"    contract_status: '{contract_status}'")
                app.logger.info(f"    years_remaining_display: '{years_remaining_display}'")
                app.logger.info(f"    draft_amount_for_calc: {draft_amount_for_calc}")
                app.logger.info(f"    projected_costs: {projected_costs}")
                app.logger.info(f"    is_on_reserve: {p_id in reserve_player_ids}")
                app.logger.info(f"    contract_rowid: {player_contract_info.get('contract_rowid') if player_contract_info else None}")
                app.logger.info(f"    contract_duration_db: {int(contract_duration_for_calc) if player_contract_info and contract_duration_for_calc else None}")
                app.logger.info(f"    contract_start_year_db: {int(contract_start_year_for_calc) if player_contract_info and contract_start_year_for_calc else None}")

                # MODIFICATION for UI: If contract setting period is active and it's an auction acquisition,
                # ensure status is 'Pending Contract Setting' for UI editability,
                # and years_remaining is 'Set Duration'. Projected costs should still reflect the saved value.
                if is_contract_setting_period_active and is_auction_acquisition:
                    contract_status_for_frontend = "Pending Contract Setting"
                    years_remaining_display_for_frontend = "Set Duration"
                    # The draft_amount_for_calc and projected_costs should reflect the current DB state for information,
                    # but the status and years_remaining text will control editability.
                    app.logger.info(f"  UI OVERRIDE for auction player {p_id}: contract_status to 'Pending Contract Setting', years_remaining_display to 'Set Duration'")
                else:
                    contract_status_for_frontend = contract_status
                    years_remaining_display_for_frontend = years_remaining_display

                player_data_for_frontend = {
                    'id': p_id,
                    'name': p_data.get('name', 'N/A'),
                    'position': p_data.get('position', 'N/A'),
                    'team_nfl': p_data.get('team', 'N/A'),
                    'draft_amount': draft_amount_for_calc, 
                    'contract_status': contract_status_for_frontend, # Use the potentially overridden status for UI
                    'years_remaining': years_remaining_display_for_frontend, # Use the potentially overridden display for UI
                    'projected_costs': projected_costs, # Always show actual projected costs based on DB
                    'is_on_reserve': p_id in reserve_player_ids,
                    'contract_rowid': player_contract_info.get('contract_rowid') if player_contract_info else None,
                    'contract_duration_db': int(contract_duration_for_calc) if player_contract_info and contract_duration_for_calc else None,
                    'contract_start_year_db': int(contract_start_year_for_calc) if player_contract_info and contract_start_year_for_calc else None,
                }
                
                position_group = p_data.get('position', 'Unknown')
                if position_group not in grouped_players:
                    position_group = 'Unknown' # Fallback for unexpected positions
                grouped_players[position_group].append(player_data_for_frontend)

        # Sort players within each position group by draft_amount (descending) or name (ascending)
        for position in grouped_players:
            grouped_players[position].sort(key=lambda x: (-x.get('draft_amount', 0), x.get('name', '')))

        # print(f"DEBUG_TEAM_DETAILS_FULL: Final team_position_spending_ranks: {team_position_spending_ranks}")
        # print(f"DEBUG_TEAM_DETAILS_FULL: Final future_yearly_total_ranks: {future_yearly_total_ranks}")

        # Calculate team_yearly_penalty_totals
        team_yearly_penalty_totals = {}
        try:
            # Get all contract_ids for the current team and league that are NOT active
            # (penalties are typically associated with inactive/dropped contracts)
            # However, penalties are directly linked to contracts.id (rowid), and penalties.contract_id points to contracts.rowid
            # We need to sum penalties for this team based on contracts associated with this team.
            # The `penalties` table itself doesn't directly link to team_id, but `contracts` does.
            # So, we join penalties with contracts where contracts.team_id matches.
            cursor.execute("""
                SELECT p.penalty_year, SUM(p.penalty_amount) as total_penalty_for_year
                FROM penalties p
                JOIN contracts c ON p.contract_id = c.rowid
                WHERE c.team_id = ? AND c.sleeper_league_id = ?
                GROUP BY p.penalty_year
            """, (team_id, roster_info['sleeper_league_id']))
            
            penalty_rows = cursor.fetchall()
            for row in penalty_rows:
                team_yearly_penalty_totals[str(row['penalty_year'])] = row['total_penalty_for_year']
            app.logger.info(f"DEBUG_TEAM_DETAILS: Calculated team_yearly_penalty_totals: {team_yearly_penalty_totals}")

        except Exception as e:
            app.logger.error(f"Error calculating team_yearly_penalty_totals for team {team_id}, league {roster_info['sleeper_league_id']}: {e}")
            # Initialize to empty if error, so frontend doesn't break
            team_yearly_penalty_totals = {}


        return jsonify({
            'success': True,
            'team_id': team_id,
            'team_name': team_name_to_display, # Use the determined team name
            'manager_name': roster_info['manager_name'],
            'sleeper_username': roster_info['sleeper_username'],
            'league_id': roster_info['sleeper_league_id'],
            'league_name': league_name_for_context,
            'players_by_position': grouped_players,
            'is_contract_setting_period_active': is_contract_setting_period_active,
            'is_offseason': is_offseason,  # Added this line
            'current_processing_year': current_processing_year,
            'auction_acquisitions_for_team': {p:a for p,a in auction_acquisitions.items() if p in all_player_ids_on_roster}, # Only those on this team
            'team_yearly_totals': team_yearly_totals,
            'team_yearly_penalty_totals': team_yearly_penalty_totals, # Added this line
            'team_position_spending_ranks': team_position_spending_ranks,
            'future_yearly_total_ranks': future_yearly_total_ranks

        })

    except Exception as e:
        app.logger.error(f"Error fetching details for team {team_id}, league {league_id_from_query}: {e}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/api/team/<team_id>/contracts/durations', methods=['POST'])
@login_required
def update_contract_durations(team_id):
    """Updates the contract durations for specified players on a team."""
    current_user_details = get_current_user()
    if not current_user_details:
        # Should be caught by @login_required, but as a safeguard
        return jsonify({'success': False, 'error': 'User not authenticated'}), 401

    data = request.get_json()
    if not data or 'player_durations' not in data or 'league_id' not in data:
        return jsonify({'success': False, 'error': 'Missing player_durations or league_id in request payload'}), 400

    player_durations_map = data.get('player_durations', {})
    request_league_id = data.get('league_id')

    if not isinstance(player_durations_map, dict):
        return jsonify({'success': False, 'error': 'player_durations must be an object'}), 400
    
    conn = None # Initialize conn to None for broader scope
    try:
        conn = get_global_db_connection()
        cursor = conn.cursor()

        # 1. Validate team_id and user authorization for this team's league
        cursor.execute("""SELECT sleeper_league_id, owner_id FROM rosters WHERE sleeper_roster_id = ? AND sleeper_league_id = ?""", (team_id, request_league_id))
        roster_info = cursor.fetchone()
        if not roster_info:
            return jsonify({'success': False, 'error': 'Team (roster) not found for the given team_id and league_id in payload'}), 404
        
        db_league_id = roster_info['sleeper_league_id']
        team_owner_sleeper_id = roster_info['owner_id'] 

        # Authorization Check: Ensure current user owns the team they are trying to update contracts for
        if team_owner_sleeper_id != current_user_details.get('sleeper_user_id'):
            return jsonify({'success': False, 'error': 'User not authorized to update contracts for this team.'}), 403

        if db_league_id != request_league_id:
            return jsonify({'success': False, 'error': 'Mismatched league_id in payload and team record'}), 400

        cursor.execute("""SELECT 1 FROM UserLeagueLinks WHERE wallet_address = ? AND sleeper_league_id = ?""",
                       (current_user_details['wallet_address'], db_league_id))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'User not authorized for this league'}), 403
        
        # 2. Check if contract setting period is active
        current_season_data = get_current_season()
        current_processing_year = int(current_season_data['current_year']) if current_season_data and current_season_data.get('current_year') else 0
        is_offseason = current_season_data['is_offseason']
        
        is_contract_setting_period_active = False
        auction_acquisitions = {} # {player_id: auction_price}

        if is_offseason and current_processing_year > 0:
            cursor.execute("""
                SELECT data 
                FROM drafts 
                WHERE league_id = ? AND season = ? AND status = ? 
                ORDER BY start_time DESC LIMIT 1
            """, (db_league_id, str(current_processing_year), "complete"))
            draft_record = cursor.fetchone()
            if draft_record and draft_record['data']:
                try:
                    draft_picks_data = json.loads(draft_record['data'])
                    if isinstance(draft_picks_data, list):
                        is_contract_setting_period_active = True 
                        for pick in draft_picks_data:
                            player_id = pick.get('player_id')
                            metadata = pick.get('metadata', {})
                            amount_str = metadata.get('amount')
                            if player_id and amount_str is not None:
                                try: # Ensure conversion for auction_acquisitions values
                                    auction_acquisitions[str(player_id)] = int(amount_str)
                                except ValueError:
                                    pass # Log or handle if needed
                except json.JSONDecodeError:
                    print(f"Warning: Could not parse draft data JSON for league {db_league_id} season {current_processing_year} in update_contract_durations.")
        
        if not is_contract_setting_period_active:
            return jsonify({'success': False, 'error': 'Contract setting period is not active for this league/season.'}), 403

        # 3. Process updates
        updated_count = 0
        errors = []
        warnings = [] # New: To store messages for skipped players

        for player_id_str, duration in player_durations_map.items():
            if not (isinstance(duration, int) and 1 <= duration <= 4):
                errors.append(f"Invalid duration for player {player_id_str}: {duration}. Must be 1-4.")
                continue

            if str(player_id_str) not in auction_acquisitions:
                warnings.append(f"Player {player_id_str} was not part of the recent auction acquisitions or is not eligible for duration update at this time. Skipped.")
                continue

            cursor.execute("""SELECT duration FROM contracts 
                              WHERE player_id = ? AND team_id = ? AND contract_year = ? AND sleeper_league_id = ?""",
                           (player_id_str, team_id, current_processing_year, db_league_id))
            contract_check = cursor.fetchone()

            if not contract_check:
                warnings.append(f"No existing default contract found for player {player_id_str} on team {team_id} for season {current_processing_year} to update. Skipped.")
                continue
            
            # Perform the update for this eligible player
            cursor.execute("""UPDATE contracts SET duration = ?, updated_at = datetime('now')
                              WHERE player_id = ? AND team_id = ? AND contract_year = ? AND sleeper_league_id = ?""",
                           (duration, player_id_str, team_id, current_processing_year, db_league_id))
            if cursor.rowcount > 0:
                updated_count += 1
            else:
                # This would be an unexpected failure if previous checks passed
                errors.append(f"Failed to update duration for player {player_id_str} on team {team_id} for season {current_processing_year}. No row affected despite passing checks.")

        if errors: # If there were any critical errors during individual updates
            conn.rollback() 
            return jsonify({'success': False, 'error': "; ".join(errors), 'warnings': warnings}), 400
        
        conn.commit()
        response_message = f'{updated_count} contract durations updated successfully.'
        if warnings:
            response_message += " Some players were skipped."
        return jsonify({'success': True, 'message': response_message, 'warnings': warnings}), 200

    except sqlite3.Error as e:
        if conn: conn.rollback()
        print(f"ERROR: /api/team/{team_id}/contracts/durations - Database error: {str(e)}")
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR: /api/team/{team_id}/contracts/durations - Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/league/<league_id>/fees', methods=['GET'])
@login_required
def get_league_fees(league_id):
    """Fetches league fee information and payment status for all rosters in a league for a given season."""
    user = get_current_user()
    wallet_address = user['wallet_address']
    
    requested_season_year_str = request.args.get('season_year')
    current_season_details = get_current_season()
    target_season_year = None

    if requested_season_year_str:
        try:
            year_val = int(requested_season_year_str)
            target_season_year = str(year_val) 
        except ValueError:
            app.logger.warning(f"Invalid season_year format received: {requested_season_year_str}")
            return jsonify({'success': False, 'error': 'Invalid season_year format. Must be a number.'}), 400
    else:
        target_season_year = str(current_season_details['current_year'])

    app.logger.info(f"Fetching fees for league {league_id}, wallet {wallet_address}, target_season_year: {target_season_year}")

    try:
        conn = get_global_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM UserLeagueLinks WHERE wallet_address = ? AND sleeper_league_id = ?", 
                       (wallet_address, league_id))
        if not cursor.fetchone():
            app.logger.warning(f"User {wallet_address} tried to access fees for league {league_id} they are not part of.")
            return jsonify({'success': False, 'error': 'User not authorized for this league or league link does not exist.'}), 403

        cursor.execute("SELECT name FROM LeagueMetadata WHERE sleeper_league_id = ?", (league_id,))
        league_meta = cursor.fetchone()
        if not league_meta:
            app.logger.error(f"LeagueMetadata not found for {league_id} in get_league_fees.")
            return jsonify({'success': False, 'error': f'League metadata not found for ID {league_id}.'}), 404
        league_name = league_meta['name']

        cursor.execute("SELECT fee_amount, fee_currency, notes FROM LeagueFees WHERE sleeper_league_id = ? AND season_year = ?", 
                       (league_id, target_season_year))
        fee_settings_row = cursor.fetchone()
        league_fee_details = {
            'fee_amount': fee_settings_row['fee_amount'] if fee_settings_row else None,
            'fee_currency': fee_settings_row['fee_currency'] if fee_settings_row else 'USD',
            'notes': fee_settings_row['notes'] if fee_settings_row else ''
        }

        # Fetch all rosters for the league, then join with Users and UserLeagueLinks
        # rosters.owner_id is sleeper_user_id
        # Users.wallet_address links Users to UserLeagueLinks
        query = """
            SELECT 
                r.sleeper_roster_id,
                r.team_name AS roster_team_name,
                r.owner_id AS sleeper_owner_id,
                u.wallet_address,
                COALESCE(u.display_name, u.username) AS manager_display_name,
                u.avatar,
                ull.is_commissioner,
                ull.fee_paid_amount,
                ull.fee_payment_status,
                -- Subquery to get the most recent transaction_id for this user/league/season
                (SELECT lp.transaction_id
                 FROM LeaguePayments lp
                 WHERE lp.sleeper_league_id = r.sleeper_league_id
                   AND lp.wallet_address = u.wallet_address
                   AND lp.season_year = ? -- Filter by target_season_year
                 ORDER BY lp.updated_at DESC, lp.created_at DESC -- Get the most recent
                 LIMIT 1
                ) AS last_transaction_id
            FROM rosters r
            LEFT JOIN Users u ON r.owner_id = u.sleeper_user_id
            LEFT JOIN UserLeagueLinks ull ON u.wallet_address = ull.wallet_address AND ull.sleeper_league_id = r.sleeper_league_id
            WHERE r.sleeper_league_id = ?
            ORDER BY manager_display_name, r.team_name 
        """
        # Pass target_season_year to the subquery. Note: it's used twice in the query.
        cursor.execute(query, (target_season_year, league_id,))
        roster_data = cursor.fetchall()
        
        roster_payment_details_list = []
        for row in roster_data:
            team_name = row['roster_team_name']
            manager_name = row['manager_display_name']

            if not row['sleeper_owner_id']: # Roster has no owner_id
                manager_name = "Open Slot"
                if not team_name: team_name = f"Team (Roster {row['sleeper_roster_id']})"
            elif not manager_name: # Roster has owner_id, but user not in our system or no display name
                 manager_name = "Unknown Manager" # Default if owner_id exists but no corresponding user / display name
                 if not team_name: team_name = f"Team {row['sleeper_owner_id'][:6]}..." # Fallback team name
            
            if not team_name: # General fallback if team_name is still null
                team_name = f"Team (Roster {row['sleeper_roster_id']})"

            roster_payment_details_list.append({
                'roster_id': row['sleeper_roster_id'],
                'team_name': team_name,
                'manager_display_name': manager_name,
                'wallet_address': row['wallet_address'], # Will be null if user not in our system
                'is_commissioner': bool(row['is_commissioner']) if row['is_commissioner'] is not None else False,
                'paid_amount': row['fee_paid_amount'] if row['fee_paid_amount'] is not None else 0.0,
                'payment_status': row['fee_payment_status'] if row['fee_payment_status'] else 'unpaid',
                'last_transaction_id': row['last_transaction_id']
            })

        return jsonify({
            'success': True,
            'league_id': league_id,
            'league_name': league_name,
            'queried_season_year': target_season_year,
            'fee_settings': league_fee_details,
            'roster_payment_details': roster_payment_details_list # Changed key name
        }), 200

    except sqlite3.Error as e:
        app.logger.error(f"Database error in /league/{league_id}/fees GET: {str(e)}")
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error in /league/{league_id}/fees GET: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/league/<league_id>/fees', methods=['POST'])
@login_required
def set_league_fees(league_id):
    """Sets or updates the league fee details for a specific league and season. Only accessible by the commissioner."""
    user = get_current_user()
    wallet_address = user['wallet_address']

    # Determine the season year to update for
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Missing JSON payload.'}), 400

    requested_season_year_str = data.get('season_year') # Get from payload
    current_season_details = get_current_season()
    target_season_year = None

    if requested_season_year_str:
        try:
            year_val = int(requested_season_year_str)
            target_season_year = str(year_val)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid season_year format in payload.'}), 400
    else:
        target_season_year = str(current_season_details['current_year'])

    app.logger.info(f"Setting fees for league {league_id}, wallet {wallet_address}, target_season_year: {target_season_year}")

    try:
        conn = get_global_db_connection()
        cursor = conn.cursor()

        # Verify the user is the commissioner for this league
        cursor.execute("""SELECT is_commissioner 
                          FROM UserLeagueLinks 
                          WHERE wallet_address = ? AND sleeper_league_id = ?""", 
                       (wallet_address, league_id))
        commish_status = cursor.fetchone()

        if not commish_status or not commish_status['is_commissioner']:
            app.logger.warning(f"User {wallet_address} (not commish) tried to set fees for league {league_id}.")
            return jsonify({'success': False, 'error': 'User is not authorized to set fees for this league.'}), 403

        # Data for fees is already in 'data' variable from above
        fee_amount = data.get('fee_amount')
        fee_currency = data.get('fee_currency')  # Remove fallback - currency must be explicitly set
        notes = data.get('notes', '')

        if fee_amount is None:
            return jsonify({'success': False, 'error': 'Missing fee_amount.'}), 400
        
        if fee_currency is None:
            return jsonify({'success': False, 'error': 'Missing fee_currency.'}), 400
        
        try:
            fee_amount_float = float(fee_amount)
            if fee_amount_float < 0:
                return jsonify({'success': False, 'error': 'fee_amount cannot be negative.'}), 400
        except ValueError:
            return jsonify({'success': False, 'error': 'fee_amount must be a valid number.'}), 400
        
        if not isinstance(fee_currency, str) or len(fee_currency) > 10:
             return jsonify({'success': False, 'error': 'Invalid fee_currency.'}), 400
        if not isinstance(notes, str):
            notes = str(notes) 

        # Insert or replace fee details for the target season
        cursor.execute("""INSERT OR REPLACE INTO LeagueFees 
                            (sleeper_league_id, season_year, fee_amount, fee_currency, notes, updated_at) 
                            VALUES (?, ?, ?, ?, ?, datetime('now'))
                       """, (league_id, target_season_year, fee_amount_float, fee_currency, notes))
        conn.commit()

        app.logger.info(f"Commissioner {wallet_address} updated fees for league {league_id} season {target_season_year}: Amount={fee_amount_float}, Currency={fee_currency}")
        return jsonify({'success': True, 'message': f'League fees for season {target_season_year} updated successfully.'}), 200

    except sqlite3.Error as e:
        app.logger.error(f"Database error in POST /league/{league_id}/fees (season {target_season_year}): {str(e)}")
        if conn: conn.rollback()
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error in POST /league/{league_id}/fees (season {target_season_year}): {str(e)}")
        if conn: conn.rollback()
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/league/<league_id>/fees/record-payment', methods=['POST'])
@login_required
def record_payment_for_league(league_id):
    """Records a successful payment for a league fee in the database."""
    user = get_current_user()
    payer_wallet_address = user['wallet_address'] # Authenticated user is the payer

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Missing JSON payload'}), 400

    # Extract data from frontend payload
    transaction_amount = data.get('amount')
    transaction_currency = data.get('currency')
    transaction_id = data.get('transaction_id')
    # league_id is already from URL path, payer_wallet_address from authenticated user

    if not all([transaction_amount is not None, transaction_currency, transaction_id]):
        return jsonify({'success': False, 'error': 'Missing amount, currency, or transaction_id in payload'}), 400

    try:
        transaction_amount = float(transaction_amount)
        if transaction_amount <= 0:
            return jsonify({'success': False, 'error': 'Payment amount must be positive'}), 400
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid payment amount format'}), 400

    conn = None
    try:
        conn = get_global_db_connection()
        cursor = conn.cursor()

        # 1. Fetch current season year to get the relevant fee settings
        current_season_details = get_current_season()
        current_season_year = int(current_season_details['current_year'])

        # 2. Get the required fee settings for this league and season
        cursor.execute("""SELECT fee_amount, fee_currency FROM LeagueFees WHERE sleeper_league_id = ? AND season_year = ?""", 
                       (league_id, current_season_year))
        league_fee_settings = cursor.fetchone()

        if not league_fee_settings or league_fee_settings['fee_amount'] is None:
            # If fee isn't set, or fee_amount is NULL, consider it either free or an error state
            app.logger.warning(f"Attempted to record payment for league {league_id}, season {current_season_year} but no fee amount is set.")
            # For now, allow it to proceed and update the paid amount/status as if fee is 0
            total_required_fee = 0.0
        else:
            total_required_fee = float(league_fee_settings['fee_amount'])
            if transaction_currency != league_fee_settings['fee_currency']:
                app.logger.warning(f"Payment currency mismatch: Transaction was {transaction_currency}, expected {league_fee_settings['fee_currency']}")
                # For simplicity, we'll still record it, but in a real app, you might want to block this or do conversion

        # 3. Get current payment status for the user in this league
        cursor.execute("""SELECT fee_paid_amount, fee_payment_status FROM UserLeagueLinks WHERE wallet_address = ? AND sleeper_league_id = ?""",
                       (payer_wallet_address, league_id))
        user_league_link = cursor.fetchone()

        if not user_league_link:
            app.logger.error(f"UserLeagueLink not found for wallet {payer_wallet_address} in league {league_id}. Cannot record payment.")
            return jsonify({'success': False, 'error': 'User is not linked to this league.'}), 404
        
        current_paid_amount = user_league_link['fee_paid_amount'] if user_league_link['fee_paid_amount'] is not None else 0.0
        
        # 4. Calculate new paid amount and status
        new_paid_amount = current_paid_amount + transaction_amount
        new_payment_status = 'unpaid'
        if new_paid_amount >= total_required_fee and total_required_fee > 0:
            new_payment_status = 'paid'
        elif new_paid_amount > 0 and new_paid_amount < total_required_fee:
            new_payment_status = 'partially_paid'
        elif total_required_fee == 0 and new_paid_amount >= 0: # If fee is 0, any payment or no payment means 'paid'
            new_payment_status = 'paid'

        # 5. Update UserLeagueLinks table
        cursor.execute("""UPDATE UserLeagueLinks SET fee_paid_amount = ?, fee_payment_status = ?, updated_at = datetime('now') WHERE wallet_address = ? AND sleeper_league_id = ?""",
                       (new_paid_amount, new_payment_status, payer_wallet_address, league_id))

        # 6. Insert new record into LeaguePayments table
        cursor.execute("""INSERT INTO LeaguePayments (
                            sleeper_league_id, season_year, wallet_address, amount, currency, transaction_id, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
                       (league_id, current_season_year, payer_wallet_address, transaction_amount, transaction_currency, transaction_id))
        
        conn.commit()

        app.logger.info(f"Payment recorded for wallet {payer_wallet_address} in league {league_id}: Amount={transaction_amount} {transaction_currency}, TxID={transaction_id}. New status: {new_payment_status}, Total Paid: {new_paid_amount}")
        return jsonify({'success': True, 'message': 'Payment recorded successfully', 'new_payment_status': new_payment_status, 'new_paid_amount': new_paid_amount}), 200

    except sqlite3.Error as e:
        if conn: conn.rollback()
        app.logger.error(f"Database error in POST /league/{league_id}/fees/record-payment: {str(e)}")
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn: conn.rollback()
        app.logger.error(f"Unexpected error in POST /league/{league_id}/fees/record-payment: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/league/<league_id>/transactions/recent', methods=['GET'])
@login_required
def get_recent_transactions(league_id):
    """Get recent transactions for a league."""
    user = get_current_user()
    
    try:
        conn = get_global_db_connection()
        cursor = conn.cursor()
        
        # 1. Check if user is part of this league
        cursor.execute("""
            SELECT 1 FROM UserLeagueLinks 
            WHERE wallet_address = ? AND sleeper_league_id = ?
        """, (user['wallet_address'], league_id))
        
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'User is not part of this league'}), 403
        
        # 2. Get league name
        cursor.execute("""
            SELECT name FROM LeagueMetadata 
            WHERE sleeper_league_id = ?
        """, (league_id,))
        
        league_data = cursor.fetchone()
        if not league_data:
            return jsonify({'success': False, 'error': 'League not found'}), 404
        
        league_name = league_data['name']
        
        # 3. Get recent transactions (limit to 15 most recent)
        cursor.execute("""
            SELECT sleeper_transaction_id, type, status, data, created_at
            FROM transactions 
            WHERE league_id = ? 
            ORDER BY created_at DESC 
            LIMIT 15
        """, (league_id,))
        
        transactions = []
        raw_transactions = cursor.fetchall()

        # Debug logging
        print(f"DEBUG: Found {len(raw_transactions)} raw transactions for league {league_id}")

        # Fetch all player names (global)
        cursor.execute("SELECT sleeper_player_id, name FROM players")
        player_map = {row['sleeper_player_id']: row['name'] for row in cursor.fetchall()}

        # Fetch team names for this league
        cursor.execute("""
            SELECT sleeper_roster_id, team_name 
            FROM rosters 
            WHERE sleeper_league_id = ?
        """, (league_id,))
        team_map = {str(row['sleeper_roster_id']): row['team_name'] for row in cursor.fetchall()}

        for row in raw_transactions:
            try:
                details = json.loads(row['data']) if row['data'] else {}
                print(f"DEBUG: Transaction {row['sleeper_transaction_id']}: type={row['type']}, status={row['status']}, details_keys={list(details.keys()) if details else 'None'}")
                
                # Resolve player names and team names
                player_names = {}
                for pid in set(list(details.get('adds', {}).keys()) + list(details.get('drops', {}).keys())):
                    player_names[pid] = player_map.get(pid, pid)  # Fallback to ID if not found
                
                team_names = {rid: team_map.get(rid, rid) for rid in set(list(details.get('adds', {}).values()) + list(details.get('drops', {}).values()))}
                
                # Add to details
                details['player_names'] = player_names
                details['team_names'] = team_names
                
            except json.JSONDecodeError:
                details = {"error": "Could not parse transaction data"}
                print(f"DEBUG: Failed to parse JSON for transaction {row['sleeper_transaction_id']}")
            
            transactions.append({
                'transaction_id': row['sleeper_transaction_id'],
                'type': row['type'],
                'status': row['status'],
                'details': details,
                'created_at': row['created_at']
            })

        print(f"DEBUG: Returning {len(transactions)} processed transactions")

        return jsonify({
            'success': True,
            'league_id': league_id,
            'league_name': league_name,
            'transactions': transactions
        }), 200
        
    except sqlite3.Error as e:
        app.logger.error(f"Database error in GET /league/{league_id}/transactions/recent: {str(e)}")
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error in GET /league/{league_id}/transactions/recent: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/nfl/current-week', methods=['GET'])
def get_current_nfl_week():
    """Get the current NFL week and season information."""
    try:
        # Use the SleeperService to get NFL state
        nfl_state = sleeper_service.get_nfl_state()
        
        if not nfl_state:
            return jsonify({'success': False, 'error': 'Unable to fetch NFL state'}), 500
        
        return jsonify({
            'success': True,
            'season': nfl_state.get('season'),
            'week': nfl_state.get('week'),
            'season_type': nfl_state.get('season_type'),
            'is_offseason': nfl_state.get('season_type', '').lower() in ['off', 'pre']
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error in GET /nfl/current-week: {str(e)}")
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/league/<league_id>/transactions/week/<int:week>', methods=['GET'])
@login_required
def get_league_transactions_by_week(league_id, week):
    """Get transactions for a specific week in a league."""
    user = get_current_user()
    
    try:
        conn = get_global_db_connection()
        cursor = conn.cursor()
        
        # 1. Check if user is part of this league
        cursor.execute("""
            SELECT 1 FROM UserLeagueLinks 
            WHERE wallet_address = ? AND sleeper_league_id = ?
        """, (user['wallet_address'], league_id))
        
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'User is not part of this league'}), 403
        
        # 2. Get league name
        cursor.execute("""
            SELECT name FROM LeagueMetadata 
            WHERE sleeper_league_id = ?
        """, (league_id,))
        
        league_data = cursor.fetchone()
        if not league_data:
            return jsonify({'success': False, 'error': 'League not found'}), 404
        
        league_name = league_data['name']
        
        # 3. Get transactions for the specific week
        # Note: We'll need to parse the data field to check if it contains week information
        # For now, we'll return all transactions and let the frontend filter by week
        cursor.execute("""
            SELECT sleeper_transaction_id, type, status, data, created_at
            FROM transactions 
            WHERE league_id = ?
            ORDER BY created_at DESC
        """, (league_id,))

        transactions = []
        raw_transactions = cursor.fetchall()

        # Debug logging
        print(f"DEBUG: Found {len(raw_transactions)} raw transactions for league {league_id}, week {week}")

        # Fetch all player names (global)
        cursor.execute("SELECT sleeper_player_id, name FROM players")
        player_map = {row['sleeper_player_id']: row['name'] for row in cursor.fetchall()}

        # Fetch team names for this league
        cursor.execute("""
            SELECT sleeper_roster_id, team_name 
            FROM rosters 
            WHERE sleeper_league_id = ?
        """, (league_id,))
        team_map = {str(row['sleeper_roster_id']): row['team_name'] for row in cursor.fetchall()}

        for row in raw_transactions:
            try:
                details = json.loads(row['data']) if row['data'] else {}
                
                # Check if this transaction is for the specified week
                # Sleeper API includes week info in transaction data
                transaction_week = details.get('week') or details.get('leg') or None
                
                print(f"DEBUG: Transaction {row['sleeper_transaction_id']}: type={row['type']}, week={transaction_week}, details_keys={list(details.keys()) if details else 'None'}")
                
                if transaction_week is None or int(transaction_week) == week:
                    # Resolve player names and team names
                    player_names = {}
                    for pid in set(list(details.get('adds', {}).keys()) + list(details.get('drops', {}).keys())):
                        player_names[pid] = player_map.get(pid, pid)
                    
                    team_names = {rid: team_map.get(rid, rid) for rid in set(list(details.get('adds', {}).values()) + list(details.get('drops', {}).values()))}
                    
                    # Add to details
                    details['player_names'] = player_names
                    details['team_names'] = team_names
                    
                    transactions.append({
                        'transaction_id': row['sleeper_transaction_id'],
                        'type': row['type'],
                        'status': row['status'],
                        'details': details,
                        'created_at': row['created_at'],
                        'week': transaction_week
                    })
            except json.JSONDecodeError:
                print(f"DEBUG: Failed to parse JSON for transaction {row['sleeper_transaction_id']}")
                transactions.append({
                    'transaction_id': row['sleeper_transaction_id'],
                    'type': row['type'],
                    'status': row['status'],
                    'details': {"error": "Could not parse transaction data"},
                    'created_at': row['created_at'],
                    'week': None
                })

        print(f"DEBUG: Returning {len(transactions)} transactions for week {week}")

        return jsonify({
            'success': True,
            'league_id': league_id,
            'league_name': league_name,
            'week': week,
            'transactions': transactions
        }), 200
        
    except sqlite3.Error as e:
        app.logger.error(f"Database error in GET /league/{league_id}/transactions/week/{week}: {str(e)}")
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error in GET /league/{league_id}/transactions/week/{week}: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}), 500

# ============================================================================
# TRADE MANAGEMENT ENDPOINTS
# ============================================================================

def get_wallet_from_token(token):
    """Retrieve wallet address from session token."""
    if not token:
        return None
    try:
        cursor = get_global_db_connection().cursor()
        cursor.execute("SELECT wallet_address FROM sessions WHERE session_token = ?", (token,))
        result = cursor.fetchone()
        return result['wallet_address'] if result else None
    except Exception as e:
        app.logger.error(f"Error in get_wallet_from_token: {str(e)}")
        return None

@app.route('/api/league/<league_id>/commissioner-status', methods=['GET'])
@login_required
def get_commissioner_status(league_id):
    """Check if the current user is a commissioner for this league."""
    try:
        wallet_address = get_wallet_from_token(request.headers.get('Authorization'))
        if not wallet_address:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        
        cursor = get_global_db_connection().cursor()
        
        # Check if user is commissioner based on UserLeagueLinks table
        cursor.execute('''
            SELECT 1 FROM UserLeagueLinks 
            WHERE sleeper_league_id = ? AND wallet_address = ? AND is_commissioner = 1
        ''', (league_id, wallet_address))
        
        is_commissioner = cursor.fetchone() is not None
        
        return jsonify({'success': True, 'is_commissioner': is_commissioner})
        
    except Exception as e:
        app.logger.error(f"Error checking commissioner status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trades/budget/create', methods=['POST'])
@login_required
def create_budget_trade():
    """Create a new budget trade between teams."""
    try:
        wallet_address = get_wallet_from_token(request.headers.get('Authorization'))
        if not wallet_address:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        
        data = request.get_json()
        initiator_team_id = data.get('initiator_team_id')
        recipient_team_id = data.get('recipient_team_id')
        league_id = data.get('league_id')
        budget_items = data.get('budget_items', [])
        
        if not all([initiator_team_id, recipient_team_id, league_id, budget_items]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        if initiator_team_id == recipient_team_id:
            return jsonify({'success': False, 'error': 'Cannot trade with yourself'}), 400
        
        cursor = get_global_db_connection().cursor()
        
        # Create trade record
        cursor.execute('''
            INSERT INTO trades (sleeper_league_id, initiator_team_id, recipient_team_id, 
                              trade_status, created_at, updated_at)
            VALUES (?, ?, ?, 'pending', datetime('now'), datetime('now'))
        ''', (league_id, initiator_team_id, recipient_team_id))
        
        trade_id = cursor.lastrowid
        
        # Create trade items
        for item in budget_items:
            if not item.get('year') or not item.get('amount') or item.get('amount', 0) <= 0:
                continue
                
            cursor.execute('''
                INSERT INTO trade_items (trade_id, from_team_id, to_team_id, 
                                      budget_amount, season_year, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            ''', (trade_id, initiator_team_id, recipient_team_id, item['amount'], item['year']))
        
        get_global_db_connection().commit()
        
        return jsonify({
            'success': True, 
            'trade_id': trade_id,
            'message': 'Trade created successfully and sent for commissioner approval'
        })
        
    except Exception as e:
        app.logger.error(f"Error creating budget trade: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trades/pending/<league_id>', methods=['GET'])
@login_required
def get_pending_trades(league_id):
    """Get all pending trades for a league."""
    try:
        cursor = get_global_db_connection().cursor()
        
        cursor.execute('''
            SELECT 
                t.trade_id,
                t.created_at,
                t.initiator_team_id,
                t.recipient_team_id,
                init_roster.team_name as initiator_team_name,
                recip_roster.team_name as recipient_team_name,
                ti.item_id,
                ti.budget_amount,
                ti.season_year
            FROM trades t
            JOIN rosters init_roster ON t.initiator_team_id = init_roster.sleeper_roster_id
            JOIN rosters recip_roster ON t.recipient_team_id = recip_roster.sleeper_roster_id
            JOIN trade_items ti ON t.trade_id = ti.trade_id
            WHERE t.sleeper_league_id = ? AND t.trade_status = 'pending'
            ORDER BY t.created_at DESC
        ''', (league_id,))
        
        trades_data = {}
        for row in cursor.fetchall():
            trade_id = row['trade_id']
            if trade_id not in trades_data:
                trades_data[trade_id] = {
                    'trade_id': trade_id,
                    'created_at': row['created_at'],
                    'initiator_team_id': row['initiator_team_id'],
                    'recipient_team_id': row['recipient_team_id'],
                    'initiator_team_name': row['initiator_team_name'],
                    'recipient_team_name': row['recipient_team_name'],
                    'budget_items': []
                }
            
            trades_data[trade_id]['budget_items'].append({
                'item_id': row['item_id'],
                'budget_amount': row['budget_amount'],
                'season_year': row['season_year']
            })
        
        trades = list(trades_data.values())
        return jsonify({'success': True, 'trades': trades})
        
    except Exception as e:
        app.logger.error(f"Error fetching pending trades: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trades/<trade_id>/approve', methods=['POST'])
@login_required
def approve_trade(trade_id):
    """Approve a pending trade."""
    try:
        wallet_address = get_wallet_from_token(request.headers.get('Authorization'))
        if not wallet_address:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        
        cursor = get_global_db_connection().cursor()
        
        # Verify user is commissioner for this trade's league
        cursor.execute('''
            SELECT t.sleeper_league_id, t.trade_status
            FROM trades t
            WHERE t.trade_id = ?
        ''', (trade_id,))
        
        trade_info = cursor.fetchone()
        if not trade_info:
            return jsonify({'success': False, 'error': 'Trade not found'}), 404
        
        if trade_info['trade_status'] != 'pending':
            return jsonify({'success': False, 'error': 'Trade is not pending'}), 400
        
        # Check if user is commissioner for this league
        cursor.execute('''
            SELECT 1 FROM UserLeagueLinks 
            WHERE sleeper_league_id = ? AND wallet_address = ? AND is_commissioner = 1
        ''', (trade_info['sleeper_league_id'], wallet_address))
        
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Commissioner access required'}), 403
        
        # Update trade status
        cursor.execute('''
            UPDATE trades 
            SET trade_status = 'completed', updated_at = datetime('now')
            WHERE trade_id = ?
        ''', (trade_id,))
        
        # Create approval record
        cursor.execute('''
            INSERT INTO trade_approvals (trade_id, approver_type, approver_id, 
                                      approval_status, approved_at, created_at)
            VALUES (?, 'commissioner', ?, 'approved', datetime('now'), datetime('now'))
        ''', (trade_id, wallet_address))
        
        get_global_db_connection().commit()
        return jsonify({'success': True, 'message': 'Trade approved successfully'})
        
    except Exception as e:
        app.logger.error(f"Error approving trade: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trades/<trade_id>/reject', methods=['POST'])
@login_required
def reject_trade(trade_id):
    """Reject a pending trade."""
    try:
        wallet_address = get_wallet_from_token(request.headers.get('Authorization'))
        if not wallet_address:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        
        data = request.get_json()
        notes = data.get('notes', '') if data else ''
        
        cursor = get_global_db_connection().cursor()
        
        # Verify user is commissioner for this trade's league
        cursor.execute('''
            SELECT t.sleeper_league_id, t.trade_status
            FROM trades t
            WHERE t.trade_id = ?
        ''', (trade_id,))
        
        trade_info = cursor.fetchone()
        if not trade_info:
            return jsonify({'success': False, 'error': 'Trade not found'}), 404
        
        if trade_info['trade_status'] != 'pending':
            return jsonify({'success': False, 'error': 'Trade is not pending'}), 400
        
        # Check if user is commissioner for this league
        cursor.execute('''
            SELECT 1 FROM UserLeagueLinks 
            WHERE sleeper_league_id = ? AND wallet_address = ? AND is_commissioner = 1
        ''', (trade_info['sleeper_league_id'], wallet_address))
        
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Commissioner access required'}), 403
        
        # Update trade status
        cursor.execute('''
            UPDATE trades 
            SET trade_status = 'rejected', updated_at = datetime('now')
            WHERE trade_id = ?
        ''', (trade_id,))
        
        # Create rejection record
        cursor.execute('''
            INSERT INTO trade_approvals (trade_id, approver_type, approver_id, 
                                      approval_status, approval_notes, created_at)
            VALUES (?, 'commissioner', ?, 'rejected', ?, datetime('now'))
        ''', (trade_id, wallet_address, notes))
        
        get_global_db_connection().commit()
        return jsonify({'success': True, 'message': 'Trade rejected successfully'})
        
    except Exception as e:
        app.logger.error(f"Error rejecting trade: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/league/<league_id>/teams', methods=['GET'])
@login_required
def get_league_teams_for_trades(league_id):
    """Get all teams in a league for trade partner selection."""
    try:
        cursor = get_global_db_connection().cursor()
        
        cursor.execute('''
            SELECT 
                r.sleeper_roster_id,
                r.team_name,
                u.display_name as manager_name,
                u.username
            FROM rosters r
            LEFT JOIN users u ON r.owner_id = u.sleeper_user_id
            WHERE r.sleeper_league_id = ?
            ORDER BY r.team_name
        ''', (league_id,))
        
        teams = []
        for row in cursor.fetchall():
            teams.append({
                'roster_id': row['sleeper_roster_id'],
                'team_name': row['team_name'] or 'Unknown Team',
                'manager_name': row['manager_name'] or row['username'] or 'Unknown Manager',
                'username': row['username']
            })
        
        return jsonify({'success': True, 'teams': teams})
        
    except Exception as e:
        app.logger.error(f"Error fetching league teams: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/teams/<team_id>/budget-status/<league_id>', methods=['GET'])
@login_required
def get_team_budget_status(team_id, league_id):
    """Get team's current budget status including contracts, penalties, and trades for future years."""
    try:
        cursor = get_global_db_connection().cursor()
        
        # Get current year from season_curr
        cursor.execute('SELECT current_year FROM season_curr LIMIT 1')
        current_year_row = cursor.fetchone()
        if not current_year_row:
            return jsonify({'success': False, 'error': 'Current season not found'}), 404
        
        current_year = int(current_year_row['current_year'])
        
        budget_status = {}
        
        # Calculate for next 4 years
        for year in range(current_year + 1, current_year + 5):
            # Get contract commitments for this year
            cursor.execute('''
                SELECT COALESCE(SUM(cost_for_season), 0) as contract_total
                FROM vw_contractByYear
                WHERE team_id = ? AND sleeper_league_id = ? AND year_number_in_contract = ?
            ''', (team_id, league_id, year))
            contract_total = cursor.fetchone()['contract_total'] or 0
            
            # Get penalties for this year
            cursor.execute('''
                SELECT COALESCE(SUM(penalty_amount), 0) as penalty_total
                FROM penalties p
                JOIN contracts c ON p.contract_id = c.rowid
                WHERE c.team_id = ? AND c.sleeper_league_id = ? AND p.penalty_year = ?
            ''', (team_id, league_id, year))
            penalty_total = cursor.fetchone()['penalty_total'] or 0
            
            # Get net trade impact for this year
            cursor.execute('''
                SELECT 
                    COALESCE(SUM(CASE WHEN to_team_id = ? THEN budget_amount ELSE 0 END), 0) as received,
                    COALESCE(SUM(CASE WHEN from_team_id = ? THEN budget_amount ELSE 0 END), 0) as sent
                FROM trade_items ti
                JOIN trades t ON ti.trade_id = t.trade_id
                WHERE t.sleeper_league_id = ? AND t.trade_status = 'completed' AND ti.season_year = ?
            ''', (team_id, team_id, league_id, year))
            trade_data = cursor.fetchone()
            trade_impact = (trade_data['received'] or 0) - (trade_data['sent'] or 0)
            
            budget_status[year] = {
                'contracts': contract_total,
                'penalties': penalty_total,
                'trades': trade_impact,
                'total_committed': contract_total + penalty_total - trade_impact,
                'remaining_budget': 200 - contract_total - penalty_total + trade_impact
            }
        
        return jsonify({'success': True, 'budget_status': budget_status})
        
    except Exception as e:
        app.logger.error(f"Error getting team budget status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Database initialization skipped - tables will be created on first use if they don't exist
print("Database initialization skipped - existing data preserved.")

# Initialize database with new schema (including trade tables)
print("Initializing database with new schema...")
init_db()
print("Database initialization complete.")

print("DEBUG: All routes and helpers defined. Entering __main__ block...")
if __name__ == '__main__':
    print("DEBUG: Inside __main__ block. About to call app.run()")
    # Ensure global connection is initialized before app runs,
    # especially if any routes might be hit immediately or by background tasks.
    # However, get_global_db_connection() is designed to init on first call.
    # init_db() call above should have initialized it.
    
    if app.config['DEBUG']:
        print("Running in DEVELOPMENT mode")
        # Suppress Flask development server warning
        import warnings
        warnings.filterwarnings("ignore", message="This is a development server")
        
        app.run(
            debug=True, 
            host=os.getenv('HOST', '127.0.0.1'),
            port=int(os.getenv('PORT', 5000))
        )
    else:
        print("Running in PRODUCTION mode")
        print("Starting production server with Waitress...")
        
        try:
            import waitress
            host = os.getenv('HOST', '0.0.0.0')
            port = int(os.getenv('PORT', 5000))
            
            print(f"Starting Waitress server on {host}:{port}")
            print("Press Ctrl+C to stop the server")
            
            # Start Waitress server
            waitress.serve(app, host=host, port=port, threads=4)
            
        except ImportError:
            print("Waitress not available. Install with: pip install waitress")
            print("Or use: python app.py (for development mode)")
        except Exception as e:
            print(f"Error starting Waitress: {e}")
            print("Falling back to development mode...")
            app.run(debug=False, host=host, port=port)
    
    print("DEBUG: app.run() has exited.")









