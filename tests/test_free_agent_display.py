import pytest
import json
from unittest.mock import patch, MagicMock
import sqlite3
import tempfile
import os

# Mock the database connection and other dependencies
@pytest.fixture
def mock_db_connection():
    """Create a mock database connection for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    # Create a test database with minimal schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create minimal tables needed for the test
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY,
            player_id TEXT,
            team_id TEXT,
            sleeper_league_id TEXT,
            draft_amount REAL,
            contract_year INTEGER,
            duration INTEGER,
            is_active INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            sleeper_player_id TEXT PRIMARY KEY,
            name TEXT,
            position TEXT,
            team TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rosters (
            sleeper_roster_id TEXT,
            sleeper_league_id TEXT,
            owner_id TEXT,
            players TEXT,
            team_name TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            sleeper_user_id TEXT PRIMARY KEY,
            username TEXT,
            display_name TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS LeagueMetadata (
            sleeper_league_id TEXT PRIMARY KEY,
            name TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS UserLeagueLinks (
            wallet_address TEXT,
            sleeper_league_id TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    os.unlink(db_path)

def test_free_agent_shows_zero_draft_amount(mock_db_connection):
    """
    Test that free agents show $0 draft amount even if they were originally acquired via auction.
    """
    from backend.app import get_team_details
    
    # Setup test data
    conn = sqlite3.connect(mock_db_connection)
    cursor = conn.cursor()
    
    # Insert test data
    cursor.execute('''
        INSERT INTO users (sleeper_user_id, username, display_name)
        VALUES ('test_user', 'testuser', 'Test User')
    ''')
    
    cursor.execute('''
        INSERT INTO LeagueMetadata (sleeper_league_id, name)
        VALUES ('test_league', 'Test League')
    ''')
    
    cursor.execute('''
        INSERT INTO UserLeagueLinks (wallet_address, sleeper_league_id)
        VALUES ('test_wallet', 'test_league')
    ''')
    
    cursor.execute('''
        INSERT INTO rosters (sleeper_roster_id, sleeper_league_id, owner_id, players, team_name)
        VALUES ('test_roster', 'test_league', 'test_user', '["test_player"]', 'Test Team')
    ''')
    
    cursor.execute('''
        INSERT INTO players (sleeper_player_id, name, position, team)
        VALUES ('test_player', 'Test Player', 'QB', 'FA')
    ''')
    
    # Note: No contract record for this player, making them a free agent
    # Even though they might have been in auction_acquisitions, they should show $0
    
    conn.commit()
    conn.close()
    
    # Mock the get_current_user function
    with patch('backend.app.get_current_user') as mock_get_user:
        mock_get_user.return_value = {'wallet_address': 'test_wallet'}
        
        # Mock the get_current_season function
        with patch('backend.app.get_current_season') as mock_get_season:
            mock_get_season.return_value = {
                'current_year': 2024,
                'is_offseason': True
            }
            
            # Mock the get_global_db_connection function
            with patch('backend.app.get_global_db_connection') as mock_get_db:
                mock_get_db.return_value = sqlite3.connect(mock_db_connection)
                
                # Create a mock request
                from flask import Request
                mock_request = MagicMock()
                mock_request.args = {'league_id': 'test_league'}
                
                with patch('backend.app.request', mock_request):
                    # Call the function
                    result = get_team_details('test_roster')
                    
                    # Parse the JSON response
                    response_data = json.loads(result[0].get_data(as_text=True))
                    
                    # Verify the response
                    assert response_data['success'] is True
                    assert 'players_by_position' in response_data
                    
                    # Find the test player in the response
                    test_player_found = False
                    for position_players in response_data['players_by_position'].values():
                        for player in position_players:
                            if player['id'] == 'test_player':
                                test_player_found = True
                                # Verify that the free agent shows $0 draft amount
                                assert player['draft_amount'] == 0, f"Free agent should show $0 draft amount, but got ${player['draft_amount']}"
                                assert player['contract_status'] == 'Free Agent', f"Free agent should have 'Free Agent' status, but got '{player['contract_status']}'"
                                break
                        if test_player_found:
                            break
                    
                    assert test_player_found, "Test player not found in response"

def test_auction_player_with_active_contract_shows_auction_amount(mock_db_connection):
    """
    Test that auction players with active contracts still show their auction amount.
    """
    from backend.app import get_team_details
    
    # Setup test data
    conn = sqlite3.connect(mock_db_connection)
    cursor = conn.cursor()
    
    # Insert test data
    cursor.execute('''
        INSERT INTO users (sleeper_user_id, username, display_name)
        VALUES ('test_user', 'testuser', 'Test User')
    ''')
    
    cursor.execute('''
        INSERT INTO LeagueMetadata (sleeper_league_id, name)
        VALUES ('test_league', 'Test League')
    ''')
    
    cursor.execute('''
        INSERT INTO UserLeagueLinks (wallet_address, sleeper_league_id)
        VALUES ('test_wallet', 'test_league')
    ''')
    
    cursor.execute('''
        INSERT INTO rosters (sleeper_roster_id, sleeper_league_id, owner_id, players, team_name)
        VALUES ('test_roster', 'test_league', 'test_user', '["test_player"]', 'Test Team')
    ''')
    
    cursor.execute('''
        INSERT INTO players (sleeper_player_id, name, position, team)
        VALUES ('test_player', 'Test Player', 'QB', 'FA')
    ''')
    
    # Insert an active contract for this player (auction acquisition)
    cursor.execute('''
        INSERT INTO contracts (player_id, team_id, sleeper_league_id, draft_amount, contract_year, duration, is_active)
        VALUES ('test_player', 'test_roster', 'test_league', 25, 2024, 1, 1)
    ''')
    
    conn.commit()
    conn.close()
    
    # Mock the get_current_user function
    with patch('backend.app.get_current_user') as mock_get_user:
        mock_get_user.return_value = {'wallet_address': 'test_wallet'}
        
        # Mock the get_current_season function
        with patch('backend.app.get_current_season') as mock_get_season:
            mock_get_season.return_value = {
                'current_year': 2024,
                'is_offseason': True
            }
            
            # Mock the get_global_db_connection function
            with patch('backend.app.get_global_db_connection') as mock_get_db:
                mock_get_db.return_value = sqlite3.connect(mock_db_connection)
                
                # Create a mock request
                from flask import Request
                mock_request = MagicMock()
                mock_request.args = {'league_id': 'test_league'}
                
                with patch('backend.app.request', mock_request):
                    # Call the function
                    result = get_team_details('test_roster')
                    
                    # Parse the JSON response
                    response_data = json.loads(result[0].get_data(as_text=True))
                    
                    # Verify the response
                    assert response_data['success'] is True
                    assert 'players_by_position' in response_data
                    
                    # Find the test player in the response
                    test_player_found = False
                    for position_players in response_data['players_by_position'].values():
                        for player in position_players:
                            if player['id'] == 'test_player':
                                test_player_found = True
                                # Verify that the auction player with active contract shows auction amount
                                assert player['draft_amount'] == 25, f"Auction player with active contract should show auction amount $25, but got ${player['draft_amount']}"
                                assert player['contract_status'] == 'Active Contract', f"Auction player with active contract should have 'Active Contract' status, but got '{player['contract_status']}'"
                                break
                        if test_player_found:
                            break
                    
                    assert test_player_found, "Test player not found in response"

if __name__ == '__main__':
    pytest.main([__file__]) 