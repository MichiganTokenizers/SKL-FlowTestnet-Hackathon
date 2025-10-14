"""
SKL Admin Dashboard API Routes
"""
from flask import jsonify, request
from functools import wraps
import sqlite3
from datetime import datetime
import json
import uuid

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get wallet address from header or session token
        wallet_address = request.headers.get('X-Wallet-Address')

        # If not in header, try to get from session token
        if not wallet_address:
            auth_header = request.headers.get('Authorization')
            if auth_header:
                # Handle both "Bearer <token>" and direct token formats
                token = auth_header.split(' ', 1)[1] if auth_header.startswith('Bearer ') else auth_header
                try:
                    conn = sqlite3.connect('keeper.db')
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT wallet_address FROM sessions WHERE session_token = ?", (token,))
                    session_data = cursor.fetchone()
                    if session_data:
                        wallet_address = session_data['wallet_address']
                    conn.close()
                except Exception as e:
                    print(f"Error getting wallet from session in decorator: {e}")

        if not wallet_address:
            return jsonify({'success': False, 'error': 'Unauthorized - No wallet address'}), 401

        # Check if user is admin
        try:
            conn = sqlite3.connect('keeper.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM AdminUsers WHERE wallet_address = ?", (wallet_address,))
            admin = cursor.fetchone()
            conn.close()

            if not admin:
                return jsonify({'success': False, 'error': f'Admin access required for wallet {wallet_address}'}), 403

            # Store admin info in request context
            request.admin_role = admin['role']
            request.admin_wallet = wallet_address

        except Exception as e:
            return jsonify({'success': False, 'error': f'Auth error: {str(e)}'}), 500

        return f(*args, **kwargs)
    return decorated_function

def register_admin_routes(app):
    """Register all admin API routes"""

    @app.route('/admin/verify', methods=['GET'])
    def admin_verify():
        """Check if current user is admin"""
        # Try to get wallet from header first
        wallet_address = request.headers.get('X-Wallet-Address')

        # If not in header, try to get from session token
        if not wallet_address:
            auth_header = request.headers.get('Authorization')
            if auth_header:
                # Handle both "Bearer <token>" and direct token formats
                token = auth_header.split(' ', 1)[1] if auth_header.startswith('Bearer ') else auth_header
                try:
                    conn = sqlite3.connect('keeper.db')
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT wallet_address FROM sessions WHERE session_token = ?", (token,))
                    session_data = cursor.fetchone()
                    if session_data:
                        wallet_address = session_data['wallet_address']
                    conn.close()
                except Exception as e:
                    print(f"Error getting wallet from session: {e}")

        if not wallet_address:
            return jsonify({'is_admin': False, 'wallet_address': None})

        try:
            conn = sqlite3.connect('keeper.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM AdminUsers WHERE wallet_address = ?", (wallet_address,))
            admin = cursor.fetchone()
            conn.close()

            if admin:
                return jsonify({'is_admin': True, 'role': admin['role'], 'wallet_address': wallet_address})
            else:
                return jsonify({'is_admin': False, 'wallet_address': wallet_address})
        except Exception as e:
            return jsonify({'is_admin': False, 'error': str(e), 'wallet_address': wallet_address})

    @app.route('/admin/dashboard/stats', methods=['GET'])
    @admin_required
    def admin_dashboard_stats():
        """Get high-level dashboard statistics"""
        try:
            conn = sqlite3.connect('keeper.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Total leagues
            cursor.execute("SELECT COUNT(*) as count FROM LeagueMetadata WHERE name LIKE 'SKL%'")
            total_leagues = cursor.fetchone()['count']

            # Total fees due and collected
            cursor.execute("""
                SELECT
                    SUM(lf.fee_amount) as total_due,
                    SUM(ull.fee_paid_amount) as total_collected
                FROM LeagueFees lf
                LEFT JOIN UserLeagueLinks ull ON lf.sleeper_league_id = ull.sleeper_league_id
            """)
            fees = cursor.fetchone()

            # Active agents
            cursor.execute("SELECT COUNT(*) as count FROM AgentExecutions WHERE status IN ('scheduled', 'running')")
            active_agents = cursor.fetchone()['count']

            # Pending payouts
            cursor.execute("SELECT COUNT(*) as count FROM PayoutSchedules WHERE payout_status = 'pending'")
            pending_payouts = cursor.fetchone()['count']

            # Total yield earned
            cursor.execute("SELECT SUM(yield_earned) as total_yield FROM YieldVaults WHERE status = 'active'")
            total_yield_row = cursor.fetchone()
            total_yield = total_yield_row['total_yield'] if total_yield_row['total_yield'] else 0.0

            # Active vaults
            cursor.execute("SELECT COUNT(*) as count FROM YieldVaults WHERE status = 'active'")
            active_vaults = cursor.fetchone()['count']

            conn.close()

            return jsonify({
                'success': True,
                'stats': {
                    'total_leagues': total_leagues,
                    'total_fees_due': fees['total_due'] or 0.0,
                    'total_fees_collected': fees['total_collected'] or 0.0,
                    'active_agents': active_agents,
                    'pending_payouts': pending_payouts,
                    'total_yield_earned': total_yield,
                    'active_vaults': active_vaults
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/admin/leagues', methods=['GET'])
    @admin_required
    def admin_get_all_leagues():
        """Get all SKL leagues with fee status"""
        try:
            conn = sqlite3.connect('keeper.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    lm.sleeper_league_id,
                    lm.name,
                    lm.season,
                    lm.status,
                    lf.fee_amount,
                    lf.fee_currency,
                    lf.fee_due_date,
                    lf.collection_deadline,
                    lf.yield_vault_id,
                    lf.automated,
                    fs.collection_status,
                    fs.total_collected,
                    (SELECT COUNT(DISTINCT sleeper_roster_id) FROM rosters WHERE sleeper_league_id = lm.sleeper_league_id) as total_teams,
                    (SELECT COUNT(DISTINCT wallet_address) FROM LeaguePayments WHERE sleeper_league_id = lm.sleeper_league_id AND season_year = lm.season) as teams_paid
                FROM LeagueMetadata lm
                LEFT JOIN LeagueFees lf ON lm.sleeper_league_id = lf.sleeper_league_id
                LEFT JOIN FeeSchedules fs ON lm.sleeper_league_id = fs.sleeper_league_id
                WHERE lm.name LIKE 'SKL%'
                ORDER BY lm.season DESC, lm.name
            """)

            leagues = []
            for row in cursor.fetchall():
                leagues.append(dict(row))

            conn.close()

            return jsonify({'success': True, 'leagues': leagues})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/admin/league/<league_id>/fees', methods=['GET', 'POST'])
    @admin_required
    def admin_manage_league_fees(league_id):
        """View/update fee schedules for a league"""
        try:
            conn = sqlite3.connect('keeper.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if request.method == 'GET':
                # Get fee schedule details
                cursor.execute("""
                    SELECT
                        lf.*,
                        fs.schedule_id,
                        fs.due_date,
                        fs.collection_status,
                        fs.total_expected,
                        fs.total_collected,
                        fs.agent_id,
                        fs.agent_status
                    FROM LeagueFees lf
                    LEFT JOIN FeeSchedules fs ON lf.sleeper_league_id = fs.sleeper_league_id
                    WHERE lf.sleeper_league_id = ?
                """, (league_id,))

                fee_data = cursor.fetchone()
                if fee_data:
                    result = dict(fee_data)
                else:
                    result = None

                conn.close()
                return jsonify({'success': True, 'fees': result})

            elif request.method == 'POST':
                # Update fee schedule
                data = request.json
                season_year = data.get('season_year', 2025)
                fee_amount = data.get('fee_amount')
                fee_due_date = data.get('fee_due_date')
                collection_deadline = data.get('collection_deadline')
                automated = data.get('automated', 0)

                # Update LeagueFees
                cursor.execute("""
                    INSERT INTO LeagueFees (sleeper_league_id, season_year, fee_amount, fee_due_date, collection_deadline, automated, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(sleeper_league_id, season_year)
                    DO UPDATE SET fee_amount=?, fee_due_date=?, collection_deadline=?, automated=?, updated_at=?
                """, (league_id, season_year, fee_amount, fee_due_date, collection_deadline, automated, datetime.now().isoformat(),
                      fee_amount, fee_due_date, collection_deadline, automated, datetime.now().isoformat()))

                # Create FeeSchedule if automated
                if automated and collection_deadline:
                    schedule_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT OR IGNORE INTO FeeSchedules (schedule_id, sleeper_league_id, season_year, due_date, total_expected, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (schedule_id, league_id, season_year, collection_deadline, fee_amount, datetime.now().isoformat()))

                conn.commit()
                conn.close()

                return jsonify({'success': True, 'message': 'Fee schedule updated'})

        except Exception as e:
            if conn:
                conn.close()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/admin/fees/overview', methods=['GET'])
    @admin_required
    def admin_fees_overview():
        """Overview of all fee collection across leagues"""
        try:
            conn = sqlite3.connect('keeper.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # By league
            cursor.execute("""
                SELECT
                    lm.name,
                    lm.sleeper_league_id,
                    fs.collection_status,
                    fs.total_expected,
                    fs.total_collected,
                    fs.due_date
                FROM FeeSchedules fs
                JOIN LeagueMetadata lm ON fs.sleeper_league_id = lm.sleeper_league_id
                ORDER BY fs.due_date ASC
            """)
            by_league = [dict(row) for row in cursor.fetchall()]

            # By status
            cursor.execute("""
                SELECT collection_status, COUNT(*) as count
                FROM FeeSchedules
                GROUP BY collection_status
            """)
            by_status = {row['collection_status']: row['count'] for row in cursor.fetchall()}

            # Upcoming deadlines (next 30 days)
            cursor.execute("""
                SELECT
                    lm.name,
                    fs.due_date,
                    fs.collection_status,
                    fs.total_collected,
                    fs.total_expected
                FROM FeeSchedules fs
                JOIN LeagueMetadata lm ON fs.sleeper_league_id = lm.sleeper_league_id
                WHERE fs.due_date >= date('now') AND fs.due_date <= date('now', '+30 days')
                ORDER BY fs.due_date ASC
            """)
            upcoming_deadlines = [dict(row) for row in cursor.fetchall()]

            conn.close()

            return jsonify({
                'success': True,
                'overview': {
                    'by_league': by_league,
                    'by_status': by_status,
                    'upcoming_deadlines': upcoming_deadlines
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/admin/agents', methods=['GET'])
    @admin_required
    def admin_list_agents():
        """List all active agents with status"""
        try:
            conn = sqlite3.connect('keeper.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    ae.execution_id,
                    ae.agent_type,
                    ae.sleeper_league_id,
                    ae.season_year,
                    ae.status,
                    ae.trigger_time,
                    ae.execution_time,
                    ae.error_message,
                    lm.name as league_name
                FROM AgentExecutions ae
                LEFT JOIN LeagueMetadata lm ON ae.sleeper_league_id = lm.sleeper_league_id
                ORDER BY ae.created_at DESC
                LIMIT 50
            """)

            agents = [dict(row) for row in cursor.fetchall()]

            # Group by type
            fee_collection = [a for a in agents if a['agent_type'] == 'fee_collection']
            yield_management = [a for a in agents if a['agent_type'] == 'yield_deposit']
            payout_agents = [a for a in agents if a['agent_type'] == 'payout_distribution']

            conn.close()

            return jsonify({
                'success': True,
                'agents': {
                    'fee_collection_agents': fee_collection,
                    'yield_management_agents': yield_management,
                    'payout_agents': payout_agents
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/admin/vaults', methods=['GET'])
    @admin_required
    def admin_list_vaults():
        """List all active yield vaults"""
        try:
            conn = sqlite3.connect('keeper.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    yv.*,
                    lm.name as league_name
                FROM YieldVaults yv
                LEFT JOIN LeagueMetadata lm ON yv.sleeper_league_id = lm.sleeper_league_id
                ORDER BY yv.created_at DESC
            """)

            vaults = [dict(row) for row in cursor.fetchall()]

            # Calculate totals
            total_deposited = sum(v['principal_amount'] for v in vaults if v['status'] == 'active')
            total_yield = sum(v['yield_earned'] or 0.0 for v in vaults if v['status'] == 'active')

            # Group by protocol
            by_protocol = {}
            for vault in vaults:
                protocol = vault['vault_protocol']
                if protocol not in by_protocol:
                    by_protocol[protocol] = []
                by_protocol[protocol].append(vault)

            conn.close()

            return jsonify({
                'success': True,
                'vaults': {
                    'active_vaults': vaults,
                    'total_deposited': total_deposited,
                    'total_yield': total_yield,
                    'by_protocol': by_protocol
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/admin/payouts', methods=['GET'])
    @admin_required
    def admin_list_payouts():
        """List all scheduled/completed payouts"""
        try:
            conn = sqlite3.connect('keeper.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    ps.*,
                    lm.name as league_name
                FROM PayoutSchedules ps
                LEFT JOIN LeagueMetadata lm ON ps.sleeper_league_id = lm.sleeper_league_id
                ORDER BY ps.payout_date DESC
            """)

            all_payouts = [dict(row) for row in cursor.fetchall()]

            # Categorize
            pending = [p for p in all_payouts if p['payout_status'] == 'pending']
            upcoming = [p for p in all_payouts if p['payout_status'] in ('pending', 'ready')]
            completed = [p for p in all_payouts if p['payout_status'] == 'completed']

            conn.close()

            return jsonify({
                'success': True,
                'payouts': {
                    'pending': pending,
                    'upcoming': upcoming,
                    'completed': completed
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/admin/league/<league_id>/playoff-bracket/sync', methods=['POST'])
    @admin_required
    def sync_playoff_bracket(league_id):
        """Fetch playoff bracket from Sleeper API and store in database"""
        try:
            import requests

            data = request.json
            season_year = data.get('season_year', 2025)

            # Fetch winners bracket from Sleeper API
            winners_url = f"https://api.sleeper.app/v1/league/{league_id}/winners_bracket"
            losers_url = f"https://api.sleeper.app/v1/league/{league_id}/losers_bracket"

            winners_response = requests.get(winners_url)
            losers_response = requests.get(losers_url)

            if winners_response.status_code != 200:
                return jsonify({'success': False, 'error': f'Failed to fetch winners bracket: {winners_response.status_code}'}), 500

            winners_bracket = winners_response.json()
            losers_bracket = losers_response.json() if losers_response.status_code == 200 else []

            conn = sqlite3.connect('keeper.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Store raw bracket data
            winners_bracket_id = f"{league_id}_{season_year}_winners"
            cursor.execute("""
                INSERT OR REPLACE INTO PlayoffBrackets (bracket_id, sleeper_league_id, season_year, bracket_type, bracket_data, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (winners_bracket_id, league_id, season_year, 'winners_bracket', json.dumps(winners_bracket), datetime.now().isoformat()))

            if losers_bracket:
                losers_bracket_id = f"{league_id}_{season_year}_losers"
                cursor.execute("""
                    INSERT OR REPLACE INTO PlayoffBrackets (bracket_id, sleeper_league_id, season_year, bracket_type, bracket_data, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (losers_bracket_id, league_id, season_year, 'losers_bracket', json.dumps(losers_bracket), datetime.now().isoformat()))

            # Parse and store individual matchups
            for matchup in winners_bracket:
                matchup_id = f"{league_id}_{season_year}_W_R{matchup.get('r')}_M{matchup.get('m')}"
                cursor.execute("""
                    INSERT OR REPLACE INTO PlayoffMatchups (
                        matchup_id, sleeper_league_id, season_year, bracket_type, round_number, match_number,
                        team1_roster_id, team2_roster_id, winner_roster_id, loser_roster_id,
                        team1_from_match, team2_from_match, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    matchup_id, league_id, season_year, 'winners_bracket',
                    matchup.get('r'), matchup.get('m'),
                    str(matchup.get('t1')) if matchup.get('t1') else None,
                    str(matchup.get('t2')) if matchup.get('t2') else None,
                    str(matchup.get('w')) if matchup.get('w') else None,
                    str(matchup.get('l')) if matchup.get('l') else None,
                    json.dumps(matchup.get('t1_from')) if matchup.get('t1_from') else None,
                    json.dumps(matchup.get('t2_from')) if matchup.get('t2_from') else None,
                    datetime.now().isoformat()
                ))

            for matchup in losers_bracket:
                matchup_id = f"{league_id}_{season_year}_L_R{matchup.get('r')}_M{matchup.get('m')}"
                cursor.execute("""
                    INSERT OR REPLACE INTO PlayoffMatchups (
                        matchup_id, sleeper_league_id, season_year, bracket_type, round_number, match_number,
                        team1_roster_id, team2_roster_id, winner_roster_id, loser_roster_id,
                        team1_from_match, team2_from_match, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    matchup_id, league_id, season_year, 'losers_bracket',
                    matchup.get('r'), matchup.get('m'),
                    str(matchup.get('t1')) if matchup.get('t1') else None,
                    str(matchup.get('t2')) if matchup.get('t2') else None,
                    str(matchup.get('w')) if matchup.get('w') else None,
                    str(matchup.get('l')) if matchup.get('l') else None,
                    json.dumps(matchup.get('t1_from')) if matchup.get('t1_from') else None,
                    json.dumps(matchup.get('t2_from')) if matchup.get('t2_from') else None,
                    datetime.now().isoformat()
                ))

            # Determine final placements from bracket
            # Find championship match (highest round in winners bracket)
            cursor.execute("""
                SELECT * FROM PlayoffMatchups
                WHERE sleeper_league_id = ? AND season_year = ? AND bracket_type = 'winners_bracket'
                ORDER BY round_number DESC
                LIMIT 1
            """, (league_id, season_year))
            championship = cursor.fetchone()

            if championship and championship['winner_roster_id']:
                # 1st place: Championship winner
                placement_id = f"{league_id}_{season_year}_{championship['winner_roster_id']}"
                cursor.execute("""
                    INSERT OR REPLACE INTO LeaguePlacements (
                        placement_id, sleeper_league_id, season_year, roster_id,
                        placement_type, final_rank, determined_by, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (placement_id, league_id, season_year, championship['winner_roster_id'],
                      '1st_place', 1, 'playoff_bracket', datetime.now().isoformat()))

                # 2nd place: Championship loser
                placement_id = f"{league_id}_{season_year}_{championship['loser_roster_id']}"
                cursor.execute("""
                    INSERT OR REPLACE INTO LeaguePlacements (
                        placement_id, sleeper_league_id, season_year, roster_id,
                        placement_type, final_rank, determined_by, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (placement_id, league_id, season_year, championship['loser_roster_id'],
                      '2nd_place', 2, 'playoff_bracket', datetime.now().isoformat()))

            # Find 3rd place match (consolation bracket or losers bracket final)
            cursor.execute("""
                SELECT * FROM PlayoffMatchups
                WHERE sleeper_league_id = ? AND season_year = ?
                    AND bracket_type = 'losers_bracket'
                    AND winner_roster_id IS NOT NULL
                ORDER BY round_number DESC
                LIMIT 1
            """, (league_id, season_year))
            third_place_match = cursor.fetchone()

            if third_place_match and third_place_match['winner_roster_id']:
                placement_id = f"{league_id}_{season_year}_{third_place_match['winner_roster_id']}"
                cursor.execute("""
                    INSERT OR REPLACE INTO LeaguePlacements (
                        placement_id, sleeper_league_id, season_year, roster_id,
                        placement_type, final_rank, determined_by, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (placement_id, league_id, season_year, third_place_match['winner_roster_id'],
                      '3rd_place', 3, 'consolation_match', datetime.now().isoformat()))

            # Get regular season winner (most wins)
            cursor.execute("""
                SELECT sleeper_roster_id FROM rosters
                WHERE sleeper_league_id = ?
                ORDER BY wins DESC, points_for DESC
                LIMIT 1
            """, (league_id,))
            reg_season_winner = cursor.fetchone()

            if reg_season_winner:
                placement_id = f"{league_id}_{season_year}_{reg_season_winner['sleeper_roster_id']}_rs"
                cursor.execute("""
                    INSERT OR REPLACE INTO LeaguePlacements (
                        placement_id, sleeper_league_id, season_year, roster_id,
                        placement_type, final_rank, determined_by, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (placement_id, league_id, season_year, reg_season_winner['sleeper_roster_id'],
                      'regular_season_winner', 0, 'regular_season', datetime.now().isoformat()))

            conn.commit()
            conn.close()

            return jsonify({
                'success': True,
                'message': f'Playoff bracket synced for league {league_id}',
                'winners_bracket_matches': len(winners_bracket),
                'losers_bracket_matches': len(losers_bracket)
            })

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/league/<league_id>/standings', methods=['GET'])
    @admin_required
    def get_league_standings_for_payouts(league_id):
        """Get league standings sorted by wins for payout calculation"""
        try:
            conn = sqlite3.connect('keeper.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Fetch rosters with wins/losses, joined with UserLeagueLinks to get wallet addresses
            cursor.execute('''
                SELECT
                    r.sleeper_roster_id,
                    r.team_name,
                    r.wins,
                    r.losses,
                    r.ties,
                    r.points_for,
                    ull.wallet_address
                FROM rosters r
                LEFT JOIN UserLeagueLinks ull ON r.sleeper_roster_id = ull.sleeper_roster_id
                    AND r.sleeper_league_id = ull.sleeper_league_id
                WHERE r.sleeper_league_id = ?
                ORDER BY r.wins DESC, r.points_for DESC
            ''', (league_id,))

            standings = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return jsonify({
                'success': True,
                'league_id': league_id,
                'standings': standings
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/admin/league/<league_id>/payouts/calculate', methods=['POST'])
    @admin_required
    def calculate_payout_distribution(league_id):
        """Calculate prize distribution based on playoff bracket and regular season standings"""
        try:
            data = request.json
            prize_pool = data.get('prize_pool')  # Total FLOW to distribute (principal only, not yield)
            season_year = data.get('season_year', 2025)

            if not prize_pool or prize_pool <= 0:
                return jsonify({'success': False, 'error': 'Valid prize_pool amount required'}), 400

            conn = sqlite3.connect('keeper.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # First, check if we have playoff placements data from LeaguePlacements
            cursor.execute('''
                SELECT
                    lp.roster_id,
                    lp.placement_type,
                    lp.final_rank,
                    r.team_name,
                    ull.wallet_address
                FROM LeaguePlacements lp
                JOIN rosters r ON lp.roster_id = r.sleeper_roster_id AND lp.sleeper_league_id = r.sleeper_league_id
                LEFT JOIN UserLeagueLinks ull ON r.sleeper_roster_id = ull.sleeper_roster_id
                    AND r.sleeper_league_id = ull.sleeper_league_id
                WHERE lp.sleeper_league_id = ? AND lp.season_year = ?
                ORDER BY lp.final_rank ASC
            ''', (league_id, season_year))

            placements = cursor.fetchall()

            if placements and len(placements) >= 4:
                # Use playoff bracket data
                distributions = []
                placement_map = {row['placement_type']: row for row in placements}

                # 1st place: 50%
                if '1st_place' in placement_map:
                    p = placement_map['1st_place']
                    distributions.append({
                        'roster_id': p['roster_id'],
                        'team_name': p['team_name'],
                        'wallet_address': p['wallet_address'],
                        'payout_type': '1st_place',
                        'percentage': 50.0,
                        'amount': prize_pool * 0.50,
                        'determined_by': 'playoff_bracket'
                    })

                # 2nd place: 30%
                if '2nd_place' in placement_map:
                    p = placement_map['2nd_place']
                    distributions.append({
                        'roster_id': p['roster_id'],
                        'team_name': p['team_name'],
                        'wallet_address': p['wallet_address'],
                        'payout_type': '2nd_place',
                        'percentage': 30.0,
                        'amount': prize_pool * 0.30,
                        'determined_by': 'playoff_bracket'
                    })

                # 3rd place: 10%
                if '3rd_place' in placement_map:
                    p = placement_map['3rd_place']
                    distributions.append({
                        'roster_id': p['roster_id'],
                        'team_name': p['team_name'],
                        'wallet_address': p['wallet_address'],
                        'payout_type': '3rd_place',
                        'percentage': 10.0,
                        'amount': prize_pool * 0.10,
                        'determined_by': 'playoff_bracket'
                    })

                # Regular season winner: 10%
                if 'regular_season_winner' in placement_map:
                    p = placement_map['regular_season_winner']
                    distributions.append({
                        'roster_id': p['roster_id'],
                        'team_name': p['team_name'],
                        'wallet_address': p['wallet_address'],
                        'payout_type': 'regular_season_winner',
                        'percentage': 10.0,
                        'amount': prize_pool * 0.10,
                        'determined_by': 'regular_season'
                    })

                conn.close()
                return jsonify({
                    'success': True,
                    'league_id': league_id,
                    'prize_pool': prize_pool,
                    'distributions': distributions,
                    'total_distributed': sum(d['amount'] for d in distributions),
                    'source': 'playoff_bracket_data'
                })

            else:
                # Fallback: Use regular season standings (wins/points_for)
                cursor.execute('''
                    SELECT
                        r.sleeper_roster_id,
                        r.team_name,
                        r.wins,
                        r.losses,
                        r.points_for,
                        ull.wallet_address
                    FROM rosters r
                    LEFT JOIN UserLeagueLinks ull ON r.sleeper_roster_id = ull.sleeper_roster_id
                        AND r.sleeper_league_id = ull.sleeper_league_id
                    WHERE r.sleeper_league_id = ?
                    ORDER BY r.wins DESC, r.points_for DESC
                    LIMIT 4
                ''', (league_id,))

                top_teams = cursor.fetchall()
                conn.close()

                if len(top_teams) < 4:
                    return jsonify({'success': False, 'error': 'Not enough teams for payout calculation (need at least 4)'}), 400

                # Calculate splits: 50%, 30%, 10%, 10%
                # NOTE: This is a simplified fallback - actual playoff results should be used
                distributions = [
                    {
                        'roster_id': top_teams[0]['sleeper_roster_id'],
                        'team_name': top_teams[0]['team_name'],
                        'wallet_address': top_teams[0]['wallet_address'],
                        'payout_type': '1st_place',
                        'percentage': 50.0,
                        'amount': prize_pool * 0.50,
                        'wins': top_teams[0]['wins'],
                        'determined_by': 'regular_season_fallback'
                    },
                    {
                        'roster_id': top_teams[1]['sleeper_roster_id'],
                        'team_name': top_teams[1]['team_name'],
                        'wallet_address': top_teams[1]['wallet_address'],
                        'payout_type': '2nd_place',
                        'percentage': 30.0,
                        'amount': prize_pool * 0.30,
                        'wins': top_teams[1]['wins'],
                        'determined_by': 'regular_season_fallback'
                    },
                    {
                        'roster_id': top_teams[2]['sleeper_roster_id'],
                        'team_name': top_teams[2]['team_name'],
                        'wallet_address': top_teams[2]['wallet_address'],
                        'payout_type': '3rd_place',
                        'percentage': 10.0,
                        'amount': prize_pool * 0.10,
                        'wins': top_teams[2]['wins'],
                        'determined_by': 'regular_season_fallback'
                    },
                    {
                        'roster_id': top_teams[0]['sleeper_roster_id'],  # Same as 1st - they get both prizes
                        'team_name': top_teams[0]['team_name'],
                        'wallet_address': top_teams[0]['wallet_address'],
                        'payout_type': 'regular_season_winner',
                        'percentage': 10.0,
                        'amount': prize_pool * 0.10,
                        'wins': top_teams[0]['wins'],
                        'determined_by': 'regular_season'
                    }
                ]

                return jsonify({
                    'success': True,
                    'league_id': league_id,
                    'prize_pool': prize_pool,
                    'distributions': distributions,
                    'total_distributed': sum(d['amount'] for d in distributions),
                    'source': 'regular_season_fallback',
                    'warning': 'No playoff bracket data found. Using regular season standings as fallback.'
                })

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/admin/league/<league_id>/vault/deposit', methods=['POST'])
    @admin_required
    def vault_deposit(league_id):
        """Create vault deposit record (Cadence transaction executed separately)"""
        try:
            data = request.json
            amount = data.get('amount')
            pool_address = data.get('pool_address', '0x8aaca41f09eb1e3d')  # Default to FLOW LendingPool testnet
            vault_protocol = data.get('vault_protocol', 'increment_fi')
            season_year = data.get('season_year', 2025)
            deposit_tx_id = data.get('deposit_tx_id')  # Passed after Cadence transaction completes

            if not amount or amount <= 0:
                return jsonify({'success': False, 'error': 'Valid deposit amount required'}), 400

            if not deposit_tx_id:
                return jsonify({'success': False, 'error': 'Transaction ID required'}), 400

            conn = sqlite3.connect('keeper.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            vault_id = f"vault_{league_id}_{season_year}"

            cursor.execute("""
                INSERT INTO YieldVaults (
                    vault_id, sleeper_league_id, season_year, vault_protocol, vault_address,
                    principal_amount, current_value, yield_earned, deposit_tx_id, deposit_date,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vault_id, league_id, season_year, vault_protocol, pool_address,
                amount, amount, 0.0, deposit_tx_id, datetime.now().isoformat(),
                'active', datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()

            return jsonify({
                'success': True,
                'vault_id': vault_id,
                'message': f'Vault deposit recorded: {amount} FLOW to {vault_protocol}'
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/admin/league/<league_id>/vault/withdrawal-record', methods=['POST'])
    @admin_required
    def vault_withdrawal(league_id):
        """Record vault withdrawal (Cadence transaction executed separately) - OLD ENDPOINT"""
        try:
            data = request.json
            vault_id = data.get('vault_id')
            withdrawal_amount = data.get('withdrawal_amount')
            withdrawal_tx_id = data.get('withdrawal_tx_id')
            yield_earned = data.get('yield_earned', 0.0)

            if not vault_id or not withdrawal_tx_id:
                return jsonify({'success': False, 'error': 'vault_id and withdrawal_tx_id required'}), 400

            conn = sqlite3.connect('keeper.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE YieldVaults
                SET
                    current_value = 0.0,
                    yield_earned = ?,
                    withdrawal_tx_id = ?,
                    withdrawal_date = ?,
                    status = 'withdrawn',
                    last_updated = ?
                WHERE vault_id = ?
            """, (
                yield_earned,
                withdrawal_tx_id,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                vault_id
            ))

            conn.commit()
            conn.close()

            return jsonify({
                'success': True,
                'vault_id': vault_id,
                'withdrawal_amount': withdrawal_amount,
                'yield_earned': yield_earned,
                'message': 'Vault withdrawal recorded successfully'
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/admin/league/<league_id>/vault/balance', methods=['GET'])
    @admin_required
    def get_vault_balance(league_id):
        """Get current vault balance from database"""
        try:
            season_year = request.args.get('season_year', 2025)
            vault_id = f"vault_{league_id}_{season_year}"

            conn = sqlite3.connect('keeper.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM YieldVaults WHERE vault_id = ?
            """, (vault_id,))

            vault = cursor.fetchone()
            conn.close()

            if not vault:
                return jsonify({'success': False, 'error': 'Vault not found'}), 404

            return jsonify({
                'success': True,
                'vault': dict(vault)
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/admin/league/<league_id>/payouts/execute-record', methods=['POST'])
    @admin_required
    def execute_payout(league_id):
        """Execute prize distribution - LEGACY endpoint for manual record creation (creates PayoutSchedule and PayoutDistributions)"""
        try:
            data = request.json
            prize_pool = data.get('prize_pool')
            vault_id = data.get('vault_id')
            season_year = data.get('season_year', 2025)
            distributions = data.get('distributions')  # Array from calculate endpoint
            transaction_id = data.get('transaction_id')  # From distribute_prizes.cdc execution

            if not prize_pool or not distributions or not transaction_id:
                return jsonify({'success': False, 'error': 'prize_pool, distributions, and transaction_id required'}), 400

            conn = sqlite3.connect('keeper.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Create PayoutSchedule
            payout_id = f"payout_{league_id}_{season_year}"
            cursor.execute("""
                INSERT INTO PayoutSchedules (
                    payout_id, sleeper_league_id, season_year, payout_date, payout_status,
                    total_prize_pool, vault_id, standings_finalized, execution_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                payout_id, league_id, season_year, datetime.now().isoformat(), 'completed',
                prize_pool, vault_id, 1, datetime.now().isoformat(), datetime.now().isoformat()
            ))

            # Create PayoutDistributions
            for dist in distributions:
                distribution_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO PayoutDistributions (
                        distribution_id, payout_id, wallet_address, payout_type,
                        amount, percentage, transaction_id, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    distribution_id, payout_id, dist['wallet_address'], dist['payout_type'],
                    dist['amount'], dist['percentage'], transaction_id, 'completed',
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))

            conn.commit()
            conn.close()

            return jsonify({
                'success': True,
                'payout_id': payout_id,
                'transaction_id': transaction_id,
                'message': f'Prize distribution executed: {len(distributions)} winners paid'
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    print("Admin routes registered successfully")
