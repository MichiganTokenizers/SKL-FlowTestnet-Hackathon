from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
import sqlite3, math
import os
import secrets
from pytonconnect import TonConnect
from pytonconnect.exceptions import TonConnectError

# Create Flask app instance at the top
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6')

@app.before_request
def log_cors_headers():
    print(f"Request method: {request.method}, URL: {request.url}")
    if request.method == "OPTIONS":
        print("Handling OPTIONS preflight request")

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
    if 'Access-Control-Allow-Origin' not in response.headers:
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    print(f"Response headers after modification: {response.headers}")
    return response

# Initialize the database
def init_db():
    try:
        with sqlite3.connect('keeper.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS sessions
                              (wallet_address TEXT PRIMARY KEY, session_token TEXT)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS leagues
                              (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, creator_id TEXT)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS payments
                              (id INTEGER PRIMARY KEY AUTOINCREMENT, league_id INTEGER, wallet_address TEXT,
                               transaction_hash TEXT, amount REAL, status TEXT)''')
            conn.commit()
            print("Database initialized successfully")
    except Exception as e:
        print(f"Failed to initialize database: {str(e)}")
        raise

init_db()

def get_current_season():
    """Retrieve the current season's year and in-season status."""
    conn = sqlite3.connect('keeper.db')  
    conn.row_factory = sqlite3.Row         # Allows column name access
    cursor = conn.cursor()
    cursor.execute('SELECT CurrentSeason, IsOffseason FROM Season')
    season = cursor.fetchone()             # Fetch the single row
    conn.close()
    if season:
        return {
            'year': season['CurrentSeason'],
            'is_offseason': season['IsOffseason'] == 1
        }
    return None

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
    manifest_url='https://e17b-181-214-151-64.ngrok-free.app/tonconnect-manifest.json'
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
            cursor.execute('SELECT rowid, wallet_address FROM user WHERE wallet_address = ?', (wallet_address,))
            user = cursor.fetchone()
            conn.close()
            if user:
                return {'id': user['rowid'], 'wallet_address': user['wallet_address']}
        except Exception as e:
            print(f"Error fetching user: {e}")
    return None

# TonConnect manifest route
@app.route('/tonconnect-manifest.json')
def tonconnect_manifest():
    return {
        "url": "https://e17b-181-214-151-64.ngrok-free.app",
        "name": "Supreme Keeper League",
        "iconUrl": "https://e17b-181-214-151-64.ngrok-free.app/icon.png"
    }

# TonConnect login initiation
@app.route('/login', methods=['GET'])
def initiate_login():
    if get_current_user():
        print("User already authenticated")
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
            cursor.execute('SELECT rowid, wallet_address FROM user WHERE wallet_address = ?', (address,))
            user = cursor.fetchone()
            if not user:
                cursor.execute('INSERT INTO user (wallet_address, CreatedAt) VALUES (?, datetime("now"))', (address,))
                conn.commit()
                user_id = cursor.lastrowid
            else:
                user_id = user['rowid']
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
            cursor.execute('INSERT OR REPLACE INTO sessions (wallet_address, session_token) VALUES (?, ?)',
                           (wallet_address, session_token))
            conn.commit()
            print("Successfully inserted session into database")

        return jsonify({'success': True, 'sessionToken': session_token})

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

        leagues = conn.execute('SELECT id, name, creator_id FROM leagues').fetchall()
        leagues_list = [{'id': league['id'], 'name': league['name'], 'creator_id': league['creator_id']} for league in leagues]
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
@login_required
def league():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        user = get_current_user()
        cursor.execute('''SELECT u.wallet_address, u.FirstName, l.LeagueName, COALESCE(t.TeamName, 'No Team') AS TeamName, u.LeagueID 
                         FROM User u
                         JOIN League l ON u.LeagueID = l.rowid 
                         LEFT JOIN Team t ON u.TeamID = t.rowid
                         WHERE u.rowid = ?''', (user['id'],))
        user_data = cursor.fetchmany(size=1)
        teams = []
        if user_data:
            wallet_address, first_name, league_name, team_name, league_id = user_data[0]
            cursor.execute('''SELECT t.rowid, t.TeamName, u.FirstName, u.LastName 
                             FROM Team t
                             LEFT JOIN User u ON t.UserID = u.rowid
                             WHERE t.LeagueID = ?
                             ORDER BY t.TeamName''', (str(league_id),))
            teams = cursor.fetchall()
        else:
            wallet_address = "Unknown"
            first_name = "Unknown"
            league_name = "Unknown"
            team_name = "Unknown"
            league_id = None
            print("No user data found for ID:", user['id'])
        conn.close()    
    except Exception as e:
        print(f"Error fetching data: {e}")
        wallet_address = "Error fetching wallet address"
        first_name = "Error"
        league_name = "Error"
        team_name = "Error"
        teams = []
        if 'conn' in locals():
            conn.close()
    print(f"Template variables: wallet_address={wallet_address}, first_name={first_name}, league_name={league_name}, team_name={team_name}, teams={teams}")
    return render_template('league.html', 
                         wallet_address=wallet_address, 
                         first_name=first_name, 
                         league_name=league_name, 
                         team_name=team_name, 
                         teams=teams)

# Team page route
@app.route('/team/<int:team_id>')
@login_required
def team(team_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch CurrentYear from Season
        cursor.execute('SELECT CurrentSeason FROM Season LIMIT 1')
        current_year = cursor.fetchone()['CurrentSeason']

        # Fetch team details
        cursor.execute('SELECT UserId, TeamName, Abbr FROM Team WHERE rowid = ?', (team_id,))
        team_data = cursor.fetchone()

        # Fetch manager
        cursor.execute('''SELECT u.FirstName, u.LastName 
                          FROM User u 
                          WHERE u.rowid = (SELECT UserID FROM Team WHERE rowid = ?)''', (team_id,))
        manager = cursor.fetchone()

        # Fetch active players with contract projections
        cursor.execute('''SELECT c.PlayerId, p.PlayerName, p.Position, c.DraftAmount, c.ContractYear, c.Duration,
                         v.year_''' + str(current_year) + ''', 
                         v.year_''' + str(current_year + 1) + ''', 
                         v.year_''' + str(current_year + 2) + ''', 
                         v.year_''' + str(current_year + 3) + ''' 
                  FROM Contract c
                  JOIN Player p ON c.PlayerId = p.rowid
                  JOIN contract_year_view v ON c.rowid = v.rowid
                  WHERE c.TeamId = ? AND c.IsActive = 1
                  ORDER BY COALESCE(c.DraftAmount, 0) DESC''', (team_id,))
        players = cursor.fetchall()

        conn.close()

        if team_data:
            team_name = team_data['TeamName']
            team_abbr = team_data['Abbr'] or 'N/A'
        else:
            team_name = "Unknown Team"
            team_abbr = "N/A"
            manager = None
            players = []
            print(f"No team found for team_id: {team_id}")
    except Exception as e:
        print(f"Error fetching team data: {e}")
        team_name = "Error fetching team"
        team_abbr = "N/A"
        manager = None
        players = []
        if 'conn' in locals():
            conn.close()
    print(f"Team data: team_id={team_id}, team_name={team_name}, team_abbr={team_abbr}, manager={manager}, players={players}")

    user = get_current_user()
    is_owner = team_data['UserId'] == user['id']
    
    return render_template('team.html', 
                          team_name=team_name, 
                          team_abbr=team_abbr, 
                          manager=manager, 
                          players=players,
                          current_year=current_year,
                          is_owner=is_owner)

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

if __name__ == '__main__':
    app.run(debug=True)