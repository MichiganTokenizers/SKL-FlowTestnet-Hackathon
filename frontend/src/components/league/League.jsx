import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom'; // Import Link
import LeagueFees from './LeagueFees'; // Import the new component
// import RecentTransactionsTable from './RecentTransactionsTable'; // Import the new transactions table
// import { Link, useNavigate } from 'react-router-dom'; // Link and useNavigate might not be needed directly if navigation is handled by App.jsx

const API_BASE_URL = "http://localhost:5000";

function League(props) { // Accept props
    const { leagues, selectedLeagueId, sessionToken, currentUserDetails } = props; // Destructure props, add currentUserDetails

    const [standings, setStandings] = useState([]);
    // const [transactions, setTransactions] = useState([]); // State for recent transactions (mocked for now) - REMOVED
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    // const navigate = useNavigate(); // Removed, navigation handled by App.jsx

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
    /* REMOVED MOCK TRANSACTIONS useEffect
    useEffect(() => {
        setTransactions([
            { id: 1, date: '2024-05-27', type: 'Trade', description: 'Team A trades Player X to Team B for Player Y' },
            { id: 2, date: '2024-05-26', type: 'Waiver', description: 'Player Z (Contracted) waived by Team C' },
            { id: 3, date: '2024-05-25', type: 'Trade', description: 'Team D trades Pick 1.05 to Team E for Player W' },
        ]);
    }, []);
    */

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
                <h1 className="display-4 fw-bold mb-4" style={{ color: 'var(--text-color)' }}>{leagueName}</h1>
                <p className="lead" style={{ color: 'var(--text-color)' }}>Welcome, {currentUserDetails?.display_name || 'Player'}</p>
                <div className="alert" style={{ backgroundColor: 'var(--input-bg-color)', color: 'var(--text-color)', border: '1px solid var(--input-border-color)' }}>
                    Please select a league from the navbar to view its details.
                </div>
            </div>
        );
    }
    
    // If there are no leagues at all for the user (passed as empty array from App.jsx)
    if ((!leagues || leagues.length === 0) && !loading) {
         return (
            <div className="container p-4">
                <h1 className="display-4 fw-bold mb-4" style={{ color: 'var(--text-color)' }}>My League</h1>
                <p className="lead" style={{ color: 'var(--text-color)' }}>Welcome, {currentUserDetails?.display_name || 'Player'}</p>
                <div className="alert" style={{ backgroundColor: '#FDEBD0', color: 'var(--text-color)', border: '1px solid var(--header-bg-color)' }}>
                    No leagues are currently associated with your account. Please import or create a league.
                </div>
            </div>
        );
    }

    return (
        <div className="container p-4" style={{ backgroundColor: 'transparent' }}>
            <h1 className="display-4 fw-bold mb-4 text-white">
                {leagueName} 
            </h1>
            <p className="lead text-white">Welcome, {currentUserDetails?.display_name || 'Player'}</p>
            
            {/* League Fees Section - only if a league is selected */}
            {selectedLeagueId && <LeagueFees leagueId={selectedLeagueId} currentUser={currentUserDetails} sessionToken={sessionToken} />}

            {selectedLeagueId && ( // Only show standings if a league is selected
                <div className="mt-3">
                    {standings.length > 0 ? (
                        <div className="card mb-4">
                            <div className="card-header d-flex justify-content-between align-items-center">
                                <h4 className="mb-0" style={{ color: 'black' }}>League Standings</h4>
                                <button
                                    className="btn btn-link text-decoration-none"
                                    type="button"
                                    data-bs-toggle="collapse"
                                    data-bs-target="#collapseStandings"
                                    aria-expanded="true"
                                    aria-controls="collapseStandings"
                                    style={{ color: '#9966CC' }}
                                >
                                    ▼
                                </button>
                            </div>
                            <div className="collapse show" id="collapseStandings">
                                <div className="card-body">
                                    <table className="table table-striped table-hover" style={{ backgroundColor: 'transparent' }}>
                                        <thead className="league-table-header" style={{ backgroundColor: 'transparent' }}>
                                            <tr>
                                                <th className="border-white">Team Name</th>
                                                <th className="border-white">Manager</th>
                                                <th className="border-white">Record (W-L-T)</th>
                                                <th className="border-white">Next Matchup</th>
                                                <th className="border-white">Transaction Count</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {standings.map(roster => (
                                                <tr key={roster.roster_id} style={{ backgroundColor: 'transparent' }}>
                                                    <td className="border-white">
                                                        {roster.roster_id ? (
                                                            <Link to={`/league/${selectedLeagueId}/team/${roster.roster_id}`} style={{ color: 'black' }}>
                                                                {roster.team_name || 'Unnamed Team'}
                                                            </Link>
                                                        ) : (
                                                            <span>{roster.team_name || 'Unnamed Team'}</span>
                                                        )}
                                                    </td>
                                                    <td className="border-white">{roster.owner_display_name || roster.owner_id}</td>
                                                    <td className="border-white">{`${roster.wins}-${roster.losses}${roster.ties > 0 ? `-${roster.ties}` : ''}`}</td>
                                                    <td className="border-white">TBD</td>
                                                    <td className="border-white">0</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    ) : (
                         !loading && <p className="text-white">No standings data available for this league, or an error occurred fetching them.</p>
                    )}
                </div>
            )}

            {/* League Transactions Section */}
            {selectedLeagueId && (
                <div className="mt-3">
                    <div className="card mb-4">
                        <div className="card-header d-flex justify-content-between align-items-center">
                            <h4 className="mb-0" style={{ color: 'black' }}>League Transactions</h4>
                            <button
                                className="btn btn-link text-decoration-none"
                                type="button"
                                data-bs-toggle="collapse"
                                data-bs-target="#collapseTransactions"
                                aria-expanded="true"
                                aria-controls="collapseTransactions"
                                style={{ color: '#9966CC' }}
                            >
                                ▼
                            </button>
                        </div>
                        <div className="collapse show" id="collapseTransactions">
                            <div className="card-body">
                                <p className="text-muted">Transaction history will be displayed here.</p>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default League;