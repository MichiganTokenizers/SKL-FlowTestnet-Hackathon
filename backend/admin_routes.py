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
                try:
                    conn = sqlite3.connect('keeper.db')
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT wallet_address FROM sessions WHERE session_token = ?", (auth_header,))
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
                try:
                    conn = sqlite3.connect('keeper.db')
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT wallet_address FROM sessions WHERE session_token = ?", (auth_header,))
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

    print("Admin routes registered successfully")
