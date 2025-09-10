import requests
import sqlite3
import json
from typing import Dict, List, Optional, Any
import logging
from utils import apply_contract_penalties_and_deactivate # Import new function from utils

class SleeperService:
    BASE_URL = "https://api.sleeper.app/v1"
    
    def __init__(self, db_connection: Optional[sqlite3.Connection] = None):
        self.logger = logging.getLogger(__name__)
        self.conn = db_connection
        if self.conn:
            # Ensure the connection uses sqlite3.Row factory for dictionary-like row access
            self.conn.row_factory = sqlite3.Row
            # print("DEBUG_SLEEPER_SERVICE: Initialized with a database connection and Row factory.") # Keep print for now if it's distinct from logger
        else:
            # print("DEBUG_SLEEPER_SERVICE: Initialized WITHOUT a database connection. DB operations will fail if no connection is provided later.") # Keep print
            pass # No specific logger.info/debug here

    def _get_db_cursor(self) -> sqlite3.Cursor:
        """Gets a cursor from the provided DB connection. Raises an error if no connection."""
        if not self.conn:
            self.logger.error("SleeperService: Database connection not provided.")
            raise ValueError("Database connection not provided to SleeperService.")
        return self.conn.cursor()
    
    def _get_current_season_details(self) -> Optional[Dict[str, Any]]:
        """
        Fetches the current season year and off-season status from the season_curr table.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with 'current_year' and 'is_offseason'
                                      if found, otherwise None.
        """
        try:
            cursor = self._get_db_cursor()
            cursor.execute("SELECT current_year, IsOffSeason FROM season_curr LIMIT 1")
            season_data_row = cursor.fetchone()
            if season_data_row:
                # Cast current_year to int here
                return {"current_year": int(season_data_row['current_year']), "is_offseason": bool(season_data_row['IsOffSeason'])}
            else:
                self.logger.warning("SleeperService._get_current_season_details: No current season data found in season_curr table.")
                return None
        except sqlite3.Error as e:
            self.logger.error(f"SleeperService._get_current_season_details: SQLite error fetching season details: {e}")
            return None
        except ValueError: # Handles _get_db_cursor error
            self.logger.error("SleeperService._get_current_season_details: DB connection error.")
            return None

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
    
    def get_draft_picks(self, draft_id: str) -> List[Dict]:
        """Get all picks for a specific draft."""
        try:
            response = requests.get(f"{self.BASE_URL}/draft/{draft_id}/picks")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching picks for draft {draft_id}: {str(e)}")
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
            
            # --- Call update_all_sleeper_players here to ensure players table is populated ---
            self.logger.info(f"SleeperService.fetch_all_data: Attempting to update all players before processing user data for wallet {wallet_address}.")
            player_update_result = self.update_all_sleeper_players()
            if not player_update_result.get("success"):
                self.logger.error(f"SleeperService.fetch_all_data: update_all_sleeper_players failed: {player_update_result.get('error', 'Unknown error')}. Player data may be incomplete.")
                # Decide if this should be a hard stop or just a warning
            else:
                self.logger.info(f"SleeperService.fetch_all_data: update_all_sleeper_players completed. Message: {player_update_result.get('message')}")
            # --- End of player update call ---
            
            # Get the sleeper_user_id for this wallet address
            cursor.execute('SELECT sleeper_user_id FROM Users WHERE wallet_address = ?', (wallet_address,))
            user_data_row = cursor.fetchone()
            
            if not user_data_row or not user_data_row['sleeper_user_id']:
                self.logger.warning(f"SleeperService.fetch_all_data: No Sleeper user ID associated with wallet {wallet_address}. Queried using provided DB conn.")
                return {"success": False, "error": "No Sleeper user ID associated with this wallet"}
            
            sleeper_user_id = user_data_row['sleeper_user_id']
            # self.logger.info(f"SleeperService.fetch_all_data: Processing for wallet {wallet_address}, sleeper_user_id {sleeper_user_id}")

            # --- Fetch and Update NFL State (Season Info) ---
            self.logger.info(f"SleeperService.fetch_all_data: Attempting to fetch NFL state from API for wallet {wallet_address}.")
            nfl_state_from_api = self.get_nfl_state()
            if nfl_state_from_api:
                year_str = nfl_state_from_api.get('season')
                season_start_date_str = nfl_state_from_api.get('season_start_date')  # e.g., "2025-09-04"
                api_year = None
                api_is_offseason = None

                if year_str:
                    try:
                        api_year = int(year_str)
                    except ValueError:
                        self.logger.error(f"SleeperService.fetch_all_data: NFL state API returned non-integer season: {year_str}")

                if season_start_date_str:
                    import datetime
                    try:
                        season_start_date = datetime.datetime.strptime(season_start_date_str, "%Y-%m-%d").date()
                        today = datetime.date.today()
                        api_is_offseason = today < season_start_date
                    except ValueError as ve:
                        self.logger.error(f"SleeperService.fetch_all_data: Error parsing season_start_date '{season_start_date_str}': {ve}. Defaulting to offseason.")
                        api_is_offseason = True  # Default to offseason on parse error
                else:
                    self.logger.warning("SleeperService.fetch_all_data: No season_start_date in NFL state API response. Defaulting to offseason.")
                    api_is_offseason = True

                if api_year is not None and api_is_offseason is not None:
                    self.logger.info(f"SleeperService.fetch_all_data: Determined from API: Year={api_year}, IsOffseason={api_is_offseason}. Updating season_curr table.")
                    try:
                        api_is_offseason_int = 1 if api_is_offseason else 0
                        cursor.execute('''
                            INSERT OR REPLACE INTO season_curr (rowid, current_year, IsOffSeason, updated_at)
                            VALUES (1, ?, ?, datetime('now'))
                        ''', (str(api_year), api_is_offseason_int))
                        self.conn.commit() 
                        self.logger.info(f"SleeperService.fetch_all_data: Successfully updated season_curr table with API data: Year={api_year}, IsOffseason={api_is_offseason}.")
                    except sqlite3.Error as db_e:
                        self.logger.error(f"SleeperService.fetch_all_data: Failed to update season_curr table with API data: {db_e}")
                else:
                    self.logger.error(f"SleeperService.fetch_all_data: Failed to parse year or determine offseason status from NFL state API response: {nfl_state_from_api}")
            else:
                self.logger.warning(f"SleeperService.fetch_all_data: Could not fetch NFL state from API for wallet {wallet_address}. season_curr table not updated by this step.")
            # --- End of Fetch and Update NFL State ---

            season_details = self._get_current_season_details()
            if not season_details:
                self.logger.error(f"SleeperService.fetch_all_data: Critical - could not retrieve current season details for wallet {wallet_address}. Penalty processing will be impacted and likely skipped for dropped players.")
            # else:
            # self.logger.info(f"SleeperService.fetch_all_data: Current season details: Year {season_details['current_year']}, Off-season: {season_details['is_offseason']}")

            # Step 1: Get user leagues for 2025 season (or a configurable/current season)
            # For now, using 2025 as per existing logic.
            current_api_season = "2025" 
            leagues = self.get_user_leagues(sleeper_user_id, sport="nfl", season=current_api_season)
            
            if not leagues:
                self.logger.warning(f"SleeperService.fetch_all_data: No leagues found on Sleeper API for user {sleeper_user_id} for season {current_api_season}.")
                return {"success": False, "error": f"No leagues found for this user for season {current_api_season}"}
            
            # Step 2: Process each league
            for league_data in leagues:
                league_id = league_data.get("league_id")
                if not league_id:
                    self.logger.warning(f"SleeperService.fetch_all_data: Found a league object without a league_id for user {sleeper_user_id}. Skipping.")
                    continue
                
                # self.logger.info(f"SleeperService.fetch_all_data: Processing league_id {league_id} for user {sleeper_user_id}.")
                # print(f"DEBUG (SleeperService): Processing league {league_id}")

                # Get details for this specific league from API to ensure all data is fresh
                full_league_details = self.get_league(league_id)
                if not full_league_details:
                    self.logger.warning(f"SleeperService.fetch_all_data: Could not fetch full details for league_id {league_id}. Skipping.")
                    continue

                # Extract data for LeagueMetadata
                league_name = full_league_details.get("name", "Unknown League")

                if not league_name.startswith("SKL"):
                    self.logger.info(f"SleeperService.fetch_all_data: Skipping league '{league_name}' (ID: {league_id}) because its name does not start with 'SKL'.")
                    print(f"DEBUG (SleeperService): Skipping league '{league_name}' (ID: {league_id}) due to naming convention.") 
                    continue

                league_season_year = full_league_details.get("season", current_api_season) 
                league_status = full_league_details.get("status", "unknown")
                league_settings_json = json.dumps(full_league_details.get("settings", {}))
                league_scoring_settings_json = json.dumps(full_league_details.get("scoring_settings", {}))
                league_roster_positions_json = json.dumps(full_league_details.get("roster_positions", []))
                league_previous_league_id = full_league_details.get("previous_league_id")
                league_metadata_obj = full_league_details.get("metadata", {})
                league_creation_time_ms = league_metadata_obj.get("league_creation_time") if isinstance(league_metadata_obj, dict) else None
                league_avatar = full_league_details.get("avatar")

                # self.logger.debug(f"SleeperService.fetch_all_data: Upserting league {league_id} into LeagueMetadata.")
                cursor.execute('''
                    INSERT INTO LeagueMetadata (
                        sleeper_league_id, name, season, status, settings, 
                        scoring_settings, roster_positions, previous_league_id, 
                        league_creation_time, avatar, created_at, updated_at,
                        display_order, company_id, bracket_id 
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), ?, ?, ?)
                    ON CONFLICT(sleeper_league_id) DO UPDATE SET
                        name = excluded.name,
                        season = excluded.season,
                        status = excluded.status,
                        settings = excluded.settings,
                        scoring_settings = excluded.scoring_settings,
                        roster_positions = excluded.roster_positions,
                        previous_league_id = excluded.previous_league_id,
                        league_creation_time = excluded.league_creation_time,
                        avatar = excluded.avatar,
                        display_order = excluded.display_order,
                        company_id = excluded.company_id,
                        bracket_id = excluded.bracket_id,
                        updated_at = datetime('now')
                ''', (
                    league_id, league_name, league_season_year, league_status, league_settings_json,
                    league_scoring_settings_json, league_roster_positions_json, league_previous_league_id,
                    league_creation_time_ms, league_avatar, 
                    None, None, None 
                ))
                
                # Insert the link for this league
                cursor.execute('''
                    INSERT OR IGNORE INTO UserLeagueLinks (wallet_address, sleeper_league_id)
                    VALUES (?, ?)
                ''', (wallet_address, league_id))
                if cursor.rowcount > 0:
                    self.logger.info(f"SleeperService.fetch_all_data: Successfully inserted new UserLeagueLinks for wallet {wallet_address}, league {league_id}.")
                else:
                    self.logger.info(f"SleeperService.fetch_all_data: UserLeagueLinks already exists for wallet {wallet_address}, league {league_id}. No change.")
                
                self.conn.commit()  # Commit immediately after link insertion
                
                # Verify insertion
                cursor.execute('''
                    SELECT 1 FROM UserLeagueLinks 
                    WHERE wallet_address = ? AND sleeper_league_id = ?
                ''', (wallet_address, league_id))
                verify_link = cursor.fetchone()
                if verify_link:
                    self.logger.info(f"SleeperService.fetch_all_data: Verified UserLeagueLinks exists for wallet {wallet_address}, league {league_id} after commit.")
                else:
                    self.logger.error(f"SleeperService.fetch_all_data: UserLeagueLinks NOT found after insert/commit for wallet {wallet_address}, league {league_id}!")

                # Step 3: Get users (participants) for this league *before* rosters
                league_participants = self.get_league_users(league_id)
                participant_map = {p['user_id']: p for p in league_participants if p and p.get('user_id')}

                if not league_participants:
                    self.logger.warning(f"SleeperService.fetch_all_data: No participants found for league {league_id}.")
                else:
                    # Log participant data for debugging team names
                    self.logger.info(f"SleeperService: Found {len(league_participants)} participants for league {league_id}")
                    for participant_data in league_participants:
                        p_user_id = participant_data.get("user_id")
                        p_display_name = participant_data.get("display_name")
                        p_avatar = participant_data.get("avatar")
                        p_username = participant_data.get("username")
                        p_metadata = participant_data.get("metadata", {}) or {}
                        p_team_name = p_metadata.get("team_name")
                        p_is_owner = participant_data.get("is_owner", False)  # Commissioner status from Sleeper

                        # ADD THIS DEBUG LOG:
                        self.logger.info(f"SleeperService: Processing participant: {p_display_name} (ID: {p_user_id})")

                        if not p_user_id:
                            self.logger.warning("SleeperService.fetch_all_data: Participant data found with no user_id. Skipping.")
                            continue

                        # Log participant details for debugging team names
                        participant_debug = {
                            'user_id': p_user_id,
                            'username': p_username,
                            'display_name': p_display_name,
                            'metadata': p_metadata,
                            'team_name_from_metadata': p_team_name,
                            'is_owner': p_is_owner
                        }
                        self.logger.info(f"SleeperService: Participant data for {p_user_id}: {json.dumps(participant_debug, indent=2)}")

                        # ADD THIS DEBUG LOG BEFORE SQL:
                        self.logger.info(f"SleeperService: About to upsert user {p_user_id} ({p_display_name}) into Users table")

                        cursor.execute('''
                            INSERT INTO Users (sleeper_user_id, username, display_name, avatar, created_at, updated_at)
                            VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
                            ON CONFLICT(sleeper_user_id) DO UPDATE SET
                                username = excluded.username,
                                display_name = excluded.display_name,
                                avatar = excluded.avatar,
                                updated_at = datetime('now')
                            -- Removed: WHERE Users.wallet_address IS NULL;  -- Now allows refreshing details for associated users
                        ''', (p_user_id, p_username, p_display_name, p_avatar))
                        
                        # ADD THIS DEBUG LOG AFTER SQL:
                        self.logger.info(f"SleeperService: SQL executed for user {p_user_id}, rows affected: {cursor.rowcount}")
                        
                        # Update commissioner status in UserLeagueLinks if this user has a wallet address
                        cursor.execute('''
                            SELECT wallet_address FROM Users WHERE sleeper_user_id = ? AND wallet_address IS NOT NULL
                        ''', (p_user_id,))
                        user_wallet = cursor.fetchone()
                        
                        if user_wallet:
                            participant_wallet_address = user_wallet['wallet_address']
                            # Only update the is_commissioner field if UserLeagueLinks already exists
                            cursor.execute('''
                                UPDATE UserLeagueLinks 
                                SET is_commissioner = ?, updated_at = datetime('now')
                                WHERE wallet_address = ? AND sleeper_league_id = ?
                            ''', (1 if p_is_owner else 0, participant_wallet_address, league_id))
                            
                            if p_is_owner:
                                self.logger.info(f"SleeperService: Set {p_display_name} ({participant_wallet_address}) as commissioner for league {league_id}")
                        
                        # if cursor.rowcount > 0:
                            # self.logger.info(f"SleeperService.fetch_all_data: User {p_user_id} ({p_display_name}) inserted/updated in Users table.")
                        # else:
                            # self.logger.info(f"SleeperService.fetch_all_data: User {p_user_id} ({p_display_name}) already exists with a wallet_address or no update needed. No change made to their user record by league sync.")

                # Step 4: Get rosters for this league (from API)
                rosters_from_api = self.get_league_rosters(league_id)

                local_rosters_db_players: Dict[str, List[str]] = {}
                cursor.execute("SELECT sleeper_roster_id, players FROM rosters WHERE sleeper_league_id = ?", (league_id,))
                local_roster_rows_for_check = cursor.fetchall()
                for db_roster_row in local_roster_rows_for_check:
                    try:
                        db_roster_id_str = str(db_roster_row['sleeper_roster_id'])
                        db_players_json = db_roster_row['players']
                        db_player_list = json.loads(db_players_json) if db_players_json else []
                        local_rosters_db_players[db_roster_id_str] = db_player_list
                    except Exception as e:
                        self.logger.error(f"SleeperService.fetch_all_data: Error decoding/processing local DB roster for league {league_id}, roster {db_roster_row.get('sleeper_roster_id') if db_roster_row else 'N/A'}: {e}")
                
                self.logger.info(f"SleeperService DEBUG: League {league_id} - Local rosters player lists before API sync: {json.dumps(local_rosters_db_players)}")

                if not rosters_from_api:
                    self.logger.warning(f"SleeperService.fetch_all_data: No rosters found from API for league_id {league_id}. Skipping roster processing and dropped player check for this league.")
                else:
                    # self.logger.info(f"SleeperService.fetch_all_data: Found {len(rosters_from_api)} rosters from API for league {league_id}.")
                    # print(f"DEBUG (SleeperService): Found {len(rosters_from_api)} roster records from API for league {league_id}")
                    
                    unique_player_ids_in_league = set()

                    for api_roster_item in rosters_from_api: # api_roster_item is one team's data from Sleeper API
                        api_roster_id_str = api_roster_item.get("roster_id") 
                        
                        if api_roster_id_str is None:
                            self.logger.warning(f"SleeperService.fetch_all_data: API Roster found without roster_id in league {league_id}. Skipping dropped player check and this roster item. Data: {api_roster_item}")
                            continue # Skip this iteration if API roster has no ID
                        
                        current_api_roster_id = str(api_roster_id_str)

                        # Log roster data for debugging team names
                        roster_debug = {
                            'roster_id': current_api_roster_id,
                            'owner_id': api_roster_item.get("owner_id"),
                            'metadata': api_roster_item.get("metadata", {}),
                            'team_name_from_metadata': api_roster_item.get("metadata", {}).get("team_name") if api_roster_item.get("metadata") else None
                        }
                        self.logger.info(f"SleeperService: Roster data for {current_api_roster_id}: {json.dumps(roster_debug, indent=2)}")

                        # Get API player IDs for current roster
                        api_player_ids_list = api_roster_item.get('players', []) 
                        if api_player_ids_list is None: 
                            api_player_ids_list = []
                        api_player_ids_set = set(api_player_ids_list)
                        self.logger.info(f"SleeperService DEBUG: Roster {current_api_roster_id} - API players: {list(api_player_ids_set)}")

                        # Get local player IDs for this specific roster from our map (state before this API sync)
                        local_players_for_this_roster_list = local_rosters_db_players.get(current_api_roster_id, [])
                        local_player_ids_for_this_roster_set = set(local_players_for_this_roster_list)
                        self.logger.info(f"SleeperService DEBUG: Roster {current_api_roster_id} - Local DB players (before this sync): {list(local_player_ids_for_this_roster_set)}")
                        
                        dropped_player_ids = local_player_ids_for_this_roster_set - api_player_ids_set
                        self.logger.info(f"SleeperService DEBUG: Roster {current_api_roster_id} - Calculated dropped players: {list(dropped_player_ids)}")

                        if dropped_player_ids:
                            # self.logger.info(f"SleeperService: Roster {current_api_roster_id} (League: {league_id}) has {len(dropped_player_ids)} dropped player(s): {list(dropped_player_ids)}")
                            if not season_details:
                                self.logger.error(f"SleeperService.fetch_all_data: Cannot process dropped player penalties for roster {current_api_roster_id}, league {league_id}: season details unavailable. Players: {list(dropped_player_ids)}")
                            else:
                                for dropped_player_id in dropped_player_ids:
                                    self.logger.info(f"SleeperService DEBUG: Processing dropped player {dropped_player_id} for roster {current_api_roster_id}")
                                    cursor.execute('''
                                        SELECT c.rowid, c.player_id, c.draft_amount, c.duration, c.contract_year 
                                        FROM contracts c
                                        JOIN rosters r ON c.team_id = r.sleeper_roster_id AND c.sleeper_league_id = r.sleeper_league_id
                                        WHERE c.player_id = ? AND r.sleeper_roster_id = ? AND c.sleeper_league_id = ? AND c.is_active = 1
                                    ''', (dropped_player_id, current_api_roster_id, league_id))
                                    contract_to_penalize_row = cursor.fetchone()
                                    self.logger.info(f"SleeperService DEBUG: Dropped player {dropped_player_id} - Contract query result: {dict(contract_to_penalize_row) if contract_to_penalize_row else 'No active contract found'}")

                                    if contract_to_penalize_row:
                                        contract_row_id = contract_to_penalize_row['rowid']
                                        draft_amount = contract_to_penalize_row['draft_amount']
                                        contract_duration = contract_to_penalize_row['duration']
                                        contract_start_year = contract_to_penalize_row['contract_year']
                                        year_dropped = int(season_details['current_year'])
                                        
                                        log_params = {
                                            'contract_row_id': contract_row_id,
                                            'player_id': dropped_player_id,
                                            'team_id': current_api_roster_id,
                                            'sleeper_league_id': league_id,
                                            'draft_amount': draft_amount,
                                            'contract_duration': contract_duration,
                                            'contract_start_year': contract_start_year,
                                            'year_dropped': year_dropped
                                        }
                                        self.logger.info(f"SleeperService DEBUG: Parameters for apply_contract_penalties_and_deactivate: {json.dumps(log_params)}")

                                        if None in [contract_row_id, draft_amount, contract_duration, contract_start_year, year_dropped]:
                                            self.logger.error(f"SleeperService: CRITICAL - Missing one or more key contract details for applying penalty... Skipping for player {dropped_player_id}.")
                                        else:
                                            current_is_offseason = season_details.get('is_offseason', True) # Default to True if not found, safer for penalties
                                            self.logger.info(f"SleeperService DEBUG: Passing is_currently_offseason_when_dropped={current_is_offseason} to penalty function for player {dropped_player_id}.")
                                            apply_contract_penalties_and_deactivate(
                                                contract_row_id=contract_row_id,
                                                draft_amount=float(draft_amount),
                                                contract_duration=int(contract_duration),
                                                contract_start_year=int(contract_start_year),
                                                year_dropped=year_dropped,
                                                is_currently_offseason_when_dropped=current_is_offseason,
                                                db_conn=self.conn,
                                                logger=self.logger
                                            )
                                            self.logger.info(f"SleeperService: Successfully processed penalties and deactivation for player {dropped_player_id}, contract_rowid {contract_row_id}.")
                        # END OF NEW DROPPED PLAYER LOGIC (before upserting the roster with API data)
                        
                        # Existing roster processing logic starts here, using api_roster_item
                        # The variable 'roster_id_str' from api_roster_item.get("roster_id") is already defined as api_roster_id
                        # We used current_api_roster_id for penalty part, which is str(api_roster_id_str)
                        
                        # Re-affirm roster_id for upsert from the API item (which is api_roster_item)
                        # api_roster_id_str was already checked for None and loop continued if so.
                        roster_id_for_upsert = str(api_roster_id_str) # This is the PK for 'rosters' table

                        owner_id = api_roster_item.get("owner_id") 
                        
                        # Enhanced team name resolution with debugging and improved priority
                        team_name_debug_info = {
                            'roster_id': roster_id_for_upsert,
                            'league_id': league_id,
                            'owner_id': owner_id,
                            'available_sources': {}
                        }
                        
                        # Source 1: Roster metadata team name (custom team name set by user)
                        roster_metadata = api_roster_item.get("metadata", {}) or {} 
                        custom_roster_team_name = roster_metadata.get("team_name")
                        team_name_debug_info['available_sources']['roster_metadata'] = {
                            'value': custom_roster_team_name,
                            'source': 'roster.metadata.team_name'
                        }
                        
                        # Source 2: User's league-specific team name (from participant metadata)
                        owner_display_name = None
                        owner_league_specific_team_name = None
                        owner_username = None
                        
                        if owner_id and owner_id in participant_map:
                            participant_details = participant_map[owner_id]
                            owner_display_name = participant_details.get("display_name")
                            owner_username = participant_details.get("username")
                            participant_user_metadata = participant_details.get("metadata", {}) or {} 
                            owner_league_specific_team_name = participant_user_metadata.get("team_name")
                            
                            team_name_debug_info['available_sources']['participant_metadata'] = {
                                'value': owner_league_specific_team_name,
                                'source': 'participant.metadata.team_name',
                                'participant_details': {
                                    'display_name': owner_display_name,
                                    'username': owner_username
                                }
                            }
                        else:
                            team_name_debug_info['available_sources']['participant_metadata'] = {
                                'value': None,
                                'source': 'participant.metadata.team_name',
                                'error': f'Owner ID {owner_id} not found in participant_map'
                            }
                        
                        # Source 3: User's display name (fallback)
                        team_name_debug_info['available_sources']['display_name'] = {
                            'value': owner_display_name,
                            'source': 'participant.display_name'
                        }
                        
                        # Source 4: User's username (final fallback)
                        team_name_debug_info['available_sources']['username'] = {
                            'value': owner_username,
                            'source': 'participant.username'
                        }
                        
                        # Enhanced priority logic with validation
                        team_name_to_store = "Unknown Team"
                        selected_source = "default"
                        
                        # Priority 1: Custom roster team name (user explicitly set this)
                        if custom_roster_team_name and custom_roster_team_name.strip():
                            team_name_to_store = custom_roster_team_name.strip()
                            selected_source = "roster_metadata"
                            self.logger.info(f"SleeperService: Roster {roster_id_for_upsert} using custom roster team name: '{team_name_to_store}'")
                        
                        # Priority 2: League-specific team name (user set for this league)
                        elif owner_league_specific_team_name and owner_league_specific_team_name.strip():
                            team_name_to_store = owner_league_specific_team_name.strip()
                            selected_source = "participant_metadata"
                            self.logger.info(f"SleeperService: Roster {roster_id_for_upsert} using league-specific team name: '{team_name_to_store}'")
                        
                        # Priority 3: User's display name (general user preference)
                        elif owner_display_name and owner_display_name.strip():
                            team_name_to_store = owner_display_name.strip()
                            selected_source = "display_name"
                            self.logger.info(f"SleeperService: Roster {roster_id_for_upsert} using display name as team name: '{team_name_to_store}'")
                        
                        # Priority 4: User's username (final fallback)
                        elif owner_username and owner_username.strip():
                            team_name_to_store = owner_username.strip()
                            selected_source = "username"
                            self.logger.info(f"SleeperService: Roster {roster_id_for_upsert} using username as team name: '{team_name_to_store}'")
                        
                        # Priority 5: Default fallback
                        else:
                            team_name_to_store = f"Unknown Team (Owner: {owner_id})"
                            selected_source = "default"
                            self.logger.warning(f"SleeperService: Roster {roster_id_for_upsert} - No valid team name found, using default")
                        
                        # Add final selection to debug info
                        team_name_debug_info['final_selection'] = {
                            'team_name': team_name_to_store,
                            'selected_source': selected_source
                        }
                        
                        # Log comprehensive debug information
                        self.logger.info(f"SleeperService: Team name resolution for roster {roster_id_for_upsert} (league {league_id}): {json.dumps(team_name_debug_info, indent=2)}")
                        
                        # Additional validation: Check for suspicious team names
                        if team_name_to_store.lower() in ['unknown team', 'unknown', 'n/a', 'null', '']:
                            self.logger.warning(f"SleeperService: Roster {roster_id_for_upsert} has suspicious team name: '{team_name_to_store}'. Debug info: {json.dumps(team_name_debug_info)}")
                        
                        # self.logger.debug(f"SleeperService: Determined team name for API roster {roster_id_for_upsert} (owner: {owner_id}) as '{team_name_to_store}'")

                        # players_list for upsert should be from the API (api_player_ids_list)
                        # The original code was: players_list = roster.get("players") which is api_player_ids_list
                        # We used current_api_roster_id for penalty part, which is str(api_roster_id_str)
                        if api_player_ids_list is None: # Should have been caught by earlier default to []
                            # self.logger.debug(f"SleeperService: API Roster {roster_id_for_upsert} in league {league_id} has a null 'players' field. Storing as empty list.")
                            players_json_for_upsert = json.dumps([])
                        elif not isinstance(api_player_ids_list, list): # Should be a list due to earlier handling
                            self.logger.warning(f"SleeperService: API Roster {roster_id_for_upsert} players field is not a list (type: {type(api_player_ids_list)}). Storing as empty list. Data: {api_player_ids_list}")
                            players_json_for_upsert = json.dumps([])
                        else:
                            players_json_for_upsert = json.dumps(api_player_ids_list)
                            for player_id_val in api_player_ids_list: 
                                unique_player_ids_in_league.add(player_id_val)
                        
                        current_metadata = api_roster_item.get("metadata")
                        metadata_json = json.dumps(current_metadata if current_metadata is not None else {})
                        reserve_list = api_roster_item.get("reserve")
                        reserve_json = json.dumps(reserve_list if reserve_list else [])
                        roster_settings = api_roster_item.get("settings", {})
                        wins = roster_settings.get("wins", 0)
                        losses = roster_settings.get("losses", 0)
                        ties = roster_settings.get("ties", 0)
                        points_for = roster_settings.get("fpts", 0.0)  # Changed from "points_for" to "fpts" to match Sleeper API

                        # self.logger.debug(f"SleeperService.fetch_all_data: Upserting roster_id {roster_id_for_upsert} (from API) for league {league_id} with team_name '{team_name_to_store}'.")
                        # print(f"DEBUG_SS_ROSTER_UPSERT: Attempting to upsert roster_id: {roster_id_for_upsert}, league_id: {league_id}, owner_id: {owner_id}, team_name: {team_name_to_store}")
                        cursor.execute('''
                            INSERT INTO rosters (
                                sleeper_roster_id, sleeper_league_id, owner_id, team_name, players, metadata, reserve,
                                wins, losses, ties, points_for, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                            ON CONFLICT(sleeper_roster_id, sleeper_league_id) DO UPDATE SET
                                owner_id = excluded.owner_id,
                                team_name = excluded.team_name,
                                players = excluded.players,
                                metadata = excluded.metadata,
                                reserve = excluded.reserve,
                                wins = excluded.wins,
                                losses = excluded.losses,
                                ties = excluded.ties,
                                points_for = excluded.points_for,
                                updated_at = datetime('now')
                        ''', (
                            roster_id_for_upsert, league_id, owner_id, team_name_to_store, players_json_for_upsert, metadata_json, 
                            reserve_json, wins, losses, ties, points_for
                        ))
                        # print(f"DEBUG_SS_ROSTER_UPSERT_RESULT: Roster_id: {roster_id_for_upsert}, league_id: {league_id}, cursor.rowcount: {cursor.rowcount}")
                    
                    # self.logger.info(f"SleeperService.fetch_all_data: Finished processing {len(rosters_from_api)} API rosters for league {league_id}.")
                    # print(f"DEBUG (SleeperService): Total unique players found on API rosters in league {league_id}: {len(unique_player_ids_in_league)}")

                # Step 5: Get transactions for this league
                # First, get current NFL state to determine max week
                nfl_state = self.get_nfl_state()
                current_week = nfl_state.get('week', 18) if nfl_state else 18  # Default to 18 if fetch fails

                league_transactions = []
                for week in range(1, current_week + 1):
                    self.logger.info(f"Fetching transactions for league {league_id}, week {week}")
                    week_transactions = self.get_league_transactions(league_id, week)
                    if week_transactions:
                        league_transactions.extend(week_transactions)
                    else:
                        self.logger.warning(f"No transactions found for league {league_id}, week {week}")

                if not league_transactions:
                    self.logger.warning(f"SleeperService.fetch_all_data: No transactions found across all weeks for league {league_id}")
                else:
                    self.logger.info(f"SleeperService.fetch_all_data: Found {len(league_transactions)} total transactions across all weeks for league {league_id}.")
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

                # Step 7: Get drafts for this league (conditional based on season status)
                # Check if we should skip draft processing based on league status or NFL state
                should_skip_drafts = False
                skip_reason = ""
                
                # Check 1: League status is "InSeason"
                if league_status == "InSeason":
                    should_skip_drafts = True
                    skip_reason = f"League status is '{league_status}' (InSeason)"
                
                # Check 2: NFL state indicates active season (not offseason)
                elif season_details and not season_details.get('is_offseason', True):
                    should_skip_drafts = True
                    skip_reason = f"NFL state indicates active season (is_offseason=False)"
                
                if should_skip_drafts:
                    self.logger.info(f"SleeperService.fetch_all_data: Skipping draft data pull for league {league_id} - {skip_reason}")
                else:
                    # Proceed with draft processing as before
                    league_drafts = self.get_league_drafts(league_id)
                    if not league_drafts:
                        self.logger.warning(f"SleeperService.fetch_all_data: No drafts found for league {league_id}.")
                    else:
                        # self.logger.info(f"SleeperService.fetch_all_data: Found {len(league_drafts)} drafts for league {league_id}.")
                        for draft_data in league_drafts:
                            d_draft_id = draft_data.get("draft_id")
                            d_status = draft_data.get("status")
                            d_start_time = draft_data.get("start_time")
                            d_season = draft_data.get("season")

                            # Determine what to store in d_data_json
                            if d_draft_id and draft_data.get("type") == "auction" and d_status == "complete":
                                # self.logger.info(f"SleeperService.fetch_all_data: Fetching picks for completed auction draft {d_draft_id} in league {league_id}.")
                                picks_data = self.get_draft_picks(d_draft_id)
                                if picks_data: # If picks were successfully fetched
                                    d_data_json = json.dumps(picks_data) # Ensure d_data_json is set with actual picks
                                    # self.logger.info(f"SleeperService.fetch_all_data: Storing actual picks for draft {d_draft_id}.")

                                    # --- Create default 1-year contracts for these auction acquisitions ---
                                    if d_season: # Ensure we have a season for the contract_year
                                        for pick in picks_data: # picks_data is the list of pick objects
                                            picked_player_id = pick.get('player_id')
                                            pick_metadata = pick.get('metadata', {})
                                            auction_amount_str = pick_metadata.get('amount')
                                            drafting_team_roster_id_int = pick.get('roster_id') # This is sleeper_roster_id

                                            if picked_player_id and auction_amount_str is not None and drafting_team_roster_id_int is not None:
                                                try:
                                                    auction_amount = int(auction_amount_str)
                                                    contract_year_int = int(d_season)
                                                    team_id_str = str(drafting_team_roster_id_int)

                                                    # Check if an active contract already exists for this player, team, and league
                                                    cursor.execute('''
                                                        SELECT 1 FROM contracts
                                                        WHERE player_id = ? AND team_id = ? AND sleeper_league_id = ? AND is_active = 1
                                                    ''', (picked_player_id, team_id_str, league_id))
                                                    existing_active_contract = cursor.fetchone()

                                                    if not existing_active_contract:
                                                        # self.logger.info(f"SleeperService: No existing active contract for player {picked_player_id}, team {team_id_str}, league {league_id}. Creating default 1-year contract, amount ${auction_amount}, season {d_season}.")
                                                        cursor.execute('''
                                                            INSERT OR IGNORE INTO contracts 
                                                                (player_id, team_id, sleeper_league_id, draft_amount, contract_year, duration, is_active, created_at, updated_at)
                                                            VALUES (?, ?, ?, ?, ?, 1, 1, datetime('now'), datetime('now'))
                                                        ''', (picked_player_id, team_id_str, league_id, auction_amount, contract_year_int))
                                                    else:
                                                        # self.logger.info(f"SleeperService: Existing active contract found for player {picked_player_id}, team {team_id_str}, league {league_id}. Skipping default contract creation.")
                                                        pass 
                                                except ValueError as e:
                                                    self.logger.error(f"SleeperService: Error converting data for default contract for player {picked_player_id}: {e} (amount: {auction_amount_str}, season: {d_season})")
                                            else:
                                                # self.logger.warning(f"SleeperService: Missing data for default contract creation from pick: {pick}")
                                                pass 
                                    else:
                                        # self.logger.warning(f"SleeperService: Missing season for draft {d_draft_id}, cannot create default contracts.")
                                        pass 
                                else: 
                                    self.logger.warning(f"SleeperService.fetch_all_data: Failed to fetch picks for completed auction draft {d_draft_id}. Storing metadata instead.")
                                    d_data_json = json.dumps(draft_data)
                            else: 
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

                            # self.logger.debug(f"SleeperService.fetch_all_data: Upserting draft {d_draft_id} for league {league_id}.")
                            cursor.execute('''
                                INSERT INTO drafts (sleeper_draft_id, league_id, season, status, start_time, data, created_at, updated_at)
                                VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                                ON CONFLICT(sleeper_draft_id) DO UPDATE SET
                                    league_id = excluded.league_id,
                                    season = excluded.season,
                                    status = excluded.status,
                                    start_time = excluded.start_time,
                                    data = excluded.data,
                                    updated_at = datetime('now')
                            ''', (d_draft_id, league_id, d_season, d_status, d_start_time_iso, d_data_json))
            
            # self.logger.info(f"SleeperService.fetch_all_data: Completed processing for wallet {wallet_address}.")
            self.conn.commit() # Commit all changes if the entire fetch_all_data process was successful
            return {"success": True, "message": "All data fetched and stored successfully"}

        except sqlite3.Error as sqle:
            self.logger.error(f"SleeperService.fetch_all_data: SQLite error for wallet {wallet_address}: {str(sqle)}")
            return {"success": False, "error": f"Database error: {str(sqle)}"}
        except ValueError as ve:
            self.logger.error(f"SleeperService.fetch_all_data: Value error (likely DB connection issue) for wallet {wallet_address}: {str(ve)}")
            return {"success": False, "error": f"Configuration error: {str(ve)}"}
        except Exception as e: # Outer exception catch for all other errors, including those from apply_contract_penalties_and_deactivate
            self.logger.error(f"SleeperService.fetch_all_data: Outer exception for wallet {wallet_address}: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            if self.conn:
                try: 
                    self.logger.info(f"SleeperService.fetch_all_data: Rolling back transaction due to error: {e}")
                    self.conn.rollback()
                except Exception as roll_e: 
                    self.logger.error(f"SleeperService: Error during rollback attempt: {roll_e}")
            return {"success": False, "error": f"Server error during fetch_all_data: {str(e)}"} 

    def update_all_sleeper_players(self) -> Dict[str, Any]:
        """
        Fetch all NFL players from Sleeper API and update the local players table.
        This should be called periodically (e.g., daily/weekly) rather than on every user action.

        Returns:
            Dict: Result of the operation with success status and message/error.
        """
        # self.logger.info("SleeperService.update_all_sleeper_players: Starting general player data update...")
        # print("DEBUG (SleeperService): Starting update_all_sleeper_players...") # Keep print
        try:
            cursor = self._get_db_cursor()
            
            all_players_api_data = self.get_players()
            if not all_players_api_data:
                self.logger.error("SleeperService.update_all_sleeper_players: Failed to retrieve any player data from Sleeper API.")
                return {"success": False, "error": "Failed to retrieve player data from Sleeper API."}
            
            # self.logger.info(f"SleeperService.update_all_sleeper_players: Retrieved {len(all_players_api_data)} players from Sleeper API.")
            # print(f"DEBUG (SleeperService): Retrieved {len(all_players_api_data)} players from Sleeper API for general update.") # Keep print
            
            players_to_insert = []
            # Define allowed positions. Consider making this a class constant or configurable if it changes.
            allowed_positions = {'QB', 'RB', 'WR', 'TE', 'DEF'} 
            
            for player_id, player_info in all_players_api_data.items():
                player_position = player_info.get('position')
                if player_position in allowed_positions:
                    players_to_insert.append((
                        player_id,
                        player_info.get('full_name', player_info.get('first_name', '') + ' ' + player_info.get('last_name', '')).strip(),
                        player_position,
                        player_info.get('team') # This will be None if the player is a free agent
                    ))
                else:
                    # self.logger.debug(f"SleeperService.update_all_sleeper_players: Skipping player {player_id} (Name: {player_info.get('full_name', 'N/A')}) due to position: {player_position}")
                    pass # No action for skipped players
            
            if players_to_insert:
                # self.logger.info(f"SleeperService.update_all_sleeper_players: Bulk inserting/updating {len(players_to_insert)} players into DB.")
                cursor.executemany('''
                    INSERT INTO players (sleeper_player_id, name, position, team, created_at, updated_at)
                    VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
                    ON CONFLICT(sleeper_player_id) DO UPDATE SET
                        name=excluded.name, 
                        position=excluded.position, 
                        team=excluded.team,
                        updated_at=datetime('now')
                ''', players_to_insert)
                # self.conn.commit() # Commit changes if autocommit is not enabled
                # self.logger.info(f"SleeperService.update_all_sleeper_players: Added/Updated {len(players_to_insert)} players to the database.")
                # print(f"DEBUG (SleeperService): update_all_sleeper_players - Added/Updated {len(players_to_insert)} players.") # Keep print
                return {"success": True, "message": f"Successfully updated {len(players_to_insert)} players."}
            else:
                # self.logger.info("SleeperService.update_all_sleeper_players: No players matched the position criteria (QB, RB, WR, TE, DEF) to be inserted/updated.")
                # print("DEBUG (SleeperService): update_all_sleeper_players - No players matched position criteria.") # Keep print
                return {"success": True, "message": "No players matched criteria to update."}

        except sqlite3.Error as sqle:
            self.logger.error(f"SleeperService.update_all_sleeper_players: SQLite error: {str(sqle)}")
            # self.conn.rollback() # Rollback in case of error
            return {"success": False, "error": f"Database error: {str(sqle)}"}
        except ValueError as ve: # For _get_db_cursor errors
            self.logger.error(f"SleeperService.update_all_sleeper_players: Value error (likely DB connection issue): {str(ve)}")
            return {"success": False, "error": f"Configuration error: {str(ve)}"}
        except Exception as e:
            self.logger.error(f"SleeperService.update_all_sleeper_players: Unexpected error: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            # self.conn.rollback() # Rollback in case of error
            return {"success": False, "error": f"Server error: {str(e)}"} 