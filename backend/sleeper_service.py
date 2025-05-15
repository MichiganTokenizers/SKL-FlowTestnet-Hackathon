import requests
import sqlite3
import json
from typing import Dict, List, Optional
import logging

class SleeperService:
    BASE_URL = "https://api.sleeper.app/v1"
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
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
    
    def fetch_all_data(self, wallet_address: str) -> Dict:
        """
        Fetch all Sleeper data for a user and store it in the local database.
        This is the main method called during login and other operations to ensure
        the local database has up-to-date information from Sleeper.
        
        Args:
            wallet_address: The wallet address of the user
            
        Returns:
            Dict: Result of the operation with success status
        """
        try:
            # Connect to the database
            with sqlite3.connect('keeper.db') as conn:
                cursor = conn.cursor()
                
                # Get the sleeper_user_id for this wallet address
                cursor.execute('SELECT sleeper_user_id FROM users WHERE wallet_address = ?', (wallet_address,))
                user_data = cursor.fetchone()
                
                if not user_data or not user_data[0]:
                    self.logger.warning(f"No Sleeper user ID associated with wallet {wallet_address}")
                    return {"success": False, "error": "No Sleeper user ID associated with this wallet"}
                
                sleeper_user_id = user_data[0]
                
                # Step 1: Get user leagues
                leagues = self.get_user_leagues(sleeper_user_id)
                if not leagues:
                    self.logger.warning(f"No leagues found for Sleeper user {sleeper_user_id}")
                    return {"success": False, "error": "No leagues found for this user"}
                
                # Step 2: Process each league
                for league in leagues:
                    league_id = league.get("league_id")
                    print(f"DEBUG: Processing league {league_id}")
                    
                    # Get current season and off-season status from season_curr table
                    cursor.execute('SELECT current_year, IsOffSeason FROM season_curr LIMIT 1')
                    season_data = cursor.fetchone()
                    
                    if season_data:
                        current_year = season_data[0]
                        is_off_season = season_data[1]
                        # Convert numeric is_off_season to text status
                        season_status = "off" if is_off_season == 1 else "in"
                    else:
                        # Default values if season_curr table is not set up
                        current_year = league.get("season")
                        season_status = league.get("status")
                    
                    # Store league details
                    cursor.execute('''
                        INSERT OR REPLACE INTO leagues (
                            sleeper_league_id,
                            sleeper_user_id,
                            name,
                            season,
                            status,
                            settings,
                            created_at,
                            updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, datetime("now"), datetime("now"))
                    ''', (
                        league_id,
                        sleeper_user_id,
                        league.get("name"),
                        current_year,  # Use value from season_curr
                        season_status, # Use value from season_curr
                        json.dumps(league.get("settings", {}))
                    ))
                    
                    # Step 3: Get and store league users
                    league_users = self.get_league_users(league_id)
                    for user in league_users:
                        user_id = user.get("user_id")
                        metadata_json = json.dumps(user.get("metadata", {})) if user.get("metadata") else None
                        
                        cursor.execute('''
                            INSERT OR REPLACE INTO users (
                                sleeper_user_id,
                                display_name,
                                avatar,
                                metadata,
                                created_at,
                                updated_at
                            ) VALUES (?, ?, ?, ?, datetime("now"), datetime("now"))
                        ''', (
                            user_id,
                            user.get("display_name"),
                            user.get("avatar"),
                            metadata_json
                        ))
                    
                    # Step 4: Get and store rosters
                    rosters = self.get_league_rosters(league_id)
                    for roster in rosters:
                        roster_id = roster.get("roster_id")
                        
                        cursor.execute('''
                            INSERT OR REPLACE INTO rosters (
                                sleeper_roster_id,
                                league_id,
                                owner_id,
                                players,
                                settings,
                                metadata,
                                created_at,
                                updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, datetime("now"), datetime("now"))
                        ''', (
                            str(roster_id),
                            league_id,
                            roster.get("owner_id"),
                            json.dumps(roster.get("players", [])),
                            json.dumps(roster.get("settings", {})),
                            json.dumps(roster.get("metadata", {}))
                        ))
                    
                    # Step 5: Get and store transactions
                    transactions = self.get_league_transactions(league_id)
                    for transaction in transactions:
                        transaction_id = transaction.get("transaction_id")
                        
                        cursor.execute('''
                            INSERT OR IGNORE INTO transactions (
                                sleeper_transaction_id,
                                league_id,
                                type,
                                status,
                                data,
                                created_at,
                                updated_at
                            ) VALUES (?, ?, ?, ?, ?, datetime("now"), datetime("now"))
                        ''', (
                            str(transaction_id),
                            league_id,
                            transaction.get("type"),
                            transaction.get("status"),
                            json.dumps(transaction)
                        ))
                    
                    # Step 6: Get and store traded picks
                    traded_picks = self.get_traded_picks(league_id)
                    for pick in traded_picks:
                        cursor.execute('''
                            INSERT OR IGNORE INTO traded_picks (
                                league_id,
                                draft_id,
                                round,
                                roster_id,
                                previous_owner_id,
                                current_owner_id,
                                created_at,
                                updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, datetime("now"), datetime("now"))
                        ''', (
                            league_id,
                            pick.get("draft_id"),
                            pick.get("round"),
                            str(pick.get("roster_id")),
                            str(pick.get("previous_owner_id")),
                            str(pick.get("owner_id"))
                        ))
                    
                    # Step 7: Get and store drafts
                    drafts = self.get_league_drafts(league_id)
                    for draft in drafts:
                        draft_id = draft.get("draft_id")
                        
                        cursor.execute('''
                            INSERT OR REPLACE INTO drafts (
                                sleeper_draft_id,
                                league_id,
                                status,
                                start_time,
                                data,
                                created_at,
                                updated_at
                            ) VALUES (?, ?, ?, ?, ?, datetime("now"), datetime("now"))
                        ''', (
                            draft_id,
                            league_id,
                            draft.get("status"),
                            draft.get("start_time"),
                            json.dumps(draft)
                        ))
                
                # Step 8: Get and store player data
                print("DEBUG: Starting player data import...")
                players_data = self.get_players()
                if players_data:
                    print(f"DEBUG: Retrieved {len(players_data)} players from Sleeper API")
                    self.logger.info(f"Retrieved {len(players_data)} players from Sleeper API")
                    
                    # Store only players that are on rosters to avoid storing thousands of unused players
                    player_ids_on_rosters = set()
                    
                    # Get all roster players
                    try:
                        cursor.execute('SELECT players FROM rosters')
                        roster_players = cursor.fetchall()
                        print(f"DEBUG: Found {len(roster_players)} roster records")
                    except Exception as e:
                        print(f"DEBUG: Error querying rosters table: {str(e)}")
                        roster_players = []
                    
                    for roster in roster_players:
                        if roster[0]:
                            try:
                                players_list = json.loads(roster[0])
                                print(f"DEBUG: Roster players raw data: {roster[0][:100]}...")
                                if isinstance(players_list, list):
                                    player_ids_on_rosters.update(players_list)
                                    print(f"DEBUG: Added {len(players_list)} players from roster")
                                else:
                                    print(f"DEBUG: Players not in list format: {type(players_list)}")
                            except json.JSONDecodeError:
                                self.logger.error(f"Error parsing players JSON: {roster[0]}")
                                print(f"DEBUG: JSON decode error for roster: {roster[0][:100]}...")
                    
                    print(f"DEBUG: Total unique players found on rosters: {len(player_ids_on_rosters)}")
                    self.logger.info(f"Found {len(player_ids_on_rosters)} players on rosters")
                    
                    # If no players found on rosters, use a sample set of top players
                    if not player_ids_on_rosters:
                        print("DEBUG: No players found on rosters, adding top players")
                        top_players = []
                        positions = ['QB', 'RB', 'WR', 'TE']
                        
                        # Get top 25 players for each position
                        for position in positions:
                            print(f"DEBUG: Selecting top players for position {position}")
                            count = 0
                            for player_id, player_data in players_data.items():
                                if player_data.get('position') == position and count < 25:
                                    if not player_data.get('active', True):
                                        continue
                                    top_players.append(player_id)
                                    count += 1
                                    if count >= 25:
                                        break
                            print(f"DEBUG: Added {count} {position} players")
                        
                        player_ids_on_rosters = top_players
                        print(f"DEBUG: Adding {len(top_players)} top players")
                    
                    # Check if players table exists
                    try:
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='players'")
                        table_exists = cursor.fetchone() is not None
                        if not table_exists:
                            print("DEBUG: players table doesn't exist, creating it")
                            cursor.execute('''
                                CREATE TABLE IF NOT EXISTS players (
                                    sleeper_player_id TEXT UNIQUE,
                                    name TEXT,
                                    position TEXT,
                                    team TEXT,
                                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    updated_at DATETIME
                                )
                            ''')
                    except Exception as e:
                        print(f"DEBUG: Error checking/creating players table: {str(e)}")
                    
                    # Insert each player that's on a roster
                    players_added = 0
                    for player_id in player_ids_on_rosters:
                        player_data = players_data.get(player_id)
                        if player_data:
                            try:
                                print(f"DEBUG: Inserting player {player_id}: {player_data.get('full_name', 'Unknown')}")
                                cursor.execute('''
                                    INSERT OR REPLACE INTO players (
                                        sleeper_player_id,
                                        name,
                                        position,
                                        team,
                                        created_at,
                                        updated_at
                                    ) VALUES (?, ?, ?, ?, datetime("now"), datetime("now"))
                                ''', (
                                    player_id,
                                    player_data.get('full_name'),
                                    player_data.get('position'),
                                    player_data.get('team'),
                                ))
                                players_added += 1
                                if players_added % 20 == 0:
                                    print(f"DEBUG: Added {players_added} players so far")
                            except Exception as e:
                                self.logger.error(f"Error inserting player {player_id}: {str(e)}")
                                print(f"DEBUG: Error inserting player {player_id}: {str(e)}")
                        else:
                            print(f"DEBUG: Player {player_id} not found in players data")
                    
                    print(f"DEBUG: Added {players_added} players to the database")
                    self.logger.info(f"Added {players_added} players to the database")
                else:
                    print("DEBUG: No player data returned from Sleeper API")
                    return {"success": False, "error": "Could not retrieve player data from Sleeper API"}
                
                conn.commit()
                self.logger.info(f"Successfully fetched and stored all data for user {sleeper_user_id}")
                return {"success": True, "message": "All data fetched and stored successfully"}
                
        except Exception as e:
            self.logger.error(f"Error in fetch_all_data: {str(e)}")
            return {"success": False, "error": str(e)} 