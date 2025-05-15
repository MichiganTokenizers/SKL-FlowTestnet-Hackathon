import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './AssociateSleeper.css';

const AssociateSleeper = ({ walletAddress }) => {
  const [username, setUsername] = useState('');
  const [leagues, setLeagues] = useState([]);
  const [selectedLeague, setSelectedLeague] = useState('');
  const [leagueUsers, setLeagueUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState('');
  const [message, setMessage] = useState({ text: '', type: '' });
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const getSessionToken = () => {
    return sessionStorage.getItem('sessionToken') || localStorage.getItem('sessionToken') || '';
  };

  const searchSleeperUser = async () => {
    if (!username.trim()) {
      setMessage({ text: 'Please enter a Sleeper username.', type: 'error' });
      return;
    }

    setIsLoading(true);
    setMessage({ text: 'Searching for user...', type: '' });
    try {
      const response = await fetch(`http://localhost:5000/sleeper/search?username=${username}`, {
        headers: {
          'Authorization': getSessionToken()
        }
      });
      const data = await response.json();
      if (data.success) {
        const foundLeagues = data.leagues || [];
        setLeagues(foundLeagues);
        if (foundLeagues.length > 0) {
          setMessage({ text: 'User found. Please select a league.', type: 'success' });
        } else {
          setMessage({ text: 'No leagues found for this user.', type: 'error' });
        }
      } else {
        setMessage({ text: `Error: ${data.error}`, type: 'error' });
      }
    } catch (error) {
      setMessage({ text: `Error searching for user: ${error.message}`, type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  const loadLeagueUsers = async (leagueId) => {
    if (!leagueId) {
      setLeagueUsers([]);
      setSelectedUser('');
      return;
    }

    setIsLoading(true);
    setMessage({ text: 'Loading league users...', type: '' });
    try {
      const response = await fetch(`http://localhost:5000/sleeper/league/${leagueId}/users`, {
        headers: {
          'Authorization': getSessionToken()
        }
      });
      const data = await response.json();
      if (data.success) {
        const users = data.users || [];
        setLeagueUsers(users);
        if (users.length > 0) {
          setMessage({ text: 'Please select your account.', type: 'success' });
        } else {
          setMessage({ text: 'No users found in this league.', type: 'error' });
        }
      } else {
        setMessage({ text: `Error: ${data.error}`, type: 'error' });
      }
    } catch (error) {
      setMessage({ text: `Error loading league users: ${error.message}`, type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  const associateAccount = async () => {
    if (!selectedLeague || !selectedUser) {
      setMessage({ text: 'Please select both a league and your account.', type: 'error' });
      return;
    }

    setIsLoading(true);
    setMessage({ text: 'Associating account...', type: '' });
    try {
      const response = await fetch('http://localhost:5000/auth/associate_sleeper', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': getSessionToken()
        },
        body: JSON.stringify({
          league_id: selectedLeague,
          sleeper_user_id: selectedUser
        })
      });
      const data = await response.json();
      if (data.success) {
        setMessage({ text: 'Account associated successfully! Redirecting...', type: 'success' });
        setTimeout(() => {
          navigate('/league');
        }, 2000);
      } else {
        setMessage({ text: `Error: ${data.error}`, type: 'error' });
      }
    } catch (error) {
      setMessage({ text: `Error associating account: ${error.message}`, type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (selectedLeague) {
      loadLeagueUsers(selectedLeague);
    }
  }, [selectedLeague]);

  return (
    <div className="container">
      <h1>Associate Sleeper Account</h1>
      <p>Welcome, {walletAddress}. Please associate your Sleeper account to continue.</p>
      
      <div className="form-group">
        <label htmlFor="username">Sleeper Username:</label>
        <input
          type="text"
          id="username"
          placeholder="Enter your Sleeper username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          disabled={isLoading}
        />
        <button onClick={searchSleeperUser} disabled={isLoading}>
          Search
        </button>
      </div>
      
      {leagues.length > 0 && (
        <div className="form-group">
          <label htmlFor="league_id">Select League:</label>
          <select
            id="league_id"
            value={selectedLeague}
            onChange={(e) => setSelectedLeague(e.target.value)}
            disabled={isLoading}
          >
            <option value="">-- Select a League --</option>
            {leagues.map((league) => (
              <option key={league.league_id} value={league.league_id}>
                {league.name}
              </option>
            ))}
          </select>
        </div>
      )}
      
      {leagueUsers.length > 0 && (
        <div className="form-group">
          <label htmlFor="sleeper_user_id">Select Your Account:</label>
          <select
            id="sleeper_user_id"
            value={selectedUser}
            onChange={(e) => setSelectedUser(e.target.value)}
            disabled={isLoading}
          >
            <option value="">-- Select Your Account --</option>
            {leagueUsers.map((user) => (
              <option key={user.user_id} value={user.user_id}>
                {user.display_name} ({user.username || 'N/A'})
              </option>
            ))}
          </select>
        </div>
      )}
      
      <div className="form-group">
        <button
          onClick={associateAccount}
          disabled={isLoading || !selectedLeague || !selectedUser}
        >
          Associate Account
        </button>
      </div>
      
      {message.text && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}
    </div>
  );
};

export default AssociateSleeper; 