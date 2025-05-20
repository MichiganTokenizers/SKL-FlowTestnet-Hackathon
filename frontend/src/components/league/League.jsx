import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom'; // Import Link
// import { Link, useNavigate } from 'react-router-dom'; // Link and useNavigate might not be needed directly if navigation is handled by App.jsx

const API_BASE_URL = "http://localhost:5000";

function League(props) { // Accept props
    const { leagues, selectedLeagueId, sessionToken } = props; // Destructure props

    const [userData, setUserData] = useState({}); // Still useful for display name
    const [standings, setStandings] = useState([]);
    const [transactions, setTransactions] = useState([]); // State for recent transactions (mocked for now)
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    // const navigate = useNavigate(); // Removed, navigation handled by App.jsx

    // Effect to fetch user data (like display name) if not already part of a shared context
    // This is a simplified version, ideally user info would come from App.jsx or context
    useEffect(() => {
        if (sessionToken) {
            // Fetch basic user info if needed and not available from props
            // For now, assuming App.jsx passes enough user context or League.jsx can derive it
            // We need the display name, which might not be in `leagues` or `selectedLeagueId` directly
            // A temporary fix: fetch /league/local again just for user_info if not available otherwise.
            // This is inefficient and should be addressed by better state management in App.jsx for user_info.
            fetch(`${API_BASE_URL}/league/local`, { // Re-fetch for user_info if necessary
                 headers: { 'Authorization': sessionToken }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success && data.user_info) {
                    setUserData({ displayName: data.user_info.display_name || 'N/A' });
                } else {
                     setUserData({ displayName: 'Player' }); // Fallback
                }
            })
            .catch(() => setUserData({ displayName: 'Player' }));
        }
    }, [sessionToken]);

    // Effect to fetch standings when selectedLeagueId or sessionToken changes from props
    useEffect(() => {
        if (selectedLeagueId && sessionToken) {
            fetchStandingsData(sessionToken, selectedLeagueId);
        } else if (!selectedLeagueId && leagues && leagues.length > 0) {
            // If no league is selected but leagues exist, prompt to select one (handled by UI)
            setStandings([]); // Clear standings
            setLoading(false);
        } else if (!selectedLeagueId && (!leagues || leagues.length === 0)){
            // No league selected and no leagues available
            setError('No leagues available to display standings.');
            setStandings([]);
            setLoading(false);
        }
    }, [selectedLeagueId, sessionToken, leagues]); // Added leagues as a dependency

    const fetchStandingsData = async (token, leagueId) => {
        console.log('(League.jsx) Fetching standings for league ID:', leagueId);
        if (!leagueId) {
            setError('Cannot fetch standings without a league ID.');
            setStandings([]);
            setLoading(false);
            return;
        }
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/league/standings/local?league_id=${leagueId}`, {
                headers: { 'Authorization': token }
            });
            const data = await response.json();
            if (data.success) {
                setStandings(data.standings || []);
            } else {
                setError(data.error || 'Failed to fetch standings');
                setStandings([]);
            }
        } catch (err) {
            setError('Error fetching standings: ' + err.message);
            setStandings([]);
        } finally {
            setLoading(false);
        }
    };
    
    // Mock transactions - this should be moved to App.jsx if it needs to persist across league selections or be global
    useEffect(() => {
        setTransactions([
            { id: 1, date: '2024-05-27', type: 'Trade', description: 'Team A trades Player X to Team B for Player Y' },
            { id: 2, date: '2024-05-26', type: 'Waiver', description: 'Player Z (Contracted) waived by Team C' },
            { id: 3, date: '2024-05-25', type: 'Trade', description: 'Team D trades Pick 1.05 to Team E for Player W' },
        ]);
    }, []);

    if (loading && standings.length === 0 && selectedLeagueId) { // Refined loading condition
        return (
            <div className="container py-4">
                <div className="text-center">
                    <div className="spinner-border text-primary" role="status">
                        <span className="visually-hidden">Loading standings...</span>
                    </div>
                    <p className="mt-2">Loading league standings...</p>
                </div>
            </div>
        );
    }

    // Error display should be prominent
    if (error) {
        return (
            <div className="container py-4">
                <div className="alert alert-danger" role="alert">
                    <h4 className="alert-heading">Error</h4>
                    <p>{error}</p>
                </div>
            </div>
        );
    }
    
    const currentLeagueObject = leagues && selectedLeagueId ? leagues.find(l => l.league_id === selectedLeagueId) : null;
    const leagueName = currentLeagueObject ? currentLeagueObject.name : (leagues && leagues.length > 0 && !selectedLeagueId ? 'Please select a league' : 'League');

    // If no league is selected from parent, but leagues are available, prompt selection.
    if (leagues && leagues.length > 0 && !selectedLeagueId && !loading) {
        return (
            <div className="container p-4">
                <h1 className="display-4 fw-bold mb-4">{leagueName}</h1>
                <p className="lead">Welcome, {userData.displayName || 'Player'}</p>
                <div className="alert alert-info">Please select a league from the navbar to view its details.</div>
            </div>
        );
    }
    
    // If there are no leagues at all for the user (passed as empty array from App.jsx)
    if ((!leagues || leagues.length === 0) && !loading) {
         return (
            <div className="container p-4">
                <h1 className="display-4 fw-bold mb-4">My League</h1>
                <p className="lead">Welcome, {userData.displayName || 'Player'}</p>
                <div className="alert alert-warning">No leagues are currently associated with your account. Please import or create a league.</div>
                 {/* You might want a link here to an import/create league page */}
            </div>
        );
    }

    return (
        <div className="container p-4">
            <h1 className="display-4 fw-bold mb-4">
                {leagueName} 
            </h1>
            {/* <p className="lead">Displaying data for: <strong>{leagueName}</strong></p> */}
            <p className="lead">Welcome, {userData.displayName || 'Player'}</p>
            
            {selectedLeagueId && ( // Only show standings if a league is selected
                <div className="mt-3">
                    {standings.length > 0 ? (
                        <div>
                            <h3>League Standings</h3>
                            <table className="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th>Team Name</th>
                                        <th>Manager</th>
                                        <th>Record (W-L-T)</th>
                                        <th>Next Matchup</th>
                                        <th>Transaction Count</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {standings.map(roster => (
                                        <tr key={roster.roster_id}>
                                            <td>
                                                {roster.roster_id ? (
                                                    <Link to={`/team/${roster.roster_id}`}>
                                                        {roster.team_name || 'Unnamed Team'}
                                                    </Link>
                                                ) : (
                                                    roster.team_name || 'Unnamed Team' // Fallback if no roster_id
                                                )}
                                            </td>
                                            <td>{roster.owner_display_name || roster.owner_id}</td>
                                            <td>{`${roster.wins}-${roster.losses}${roster.ties > 0 ? `-${roster.ties}` : ''}`}</td>
                                            <td>TBD</td>
                                            <td>0</td>{/* Placeholder */}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                         !loading && <p>No standings data available for this league, or an error occurred fetching them.</p>
                    )}
                </div>
            )}

            <div className="mt-5">
                <h3>Recent Transactions</h3>
                {transactions.length > 0 ? (
                    <table className="table table-striped table-hover mt-3">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Type</th>
                                <th>Description</th>
                            </tr>
                        </thead>
                        <tbody>{transactions.map(tx => (<tr key={tx.id}><td>{tx.date}</td><td>{tx.type}</td><td>{tx.description}</td></tr>))}</tbody>
                    </table>
                ) : (
                    <p className="mt-3">No recent transactions to display.</p>
                )}
            </div>
        </div>
    );
}

export default League;