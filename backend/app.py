from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
import sqlite3, math
import os
import secrets
from pytonconnect import TonConnect
from pytonconnect.exceptions import TonConnectError
from sleeper_service import SleeperService
import json
import time # Added for potential sleep, though might not be used in final global conn version

# Create Flask app instance at the top
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6')

# --- TEMPORARY DEBUGGING: Global DB Connection ---
# DO NOT USE IN PRODUCTION
_global_db_conn = None

def get_global_db_connection():
    global _global_db_conn
    if _global_db_conn is None:
        print("DEBUG_GLOBAL_CONN: Initializing global database connection...")
        try:
            # connect_args = {'check_same_thread': False} # For older python versions
            _global_db_conn = sqlite3.connect('keeper.db', check_same_thread=False)
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

@app.before_request
def log_cors_headers():
    print(f"Request method: {request.method}, URL: {request.url}")
    if request.method == "OPTIONS":
        print("Handling OPTIONS preflight request")
        response = app.make_response('')
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
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
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    print(f"Response headers after modification: {response.headers}")
    return response

# Initialize the database
def init_db(force_create=False):
    try:
        conn = get_global_db_connection() # Use global connection
        cursor = conn.cursor()
        
        # Enable WAL mode is handled by get_global_db_connection() now
        # So, no specific PRAGMA call here unless to re-verify or if get_global_db_connection fails.

        if force_create:
            print("Forcing recreation of all tables...")
            # Drop existing tables
            tables = ["sessions", "UserLeagueLinks", "rosters", "contracts", 
                      "transactions", "traded_picks", "drafts", 
                      "LeagueMetadata", "Users", "players", "leagues"] # Added leagues to ensure it's dropped if old schema exists
            for table in tables:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    print(f"Dropped table {table}")
                except Exception as e:
                    print(f"Error dropping table {table}: {str(e)}")
        
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

        cursor.execute('''CREATE TABLE IF NOT EXISTS UserLeagueLinks (
                            wallet_address TEXT,
                            sleeper_league_id TEXT,
                            PRIMARY KEY (wallet_address, sleeper_league_id),
                            FOREIGN KEY (wallet_address) REFERENCES Users(wallet_address) ON DELETE CASCADE,
                            FOREIGN KEY (sleeper_league_id) REFERENCES LeagueMetadata(sleeper_league_id) ON DELETE CASCADE
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
                           players TEXT, -- JSON list of player_ids on main roster
                           metadata TEXT, -- JSON of roster metadata (e.g., custom team name from Sleeper)
                           reserve TEXT, -- JSON list of player_ids on reserve
                           taxi TEXT, -- JSON list of player_ids on taxi squad
                           wins INTEGER DEFAULT 0,
                           losses INTEGER DEFAULT 0,
                           ties INTEGER DEFAULT 0,
                           created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                           updated_at DATETIME,
                           PRIMARY KEY (sleeper_roster_id, sleeper_league_id),
                           FOREIGN KEY (sleeper_league_id) REFERENCES LeagueMetadata(sleeper_league_id) ON DELETE CASCADE
                           )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS contracts
                          (player_id TEXT,
                           team_id TEXT,
                           sleeper_league_id TEXT, -- Added
                           draft_amount REAL,
                           contract_year INTEGER,
                           duration INTEGER,
                           is_active BOOLEAN DEFAULT 1,
                           penalty_incurred REAL,
                           penalty_year INTEGER,
                           created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                           updated_at DATETIME,
                           UNIQUE (player_id, team_id, contract_year, sleeper_league_id), -- Updated
                           FOREIGN KEY (sleeper_league_id) REFERENCES LeagueMetadata(sleeper_league_id) ON DELETE CASCADE -- Added
                           )''') 
        cursor.execute('''CREATE TABLE IF NOT EXISTS transactions
                          (sleeper_transaction_id TEXT UNIQUE,
                           league_id INTEGER,
                           type TEXT,
                           status TEXT,
                           data TEXT,
                           created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                           updated_at DATETIME)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS traded_picks
                          (league_id INTEGER,
                           draft_id TEXT,
                           round INTEGER,
                           roster_id TEXT,
                           previous_owner_id TEXT,
                           current_owner_id TEXT,
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
        # Optionally, insert a default row if it's always needed, or update existing if it exists.
        # Using INSERT OR REPLACE to handle the single-row nature:
        cursor.execute('''INSERT OR REPLACE INTO season_curr (rowid, current_year, IsOffSeason, updated_at)
                          VALUES (1, ?, ?, datetime('now'))''', ('2025', 1)) # Using fixed rowid=1

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

init_db()

def get_current_season():
    """Retrieve the current season's year and in-season status from the season_curr table."""
    try:
        conn = get_global_db_connection() # Use global connection
        cursor = conn.cursor()
        cursor.execute('SELECT current_year, IsOffSeason FROM season_curr LIMIT 1')
        season_data = cursor.fetchone()
        
        if season_data:
            return {
                'year': season_data['current_year'],
                'is_offseason': season_data['IsOffSeason'] == 1
            }
        else:
            # Default values if season_curr table is not set up
            return {
                'year': 2025,
                'is_offseason': True
            }
    except Exception as e:
        print(f"Error getting current season data: {e}")
        # Default values in case of error
        return {
            'year': 2025,
            'is_offseason': True
        }

def calculate_penalty(contract, current_year, is_offseason):
    """Calculate the penalty for waiving a player based on season status."""
    draft_amount = contract['DraftAmount'] or 0  # Handle NULL as 0
    contract_year = contract['ContractYear']
    duration = contract['Duration']
    
    # Calculate remaining years
    if current_year < contract_year:
        remaining_years = duration  # Contract hasn't started
    elif contract_year <= current_year <= contract_year + duration - 1:
        remaining_years = contract_year + duration - current_year
    else:
        remaining_years = 0  # Contract has expired
    
    if remaining_years <= 0:
        return 0  # No penalty if contract is expired
    
    if is_offseason:
        # Off-season: 10% on first year, 5% on future years, rounded up, min $1 per year
        if remaining_years >= 1:
            penalty_first_year = int(max(math.ceil(0.1 * draft_amount), 1))
            if remaining_years > 1:
                penalty_subsequent = int(max(math.ceil(0.05 * draft_amount), 1))
                total_penalty = penalty_first_year + (remaining_years - 1) * penalty_subsequent
            else:
                total_penalty = penalty_first_year
        else:
            total_penalty = 0
    else:
        # In-season: 10% of DraftAmount per year, rounded up, min $1 per year
        penalty_per_year = int(max(math.ceil(0.1 * draft_amount), 1))
        total_penalty = remaining_years * penalty_per_year
    
    return total_penalty

# Initialize TonConnect
ton_connect = TonConnect(
    manifest_url='https://6feb-45-14-195-35.ngrok-free.app/tonconnect-manifest.json'
)

# Helper function to get current user from session
def get_current_user():
    session_token = request.headers.get('Authorization')
    # Assuming the token might be sent as "Bearer <token>", remove "Bearer " if present.
    if session_token and session_token.startswith("Bearer "):
        session_token = session_token.split(" ", 1)[1]

    if not session_token:
        print("DEBUG: get_current_user - No session_token in Authorization header")
        return None

    try:
        conn = get_global_db_connection()
        cursor = conn.cursor()
        
        # Get wallet_address from sessions table using the token
        cursor.execute('SELECT wallet_address FROM sessions WHERE session_token = ?', (session_token,))
        session_data = cursor.fetchone()
        
        if not session_data:
            print(f"DEBUG: get_current_user - No session found for token: {session_token[:10]}...")
            return None 
        
        wallet_address = session_data['wallet_address']
        
        # Now get user details from Users table
        # Ensure all necessary fields are selected, e.g., username, display_name
        cursor.execute('SELECT username, display_name, wallet_address, sleeper_user_id FROM Users WHERE wallet_address = ?', (wallet_address,))
        user_data = cursor.fetchone()
        
        if user_data:
            print(f"DEBUG: get_current_user - User found: {user_data['wallet_address']}")
            return dict(user_data) # Return as a dictionary
        else:
            print(f"DEBUG: get_current_user - No user found in Users table for wallet_address: {wallet_address}")
            return None # Should not happen if session exists and Users table is consistent
            
    except Exception as e:
        print(f"Error in get_current_user: {e}")
        import traceback
        traceback.print_exc()
    return None

# TonConnect manifest route
@app.route('/tonconnect-manifest.json')
def tonconnect_manifest():
    return {
        "url": "https://6feb-45-14-195-35.ngrok-free.app",
        "name": "Supreme Keeper League",
        "iconUrl": "https://6feb-45-14-195-35.ngrok-free.app/static/icon.png"
    }

# TonConnect login initiation
@app.route('/login', methods=['GET'])
def initiate_login():
    if get_current_user():
        user = get_current_user()
        conn = get_global_db_connection() # Use global connection
        cursor = conn.cursor()
        cursor.execute('SELECT sleeper_user_id FROM Users WHERE wallet_address = ?', (user['wallet_address'],))
        result = cursor.fetchone()
        if result and result['sleeper_user_id']:
            print("User already authenticated and associated with Sleeper")
            # Fetch user's leagues
            cursor = conn.cursor()
            cursor.execute('SELECT sleeper_league_id FROM leagues WHERE sleeper_user_id = ?', (result['sleeper_user_id'],))
            leagues = cursor.fetchall()
            if leagues:
                first_league_id = leagues[0]['sleeper_league_id']
                return redirect(url_for('league', league_id=first_league_id))
            else:
                return redirect(url_for('league'))
        else:
            print("User authenticated but not associated with Sleeper")
            # Bypassing Sleeper association, redirect directly to league page
            return redirect(url_for('league'))
    flash('Please connect your TON wallet from the frontend.', 'info')
    return redirect("http://localhost:5173")

# TonConnect callback (optional, if used by frontend)
@app.route('/tonconnect-callback', methods=['GET'])
def tonconnect_callback():
    try:
        proof = request.args.get('proof')
        address = request.args.get('address')
        if ton_connect.verify_proof(proof, address):
            conn = get_global_db_connection() # Use global connection
            cursor = conn.cursor()
            cursor.execute('SELECT wallet_address FROM Users WHERE wallet_address = ?', (address,))
            user = cursor.fetchone()
            if not user:
                cursor.execute('INSERT INTO Users (wallet_address, CreatedAt) VALUES (?, datetime("now"))', (address,))
                conn.commit()
                user_id = cursor.lastrowid
            else:
                user_id = user['wallet_address']
            session['wallet_address'] = address
            flash('Logged in successfully.', 'success')
            return redirect(url_for('league'))
        else:
            flash('Invalid TonConnect proof.', 'error')
            return redirect(url_for('initiate_login'))
    except TonConnectError as e:
        flash(f'TonConnect error: {str(e)}', 'error')
        return redirect(url_for('initiate_login'))

# Auth login route (for frontend to verify TonConnect proof)
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
        nonce = data.get('nonce')

        if not wallet_address or not nonce:
            print("Missing walletAddress or nonce")
            return jsonify({'success': False, 'error': 'Missing walletAddress or nonce'}), 400

        session_token = secrets.token_urlsafe(32)
        print(f"Generated session token: {session_token}")

        conn = get_global_db_connection() # Use global connection
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT wallet_address FROM Users WHERE wallet_address = ?', (wallet_address,))
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

        else:
            # For existing users, trigger a full data pull from Sleeper
            print("Existing user detected, triggering full Sleeper data pull via /auth/login path")
            full_data_response = sleeper_service.fetch_all_data(wallet_address)
            if not full_data_response['success']:
                print(f"Failed to fetch full Sleeper data in /auth/login: {full_data_response.get('error', 'Unknown error')}")
            # Create session
            cursor.execute('''
                INSERT OR REPLACE INTO sessions (
                    wallet_address,
                    session_token
                ) VALUES (?, ?)''',
                (wallet_address, session_token)
            )
            conn.commit()
            print("Successfully created session")

        return jsonify({
            'success': True,
            'sessionToken': session_token,
            'isNewUser': is_new_user
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
    def wrap(*args, **kwargs):
        current_user = get_current_user()
        if not current_user:
            # For APIs, return a JSON response indicating unauthorized access
            print(f"DEBUG: login_required - Denying access to {f.__name__} due to failed authentication.")
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        # Pass the fetched user object to the decorated function, if needed.
        # This can be done by adding a parameter to the decorated function (e.g., def my_route(current_user_obj):)
        # and then passing it: return f(current_user_obj, *args, **kwargs)
        # For now, just call as is if this pattern is not used.
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
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
@app.route('/waive_player', methods=['POST'])
@login_required
def waive_player():
    conn = None
    try:
        conn = get_global_db_connection() # Use global connection
        cursor = conn.cursor()
        cursor.execute('PRAGMA foreign_keys = ON;')

        user = get_current_user()
        cursor.execute('SELECT TeamID FROM User WHERE rowid = ?', (user['id'],))
        user_data = cursor.fetchone()
        team_id = user_data['TeamID'] if user_data else None
        print(f"Team ID: {team_id}")
        if not team_id:
            flash('You are not associated with a team.', 'error')
            return redirect(url_for('league'))

        player_id = request.form.get('player_id')
        print(f"Player ID: {player_id}")
        if not player_id:
            flash('No player selected.', 'error')
            return redirect(url_for('team', team_id=team_id))

        cursor.execute(
            'SELECT rowid, * FROM Contract WHERE TeamId = ? AND PlayerId = ? AND IsActive = 1',
            (team_id, player_id)
        )
        contract = cursor.fetchone()
        print(f"Contract found: {contract}")
        contract_id = contract['rowid'] if contract else None
        if not contract:
            flash('No active contract found for this player on your team.', 'error')
            return redirect(url_for('team', team_id=team_id))

        season = get_current_season()
        print(f"Season: {season}")
        if not season:
            flash('Season configuration error.', 'error')
            return redirect(url_for('team', team_id=team_id))

        current_year = season['year']
        is_offseason = season['is_offseason']

        penalty = calculate_penalty(contract, current_year, is_offseason)
        print(f"Penalty calculated: {penalty}")
        penalty_year = current_year + 1 if is_offseason else current_year

        cursor.execute(
            'UPDATE Contract SET IsActive = 0, PenaltyIncurred = ?, PenaltyYear = ? WHERE rowid = ?',
            (penalty, penalty_year, contract_id)
        )
        print(f"Contract updated, rows affected: {cursor.rowcount}")
        if cursor.rowcount == 0:
            flash('Failed to waive player. No active contract updated.', 'error')
        else:
            cursor.execute(
                'INSERT INTO Waived (ContractID, SeasonYear, IsOffseason, WaivedAt) VALUES (?, ?, ?, datetime("now"))',
                (contract_id, current_year, 1 if is_offseason else 0)
            )
            print(f"Waived record inserted, rows affected: {cursor.rowcount}")
            if cursor.rowcount == 0:
                print("Warning: No rows inserted into Waived table.")
            else:
                conn.commit()
                flash('Player waived successfully.', 'success')

    except Exception as e:
        print(f"Error waiving player: {e}")
        import traceback
        traceback.print_exc()
        flash('An error occurred while waiving the player.', 'error')
        if conn:
            conn.rollback()

    return redirect(url_for('team', team_id=team_id))

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

@app.route('/auth/associate_sleeper', methods=['POST'])
def associate_sleeper():
    data = request.get_json()
    wallet_address = data.get('walletAddress')
    sleeper_id = data.get('sleeperId')
    
    if not wallet_address or not sleeper_id:
        return jsonify({'error': 'Missing walletAddress or sleeperId'}), 400
    
    db = KeeperDB()
    db.associate_sleeper(wallet_address, sleeper_id)
    
    # Trigger full data pull for the associated Sleeper account
    sleeper_service.fetch_all_data(wallet_address)
    
    return jsonify({'message': 'Sleeper account associated successfully'}), 200

@app.route('/sleeper/fetchAll', methods=['POST'])
def fetch_all_data_route():
    session_token = request.headers.get('Authorization')
    if not session_token:
        return jsonify({'success': False, 'error': 'No session token'}), 401
    
    try:
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
        # The rosters table now uses sleeper_league_id and does not store detailed stats or the 'settings' blob.
        cursor.execute('''
            SELECT 
                r.sleeper_roster_id,
                r.owner_id, -- This is sleeper_user_id
                COALESCE(u.display_name, u.username, r.owner_id) as owner_display_name, -- Use display_name, fallback to username, then owner_id
                u.avatar as owner_avatar,
                r.metadata, -- For team name
                r.players, -- JSON string of player_ids
                r.wins,
                r.losses,
                r.ties
            FROM rosters r
            LEFT JOIN Users u ON r.owner_id = u.sleeper_user_id -- Join with Users table
            WHERE r.sleeper_league_id = ?
        ''', (league_id_from_request,))
        rosters_data = cursor.fetchall()

        simplified_roster_info = []
        for row in rosters_data:
            # Extract team name from roster metadata if available
            team_name = None
            if row['metadata']:
                try:
                    roster_metadata = json.loads(row['metadata'])
                    team_name = roster_metadata.get('team_name', roster_metadata.get('name'))
                except json.JSONDecodeError:
                    app.logger.warning(f"Could not parse metadata for roster {row['sleeper_roster_id']}: {row['metadata']}")

            simplified_roster_info.append({
                'roster_id': row['sleeper_roster_id'],
                'owner_id': row['owner_id'],
                'owner_display_name': row['owner_display_name'],
                'owner_avatar': row['owner_avatar'],
                'team_name': team_name or row['owner_display_name'], # Fallback to owner display name if team name not found
                'player_count': len(json.loads(row['players'])) if row['players'] else 0,
                'wins': row['wins'],
                'losses': row['losses'],
                'ties': row['ties']
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

        # Step 1: Pre-emptive cleanup. Ensure the target sleeper_user_id is not associated with any OTHER wallet,
        # or any record with a NULL wallet. This is to prevent UNIQUE constraint errors on the subsequent UPDATE.
        print(f"DEBUG: Pre-emptive Cleanup: Deleting other user rows with sleeper_user_id {sleeper_user_id} that don't match current wallet {wallet_address} or have a NULL wallet.")
        cursor.execute('''DELETE FROM Users
                          WHERE sleeper_user_id = ? AND (wallet_address IS NULL OR wallet_address != ?)''',
                       (sleeper_user_id, wallet_address))
        delete_rowcount = cursor.rowcount
        print(f"DEBUG: Pre-emptive cleanup delete rowcount: {delete_rowcount}")

        # Step 2: Update the user record associated with the current wallet_address.
        # This record should have been created by /auth/login with a NULL sleeper_user_id.
        print(f"DEBUG: Attempting to UPDATE users table for wallet_address: {wallet_address} to set sleeper_id: {sleeper_user_id}")
        cursor.execute('''
            UPDATE Users 
            SET sleeper_user_id = ?, username = ?, display_name = ?, avatar = ?, updated_at = datetime('now')
            WHERE wallet_address = ?
        ''', (sleeper_user_id, sleeper_username, display_name, avatar, wallet_address))
        
        update_rowcount = cursor.rowcount
        print(f"DEBUG: UPDATE users for wallet_address {wallet_address} rowcount: {update_rowcount}")

        if update_rowcount == 0:
            # This is unexpected if /auth/login created the user row with this wallet_address.
            # It implies the row for this wallet_address was somehow deleted or altered before this update.
            # The pre-emptive delete above should NOT have deleted this row (as it checks wallet_address != ?).
            print(f"WARNING: User record for wallet_address: {wallet_address} was NOT updated with Sleeper details. " +
                  "This might indicate the user record for the session was missing or already had this sleeper_user_id with a different wallet " +
                  "that wasn't cleaned up as expected. The sleeper_user_id may now be orphaned if the cleanup above removed its only valid entry.")
            # Depending on desired strictness, this could be a hard error.
            # Previous logic was 'pass'. Keeping it as a warning for now, but it's a significant state to log.
            pass

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
            conn.commit() # Commit changes made by fetch_all_data
            print(f"DEBUG: conn.commit() executed for wallet_address: {wallet_address} (after successful fetch_all_data)")
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

@app.route('/season/settings', methods=['POST'])
def update_season_settings():
    session_token = request.headers.get('Authorization')
    if not session_token:
        return jsonify({'success': False, 'error': 'No session token'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request data'}), 400
        
        year = data.get('year')
        is_offseason = data.get('is_offseason')
        
        if year is None and is_offseason is None:
            return jsonify({'success': False, 'error': 'No settings provided to update'}), 400
        
        # Verify session
        with get_global_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT current_year, IsOffSeason FROM season_curr LIMIT 1')
            current_settings = cursor.fetchone()
            
            if current_settings:
                # Use current values for any missing parameters
                if year is None:
                    year = current_settings['current_year']
                if is_offseason is None:
                    is_offseason = current_settings['IsOffSeason'] == 1
            else:
                # Default values if no current settings
                if year is None:
                    year = 2025
                if is_offseason is None:
                    is_offseason = True
            
            # Convert is_offseason to integer
            is_offseason_int = 1 if is_offseason else 0
            
            # Update settings
            cursor.execute('DELETE FROM season_curr')
            cursor.execute('''
                INSERT INTO season_curr (current_year, IsOffSeason, updated_at)
                VALUES (?, ?, datetime("now"))
            ''', (year, is_offseason_int))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Season settings updated successfully',
                'season': {
                    'year': year,
                    'is_offseason': is_offseason_int == 1
                }
            })
    except Exception as e:
        print(f"Error in update_season_settings: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

@app.route('/auth/me', methods=['GET'])
@login_required
def get_me():
    """Returns the details of the currently authenticated user."""
    user = get_current_user() # This already fetches from DB based on session token
    if not user:
        # This case should ideally be handled by @login_required, 
        # but as a safeguard:
        return jsonify({'success': False, 'error': 'User not authenticated or session invalid'}), 401
    
    # get_current_user() returns a dict. We can augment or filter it if needed.
    # For now, return what get_current_user() provides.
    # Ensure sensitive data is not exposed if get_current_user() returns more than needed.
    # Based on its definition, it returns: {'username', 'display_name', 'wallet_address', 'sleeper_user_id'}
    
    print(f"DEBUG: /auth/me - Returning user data: {user}")
    return jsonify({'success': True, 'user': user}), 200

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
                   r.reserve as reserve_ids_json, r.taxi as taxi_ids_json, r.metadata as roster_metadata_json,
                   COALESCE(u.display_name, u.username) as manager_name, u.username as sleeper_username
            FROM rosters r
            LEFT JOIN Users u ON r.owner_id = u.sleeper_user_id
            WHERE r.sleeper_roster_id = ? AND r.sleeper_league_id = ?
        """, (team_id, league_id_from_query))
        roster_info = cursor.fetchone()

        if not roster_info:
            return jsonify({'success': False, 'error': 'Team (roster) not found'}), 404

        # Verify that the current user is part of the league this team belongs to.
        # This prevents users from viewing teams in leagues they are not a part of.
        cursor.execute("""SELECT 1 FROM UserLeagueLinks WHERE wallet_address = ? AND sleeper_league_id = ?""",
                       (current_user_details['wallet_address'], roster_info['sleeper_league_id']))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'User not authorized to view this team (not part of the league)'}), 403

        # Default team name will be the manager's display name if no custom name is found
        team_name = roster_info['manager_name']  # Use manager's name as a better default
        if roster_info['roster_metadata_json']:
            try:
                roster_metadata = json.loads(roster_info['roster_metadata_json'])
                custom_name = roster_metadata.get('team_name', roster_metadata.get('name'))
                if custom_name: 
                    team_name = custom_name
            except json.JSONDecodeError:
                app.logger.warning(f"Could not parse roster metadata for roster_id {team_id}. Using manager name '{team_name}' as fallback.")

        main_player_ids = json.loads(roster_info['player_ids_json']) if roster_info['player_ids_json'] else []
        reserve_player_ids = json.loads(roster_info['reserve_ids_json']) if roster_info['reserve_ids_json'] else []
        all_player_ids_on_roster = list(set(main_player_ids + reserve_player_ids))
        
        current_season_data = get_current_season()
        current_processing_year = int(current_season_data['year']) if current_season_data and current_season_data['year'] else 0
        is_offseason = current_season_data['is_offseason']
        
        print(f"DEBUG_TEAM_DETAILS_FULL: current_season_data = {current_season_data}")
        print(f"DEBUG_TEAM_DETAILS_FULL: current_processing_year = {current_processing_year}")
        print(f"DEBUG_TEAM_DETAILS_FULL: is_offseason = {is_offseason}")
        print(f"DEBUG_TEAM_DETAILS_FULL: Roster's league_id = {roster_info['sleeper_league_id']}")

        # Determine if the contract setting period is active for this league
        is_contract_setting_period_active = False
        auction_acquisitions = {} 
        
        if is_offseason and current_processing_year > 0:
            cursor.execute("""
                SELECT data 
                FROM drafts 
                WHERE league_id = ? AND season = ? AND status = ? 
                ORDER BY start_time DESC LIMIT 1
            """, (roster_info['sleeper_league_id'], str(current_processing_year), "complete"))
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
                                try:
                                    auction_acquisitions[str(player_id)] = int(amount_str)
                                except ValueError:
                                    app.logger.warning(f"DEBUG_TEAM_DETAILS_FULL: Warning: Could not convert auction amount '{amount_str}' to int for player {player_id}")
                except json.JSONDecodeError:
                    app.logger.warning(f"DEBUG_TEAM_DETAILS_FULL: Warning: Could not parse draft data JSON for league {roster_info['sleeper_league_id']} season {current_processing_year}")

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

        active_roster_players = []
        if all_player_ids_on_roster:
            placeholders = ', '.join('?' * len(all_player_ids_on_roster))
            query = f"""
                SELECT p.sleeper_player_id, p.name, p.position, p.team as nfl_team,
                       c.draft_amount, c.contract_year, c.duration, c.is_active
                FROM players p
                LEFT JOIN contracts c ON p.sleeper_player_id = c.player_id AND c.team_id = ? AND c.sleeper_league_id = ?
                WHERE p.sleeper_player_id IN ({placeholders})
            """
            cursor.execute(query, (team_id, roster_info['sleeper_league_id'], *all_player_ids_on_roster))
            player_details_list = cursor.fetchall()
            player_map = {str(p['sleeper_player_id']): dict(p) for p in player_details_list}
            
            player_future_costs = {}
            if all_player_ids_on_roster and current_processing_year > 0:
                costs_placeholders = ', '.join('?' * len(all_player_ids_on_roster))
                seasons_to_fetch = [current_processing_year + i for i in range(4)]
                cost_query = f"""
                    SELECT player_id, season_for_this_year_of_contract, cost_for_season
                    FROM vw_contractByYear
                    WHERE player_id IN ({costs_placeholders})
                      AND team_id = ?
                      AND sleeper_league_id = ?
                      AND season_for_this_year_of_contract BETWEEN ? AND ?
                """
                cost_params = list(all_player_ids_on_roster) + [team_id, roster_info['sleeper_league_id'], seasons_to_fetch[0], seasons_to_fetch[-1]]
                cursor.execute(cost_query, cost_params)
                costs_data = cursor.fetchall()
                for cost_row in costs_data:
                    p_id = str(cost_row['player_id'])
                    season = int(cost_row['season_for_this_year_of_contract'])
                    cost = cost_row['cost_for_season']
                    if p_id not in player_future_costs:
                        player_future_costs[p_id] = {}
                    player_future_costs[p_id][season] = cost

            for player_id_str in main_player_ids:
                player_data = player_map.get(player_id_str)
                if player_data:
                    print(f"DEBUG_TEAM_DETAILS_FULL: Processing player_id_str: {player_id_str}, Data from player_map: {player_data}")
                    
                    # Calculate years_remaining based on contract data from DB
                    years_remaining = 0
                    # Helper function to check if any contract (historical or current) is active for this player in the current_processing_year
                    def is_contract_active_this_year(p_data, current_year_int):
                        if p_data.get('contract_year') and p_data.get('duration'):
                            contract_start = int(p_data['contract_year'])
                            contract_dur = int(p_data['duration'])
                            contract_end = contract_start + contract_dur - 1
                            return contract_start <= current_year_int <= contract_end
                        return False

                    has_any_active_contract_for_current_year = is_contract_active_this_year(player_data, current_processing_year)

                    if player_data['contract_year'] and player_data['duration'] and current_processing_year > 0:
                        contract_start_year = int(player_data['contract_year'])
                        contract_duration = int(player_data['duration'])
                        contract_end_year = contract_start_year + contract_duration - 1
                        if current_processing_year < contract_start_year:
                            years_remaining = contract_duration
                        elif current_processing_year <= contract_end_year:
                            years_remaining = contract_end_year - current_processing_year + 1
                    
                    player_contract_ctx = {'status': 'default', 'recent_auction_value': None}
                    
                    # Determine eligibility for showing the contract duration dropdown
                    is_current_year_auction_acquisition = str(player_id_str) in auction_acquisitions
                    player_has_historical_contract = player_data.get('contract_year') and int(player_data['contract_year']) < current_processing_year

                    is_eligible_for_dropdown = False
                    if is_contract_setting_period_active and is_current_year_auction_acquisition:
                        if player_has_historical_contract:
                            # In 2025 auction data, but contract in DB starts < 2025 (e.g. 2024) -> MIGRATION CASE, NO DROPDOWN
                            is_eligible_for_dropdown = False
                            print(f"DEBUG_TEAM_DETAILS_FULL: Player {player_id_str} -> Has historical contract (year {player_data.get('contract_year')}), NOT eligible for dropdown despite being in current auction data.")
                        else:
                            # In 2025 auction, and no overriding historical contract from DB. Eligible for dropdown.
                            is_eligible_for_dropdown = True
                    
                    if is_eligible_for_dropdown:
                        player_contract_ctx['status'] = 'pending_setting'
                        player_contract_ctx['recent_auction_value'] = auction_acquisitions.get(str(player_id_str))
                        print(f"DEBUG_TEAM_DETAILS_FULL: Player {player_id_str} -> Set to 'pending_setting' (Eligible for duration input), auction_value: {player_contract_ctx['recent_auction_value']}")
                    elif has_any_active_contract_for_current_year: # Check if ANY contract makes them active this year
                        player_contract_ctx['status'] = 'active_contract'
                        print(f"DEBUG_TEAM_DETAILS_FULL: Player {player_id_str} -> Set to 'active_contract' (Existing contract active this year or historical)")
                    else:
                        player_contract_ctx['status'] = 'no_contract_or_expired'
                        print(f"DEBUG_TEAM_DETAILS_FULL: Player {player_id_str} -> Set to 'no_contract_or_expired'")

                    print(f"DEBUG_TEAM_DETAILS_FULL: Player {player_id_str} -> Final player_contract_ctx = {player_contract_ctx}")

                    yearly_costs_payload = {}
                    player_has_explicit_contract_costs_from_view = str(player_id_str) in player_future_costs

                    if player_has_explicit_contract_costs_from_view:
                        player_specific_yearly_data = player_future_costs[str(player_id_str)]
                        for i in range(4):
                            target_season = current_processing_year + i
                            yearly_costs_payload[target_season] = player_specific_yearly_data.get(target_season)
                        print(f"DEBUG_TEAM_DETAILS_FULL: Player {player_id_str} -> Costs from vw_contractByYear: {yearly_costs_payload}")
                    elif player_contract_ctx['status'] == 'pending_setting' and player_contract_ctx['recent_auction_value'] is not None:
                        yearly_costs_payload[current_processing_year] = player_contract_ctx['recent_auction_value']
                        for i in range(1, 4):
                            yearly_costs_payload[current_processing_year + i] = None
                        print(f"DEBUG_TEAM_DETAILS_FULL: Player {player_id_str} -> Costs for 'pending_setting': {yearly_costs_payload}")
                    else:
                        original_draft_amount_from_join = player_data.get('draft_amount')
                        if original_draft_amount_from_join is not None and original_draft_amount_from_join > 0:
                            yearly_costs_payload[current_processing_year] = original_draft_amount_from_join
                            for i in range(1, 4):
                                yearly_costs_payload[current_processing_year + i] = None
                            print(f"DEBUG_TEAM_DETAILS_FULL: Player {player_id_str} -> Costs from existing c.draft_amount: {yearly_costs_payload}")
                        else:
                            for i in range(4):
                                yearly_costs_payload[current_processing_year + i] = None
                            print(f"DEBUG_TEAM_DETAILS_FULL: Player {player_id_str} -> All costs set to None (default/no contract/no auction value): {yearly_costs_payload}")
                                
                    active_roster_players.append({
                        'id': player_data['sleeper_player_id'],
                        'name': player_data['name'],
                        'position': player_data['position'],
                        'team': player_data['nfl_team'],
                        'status': 'Active' if player_data.get('is_active', True) else 'Inactive', 
                        'draft_amount': player_data.get('draft_amount'),
                        'years_remaining': years_remaining,
                        'yearly_costs': yearly_costs_payload,
                        'player_contract_context': player_contract_ctx
                    })
                else:
                    print(f"Warning: Player ID {player_id_str} from main roster not found in detailed player fetch for team {team_id}")
        
        # Prepare taxi and reserve lists (IDs only, as per current frontend Team.jsx)
        # Frontend currently expects player objects for these lists, but it looks them up in the main `roster` array.
        # For now, let's send the full player objects if available.
        def get_player_object_for_squad(player_id_str_squad, player_map_local, squad_status_text):
            player_data_squad = player_map_local.get(str(player_id_str_squad))
            if player_data_squad:
                # Simplified logging for squad players for brevity
                squad_years_remaining = 0
                squad_has_existing_active_contract = False
                if player_data_squad.get('contract_year') and player_data_squad.get('duration') and current_processing_year > 0:
                    contract_start_year = int(player_data_squad['contract_year'])
                    contract_duration = int(player_data_squad['duration'])
                    contract_end_year = contract_start_year + contract_duration - 1
                    if current_processing_year < contract_start_year:
                        squad_years_remaining = contract_duration
                    elif current_processing_year <= contract_end_year:
                        squad_years_remaining = contract_end_year - current_processing_year + 1
                        squad_has_existing_active_contract = True
                
                squad_player_contract_ctx = {'status': 'default', 'recent_auction_value': None}
                if is_contract_setting_period_active and not squad_has_existing_active_contract:
                    squad_player_contract_ctx['status'] = 'pending_setting'
                    if str(player_id_str_squad) in auction_acquisitions:
                        squad_player_contract_ctx['recent_auction_value'] = auction_acquisitions[str(player_id_str_squad)]
                    elif squad_has_existing_active_contract:
                        squad_player_contract_ctx['status'] = 'active_contract'
                    else:
                        squad_player_contract_ctx['status'] = 'no_contract_or_expired'

                squad_yearly_costs_payload = {}
                squad_player_has_costs_from_view = str(player_id_str_squad) in player_future_costs
                if squad_player_has_costs_from_view:
                    squad_specific_yearly_data = player_future_costs[str(player_id_str_squad)]
                    for i in range(4):
                        target_season = current_processing_year + i
                        squad_yearly_costs_payload[target_season] = squad_specific_yearly_data.get(target_season)
                elif squad_player_contract_ctx['status'] == 'pending_setting' and squad_player_contract_ctx['recent_auction_value'] is not None:
                    squad_yearly_costs_payload[current_processing_year] = squad_player_contract_ctx['recent_auction_value']
                    for i in range(1, 4):
                        squad_yearly_costs_payload[current_processing_year + i] = None
                else:
                    original_draft_amount_squad = player_data_squad.get('draft_amount')
                    if original_draft_amount_squad is not None and original_draft_amount_squad > 0:
                        squad_yearly_costs_payload[current_processing_year] = original_draft_amount_squad
                        for i in range(1, 4):
                            squad_yearly_costs_payload[current_processing_year + i] = None
                    else:
                        for i in range(4):
                            squad_yearly_costs_payload[current_processing_year + i] = None
                
                return {
                    'id': player_data_squad['sleeper_player_id'],
                    'name': player_data_squad['name'],
                    'position': player_data_squad['position'],
                    'team': player_data_squad['nfl_team'],
                    'status': squad_status_text, # This is 'Reserve' or 'Taxi'
                    'draft_amount': player_data_squad.get('draft_amount'), # This is from contracts table if exists
                    'years_remaining': squad_years_remaining,
                    'yearly_costs': squad_yearly_costs_payload,
                    'player_contract_context': squad_player_contract_ctx
                }
            return None

        processed_reserve_squad = [p for p_id in reserve_player_ids if (p := get_player_object_for_squad(str(p_id), player_map, 'Reserve')) is not None]

        team_payload = {
            'name': team_name,
            'manager': {
                'name': roster_info['manager_name'],
                'sleeper_username': roster_info['sleeper_username']
            },
            'roster': active_roster_players,
            'reserve': processed_reserve_squad,
            'league_id': roster_info['sleeper_league_id'] # Add league_id here
        }

        league_context_payload = {
            'current_season_year': current_processing_year,
            'is_offseason': is_offseason,
            'is_contract_setting_period_active': is_contract_setting_period_active
        }

        print(f"DEBUG_TEAM_DETAILS_FULL: Final league_context_payload = {league_context_payload}")
        print(f"DEBUG_TEAM_DETAILS_FULL: Returning {len(team_payload['roster'])} roster players, {len(team_payload['reserve'])} reserve players.")

        return jsonify({
            'success': True, 
            'team': team_payload, 
            'league_context': league_context_payload,
            'team_position_spending_ranks': team_position_spending_ranks # Added new ranks data
        }), 200
    except sqlite3.Error as e:
        print(f"ERROR: /team/{team_id} - Database error: {str(e)}")
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        print(f"ERROR: /team/{team_id} - Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
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
        cursor.execute("""SELECT sleeper_league_id, owner_id FROM rosters WHERE sleeper_roster_id = ?""", (team_id,))
        roster_info = cursor.fetchone()
        if not roster_info:
            return jsonify({'success': False, 'error': 'Team (roster) not found'}), 404
        
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
        current_processing_year = int(current_season_data['year']) if current_season_data and current_season_data['year'] else 0
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
            
            if contract_check['duration'] != 1:
                # This is now a warning, and we skip this player, not an error for the whole batch
                warnings.append(f"Contract for player {player_id_str} on team {team_id} for season {current_processing_year} is not a 1-year default (current duration: {contract_check['duration']}). Skipped.")
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

if __name__ == '__main__':
    # Ensure global connection is initialized before app runs,
    # especially if any routes might be hit immediately or by background tasks.
    # However, get_global_db_connection() is designed to init on first call.
    # init_db() call above should have initialized it.
    app.run(debug=True, port=5000)







