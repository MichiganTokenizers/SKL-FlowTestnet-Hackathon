import { useState, useEffect } from 'react';

const API_BASE_URL = "https://e17b-181-214-151-64.ngrok-free.app"; // Your ngrok URL

function SleeperImport() {
    const [username, setUsername] = useState('');
    const [user, setUser] = useState(null);
    const [leagues, setLeagues] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const searchLeagues = async () => {
        const sessionToken = localStorage.getItem('sessionToken');
        if (!sessionToken) {
            setError('Please log in to search for Sleeper leagues.');
            return;
        }

        if (!username) {
            setError('Please enter a Sleeper username.');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE_URL}/sleeper/search?username=${encodeURIComponent(username)}`, {
                headers: { 'Authorization': sessionToken }
            });
            const text = await response.text(); // Get raw text first
            console.log("Raw response:", text); // Log raw response for debugging
            const data = JSON.parse(text); // Try to parse as JSON
            if (data.success) {
                setUser(data.user);
                setLeagues(data.leagues);
            } else {
                setError(data.error || 'Failed to search for leagues');
                setUser(null);
                setLeagues([]);
            }
        } catch (err) {
            setError('Error searching for leagues: ' + err.message);
            setUser(null);
            setLeagues([]);
        } finally {
            setLoading(false);
        }
    };

    const importLeague = async (leagueId) => {
        const sessionToken = localStorage.getItem('sessionToken');
        if (!sessionToken) {
            setError('Please log in to import a league.');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE_URL}/sleeper/import`, {
                method: 'POST',
                headers: {
                    'Authorization': sessionToken,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ league_id: leagueId })
            });
            const data = await response.json();
            if (data.success) {
                alert('League imported successfully!');
                // Optionally, redirect or update UI
            } else {
                setError(data.error || 'Failed to import league');
            }
        } catch (err) {
            setError('Error importing league: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const sessionToken = localStorage.getItem('sessionToken');
        if (!sessionToken) {
            setError('Please log in to access this page.');
        }
    }, []);

    return (
        <div className="container p-4">
            <h1 className="display-4 fw-bold mb-4">Import Sleeper League</h1>
            <div className="mb-3">
                <label htmlFor="username" className="form-label">Sleeper Username</label>
                <div className="input-group">
                    <input
                        type="text"
                        className="form-control"
                        id="username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="Enter Sleeper username"
                    />
                    <button
                        className="btn btn-primary"
                        onClick={searchLeagues}
                        disabled={loading}
                    >
                        {loading ? 'Searching...' : 'Search'}
                    </button>
                </div>
            </div>
            {error && <div className="alert alert-danger">{error}</div>}
            {user && (
                <div className="mb-3">
                    <h3>User Found: {user.display_name}</h3>
                </div>
            )}
            {leagues.length > 0 && (
                <div>
                    <h3>Available Leagues</h3>
                    <div className="row">
                        {leagues.map(league => (
                            <div key={league.league_id} className="col-md-4 mb-3">
                                <div className="card">
                                    <div className="card-body">
                                        <h5 className="card-title">{league.name}</h5>
                                        <p className="card-text">Season: {league.season}</p>
                                        <button
                                            className="btn btn-success"
                                            onClick={() => importLeague(league.league_id)}
                                            disabled={loading}
                                        >
                                            Import League
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

export default SleeperImport;