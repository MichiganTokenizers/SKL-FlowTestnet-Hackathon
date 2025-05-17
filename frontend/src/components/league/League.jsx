import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const API_BASE_URL = "http://localhost:5000";

function League() {
    const [userData, setUserData] = useState({});
    // const [leagues, setLeagues] = useState([]); // To store all leagues from /league/local - Commented out for now
    const [selectedLeague, setSelectedLeague] = useState(null); // To store the first league object
    const [standings, setStandings] = useState([]); // Changed from teams to standings
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        const sessionToken = localStorage.getItem('sessionToken');
        console.log('Session Token being used:', sessionToken ? 'Token exists' : 'No token found');
        if (!sessionToken) {
            setError('Please log in to view league information.');
            setLoading(false);
            navigate('/');
            return;
        }

        fetch(`${API_BASE_URL}/league/local`, {
            headers: { 'Authorization': sessionToken }
        })
            .then(res => {
                console.log('Response status from /league/local:', res.status);
                console.log('Response headers:', res.headers);
                if (!res.ok) {
                    if (res.status === 401) {
                        localStorage.removeItem('sessionToken');
                        setError('Session expired. Please log in again.');
                        navigate('/');
                        throw new Error('Session expired. Please log in again.');
                    }
                    return res.json().then(data => {
                        throw new Error(data.error || 'Failed to fetch league data');
                    });
                }
                return res.json();
            })
            .then(data => {
                console.log('Response data from /league/local:', data);
                if (data.success) {
                    setUserData({
                        walletAddress: data.user_info?.wallet_address || 'Unknown',
                        displayName: data.user_info?.display_name || 'N/A', // Using displayName
                        // leagueName and teamName will come from selectedLeague or standings
                    });
                    const allLeagues = data.leagues || [];
                    // setLeagues(allLeagues); // Commented out as the 'leagues' state is not yet used for multi-league selection
                    console.log('All leagues fetched (raw data):', allLeagues);

                    if (allLeagues.length > 0) {
                        const firstLeague = allLeagues[0];
                        setSelectedLeague(firstLeague);
                        fetchStandingsData(sessionToken, firstLeague.league_id);
                    } else {
                        setError('No leagues found for this user.');
                        setLoading(false);
                    }
                } else {
                    setError(data.error || 'Failed to fetch league data');
                    setLoading(false);
                }
            })
            .catch(err => {
                setError(err.message);
                setLoading(false);
            });
    }, [navigate]);

    const fetchStandingsData = async (sessionToken, leagueId) => {
        if (!leagueId) {
            setError('Cannot fetch standings without a league ID.');
            setLoading(false);
            return;
        }
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/league/standings/local?league_id=${leagueId}`, {
                headers: { 'Authorization': sessionToken }
            });
            const data = await response.json();
            if (data.success) {
                setStandings(data.standings || []);
            } else {
                setError(data.error || 'Failed to fetch standings');
            }
        } catch (err) {
            setError('Error fetching standings: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="container py-4">
                <div className="text-center">
                    <div className="spinner-border text-primary" role="status">
                        <span className="visually-hidden">Loading...</span>
                    </div>
                    <p className="mt-2">Loading league data...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="container py-4">
                <div className="alert alert-danger" role="alert">
                    <h4 className="alert-heading">Error Loading League</h4>
                    <p>{error}</p>
                </div>
            </div>
        );
    }

    const leagueName = selectedLeague ? selectedLeague.name : 'No league selected';
    const leagueAvatar = selectedLeague ? selectedLeague.avatar : null;

    return (
        <div className="container p-4">
            <h1 className="display-4 fw-bold mb-4">
                {leagueAvatar && <img src={leagueAvatar} alt="League Avatar" style={{ width: '50px', height: '50px', marginRight: '15px', borderRadius: '50%' }} />}
                Supreme Keeper League - {leagueName}
            </h1>
            <p className="lead">Welcome, {userData.displayName} ({userData.walletAddress})</p>
            <div className="mt-3">
                {standings.length > 0 ? (
                    <div>
                        <h3>League Rosters</h3>
                        <table className="table table-striped table-hover">
                            <thead>
                                <tr>
                                    <th>Team Name</th>
                                    <th>Manager</th>
                                    <th>Record (W-L-T)</th>
                                    <th>Player Count</th>
                                </tr>
                            </thead>
                            <tbody>
                                {standings.map(roster => (
                                    <tr key={roster.roster_id}>
                                        <td>
                                            {roster.team_name || 'Unnamed Team'}
                                        </td>
                                        <td>
                                            {roster.owner_avatar && <img src={roster.owner_avatar} alt="Owner Avatar" style={{ width: '25px', height: '25px', marginRight: '8px', borderRadius: '50%' }} />}
                                            {roster.owner_display_name || roster.owner_id}
                                        </td>
                                        <td>{`${roster.wins}-${roster.losses}${roster.ties > 0 ? `-${roster.ties}` : ''}`}</td>
                                        <td>{roster.player_count}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <p>No standings data available for this league yet, or league not selected.</p>
                )}
            </div>
        </div>
    );
}

export default League;