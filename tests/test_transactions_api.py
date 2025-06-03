import pytest
import json
from unittest.mock import patch, MagicMock

# Assuming your Flask app instance is named 'app' in 'backend.app'
# You might need to adjust the import path based on your project structure
from backend.app import app as flask_app

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # flask_app.config.update({
    #     "TESTING": True,
    #     # Add other configurations if necessary, e.g., for a test database
    # })
    # If you have specific setup for testing (like a test DB), do it here.
    yield flask_app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def mock_db_connection():
    """Fixture to mock the global database connection and cursor."""
    with patch('backend.app.get_global_db_connection') as mock_get_conn:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        yield mock_cursor # Yield the cursor for test-specific return values

@pytest.fixture
def mock_get_current_user():
    """Fixture to mock get_current_user."""
    with patch('backend.app.get_current_user') as mock_user_func:
        yield mock_user_func


# --- Test Cases for /league/<league_id>/transactions/recent --- 

COMMON_USER_WALLET = 'test_wallet_123'
COMMON_LEAGUE_ID = 'league_789'
VALID_SESSION_TOKEN = 'valid_token_abc'


def test_get_recent_transactions_success(client, mock_db_connection, mock_get_current_user):
    """Test successful retrieval of recent transactions."""
    mock_get_current_user.return_value = {'wallet_address': COMMON_USER_WALLET, 'sleeper_user_id': 'sleeper_user_1'}
    
    # Mock UserLeagueLinks check (user is part of the league)
    mock_db_connection.fetchone.side_effect = [
        (1,), # First fetchone for UserLeagueLinks check
        {'name': 'Test League Name'} # Second fetchone for LeagueMetadata
    ]
    
    mock_transactions = [
        {'sleeper_transaction_id': 'tx1', 'type': 'trade', 'status': 'complete', 'data': '{"key": "value1"}', 'created_at': '2023-01-01 10:00:00'},
        {'sleeper_transaction_id': 'tx2', 'type': 'waiver', 'status': 'processed', 'data': '{"key": "value2"}', 'created_at': '2023-01-02 10:00:00'},
    ]
    mock_db_connection.fetchall.return_value = mock_transactions # For transactions query

    response = client.get(f'/league/{COMMON_LEAGUE_ID}/transactions/recent', headers={'Authorization': VALID_SESSION_TOKEN})
    data = json.loads(response.data)

    assert response.status_code == 200
    assert data['success'] is True
    assert data['league_id'] == COMMON_LEAGUE_ID
    assert data['league_name'] == 'Test League Name'
    assert len(data['transactions']) == 2
    assert data['transactions'][0]['transaction_id'] == 'tx1'
    assert data['transactions'][1]['details'] == {'key': 'value2'}
    
    # Check that the correct query was made (LIMIT 15 and ORDER BY)
    query_string = mock_db_connection.execute.call_args_list[2][0][0] # Third execute call is for transactions
    assert 'LIMIT 15' in query_string
    assert 'ORDER BY created_at DESC' in query_string
    assert 'WHERE league_id = ?' in query_string
    assert mock_db_connection.execute.call_args_list[2][0][1] == (COMMON_LEAGUE_ID,)


def test_get_recent_transactions_not_authenticated(client, mock_get_current_user):
    """Test endpoint access when user is not authenticated."""
    mock_get_current_user.return_value = None # Simulate no user logged in
    response = client.get(f'/league/{COMMON_LEAGUE_ID}/transactions/recent', headers={'Authorization': 'invalid_token'})
    data = json.loads(response.data)

    assert response.status_code == 401
    assert data['success'] is False
    assert data['error'] == 'User not authenticated'


def test_get_recent_transactions_user_not_in_league(client, mock_db_connection, mock_get_current_user):
    """Test when user is authenticated but not part of the requested league."""
    mock_get_current_user.return_value = {'wallet_address': COMMON_USER_WALLET, 'sleeper_user_id': 'sleeper_user_1'}
    
    # Mock UserLeagueLinks check (user is NOT part of the league)
    mock_db_connection.fetchone.return_value = None 

    response = client.get(f'/league/{COMMON_LEAGUE_ID}/transactions/recent', headers={'Authorization': VALID_SESSION_TOKEN})
    data = json.loads(response.data)

    assert response.status_code == 403
    assert data['success'] is False
    assert 'User not authorized for this league' in data['error']


def test_get_recent_transactions_league_not_found(client, mock_db_connection, mock_get_current_user):
    """Test when the league metadata itself is not found."""
    mock_get_current_user.return_value = {'wallet_address': COMMON_USER_WALLET, 'sleeper_user_id': 'sleeper_user_1'}
    
    # Mock UserLeagueLinks check (user is part of the league)
    # Then, LeagueMetadata check fails
    mock_db_connection.fetchone.side_effect = [
        (1,), # UserLeagueLinks check passes
        None  # LeagueMetadata check fails
    ]

    response = client.get(f'/league/{COMMON_LEAGUE_ID}/transactions/recent', headers={'Authorization': VALID_SESSION_TOKEN})
    data = json.loads(response.data)

    assert response.status_code == 404
    assert data['success'] is False
    assert f'League metadata not found for ID {COMMON_LEAGUE_ID}' in data['error']


def test_get_recent_transactions_no_transactions(client, mock_db_connection, mock_get_current_user):
    """Test successful retrieval when there are no transactions for the league."""
    mock_get_current_user.return_value = {'wallet_address': COMMON_USER_WALLET, 'sleeper_user_id': 'sleeper_user_1'}
    
    mock_db_connection.fetchone.side_effect = [
        (1,), 
        {'name': 'Test League Name'}
    ]
    mock_db_connection.fetchall.return_value = [] # No transactions

    response = client.get(f'/league/{COMMON_LEAGUE_ID}/transactions/recent', headers={'Authorization': VALID_SESSION_TOKEN})
    data = json.loads(response.data)

    assert response.status_code == 200
    assert data['success'] is True
    assert len(data['transactions']) == 0


def test_get_recent_transactions_data_json_parse_error(client, mock_db_connection, mock_get_current_user):
    """Test handling of invalid JSON in transaction data field."""
    mock_get_current_user.return_value = {'wallet_address': COMMON_USER_WALLET, 'sleeper_user_id': 'sleeper_user_1'}
    
    mock_db_connection.fetchone.side_effect = [
        (1,), 
        {'name': 'Test League Name'}
    ]
    
    mock_transactions = [
        {'sleeper_transaction_id': 'tx_bad_json', 'type': 'trade', 'status': 'complete', 'data': 'this is not json', 'created_at': '2023-01-03 10:00:00'},
    ]
    mock_db_connection.fetchall.return_value = mock_transactions

    response = client.get(f'/league/{COMMON_LEAGUE_ID}/transactions/recent', headers={'Authorization': VALID_SESSION_TOKEN})
    data = json.loads(response.data)

    assert response.status_code == 200
    assert data['success'] is True
    assert len(data['transactions']) == 1
    assert data['transactions'][0]['transaction_id'] == 'tx_bad_json'
    assert data['transactions'][0]['details'] == {"error": "Could not parse transaction data"}


def test_get_recent_transactions_ordering_and_limit(client, mock_db_connection, mock_get_current_user):
    """Test that the SQL query uses ORDER BY and LIMIT correctly (verified by inspecting mock calls)."""
    mock_get_current_user.return_value = {'wallet_address': COMMON_USER_WALLET, 'sleeper_user_id': 'sleeper_user_1'}
    
    mock_db_connection.fetchone.side_effect = [
        (1,), 
        {'name': 'Test League Name'}
    ]
    mock_db_connection.fetchall.return_value = [] # Actual transactions don't matter for this specific check

    client.get(f'/league/{COMMON_LEAGUE_ID}/transactions/recent', headers={'Authorization': VALID_SESSION_TOKEN})
    
    # The third call to execute on the cursor should be the one fetching transactions
    # Calls are: 0=UserLeagueLinks, 1=LeagueMetadata, 2=Transactions query
    assert len(mock_db_connection.execute.call_args_list) >= 3
    actual_query = mock_db_connection.execute.call_args_list[2][0][0]
    
    print(f"Actual query for transactions: {actual_query}") # For debugging if test fails
    
    assert 'FROM transactions' in actual_query
    assert 'WHERE league_id = ?' in actual_query
    assert 'ORDER BY created_at DESC' in actual_query
    assert 'LIMIT 15' in actual_query
    assert mock_db_connection.execute.call_args_list[2][0][1] == (COMMON_LEAGUE_ID,)

# Add more tests as needed, e.g., for different transaction types and their 'data' parsing if enhanced later. 