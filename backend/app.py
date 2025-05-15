from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
import sqlite3, math
import os
import secrets
from pytonconnect import TonConnect
from pytonconnect.exceptions import TonConnectError
from sleeper_service import SleeperService
import json

# Create Flask app instance at the top
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6')

# Initialize SleeperService
sleeper_service = SleeperService()

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
        with sqlite3.connect('keeper.db') as conn:
            cursor = conn.cursor()
            
            if force_create:
                print("Forcing recreation of all tables...")
                # Drop existing tables
                tables = ["sessions", "leagues", "users", "players", "rosters", 
                          "contracts", "transactions", "traded_picks", "drafts"]
                for table in tables:
                    try:
                        cursor.execute(f"DROP TABLE IF EXISTS {table}")
                        print(f"Dropped table {table}")
                    except Exception as e:
                        print(f"Error dropping table {table}: {str(e)}")
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS sessions
                              (wallet_address TEXT PRIMARY KEY, session_token TEXT)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS leagues
                              (sleeper_user_id TEXT,
                               sleeper_league_id TEXT,
                               created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                               updated_at DATETIME
                               )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS users
                              (sleeper_user_id TEXT UNIQUE,
                               username TEXT,
                               wallet_address TEXT UNIQUE,
                               created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                               updated_at DATETIME)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS players
                              (sleeper_player_id TEXT UNIQUE,
                               name TEXT,
                               position TEXT,
                               team TEXT,
                               created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                               updated_at DATETIME)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS rosters
                              (sleeper_roster_id TEXT,
                               league_id TEXT,
                               owner_id TEXT,
                               players TEXT,
                               settings TEXT,
                               metadata TEXT,
                               created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                               updated_at DATETIME)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS contracts
                              (player_id INTEGER,
                               team_id INTEGER,
                               draft_amount REAL,
                               contract_year INTEGER,
                               duration INTEGER,
                               is_active BOOLEAN DEFAULT 1,
                               penalty_incurred REAL,
                               penalty_year INTEGER,
                               created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                               updated_at DATETIME)''')
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
                               league_id INTEGER,
                               status TEXT,
                               start_time DATETIME,
                               data TEXT,
                               created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                               updated_at DATETIME)''')
            
            conn.commit()
            print("Database initialized successfully")
    except Exception as e:
        print(f"Failed to initialize database: {str(e)}")
        raise

init_db()

def get_current_season():
    """Retrieve the current season's year and in-season status from the season_curr table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT current_year, IsOffSeason FROM season_curr LIMIT 1')
        season_data = cursor.fetchone()
        conn.close()
        
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
    manifest_url=' https://c724-193-43-135-218.ngrok-free.app/tonconnect-manifest.json'
)

# Database connection
def get_db_connection():
    try:
        conn = sqlite3.connect('keeper.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

# Helper function to get current user from session
def get_current_user():
    wallet_address = session.get('wallet_address')
    if wallet_address:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT username, wallet_address FROM users WHERE wallet_address = ?', (wallet_address,))
            user = cursor.fetchone()
            conn.close()
            if user:
                return {'username': user['username'], 'wallet_address': user['wallet_address']}
        except Exception as e:
            print(f"Error fetching user: {e}")
    return None

# TonConnect manifest route
@app.route('/tonconnect-manifest.json')
def tonconnect_manifest():
    return {
        "url": " https://c724-193-43-135-218.ngrok-free.app",
        "name": "Supreme Keeper League",
        "iconUrl": " https://c724-193-43-135-218.ngrok-free.app/static/icon.png"
    }

# TonConnect login initiation
@app.route('/login', methods=['GET'])
def initiate_login():
    if get_current_user():
        user = get_current_user()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT sleeper_user_id FROM users WHERE wallet_address = ?', (user['wallet_address'],))
        result = cursor.fetchone()
        conn.close()
        if result and result['sleeper_user_id']:
            print("User already authenticated and associated with Sleeper")
            # Fetch user's leagues
            cursor = conn.cursor()
            cursor.execute('SELECT sleeper_league_id FROM leagues WHERE sleeper_user_id = ?', (result['sleeper_user_id'],))
            leagues = cursor.fetchall()
            conn.close()
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
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT wallet_address FROM users WHERE wallet_address = ?', (address,))
            user = cursor.fetchone()
            if not user:
                cursor.execute('INSERT INTO users (wallet_address, CreatedAt) VALUES (?, datetime("now"))', (address,))
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

        with sqlite3.connect('keeper.db') as conn:
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute('SELECT wallet_address FROM users WHERE wallet_address = ?', (wallet_address,))
            user = cursor.fetchone()
            is_new_user = not user

            if is_new_user:
                # Create new user
                cursor.execute('''
                    INSERT INTO users (
                        wallet_address,
                        created_at
                    ) VALUES (?, datetime("now"))''',
                    (wallet_address,)
                )
                print("Created new user")

            else:
                # For existing users, trigger a full data pull from Sleeper
                print("Existing user detected, triggering full Sleeper data pull")
                full_data_response = sleeper_service.fetch_all_data(wallet_address)
                if not full_data_response['success']:
                    print(f"Failed to fetch full Sleeper data: {full_data_response.get('error', 'Unknown error')}")

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

    with sqlite3.connect('keeper.db') as conn:
        conn.row_factory = sqlite3.Row
        session_data = conn.execute('SELECT wallet_address FROM sessions WHERE session_token = ?', (session_token,)).fetchone()
        if not session_data:
            return jsonify({'success': False, 'error': 'Invalid session'}), 401

        return jsonify({'success': True, 'walletAddress': session_data['wallet_address']})

# Leagues route
@app.route('/leagues', methods=['GET'])
def get_leagues():
    session_token = request.headers.get('Authorization')
    if not session_token:
        return jsonify({'success': False, 'error': 'No session token'}), 401

    with sqlite3.connect('keeper.db') as conn:
        conn.row_factory = sqlite3.Row
        session_data = conn.execute('SELECT wallet_address FROM sessions WHERE session_token = ?', (session_token,)).fetchone()
        if not session_data:
            return jsonify({'success': False, 'error': 'Invalid session'}), 401

        leagues = conn.execute('SELECT sleeper_user_id, sleeper_league_id FROM leagues').fetchall()
        leagues_list = [{'sleeper_user_id': league['sleeper_user_id'], 'sleeper_league_id': league['sleeper_league_id']} for league in leagues]
        return jsonify({'success': True, 'leagues': leagues_list})

# Logout route
@app.route('/logout')
def logout():
    session.pop('wallet_address', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('initiate_login'))

# Decorator for protected routes
def login_required(f):
    def wrap(*args, **kwargs):
        if not get_current_user():
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('initiate_login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

# League page route
@app.route('/league')
def get_league():
    session_token = request.headers.get('Authorization')
    if not session_token:
        return jsonify({'success': False, 'error': 'No session token'}), 401
    
    try:
        db = KeeperDB()
        with sqlite3.connect('keeper.db') as conn:
            cursor = conn.cursor()
            
            # Get user from session
            cursor.execute('SELECT wallet_address FROM sessions WHERE session_token = ?', (session_token,))
            session_data = cursor.fetchone()
            if not session_data:
                return jsonify({'success': False, 'error': 'Invalid session'}), 401
            
            wallet_address = session_data[0]
            
            # Get league data from local database
            league_data = db.get_league_data(wallet_address)
            
            if not league_data:
                return jsonify({'success': False, 'error': 'No league data found'}), 404
            
            return jsonify({'success': True, 'league': league_data})
    except Exception as e:
        print(f"Error in /league: {str(e)}")
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

# Waive player route
@app.route('/waive_player', methods=['POST'])
@login_required
def waive_player():
    conn = None
    try:
        conn = get_db_connection()
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
    finally:
        if conn:
            conn.close()

    return redirect(url_for('team', team_id=team_id))

# League connection route
@app.route('/league/connect', methods=['POST'])
def connect_league():
    data = request.get_json()
    league_id = data.get('leagueId')
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
        with sqlite3.connect('keeper.db') as conn:
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
        with sqlite3.connect('keeper.db') as conn:
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
def fetch_all_data():
    session_token = request.headers.get('Authorization')
    if not session_token:
        return jsonify({'success': False, 'error': 'No session token'}), 401
    
    try:
        print(f"DEBUG: Processing /sleeper/fetchAll request, method: {request.method}")
        print(f"DEBUG: Headers: {request.headers}")
        
        with sqlite3.connect('keeper.db') as conn:
            cursor = conn.cursor()
            
            # Get user from session
            cursor.execute('SELECT wallet_address FROM sessions WHERE session_token = ?', (session_token,))
            session_data = cursor.fetchone()
            if not session_data:
                print("DEBUG: Invalid session token")
                return jsonify({'success': False, 'error': 'Invalid session'}), 401
            
            wallet_address = session_data[0]
            print(f"DEBUG: Wallet address: {wallet_address}")
            
            # Trigger full data pull
            print("DEBUG: Calling sleeper_service.fetch_all_data()")
            result = sleeper_service.fetch_all_data(wallet_address)
            print(f"DEBUG: Result from fetch_all_data: {result}")
            
            if not result.get('success', False):
                print(f"DEBUG: fetch_all_data failed: {result.get('error', 'Unknown error')}")
                return jsonify(result), 500
            
            return jsonify({'success': True, 'message': 'Full data pull triggered successfully'})
    except Exception as e:
        print(f"ERROR in /sleeper/fetchAll: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

# League local data route
@app.route('/league/local', methods=['GET'])
def get_league_local():
    session_token = request.headers.get('Authorization')
    if not session_token:
        return jsonify({'success': False, 'error': 'No session token'}), 401
    
    try:
        with sqlite3.connect('keeper.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get user from session
            cursor.execute('SELECT wallet_address FROM sessions WHERE session_token = ?', (session_token,))
            session_data = cursor.fetchone()
            if not session_data:
                return jsonify({'success': False, 'error': 'Invalid session'}), 401
            
            wallet_address = session_data[0]
            
            # Get user's sleeper_user_id
            cursor.execute('SELECT sleeper_user_id FROM users WHERE wallet_address = ?', (wallet_address,))
            user_data = cursor.fetchone()
            if not user_data or not user_data['sleeper_user_id']:
                return jsonify({'success': False, 'error': 'No Sleeper account associated with this wallet'}), 404
            
            sleeper_user_id = user_data['sleeper_user_id']
            
            # Get leagues for this user
            cursor.execute('''
                SELECT l.*, u.display_name as owner_name
                FROM leagues l
                LEFT JOIN users u ON l.sleeper_user_id = u.sleeper_user_id
                WHERE l.sleeper_user_id = ?
            ''', (sleeper_user_id,))
            leagues = cursor.fetchall()
            
            if not leagues:
                return jsonify({'success': False, 'error': 'No leagues found for this user'}), 404
            
            # Convert leagues to dictionary
            league_list = []
            for league in leagues:
                league_dict = dict(league)
                
                # Get rosters for this league
                cursor.execute('''
                    SELECT r.*, u.display_name, u.avatar
                    FROM rosters r
                    LEFT JOIN users u ON r.owner_id = u.sleeper_user_id
                    WHERE r.league_id = ?
                ''', (league['sleeper_league_id'],))
                rosters = cursor.fetchall()
                
                # Convert rosters to list of dictionaries
                roster_list = []
                for roster in rosters:
                    roster_dict = dict(roster)
                    # Parse JSON fields
                    for field in ['players', 'settings', 'metadata']:
                        if roster_dict.get(field) and isinstance(roster_dict[field], str):
                            try:
                                roster_dict[field] = json.loads(roster_dict[field])
                            except:
                                roster_dict[field] = {}
                    roster_list.append(roster_dict)
                
                league_dict['rosters'] = roster_list
                
                # Parse league settings if stored as JSON
                if league_dict.get('settings') and isinstance(league_dict['settings'], str):
                    try:
                        league_dict['settings'] = json.loads(league_dict['settings'])
                    except:
                        league_dict['settings'] = {}
                
                league_list.append(league_dict)
            
            return jsonify({
                'success': True,
                'leagues': league_list
            })
    except Exception as e:
        print(f"Error in /league/local: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

# League standings local data route
@app.route('/league/standings/local', methods=['GET'])
def get_league_standings_local():
    session_token = request.headers.get('Authorization')
    if not session_token:
        return jsonify({'success': False, 'error': 'No session token'}), 401
    
    try:
        with sqlite3.connect('keeper.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get user from session
            cursor.execute('SELECT wallet_address FROM sessions WHERE session_token = ?', (session_token,))
            session_data = cursor.fetchone()
            if not session_data:
                return jsonify({'success': False, 'error': 'Invalid session'}), 401
            
            wallet_address = session_data[0]
            
            # Get user's sleeper_user_id
            cursor.execute('SELECT sleeper_user_id FROM users WHERE wallet_address = ?', (wallet_address,))
            user_data = cursor.fetchone()
            if not user_data or not user_data['sleeper_user_id']:
                return jsonify({'success': False, 'error': 'No Sleeper account associated with this wallet'}), 404
            
            sleeper_user_id = user_data['sleeper_user_id']
            
            # Get leagues for this user
            cursor.execute('''
                SELECT sleeper_league_id
                FROM leagues
                WHERE sleeper_user_id = ?
            ''', (sleeper_user_id,))
            leagues = cursor.fetchall()
            
            if not leagues:
                return jsonify({'success': False, 'error': 'No leagues found for this user'}), 404
            
            # Use first league found for now (can be expanded to handle multiple leagues)
            league_id = leagues[0]['sleeper_league_id']
            
            # Get all rosters with standings data for this league
            cursor.execute('''
                SELECT r.*, u.display_name, u.avatar 
                FROM rosters r
                LEFT JOIN users u ON r.owner_id = u.sleeper_user_id
                WHERE r.league_id = ?
            ''', (league_id,))
            rosters = cursor.fetchall()
            
            # Modified: Return empty standings with success status if no rosters found
            if not rosters:
                return jsonify({
                    'success': True,
                    'league_id': league_id,
                    'standings': [],
                    'message': 'No standings data available yet for this league'
                })
            
            # Process roster data to create standings
            standings = []
            for roster in rosters:
                roster_dict = dict(roster)
                
                # Parse JSON fields if they're stored as strings
                if roster_dict.get('settings') and isinstance(roster_dict['settings'], str):
                    try:
                        settings = json.loads(roster_dict['settings'])
                        # Extract win/loss data from settings
                        wins = settings.get('wins', 0)
                        losses = settings.get('losses', 0)
                        ties = settings.get('ties', 0)
                        fpts = settings.get('fpts', 0)
                        fpts_against = settings.get('fpts_against', 0)
                    except:
                        wins = losses = ties = fpts = fpts_against = 0
                else:
                    # If settings is already a dict or is None
                    settings = roster_dict.get('settings', {}) or {}
                    wins = settings.get('wins', 0)
                    losses = settings.get('losses', 0)
                    ties = settings.get('ties', 0)
                    fpts = settings.get('fpts', 0)
                    fpts_against = settings.get('fpts_against', 0)
                
                # Create standings entry
                standings.append({
                    'roster_id': roster_dict.get('sleeper_roster_id'),
                    'owner_id': roster_dict.get('owner_id'),
                    'display_name': roster_dict.get('display_name', 'Unknown Manager'),
                    'avatar': roster_dict.get('avatar'),
                    'wins': wins,
                    'losses': losses,
                    'ties': ties,
                    'fpts': fpts,
                    'fpts_against': fpts_against,
                    'record': f"{wins}-{losses}" + (f"-{ties}" if ties > 0 else ""),
                    'win_pct': (wins + (ties * 0.5)) / max(1, (wins + losses + ties))
                })
            
            # Sort standings by win percentage, then by points
            standings.sort(key=lambda x: (-x['win_pct'], -x['fpts']))
            
            return jsonify({
                'success': True,
                'league_id': league_id,
                'standings': standings
            })
    except Exception as e:
        print(f"Error in /league/standings/local: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

# Sleeper user search endpoint
@app.route('/sleeper/search', methods=['GET'])
def search_sleeper_user():
    session_token = request.headers.get('Authorization')
    if not session_token:
        return jsonify({'success': False, 'error': 'No session token'}), 401
    
    try:
        # Verify session
        with sqlite3.connect('keeper.db') as conn:
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
        with sqlite3.connect('keeper.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT wallet_address FROM sessions WHERE session_token = ?', (session_token,))
            session_data = cursor.fetchone()
            
            if not session_data:
                return jsonify({'success': False, 'error': 'Invalid session'}), 401
            
            wallet_address = session_data['wallet_address']
            
            # Check if wallet address is already associated with a Sleeper account
            cursor.execute('SELECT sleeper_user_id FROM users WHERE wallet_address = ?', (wallet_address,))
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
def complete_association():
    session_token = request.headers.get('Authorization')
    if not session_token:
        return jsonify({'success': False, 'error': 'No session token'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request data'}), 400
        
        sleeper_user_id = data.get('sleeper_user_id')
        sleeper_username = data.get('sleeper_username')
        sleeper_display_name = data.get('sleeper_display_name')
        sleeper_avatar = data.get('sleeper_avatar')
        league_id = data.get('league_id')
        
        if not sleeper_user_id or not league_id:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Get wallet address from session
        with sqlite3.connect('keeper.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT wallet_address FROM sessions WHERE session_token = ?', (session_token,))
            session_data = cursor.fetchone()
            
            if not session_data:
                return jsonify({'success': False, 'error': 'Invalid session'}), 401
            
            wallet_address = session_data['wallet_address']
            
            # Update user record with Sleeper information
            cursor.execute('''
                UPDATE users
                SET sleeper_user_id = ?,
                    username = ?,
                    display_name = ?,
                    avatar = ?,
                    updated_at = datetime("now")
                WHERE wallet_address = ?
            ''', (sleeper_user_id, sleeper_username, sleeper_display_name, sleeper_avatar, wallet_address))
            
            # Add league association if it doesn't exist
            cursor.execute('''
                INSERT OR IGNORE INTO leagues (
                    sleeper_league_id,
                    sleeper_user_id,
                    created_at,
                    updated_at
                ) VALUES (?, ?, datetime("now"), datetime("now"))
            ''', (league_id, sleeper_user_id))
            
            conn.commit()
            
            # Trigger data pull from Sleeper API
            sleeper_service.fetch_all_data(wallet_address)
            
            return jsonify({
                'success': True,
                'message': 'Sleeper account association completed successfully'
            })
            
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
        with sqlite3.connect('keeper.db') as conn:
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
        with sqlite3.connect('keeper.db') as conn:
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
        with sqlite3.connect('keeper.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT wallet_address FROM sessions WHERE session_token = ?', (session_token,))
            session_data = cursor.fetchone()
            
            if not session_data:
                return jsonify({'success': False, 'error': 'Invalid session'}), 401
            
            # Get current settings
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)







