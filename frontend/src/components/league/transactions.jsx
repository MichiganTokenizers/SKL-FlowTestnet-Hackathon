import { useState, useEffect } from 'react';
import { API_BASE_URL } from '../../config';

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

function Transactions({ leagueId, sessionToken }) {
    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [currentWeek, setCurrentWeek] = useState(null);
    const [selectedWeek, setSelectedWeek] = useState('all');
    const [availableWeeks, setAvailableWeeks] = useState([]);
    const [teamMap, setTeamMap] = useState({});
    const [playerMap, setPlayerMap] = useState({});
    const [penalties, setPenalties] = useState({});

    useEffect(() => {
        if (leagueId && sessionToken) {
            fetchCurrentWeek();
            fetchTeamMap();
            fetchPlayerMap();
            fetchPenalties();
            fetchTransactions();
        }
    }, [leagueId, sessionToken]);

    useEffect(() => {
        if (selectedWeek !== 'all') {
            fetchTransactionsByWeek(selectedWeek);
        } else {
            fetchTransactions();
        }
    }, [selectedWeek, leagueId, sessionToken]);

    const fetchCurrentWeek = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/nfl/current-week`);
            const data = await response.json();
            
            if (data.success && !data.is_offseason) {
                setCurrentWeek(data.week);
                // Generate available weeks (1-18 for regular season, 19+ for playoffs)
                const weeks = [];
                for (let i = 1; i <= Math.max(data.week || 18, 18); i++) {
                    weeks.push(i);
                }
                setAvailableWeeks(weeks);
            }
        } catch {
            console.error('Error fetching current week');
        }
    };

    const fetchTeamMap = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/league/${leagueId}/teams`, {
                headers: { 'Authorization': sessionToken }
            });
            const data = await response.json();
            
            if (data.success) {
                const teamMapping = {};
                data.teams.forEach(team => {
                    teamMapping[team.roster_id] = team.team_name;
                });
                setTeamMap(teamMapping);
            }
        } catch (err) {
            console.error('Error fetching team map:', err);
        }
    };

    const fetchPlayerMap = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/players`, {
                headers: { 'Authorization': sessionToken }
            });
            const data = await response.json();
            
            if (data.success) {
                setPlayerMap(data.players);
            }
        } catch (err) {
            console.error('Error fetching player map:', err);
        }
    };

    const fetchPenalties = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/league/${leagueId}/penalties`, {
                headers: { 'Authorization': sessionToken }
            });
            const data = await response.json();
            
            if (data.success) {
                const penaltyMap = {};
                data.penalties.forEach(penalty => {
                    const key = `${penalty.player_id}_${penalty.transaction_id}`;
                    penaltyMap[key] = penalty.amount;
                });
                setPenalties(penaltyMap);
            }
        } catch (err) {
            console.error('Error fetching penalties:', err);
        }
    };

    const fetchTransactions = async () => {
        if (!leagueId || !sessionToken) return;
        
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch(`${API_BASE_URL}/league/${leagueId}/transactions/recent`, {
                headers: { 'Authorization': sessionToken }
            });
            
            const data = await response.json();
            
            if (data.success) {
                setTransactions(data.transactions || []);
            } else {
                setError(data.error || 'Failed to fetch transactions');
                setTransactions([]);
            }
        } catch (err) {
            setError('Error fetching transactions: ' + err.message);
            setTransactions([]);
        } finally {
            setLoading(false);
        }
    };

    const fetchTransactionsByWeek = async (week) => {
        if (!leagueId || !sessionToken || week === 'all') return;
        
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch(`${API_BASE_URL}/league/${leagueId}/transactions/week/${week}`, {
                headers: { 'Authorization': sessionToken }
            });
            
            const data = await response.json();
            
            if (data.success) {
                setTransactions(data.transactions || []);
            } else {
                setError(data.error || 'Failed to fetch transactions');
                setTransactions([]);
            }
        } catch (err) {
            setError('Error fetching transactions: ' + err.message);
            setTransactions([]);
        } finally {
            setLoading(false);
        }
    };

    const getTransactionDetails = (transaction) => {
        const { type, adds, drops, leg, transaction_id } = transaction;
        let players = [];
        let descriptions = [];
        let fromTeams = [];
        let toTeams = [];
        let totalPenalties = [];

        if (type === 'trade') {
            // Handle trades - only include players who are actually traded
            if (adds && drops) {
                // Find players that are both added and dropped (traded)
                const tradedPlayers = [];
                
                Object.entries(adds).forEach(([playerId, toRosterId]) => {
                    if (drops[playerId]) {
                        const fromRosterId = drops[playerId];
                        tradedPlayers.push({
                            playerId,
                            fromRosterId,
                            toRosterId
                        });
                    }
                });

                tradedPlayers.forEach(({ playerId, fromRosterId, toRosterId }) => {
                    players.push(playerMap[playerId] || playerId);
                    descriptions.push('Trade');
                    
                    const fromTeamName = teamMap[fromRosterId];
                    const toTeamName = teamMap[toRosterId];
                    
                    fromTeams.push(fromTeamName ? createTeamAbbreviation(fromTeamName) : `Team ${fromRosterId}`);
                    toTeams.push(toTeamName ? createTeamAbbreviation(toTeamName) : `Team ${toRosterId}`);
                    
                    // Check for penalties
                    const penaltyKey = `${playerId}_${transaction_id}`;
                    const penaltyAmount = penalties[penaltyKey] || 0;
                    totalPenalties.push(penaltyAmount);
                });
            }
        } else if (type === 'free_agent' || type === 'waiver') {
            // Handle waivers - only include players who were dropped and had contracts (penalties)
            if (drops) {
                Object.entries(drops).forEach(([playerId, fromRosterId]) => {
                    // Check if this player had a contract (indicated by penalty)
                    const penaltyKey = `${playerId}_${transaction_id}`;
                    const penaltyAmount = penalties[penaltyKey] || 0;
                    
                    if (penaltyAmount > 0) {
                        players.push(playerMap[playerId] || playerId);
                        descriptions.push('Waive');
                        
                        const fromTeamName = teamMap[fromRosterId];
                        fromTeams.push(fromTeamName ? createTeamAbbreviation(fromTeamName) : `Team ${fromRosterId}`);
                        toTeams.push('FA');
                        totalPenalties.push(penaltyAmount);
                    }
                });
            }
        }

        return { players, descriptions, fromTeams, toTeams, totalPenalties, week: leg };
    };

    const formatDate = (timestamp) => {
        if (!timestamp) return 'Unknown';
        
        try {
            const date = new Date(timestamp);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return 'Invalid date';
        }
    };

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    };

    if (loading) {
        return (
            <div className="text-center py-3">
                <div className="spinner-border spinner-border-sm text-primary" role="status">
                    <span className="visually-hidden">Loading transactions...</span>
                </div>
                <span className="ms-2">Loading transactions...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="alert alert-warning" role="alert">
                <strong>Warning:</strong> {error}
                <button 
                    className="btn btn-sm btn-outline-warning ms-2"
                    onClick={() => selectedWeek === 'all' ? fetchTransactions() : fetchTransactionsByWeek(selectedWeek)}
                >
                    Retry
                </button>
            </div>
        );
    }

    // Process all transactions and flatten the results
    const allTransactionRows = [];
    transactions.forEach(transaction => {
        const { players, descriptions, fromTeams, toTeams, totalPenalties, week } = getTransactionDetails(transaction);
        
        players.forEach((player, index) => {
            allTransactionRows.push({
                date: transaction.created,
                description: descriptions[index],
                player: player,
                from: fromTeams[index],
                to: toTeams[index],
                week: week,
                penalty: totalPenalties[index] || 0
            });
        });
    });

    return (
        <div>
            {/* Week Filter */}
            {availableWeeks.length > 0 && (
                <div className="mb-3">
                    <select 
                        id="weekFilter" 
                        className="form-select form-select-sm" 
                        style={{ maxWidth: '200px' }}
                        value={selectedWeek}
                        onChange={(e) => setSelectedWeek(e.target.value)}
                    >
                        <option value="all">All Weeks</option>
                        {availableWeeks.map(week => (
                            <option key={week} value={week}>
                                Week {week} {week === currentWeek ? '(Current)' : ''}
                            </option>
                        ))}
                    </select>
                </div>
            )}

            {/* Transactions Table */}
            {allTransactionRows.length === 0 ? (
                <div className="text-center py-3">
                    <p className="text-muted mb-0">
                        {selectedWeek === 'all' 
                            ? 'No relevant transactions found for this league.' 
                            : `No relevant transactions found for Week ${selectedWeek}.`
                        }
                    </p>
                </div>
            ) : (
                <div className="table-responsive">
                    <table className="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Description</th>
                                <th>Player</th>
                                <th>From</th>
                                <th>To</th>
                                <th>Week</th>
                                <th>Total Penalties</th>
                            </tr>
                        </thead>
                        <tbody>
                            {allTransactionRows.map((row, index) => (
                                <tr key={index}>
                                    <td>{formatDate(row.date)}</td>
                                    <td>{row.description}</td>
                                    <td>{row.player}</td>
                                    <td>{row.from}</td>
                                    <td>{row.to}</td>
                                    <td>{row.week || 'Unknown'}</td>
                                    <td>{row.penalty > 0 ? formatCurrency(row.penalty) : '-'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}

export default Transactions;
