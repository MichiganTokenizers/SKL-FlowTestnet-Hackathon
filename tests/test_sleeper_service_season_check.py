"""
Test cases for SleeperService season-based player data update logic.
"""
import pytest
import sqlite3
from unittest.mock import Mock, patch
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sleeper_service import SleeperService


class TestSleeperServiceSeasonCheck:
    """Test cases for season-based player data update logic."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create in-memory database for testing
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        
        # Create necessary tables
        self.conn.execute('''
            CREATE TABLE season_curr (
                rowid INTEGER PRIMARY KEY,
                current_year TEXT,
                IsOffSeason INTEGER,
                updated_at TEXT
            )
        ''')
        
        self.conn.execute('''
            CREATE TABLE players (
                sleeper_player_id TEXT PRIMARY KEY,
                name TEXT,
                position TEXT,
                team TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        self.conn.commit()
        
        # Create SleeperService instance with test database
        self.sleeper_service = SleeperService(self.conn)

    def teardown_method(self):
        """Clean up test fixtures."""
        self.conn.close()

    def test_update_players_skipped_during_in_season(self):
        """Test that player data update is skipped when NFL season is in-season."""
        # Set up database to indicate in-season (IsOffSeason = 0)
        self.conn.execute('''
            INSERT INTO season_curr (rowid, current_year, IsOffSeason, updated_at)
            VALUES (1, '2024', 0, datetime('now'))
        ''')
        self.conn.commit()
        
        # Mock the get_players method to ensure it's not called
        with patch.object(self.sleeper_service, 'get_players') as mock_get_players:
            result = self.sleeper_service.update_all_sleeper_players()
            
            # Verify the method was not called
            mock_get_players.assert_not_called()
            
            # Verify the result indicates skip
            assert result['success'] is True
            assert 'Skipped' in result['message']
            assert 'currently in-season' in result['message']

    def test_update_players_proceeds_during_offseason(self):
        """Test that player data update proceeds when NFL season is in offseason."""
        # Set up database to indicate offseason (IsOffSeason = 1)
        self.conn.execute('''
            INSERT INTO season_curr (rowid, current_year, IsOffSeason, updated_at)
            VALUES (1, '2024', 1, datetime('now'))
        ''')
        self.conn.commit()
        
        # Mock the get_players method to return test data
        mock_players_data = {
            '123': {
                'full_name': 'Test Player',
                'position': 'QB',
                'team': 'TEST'
            }
        }
        
        with patch.object(self.sleeper_service, 'get_players', return_value=mock_players_data) as mock_get_players:
            result = self.sleeper_service.update_all_sleeper_players()
            
            # Verify the method was called
            mock_get_players.assert_called_once()
            
            # Verify the result indicates success
            assert result['success'] is True
            assert 'Successfully updated' in result['message']

    def test_update_players_proceeds_when_no_season_data(self):
        """Test that player data update proceeds when no season data is available."""
        # Don't insert any season data
        
        # Mock the get_players method to return test data
        mock_players_data = {
            '123': {
                'full_name': 'Test Player',
                'position': 'QB',
                'team': 'TEST'
            }
        }
        
        with patch.object(self.sleeper_service, 'get_players', return_value=mock_players_data) as mock_get_players:
            result = self.sleeper_service.update_all_sleeper_players()
            
            # Verify the method was called (defaults to offseason when no data)
            mock_get_players.assert_called_once()
            
            # Verify the result indicates success
            assert result['success'] is True
            assert 'Successfully updated' in result['message']

    def test_fetch_all_data_handles_skipped_player_update(self):
        """Test that fetch_all_data properly handles when player update is skipped."""
        # Set up database to indicate in-season
        self.conn.execute('''
            INSERT INTO season_curr (rowid, current_year, IsOffSeason, updated_at)
            VALUES (1, '2024', 0, datetime('now'))
        ''')
        
        # Set up a test user
        self.conn.execute('''
            INSERT INTO Users (wallet_address, sleeper_user_id, username, display_name, created_at, updated_at)
            VALUES ('test_wallet', 'test_user_id', 'test_user', 'Test User', datetime('now'), datetime('now'))
        ''')
        self.conn.commit()
        
        # Mock the external API calls
        with patch.object(self.sleeper_service, 'get_nfl_state', return_value={'season': '2024', 'season_start_date': '2024-09-01'}):
            with patch.object(self.sleeper_service, 'get_user_leagues', return_value=[]):
                result = self.sleeper_service.fetch_all_data('test_wallet')
                
                # Should still succeed even though player update was skipped
                assert result['success'] is True
                assert 'All data fetched and stored successfully' in result['message']


if __name__ == '__main__':
    pytest.main([__file__])
