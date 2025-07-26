import sqlite3
import os
import json

# Connect to the database
db_path = '/var/data/keeper.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check current league data
cursor.execute('SELECT * FROM leagues WHERE sleeper_league_id = ?', ('1224829460549738496',))
league = cursor.fetchone()
if league:
    print('Current league data:', league)
    # Check if user ID is already associated
    if league[0] == '1224829004754718720':
        print('User 1224829004754718720 is already associated with league 1224829460549738496')
    else:
        # Update to associate user ID with league
        cursor.execute('UPDATE leagues SET sleeper_user_id = ? WHERE sleeper_league_id = ?', ('1224829004754718720', '1224829460549738496'))
        print('Associated user 1224829004754718720 with league 1224829460549738496')
    # Force update of other fields
    cursor.execute('''
        UPDATE leagues SET name = ?, season = ?, status = ?, settings = ?, updated_at = datetime('now')
        WHERE sleeper_league_id = ?
    ''', ('Supreme Keeper League', '2025', 'in', json.dumps({'best_ball': 0, 'waiver_budget': 100, 'disable_adds': 0, 'capacity_override': 0, 'waiver_bid_min': 0, 'taxi_deadline': 0, 'draft_rounds': 3, 'reserve_allow_na': 1, 'start_week': 1, 'playoff_seed_type': 0, 'playoff_teams': 6, 'veto_votes_needed': 5, 'position_limit_qb': 4, 'num_teams': 10, 'daily_waivers_hour': 0, 'playoff_type': 0, 'taxi_slots': 0, 'sub_start_time_eligibility': 0, 'daily_waivers_days': 5461, 'sub_lock_if_starter_active': 0, 'playoff_week_start': 15, 'waiver_clear_days': 2, 'reserve_allow_doubtful': 0, 'commissioner_direct_invite': 0, 'veto_auto_poll': 0, 'reserve_allow_dnr': 1, 'taxi_allow_vets': 0, 'waiver_day_of_week': 2, 'playoff_round_type': 0, 'reserve_allow_out': 1, 'reserve_allow_sus': 1, 'veto_show_votes': 0, 'trade_deadline': 11, 'taxi_years': 0, 'daily_waivers': 0, 'faab_suggestions': 1, 'disable_trades': 0, 'pick_trading': 0, 'type': 1, 'max_keepers': 18, 'waiver_type': 2, 'max_subs': 2, 'league_average_match': 0, 'trade_review_days': 2, 'bench_lock': 0, 'offseason_adds': 0, 'leg': 1, 'reserve_slots': 4, 'reserve_allow_cov': 0}), '1224829460549738496'))
    print('Updated league fields for sleeper_league_id 1224829460549738496')
else:
    print('No league data found for sleeper_league_id 1224829460549738496')
    # Insert league data with user ID and all fields
    cursor.execute('''
        INSERT INTO leagues (sleeper_league_id, sleeper_user_id, name, season, status, settings, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    ''', ('1224829460549738496', '1224829004754718720', 'Supreme Keeper League', '2025', 'in', json.dumps({'best_ball': 0, 'waiver_budget': 100, 'disable_adds': 0, 'capacity_override': 0, 'waiver_bid_min': 0, 'taxi_deadline': 0, 'draft_rounds': 3, 'reserve_allow_na': 1, 'start_week': 1, 'playoff_seed_type': 0, 'playoff_teams': 6, 'veto_votes_needed': 5, 'position_limit_qb': 4, 'num_teams': 10, 'daily_waivers_hour': 0, 'playoff_type': 0, 'taxi_slots': 0, 'sub_start_time_eligibility': 0, 'daily_waivers_days': 5461, 'sub_lock_if_starter_active': 0, 'playoff_week_start': 15, 'waiver_clear_days': 2, 'reserve_allow_doubtful': 0, 'commissioner_direct_invite': 0, 'veto_auto_poll': 0, 'reserve_allow_dnr': 1, 'taxi_allow_vets': 0, 'waiver_day_of_week': 2, 'playoff_round_type': 0, 'reserve_allow_out': 1, 'reserve_allow_sus': 1, 'veto_show_votes': 0, 'trade_deadline': 11, 'taxi_years': 0, 'daily_waivers': 0, 'faab_suggestions': 1, 'disable_trades': 0, 'pick_trading': 0, 'type': 1, 'max_keepers': 18, 'waiver_type': 2, 'max_subs': 2, 'league_average_match': 0, 'trade_review_days': 2, 'bench_lock': 0, 'offseason_adds': 0, 'leg': 1, 'reserve_slots': 4, 'reserve_allow_cov': 0})))
    print('Inserted league data for sleeper_league_id 1224829460549738496 with user association and all fields')

# Commit changes and close connection
conn.commit()
conn.close()
print('Database updated successfully.') 