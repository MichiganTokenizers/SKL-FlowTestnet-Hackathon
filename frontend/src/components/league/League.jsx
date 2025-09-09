import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom'; // Import Link
import LeagueFees from './LeagueFees'; // Import the new component
import Transactions from './transactions'; // Import the new transactions component
import { API_BASE_URL } from '../../config';
// import RecentTransactionsTable from './RecentTransactionsTable'; // Import the new transactions table
// import { Link, useNavigate } from 'react-router-dom'; // Link and useNavigate might not be needed directly if navigation is handled by App.jsx

// Function to create team abbreviations
const createTeamAbbreviation = (teamName, maxLength = 3) => {
    // Ensure teamName is a string
    if (typeof teamName !== 'string') {
        teamName = String(teamName || '');
    }
    
    if (!teamName || teamName.length <= maxLength) {
        return teamName?.toUpperCase() || 'TBD';
    }
    
    // Remove common words
    const skipWords = ['the', 'and', 'of', 'for', 'in', 'on', 'at', 'to', 'a', 'an', 'team'];
    const words = teamName.split(' ')
        .filter(word => !skipWords.includes(word.toLowerCase()))
        .filter(word => word.length > 0);
    
    if (words.length === 1) {
        return words[0].substring(0, maxLength).toUpperCase();
    }
    
    // Take first letter of each word
    const abbreviation = words.map(word => word[0]).join('');
    return abbreviation.substring(0, maxLength).toUpperCase();
};

function League(props) { // Accept props
    const { leagues, selectedLeagueId, sessionToken, currentUserDetails } = props; // Destructure props, add currentUserDetails

    const [standings, setStandings] = useState([]);
    // const [transactions, setTransactions] = useState([]); // State for recent transactions (mocked for now) - REMOVED
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [leagueFeeSettings, setLeagueFeeSettings] = useState(null);
    
    // Trade-related state
    const [pendingTrades, setPendingTrades] = useState([]);
    const [isCommissioner, setIsCommissioner] = useState(false);
    const [tradesLoading, setTradesLoading] = useState(false);
    // const navigate = useNavigate(); // Removed, navigation handled by App.jsx

    // Effect to fetch standings when selectedLeagueId or sessionToken changes from props
    useEffect(() => {
        if (selectedLeagueId && sessionToken) {
            fetchStandingsData(sessionToken, selectedLeagueId);
            fetchLeagueFeeData(sessionToken, selectedLeagueId);
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

    // Trade-related useEffect
    useEffect(() => {
        if (selectedLeagueId && sessionToken) {
            checkCommissionerStatus();
            fetchPendingTrades();
        }
    }, [selectedLeagueId, sessionToken]);

    const checkCommissionerStatus = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/league/${selectedLeagueId}/commissioner-status`, {
                headers: { 'Authorization': sessionToken }
            });
            const data = await response.json();
            setIsCommissioner(data.is_commissioner || false);
        } catch (error) {
            console.error('Error checking commissioner status:', error);
        }
    };

    const fetchPendingTrades = async () => {
        if (!selectedLeagueId) return;
        
        setTradesLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/api/trades/pending/${selectedLeagueId}`, {
                headers: { 'Authorization': sessionToken }
            });
            const data = await response.json();
            if (data.success) {
                setPendingTrades(data.trades);
            } else {
                console.error('Error fetching trades:', data.error);
            }
        } catch (error) {
            console.error('Error fetching pending trades:', error);
        } finally {
            setTradesLoading(false);
        }
    };

    const handleTradeApproval = async (tradeId, action, notes = '') => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/trades/${tradeId}/${action}`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': sessionToken 
                },
                body: JSON.stringify({ notes })
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                // Show success message
                alert(`Trade ${action}ed successfully!`);
                // Refresh pending trades
                fetchPendingTrades();
                // Optionally refresh league data to show updated standings
                if (selectedLeagueId) {
                    fetchStandingsData(sessionToken, selectedLeagueId);
                }
            } else {
                alert(result.error || `Failed to ${action} trade`);
            }
        } catch (error) {
            console.error('Error updating trade:', error);
            alert(`Error ${action}ing trade: ${error.message}`);
        }
    };

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

    const fetchLeagueFeeData = async (token, leagueId) => {
        if (!leagueId || !token) return;
        
        try {
            const response = await fetch(`${API_BASE_URL}/league/${leagueId}/fees`, {
                headers: { 'Authorization': token }
            });
            const data = await response.json();
            if (data.success) {
                setLeagueFeeSettings(data.fee_settings);
            }
        } catch (err) {
            console.error('Error fetching league fees:', err);
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

    // Calculate prize amounts based on league fee
    const calculatePrizeAmounts = () => {
        if (!leagueFeeSettings || !leagueFeeSettings.fee_amount) {
            return { first: 0, second: 0, third: 0, bestRecord: 0, total: 0 };
        }
        
        const totalFee = leagueFeeSettings.fee_amount;
        const teamCount = standings.length || 0; // Use actual number of teams from standings
        const totalPrizePool = totalFee * teamCount;
        
        return {
            first: totalPrizePool * 0.50,
            second: totalPrizePool * 0.30,
            third: totalPrizePool * 0.10,
            bestRecord: totalPrizePool * 0.10,
            total: totalPrizePool
        };
    };

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

    const prizeAmounts = calculatePrizeAmounts();

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
                                                <th className="border-white">Team</th>
                                                <th className="border-white">Record (W-L-T)</th>
                                                <th className="border-white">Total Points</th>
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
                                                                <small className="text-muted ms-1">
                                                                    ({createTeamAbbreviation(roster.team_name || 'Unnamed Team')})
                                                                </small>
                                                            </Link>
                                                        ) : (
                                                            <span>
                                                                {roster.team_name || 'Unnamed Team'} 
                                                                <small className="text-muted ms-1">
                                                                    ({createTeamAbbreviation(roster.team_name || 'Unnamed Team')})
                                                                </small>
                                                            </span>
                                                        )}
                                                    </td>
                                                    <td className="border-white">{`${roster.wins}-${roster.losses}${roster.ties > 0 ? `-${roster.ties}` : ''}`}</td>
                                                    <td className="border-white">{roster.points_for ? Number(roster.points_for).toFixed(2) : '0.00'}</td>
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
                            <h4 className="mb-0" style={{ color: 'black' }}>Trades and Waived Contracts</h4>
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
                                <Transactions leagueId={selectedLeagueId} sessionToken={sessionToken} />
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Pending Trades Section - Visible to All Users */}
            {selectedLeagueId && (
                <div className="mt-3">
                    <div className="card mb-4">
                        <div className="card-header d-flex justify-content-between align-items-center">
                            <h4 className="mb-0" style={{ color: 'black' }}>
                                Pending Budget Trades
                                {pendingTrades.length > 0 && (
                                    <span className="badge bg-warning text-dark ms-2">{pendingTrades.length}</span>
                                )}
                            </h4>
                            {isCommissioner && (
                                <button 
                                    className="btn btn-outline-primary btn-sm"
                                    onClick={fetchPendingTrades}
                                    disabled={tradesLoading}
                                >
                                    {tradesLoading ? 'Refreshing...' : 'Refresh'}
                                </button>
                            )}
                        </div>
                        <div className="card-body">
                            {tradesLoading ? (
                                <p>Loading pending trades...</p>
                            ) : pendingTrades.length === 0 ? (
                                <p className="text-muted mb-0">No pending trades to review.</p>
                            ) : (
                                <div className="table-responsive">
                                    <table className="table table-hover mb-0">
                                        <thead className="table-light">
                                            <tr>
                                                <th>Teams</th>
                                                <th>Budget Items</th>
                                                <th>Created</th>
                                                {isCommissioner && <th>Actions</th>}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {pendingTrades.map(trade => (
                                                <tr key={trade.trade_id}>
                                                    <td>
                                                        <div>
                                                            <strong className="text-primary">{trade.initiator_team_name}</strong>
                                                            <br />
                                                            <small className="text-muted">
                                                                ↔ trading with <strong className="text-success">{trade.recipient_team_name}</strong>
                                                            </small>
                                                        </div>
                                                    </td>
                                                    <td>
                                                        <div className="d-flex flex-wrap gap-1">
                                                            {trade.budget_items.map(item => (
                                                                <span 
                                                                    key={item.item_id} 
                                                                    className="badge bg-info text-dark"
                                                                    title={`${item.season_year} Budget`}
                                                                >
                                                                    {item.season_year}: ${item.budget_amount}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </td>
                                                    <td>
                                                        <small className="text-muted">
                                                            {new Date(trade.created_at + 'Z').toLocaleDateString()}
                                                            <br />
                                                            {new Date(trade.created_at + 'Z').toLocaleTimeString()}
                                                        </small>
                                                    </td>
                                                    {isCommissioner && (
                                                        <td>
                                                            <div className="btn-group" role="group">
                                                                <button 
                                                                    className="btn btn-success btn-sm"
                                                                    onClick={() => handleTradeApproval(trade.trade_id, 'approve')}
                                                                    title="Approve this trade"
                                                                >
                                                                    ✓ Approve
                                                                </button>
                                                                <button 
                                                                    className="btn btn-danger btn-sm"
                                                                    onClick={() => {
                                                                        const notes = prompt('Rejection reason (optional):');
                                                                        if (notes !== null) { // User didn't cancel
                                                                            handleTradeApproval(trade.trade_id, 'reject', notes);
                                                                        }
                                                                    }}
                                                                    title="Reject this trade"
                                                                >
                                                                    ✗ Reject
                                                                </button>
                                                            </div>
                                                        </td>
                                                    )}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Payouts Section */}
            {selectedLeagueId && (
                <div className="mt-3">
                    <div className="card mb-4">
                        <div className="card-header d-flex justify-content-between align-items-center">
                            <h4 className="mb-0" style={{ color: 'black' }}>Payouts</h4>
                            <button
                                className="btn btn-link text-decoration-none"
                                type="button"
                                data-bs-toggle="collapse"
                                data-bs-target="#collapsePayouts"
                                aria-expanded="true"
                                aria-controls="collapsePayouts"
                                style={{ color: '#9966CC' }}
                            >
                                ▼
                            </button>
                        </div>
                        <div className="collapse show" id="collapsePayouts">
                            <div className="card-body">
                                {leagueFeeSettings && leagueFeeSettings.fee_amount ? (
                                    <>
                                        <div className="text-center mb-3">
                                            <p className="text-muted mb-1">Based on {leagueFeeSettings.fee_amount} {leagueFeeSettings.fee_currency} per team</p>
                                            <p className="text-muted mb-0">Total Prize Pool: {prizeAmounts.total.toFixed(2)} {leagueFeeSettings.fee_currency}</p>
                                        </div>
                                        <div className="row">
                                            <div className="col-md-3">
                                                <div className="text-center p-3">
                                                    <h5 className="text-success mb-2">🥇 1st Place</h5>
                                                    <h3 className="text-success fw-bold">50%</h3>
                                                    <p className="text-success mb-0 fw-bold">{prizeAmounts.first.toFixed(2)} {leagueFeeSettings.fee_currency}</p>
                                                </div>
                                            </div>
                                            <div className="col-md-3">
                                                <div className="text-center p-3">
                                                    <h5 className="text-secondary mb-2">🥈 2nd Place</h5>
                                                    <h3 className="text-secondary fw-bold">30%</h3>
                                                    <p className="text-secondary mb-0 fw-bold">{prizeAmounts.second.toFixed(2)} {leagueFeeSettings.fee_currency}</p>
                                                </div>
                                            </div>
                                            <div className="col-md-3">
                                                <div className="text-center p-3">
                                                    <h5 className="text-warning mb-2">🥉 3rd Place</h5>
                                                    <h3 className="text-warning fw-bold">10%</h3>
                                                    <p className="text-warning mb-0 fw-bold">{prizeAmounts.third.toFixed(2)} {leagueFeeSettings.fee_currency}</p>
                                                </div>
                                            </div>
                                            <div className="col-md-3">
                                                <div className="text-center p-3">
                                                    <h5 className="text-info mb-2">📊 Best Record</h5>
                                                    <h3 className="text-info fw-bold">10%</h3>
                                                    <p className="text-info mb-0 fw-bold">{prizeAmounts.bestRecord.toFixed(2)} {leagueFeeSettings.fee_currency}</p>
                                                </div>
                                            </div>
                                        </div>
                                    </>
                                ) : (
                                    <div className="text-center">
                                        <p className="text-muted">League fees not yet set. Payout amounts will be calculated once fees are configured.</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default League;