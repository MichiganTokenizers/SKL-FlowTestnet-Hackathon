import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './SleeperAssociation.css';

// Use a constant for the API URL (this can be updated to use environment variables in your build system)
const API_BASE_URL = 'http://localhost:5000';

const SleeperAssociation = ({ sessionToken }) => {
  const [username, setUsername] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [leagues, setLeagues] = useState([]);
  const [selectedLeague, setSelectedLeague] = useState('');
  const [leagueUsers, setLeagueUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  // Check if association is needed when component loads
  useEffect(() => {
    if (!sessionToken) {
      setError('No session token available. Please log in again.');
      return;
    }

    checkAssociation();
  }, [sessionToken]);

  const checkAssociation = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/check_association`, {
        headers: {
          'Authorization': sessionToken
        }
      });
      
      const data = await response.json();
      
      if (!data.success) {
        setError(data.error || 'Failed to check association status');
        return;
      }
      
      // If user is already associated, redirect to main page
      if (!data.needs_association) {
        navigate('/dashboard');
      }
    } catch (err) {
      setError('Error checking association status: ' + err.message);
    }
  };

  const searchSleeperUser = async () => {
    if (!username.trim()) {
      setError('Please enter a Sleeper username');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      const response = await fetch(`${API_BASE_URL}/sleeper/search?username=${encodeURIComponent(username)}`, {
        headers: {
          'Authorization': sessionToken
        }
      });
      
      const data = await response.json();
      
      if (!data.success) {
        setError(data.error || 'Failed to find Sleeper user');
        setSearchResults(null);
        setLeagues([]);
        setSelectedLeague('');
        setLeagueUsers([]);
        setSelectedUser('');
        return;
      }
      
      setSearchResults(data.user);
      setLeagues(data.leagues || []);
      setSuccess(`Found user: ${data.user.display_name}`);
    } catch (err) {
      setError('Error searching for Sleeper user: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLeagueSelect = async (e) => {
    const leagueId = e.target.value;
    setSelectedLeague(leagueId);
    
    if (!leagueId) {
      setLeagueUsers([]);
      setSelectedUser('');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${API_BASE_URL}/sleeper/league/${leagueId}/users`, {
        headers: {
          'Authorization': sessionToken
        }
      });
      
      const data = await response.json();
      
      if (!data.success) {
        setError(data.error || 'Failed to load league users');
        setLeagueUsers([]);
        return;
      }
      
      setLeagueUsers(data.users || []);
    } catch (err) {
      setError('Error loading league users: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const completeAssociation = async () => {
    if (!selectedUser || !selectedLeague) {
      setError('Please select both a league and your Sleeper account');
      return;
    }
    
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      // Find the selected user from leagueUsers array
      const userDetails = leagueUsers.find(user => user.user_id === selectedUser);
      
      if (!userDetails) {
        setError('Selected user not found in league users');
        return;
      }
      
      const response = await fetch(`${API_BASE_URL}/auth/complete_association`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': sessionToken
        },
        body: JSON.stringify({
          sleeper_user_id: userDetails.user_id,
          sleeper_username: userDetails.username,
          sleeper_display_name: userDetails.display_name,
          sleeper_avatar: userDetails.avatar,
          league_id: selectedLeague
        })
      });
      
      const data = await response.json();
      
      if (!data.success) {
        setError(data.error || 'Failed to complete association');
        return;
      }
      
      setSuccess('Association completed successfully!');
      
      // Redirect to dashboard after successful association
      setTimeout(() => {
        navigate('/dashboard');
      }, 1500);
      
    } catch (err) {
      setError('Error completing association: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sleeper-association-container">
      <h1>Associate Your Sleeper Account</h1>
      <p className="description">
        To complete your account setup, please connect your Sleeper fantasy football account.
      </p>
      
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}
      
      <div className="search-section">
        <div className="input-group">
          <label htmlFor="username">Sleeper Username:</label>
          <div className="input-with-button">
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your Sleeper username"
              disabled={loading}
            />
            <button 
              className="search-button"
              onClick={searchSleeperUser}
              disabled={loading || !username.trim()}
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </div>
      </div>
      
      {searchResults && (
        <div className="search-results">
          <div className="user-info">
            <div className="avatar">
              {searchResults.avatar && (
                <img 
                  src={`https://sleepercdn.com/avatars/thumbs/${searchResults.avatar}`} 
                  alt={`${searchResults.display_name}'s avatar`}
                />
              )}
            </div>
            <div className="user-details">
              <h3>{searchResults.display_name}</h3>
              <p>Username: {searchResults.username}</p>
            </div>
          </div>
          
          {leagues.length > 0 ? (
            <div className="leagues-section">
              <h3>Select Your League:</h3>
              <select 
                value={selectedLeague} 
                onChange={handleLeagueSelect}
                disabled={loading}
              >
                <option value="">-- Select a League --</option>
                {leagues.map(league => (
                  <option key={league.league_id} value={league.league_id}>
                    {league.name} ({league.season})
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div className="no-leagues">
              <p>No leagues found for this user.</p>
            </div>
          )}
          
          {selectedLeague && leagueUsers.length > 0 && (
            <div className="users-section">
              <h3>Confirm Your Account:</h3>
              <select
                value={selectedUser}
                onChange={(e) => setSelectedUser(e.target.value)}
                disabled={loading}
              >
                <option value="">-- Select Your Account --</option>
                {leagueUsers.map(user => (
                  <option key={user.user_id} value={user.user_id}>
                    {user.display_name} ({user.username || 'No username'})
                  </option>
                ))}
              </select>
            </div>
          )}
          
          {selectedLeague && selectedUser && (
            <div className="action-buttons">
              <button
                className="complete-button"
                onClick={completeAssociation}
                disabled={loading}
              >
                {loading ? 'Processing...' : 'Complete Association'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SleeperAssociation; 