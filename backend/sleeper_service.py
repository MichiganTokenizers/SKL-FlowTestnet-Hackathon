import requests
import sqlite3
import json
from typing import Dict, List, Optional, Any
import logging

class SleeperService:
    BASE_URL = "https://api.sleeper.app/v1"
    
    def __init__(self, db_connection: Optional[sqlite3.Connection] = None):
        self.logger = logging.getLogger(__name__)
        self.conn = db_connection
        if self.conn:
            print("DEBUG_SLEEPER_SERVICE: Initialized with a database connection.")
        else:
            print("DEBUG_SLEEPER_SERVICE: Initialized WITHOUT a database connection. DB operations will fail if no connection is provided later.")

    def _get_db_cursor(self) -> sqlite3.Cursor:
        """Gets a cursor from the provided DB connection. Raises an error if no connection."""
        if not self.conn:
            self.logger.error("SleeperService: Database connection not provided.")
            raise ValueError("Database connection not provided to SleeperService.")
        return self.conn.cursor()
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user information by username."""
        try:
            response = requests.get(f"{self.BASE_URL}/user/{username}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching user {username}: {str(e)}")
            return None
    
    def get_user_leagues(self, user_id: str, sport: str = "nfl", season: str = "2024") -> List[Dict]:
        """Get all leagues for a user."""
        try:
            response = requests.get(f"{self.BASE_URL}/user/{user_id}/leagues/{sport}/{season}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching leagues for user {user_id}: {str(e)}")
            return []
    
    def get_league(self, league_id: str) -> Optional[Dict]:
        """Get specific league information."""
        try:
            response = requests.get(f"{self.BASE_URL}/league/{league_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching league {league_id}: {str(e)}")
            return None
    
    def get_league_rosters(self, league_id: str) -> List[Dict]:
        """Get all rosters in a league."""
        try:
            response = requests.get(f"{self.BASE_URL}/league/{league_id}/rosters")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching rosters for league {league_id}: {str(e)}")
            return []
    
    def get_league_users(self, league_id: str) -> List[Dict]:
        """Get all users in a league."""
        try:
            response = requests.get(f"{self.BASE_URL}/league/{league_id}/users")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching users for league {league_id}: {str(e)}")
            return []
    
    def get_league_matchups(self, league_id: str, week: int) -> List[Dict]:
        """Get matchups for a specific week."""
        try:
            response = requests.get(f"{self.BASE_URL}/league/{league_id}/matchups/{week}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching matchups for league {league_id} week {week}: {str(e)}")
            return []
    
    def get_players(self) -> Dict:
        """Get all players data."""
        try:
            response = requests.get(f"{self.BASE_URL}/players/nfl")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching players: {str(e)}")
            return {}

    def get_league_transactions(self, league_id: str, week: Optional[int] = None) -> List[Dict]:
        """Get transactions for a league. If week is specified, get transactions for that week; otherwise, get all transactions for the current season."""
        try:
            url = f"{self.BASE_URL}/league/{league_id}/transactions"
            if week is not None:
                url += f"/{week}"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching transactions for league {league_id}: {str(e)}")
            return []

    def get_traded_picks(self, league_id: str) -> List[Dict]:
        """Get traded picks for a league."""
        try:
            response = requests.get(f"{self.BASE_URL}/league/{league_id}/traded_picks")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching traded picks for league {league_id}: {str(e)}")
            return []

    def get_nfl_state(self) -> Optional[Dict]:
        """Get current NFL state."""
        try:
            response = requests.get(f"{self.BASE_URL}/state/nfl")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching NFL state: {str(e)}")
            return None

    def get_league_drafts(self, league_id: str) -> List[Dict]:
        """Get drafts for a league."""
        try:
            response = requests.get(f"{self.BASE_URL}/league/{league_id}/drafts")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching drafts for league {league_id}: {str(e)}")
            return []
    
    def fetch_all_data(self, wallet_address: str) -> Dict[str, Any]:
        """
        Fetch all Sleeper data for a user and store it in the local database.
        Uses the connection provided during __init__.
        Args:
            wallet_address: The wallet address of the user
            
        Returns:
            Dict: Result of the operation with success status
        """
        try:
            cursor = self._get_db_cursor()
            
            # Get the sleeper_user_id for this wallet address
            cursor.execute('SELECT sleeper_user_id FROM users WHERE wallet_address = ?', (wallet_address,))
            user_data_row = cursor.fetchone()
            
            if not user_data_row or not user_data_row['sleeper_user_id']:
                self.logger.warning(f"SleeperService.fetch_all_data: No Sleeper user ID associated with wallet {wallet_address}. Queried using provided DB conn.")
                return {"success": False, "error": "No Sleeper user ID associated with this wallet"}
            
            sleeper_user_id = user_data_row['sleeper_user_id']
            self.logger.info(f"SleeperService.fetch_all_data: Processing for wallet {wallet_address}, sleeper_user_id {sleeper_user_id}")

            # Step 1: Get user leagues for 2025 season (or a configurable/current season)
            # For now, using 2025 as per existing logic.
            current_api_season = "2025" 
            leagues = self.get_user_leagues(sleeper_user_id, sport="nfl", season=current_api_season)
            
            if not leagues:
                self.logger.warning(f"SleeperService.fetch_all_data: No leagues found on Sleeper API for user {sleeper_user_id} for season {current_api_season}.")
                # This is not necessarily an error for the fetch_all_data process itself if the user has no leagues.
                # The users table should be correct, leagues table will just be empty for this user.
                # However, the calling context might expect leagues to be found.
                # For now, let's match prior logic which returned an error.
                return {"success": False, "error": f"No leagues found for this user for season {current_api_season}"}
            
            # Step 2: Process each league
            for league_data in leagues:
                league_id = league_data.get("league_id")
                if not league_id:
                    self.logger.warning(f"SleeperService.fetch_all_data: Found a league object without a league_id for user {sleeper_user_id}. Skipping.")
                    continue
                
                self.logger.info(f"SleeperService.fetch_all_data: Processing league_id {league_id} for user {sleeper_user_id}.")
                print(f"DEBUG (SleeperService): Processing league {league_id}")

                # Get details for this specific league from API to ensure all data is fresh
                full_league_details = self.get_league(league_id)
                if not full_league_details:
                    self.logger.warning(f"SleeperService.fetch_all_data: Could not fetch full details for league_id {league_id}. Skipping.")
                    continue

                # Determine season year and status from the full_league_details
                # (as season_curr table in DB might be for a different purpose or general app state)
                league_season_year = full_league_details.get("season", current_api_season)
                league_status = full_league_details.get("status", "unknown")
                league_name = full_league_details.get("name", "Unknown League")
                league_settings_json = json.dumps(full_league_details.get("settings", {}))

                # Store league details
                self.logger.debug(f"SleeperService.fetch_all_data: Upserting league {league_id} into DB.")
                cursor.execute('''
                    INSERT INTO leagues (
                        sleeper_league_id, sleeper_user_id, name, season, status, settings, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                    ON CONFLICT(sleeper_user_id, sleeper_league_id) DO UPDATE SET
                        name = excluded.name,
                        season = excluded.season,
                        status = excluded.status,
                        settings = excluded.settings,
                        updated_at = datetime('now')
                ''', (
                    league_id, sleeper_user_id, league_name, league_season_year, 
                    league_status, league_settings_json
                ))

                # Step 3: Get rosters for this league
                rosters = self.get_league_rosters(league_id)
                if not rosters:
                    self.logger.warning(f"SleeperService.fetch_all_data: No rosters found for league {league_id}. Skipping roster processing.")
                else:
                    self.logger.info(f"SleeperService.fetch_all_data: Found {len(rosters)} rosters for league {league_id}.")
                    print(f"DEBUG (SleeperService): Found {len(rosters)} roster records for league {league_id}")
                    all_roster_player_ids = set()

                    for roster_data in rosters:
                        roster_id = roster_data.get("roster_id")
                        owner_id = roster_data.get("owner_id")
                        players_list = roster_data.get("players")
                        roster_settings_json = json.dumps(roster_data.get("settings", {}))

                        self.logger.debug(f"SleeperService.fetch_all_data: Upserting roster {roster_id} for league {league_id}.")
                        cursor.execute('''
                            INSERT INTO rosters (
                                sleeper_roster_id, league_id, owner_id, players, settings, updated_at
                            ) VALUES (?, ?, ?, ?, ?, datetime('now'))
                            ON CONFLICT(sleeper_roster_id) DO UPDATE SET 
                                league_id=excluded.league_id, 
                                owner_id=excluded.owner_id, 
                                players=excluded.players, 
                                settings=excluded.settings,
                                updated_at=datetime('now')
                        ''', (
                            roster_id, league_id, owner_id, 
                            json.dumps(players_list) if players_list else None, 
                            roster_settings_json
                        ))

                        if isinstance(players_list, list):
                            print(f"DEBUG (SleeperService): Roster {roster_id} players raw data: {str(players_list)[:50]}...")
                            all_roster_player_ids.update(players_list)
                            print(f"DEBUG (SleeperService): Added {len(players_list)} players from roster {roster_id}. Total unique now: {len(all_roster_player_ids)}")
                        else:
                            print(f"DEBUG (SleeperService): Roster {roster_id} players not in list format or is None: {type(players_list)}")

                    self.logger.info(f"SleeperService.fetch_all_data: Total unique players found on rosters in league {league_id}: {len(all_roster_player_ids)}")
                    print(f"DEBUG (SleeperService): Total unique players found on rosters in league {league_id}: {len(all_roster_player_ids)}")

                # Step 4: Get users (participants) for this league
                league_participants = self.get_league_users(league_id)
                if not league_participants:
                    self.logger.warning(f"SleeperService.fetch_all_data: No participants found for league {league_id}.")
                else:
                    self.logger.info(f"SleeperService.fetch_all_data: Found {len(league_participants)} participants for league {league_id}.")
                    for participant_data in league_participants:
                        p_user_id = participant_data.get("user_id")
                        p_display_name = participant_data.get("display_name")
                        p_avatar = participant_data.get("avatar")
                        p_username = participant_data.get("username")

                        if not p_user_id:
                            self.logger.warning("SleeperService.fetch_all_data: Participant data found with no user_id. Skipping.")
                            continue

                        self.logger.debug(f"SleeperService.fetch_all_data: Upserting league participant {p_user_id} ({p_display_name}) into users table.")
                        cursor.execute('''
                            INSERT INTO users (sleeper_user_id, username, display_name, avatar, created_at, updated_at)
                            VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
                            ON CONFLICT(sleeper_user_id) DO UPDATE SET
                                username = excluded.username,
                                display_name = excluded.display_name,
                                avatar = excluded.avatar,
                                updated_at = datetime('now')
                            WHERE users.wallet_address IS NULL;
                        ''', (p_user_id, p_username, p_display_name, p_avatar))
                        
                        if cursor.rowcount > 0:
                            self.logger.info(f"SleeperService.fetch_all_data: User {p_user_id} ({p_display_name}) inserted/updated in users table.")
                        else:
                            self.logger.info(f"SleeperService.fetch_all_data: User {p_user_id} ({p_display_name}) already exists with a wallet_address or no update needed. No change made to their user record by league sync.")

                # Step 5: Get transactions for this league
                league_transactions = self.get_league_transactions(league_id)
                if not league_transactions:
                    self.logger.warning(f"SleeperService.fetch_all_data: No transactions found for league {league_id} (current season). Error was: {getattr(league_transactions, 'error', 'Unknown, but no data')}")
                    print(f"Error fetching transactions for league {league_id}: {getattr(league_transactions, 'error', 'No transactions returned or error')}")
                else:
                    self.logger.info(f"SleeperService.fetch_all_data: Found {len(league_transactions)} transactions for league {league_id}.")
                    for tx_data in league_transactions:
                        tx_id = tx_data.get("transaction_id")
                        tx_type = tx_data.get("type")
                        tx_status = tx_data.get("status")
                        tx_data_json = json.dumps(tx_data)

                        if not tx_id:
                            self.logger.warning("SleeperService.fetch_all_data: Transaction data found with no transaction_id. Skipping.")
                            continue
                        
                        self.logger.debug(f"SleeperService.fetch_all_data: Upserting transaction {tx_id} for league {league_id}.")
                        cursor.execute('''
                            INSERT INTO transactions (sleeper_transaction_id, league_id, type, status, data, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                            ON CONFLICT(sleeper_transaction_id) DO UPDATE SET
                                league_id = excluded.league_id,
                                type = excluded.type,
                                status = excluded.status,
                                data = excluded.data,
                                updated_at = datetime('now')
                        ''', (tx_id, league_id, tx_type, tx_status, tx_data_json))

                # Step 6: Get traded picks for this league
                traded_picks = self.get_traded_picks(league_id)
                if not traded_picks:
                    self.logger.warning(f"SleeperService.fetch_all_data: No traded_picks found for league {league_id}.")
                else:
                    self.logger.info(f"SleeperService.fetch_all_data: Found {len(traded_picks)} traded_picks for league {league_id}.")
                    for pick_data in traded_picks:
                        pick_season = pick_data.get("season")
                        pick_round = pick_data.get("round")
                        pick_roster_id = pick_data.get("roster_id")
                        pick_prev_owner = pick_data.get("previous_owner_id")
                        pick_curr_owner = pick_data.get("owner_id")
                        
                        self.logger.debug(f"SleeperService.fetch_all_data: Inserting traded pick for league {league_id}, season {pick_season}, round {pick_round}.")
                        cursor.execute('''
                            INSERT INTO traded_picks (league_id, draft_id, round, roster_id, previous_owner_id, current_owner_id, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                        ''', (league_id, str(pick_season), pick_round, pick_roster_id, pick_prev_owner, pick_curr_owner))

                # Step 7: Get drafts for this league
                league_drafts = self.get_league_drafts(league_id)
                if not league_drafts:
                    self.logger.warning(f"SleeperService.fetch_all_data: No drafts found for league {league_id}.")
                else:
                    self.logger.info(f"SleeperService.fetch_all_data: Found {len(league_drafts)} drafts for league {league_id}.")
                    for draft_data in league_drafts:
                        d_draft_id = draft_data.get("draft_id")
                        d_status = draft_data.get("status")
                        d_start_time = draft_data.get("start_time")
                        d_data_json = json.dumps(draft_data)

                        if d_start_time:
                            try:
                                d_start_time_iso = sqlite3.TimestampFromTicks(d_start_time / 1000).isoformat()
                            except:
                                d_start_time_iso = None
                        else:
                            d_start_time_iso = None

                        if not d_draft_id:
                            self.logger.warning("SleeperService.fetch_all_data: Draft data found with no draft_id. Skipping.")
                            continue

                        self.logger.debug(f"SleeperService.fetch_all_data: Upserting draft {d_draft_id} for league {league_id}.")
                        cursor.execute('''
                            INSERT INTO drafts (sleeper_draft_id, league_id, status, start_time, data, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                            ON CONFLICT(sleeper_draft_id) DO UPDATE SET
                                league_id = excluded.league_id,
                                status = excluded.status,
                                start_time = excluded.start_time,
                                data = excluded.data,
                                updated_at = datetime('now')
                        ''', (d_draft_id, league_id, d_status, d_start_time_iso, d_data_json))
            
            # Step 8: Consolidate and store all unique players from rosters
            self.logger.info("SleeperService.fetch_all_data: Starting general player data import...")
            print("DEBUG (SleeperService): Starting player data import...")
            all_players_api_data = self.get_players()
            if not all_players_api_data:
                self.logger.error("SleeperService.fetch_all_data: Failed to retrieve any player data from Sleeper API.")
            else:
                self.logger.info(f"SleeperService.fetch_all_data: Retrieved {len(all_players_api_data)} players from Sleeper API for general import.")
                print(f"DEBUG (SleeperService): Retrieved {len(all_players_api_data)} players from Sleeper API")
                players_to_insert = []
                for player_id, player_info in all_players_api_data.items():
                    players_to_insert.append((
                        player_id,
                        player_info.get('full_name', player_info.get('first_name', '') + ' ' + player_info.get('last_name', '')).strip(),
                        player_info.get('position'),
                        player_info.get('team')
                    ))
                
                if players_to_insert:
                    self.logger.info(f"SleeperService.fetch_all_data: Bulk inserting/updating {len(players_to_insert)} players into DB.")
                    cursor.executemany('''
                        INSERT INTO players (sleeper_player_id, name, position, team, created_at, updated_at)
                        VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
                        ON CONFLICT(sleeper_player_id) DO UPDATE SET
                            name=excluded.name, 
                            position=excluded.position, 
                            team=excluded.team,
                            updated_at=datetime('now')
                    ''', players_to_insert)
                    self.logger.info(f"SleeperService.fetch_all_data: Added/Updated {len(players_to_insert)} players to the database.")
                    print(f"DEBUG (SleeperService): Added {len(players_to_insert)} players to the database")

            self.logger.info(f"SleeperService.fetch_all_data: Completed processing for wallet {wallet_address}.")
            return {"success": True, "message": "All data fetched and stored successfully"}

        except sqlite3.Error as sqle:
            self.logger.error(f"SleeperService.fetch_all_data: SQLite error for wallet {wallet_address}: {str(sqle)}")
            return {"success": False, "error": f"Database error: {str(sqle)}"}
        except ValueError as ve:
            self.logger.error(f"SleeperService.fetch_all_data: Value error (likely DB connection issue) for wallet {wallet_address}: {str(ve)}")
            return {"success": False, "error": f"Configuration error: {str(ve)}"}
        except Exception as e:
            self.logger.error(f"SleeperService.fetch_all_data: Unexpected error for wallet {wallet_address}: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {"success": False, "error": f"Server error: {str(e)}"} 