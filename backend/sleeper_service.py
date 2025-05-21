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

                # Extract data for LeagueMetadata
                league_name = full_league_details.get("name", "Unknown League")

                if not league_name.startswith("SKL"):
                    self.logger.info(f"SleeperService.fetch_all_data: Skipping league '{league_name}' (ID: {league_id}) because its name does not start with 'SKL'.")
                    print(f"DEBUG (SleeperService): Skipping league '{league_name}' (ID: {league_id}) due to naming convention.") # Optional: for more prominent console debugging
                    continue

                league_season_year = full_league_details.get("season", current_api_season) # current_api_season is defined earlier
                league_status = full_league_details.get("status", "unknown")
                league_settings_json = json.dumps(full_league_details.get("settings", {}))
                league_scoring_settings_json = json.dumps(full_league_details.get("scoring_settings", {}))
                league_roster_positions_json = json.dumps(full_league_details.get("roster_positions", []))
                league_previous_league_id = full_league_details.get("previous_league_id")
                # Sleeper's league_creation_time is often in metadata, but can vary or be absent.
                # It's usually a Unix timestamp in milliseconds.
                league_metadata_obj = full_league_details.get("metadata", {})
                league_creation_time_ms = league_metadata_obj.get("league_creation_time") if isinstance(league_metadata_obj, dict) else None

                league_avatar = full_league_details.get("avatar")
                # Other fields from LeagueMetadata schema (display_order, company_id, bracket_id)
                # are not standard in Sleeper's main league object. They might be in settings or metadata if at all.
                # For now, we'll insert NULL or default for them if not directly found.
                # display_order = full_league_details.get("display_order") # unlikely to be top-level
                # company_id = full_league_details.get("company_id") # unlikely
                # bracket_id = full_league_details.get("bracket_id") # unlikely

                # Store/Update LeagueMetadata
                self.logger.debug(f"SleeperService.fetch_all_data: Upserting league {league_id} into LeagueMetadata.")
                cursor.execute('''
                    INSERT INTO LeagueMetadata (
                        sleeper_league_id, name, season, status, settings, 
                        scoring_settings, roster_positions, previous_league_id, 
                        league_creation_time, avatar, created_at, updated_at,
                        display_order, company_id, bracket_id 
                        -- Ensure all columns from app.py's LeagueMetadata are listed
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
                    None, None, None # Values for display_order, company_id, bracket_id
                ))
                
                # Link user to this league in UserLeagueLinks
                self.logger.debug(f"SleeperService.fetch_all_data: Linking wallet {wallet_address} to league {league_id} in UserLeagueLinks.")
                cursor.execute('''
                    INSERT OR IGNORE INTO UserLeagueLinks (wallet_address, sleeper_league_id)
                    VALUES (?, ?)
                ''', (wallet_address, league_id))

                # Step 3: Get rosters for this league
                rosters = self.get_league_rosters(league_id)
                if not rosters:
                    self.logger.warning(f"SleeperService.fetch_all_data: No rosters found for league_id {league_id}. Skipping roster processing.")
                else:
                    self.logger.info(f"SleeperService.fetch_all_data: Found {len(rosters)} rosters for league {league_id}.")
                    print(f"DEBUG (SleeperService): Found {len(rosters)} roster records for league {league_id}")
                    
                    unique_player_ids_in_league = set()

                    for roster in rosters:
                        roster_id_str = roster.get("roster_id") # Sleeper roster_id is an int, but we store as TEXT
                        if roster_id_str is None:
                            self.logger.warning(f"SleeperService.fetch_all_data: Roster found without roster_id in league {league_id}. Skipping.")
                            continue
                        
                        # Ensure roster_id is string for DB consistency if it's ever not
                        roster_id = str(roster_id_str)

                        # Prepare roster data for DB insertion/update
                        # owner_id is the sleeper_user_id of the roster owner
                        owner_id = roster.get("owner_id") 
                        
                        # Players list (player_ids on this roster)
                        players_list = roster.get("players")
                        if players_list is None:
                            self.logger.debug(f"SleeperService: Roster {roster_id} in league {league_id} has a null 'players' field. Storing as empty list.")
                            players_json = json.dumps([])
                        elif not isinstance(players_list, list):
                            self.logger.warning(f"SleeperService: Roster {roster_id} players field is not a list (type: {type(players_list)}). Storing as empty list. Data: {players_list}")
                            print(f"DEBUG (SleeperService): Roster {roster_id} players not in list format or is None: {type(players_list)}")
                            players_json = json.dumps([])
                        else:
                            players_json = json.dumps(players_list)
                            for player_id in players_list:
                                unique_player_ids_in_league.add(player_id)
                        
                        current_metadata = roster.get("metadata")
                        metadata_json = json.dumps(current_metadata if current_metadata is not None else {})

                        reserve_list = roster.get("reserve")
                        reserve_json = json.dumps(reserve_list if reserve_list else [])

                        taxi_list = roster.get("taxi")
                        taxi_json = json.dumps(taxi_list if taxi_list else [])

                        # Extract wins, losses, ties from roster.settings
                        roster_settings = roster.get("settings", {})
                        wins = roster_settings.get("wins", 0)
                        losses = roster_settings.get("losses", 0)
                        ties = roster_settings.get("ties", 0)

                        self.logger.debug(f"SleeperService.fetch_all_data: Upserting roster_id {roster_id} for league {league_id}.")
                        print(f"DEBUG_SS_ROSTER_UPSERT: Attempting to upsert roster_id: {roster_id}, league_id: {league_id}, owner_id: {owner_id}")
                        cursor.execute('''
                            INSERT INTO rosters (
                                sleeper_roster_id, sleeper_league_id, owner_id, players, metadata, reserve, taxi,
                                wins, losses, ties, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                            ON CONFLICT(sleeper_roster_id, sleeper_league_id) DO UPDATE SET
                                sleeper_league_id = excluded.sleeper_league_id,
                                owner_id = excluded.owner_id,
                                players = excluded.players,
                                metadata = excluded.metadata,
                                reserve = excluded.reserve,
                                taxi = excluded.taxi,
                                wins = excluded.wins,
                                losses = excluded.losses,
                                ties = excluded.ties,
                                updated_at = datetime('now')
                        ''', (
                            roster_id, league_id, owner_id, players_json, metadata_json, 
                            reserve_json, taxi_json, wins, losses, ties
                        ))
                        print(f"DEBUG_SS_ROSTER_UPSERT_RESULT: Roster_id: {roster_id}, league_id: {league_id}, cursor.rowcount: {cursor.rowcount}")
                    
                    self.logger.info(f"SleeperService.fetch_all_data: Finished processing {len(rosters)} rosters for league {league_id}.")
                    print(f"DEBUG (SleeperService): Total unique players found on rosters in league {league_id}: {len(unique_player_ids_in_league)}")

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
                        d_season = draft_data.get("season")

                        # Determine what to store in d_data_json
                        if d_draft_id and draft_data.get("type") == "auction" and d_status == "complete":
                            self.logger.info(f"SleeperService.fetch_all_data: Fetching picks for completed auction draft {d_draft_id} in league {league_id}.")
                            picks_data = self.get_draft_picks(d_draft_id)
                            if picks_data: # If picks were successfully fetched
                                d_data_json = json.dumps(picks_data) # Ensure d_data_json is set with actual picks
                                self.logger.info(f"SleeperService.fetch_all_data: Storing actual picks for draft {d_draft_id}.")

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

                                                self.logger.info(f"SleeperService: Creating default 1-year contract for player {picked_player_id} on team {team_id_str}, amount ${auction_amount}, season {d_season}.")
                                                cursor.execute('''
                                                    INSERT OR IGNORE INTO contracts 
                                                        (player_id, team_id, draft_amount, contract_year, duration, is_active, created_at, updated_at)
                                                    VALUES (?, ?, ?, ?, 1, 1, datetime('now'), datetime('now'))
                                                ''', (picked_player_id, team_id_str, auction_amount, contract_year_int))
                                            except ValueError as e:
                                                self.logger.error(f"SleeperService: Error converting data for default contract for player {picked_player_id}: {e} (amount: {auction_amount_str}, season: {d_season})")
                                        else:
                                            self.logger.warning(f"SleeperService: Missing data for default contract creation from pick: {pick}")
                                else:
                                    self.logger.warning(f"SleeperService: Missing season for draft {d_draft_id}, cannot create default contracts.")
                                # --- End default contract creation ---

                            else: # Fallback if fetching picks fails, store original draft_data
                                self.logger.warning(f"SleeperService.fetch_all_data: Failed to fetch picks for completed auction draft {d_draft_id}. Storing metadata instead.")
                                d_data_json = json.dumps(draft_data)
                        else: # For non-auction drafts or incomplete auction drafts, store the metadata
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
                allowed_positions = {'QB', 'RB', 'WR', 'TE', 'DEF'}
                for player_id, player_info in all_players_api_data.items():
                    player_position = player_info.get('position')
                    if player_position in allowed_positions:
                        players_to_insert.append((
                            player_id,
                            player_info.get('full_name', player_info.get('first_name', '') + ' ' + player_info.get('last_name', '')).strip(),
                            player_position,
                            player_info.get('team')
                        ))
                    else:
                        self.logger.debug(f"SleeperService.fetch_all_data: Skipping player {player_id} (Name: {player_info.get('full_name', 'N/A')}) due to position: {player_position}")
                
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
                else:
                    self.logger.info("SleeperService.fetch_all_data: No players matched the position criteria (QB, RB, WR, TE, DEF) to be inserted/updated.")
                    print("DEBUG (SleeperService): No players matched position criteria for DB operation.")

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