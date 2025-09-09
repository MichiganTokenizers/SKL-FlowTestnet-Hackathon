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

function TransactionsTable({ leagueId, sessionToken }) {
    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [currentWeek, setCurrentWeek] = useState(null);
    const [selectedWeek, setSelectedWeek] = useState('all');
    const [availableWeeks, setAvailableWeeks] = useState([]);

    useEffect(() => {
        if (leagueId && sessionToken) {
            fetchCurrentWeek();
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
        const { type, details } = transaction;
        let players = [];
        let oldTeams = [];
        let newTeams = [];
        let description = '';

        if (type === 'trade') {
            description = 'Trade';
            
            // For trades, include all involved players without contract check
            const adds = details.adds || {};
            const drops = details.drops || {};
            
            Object.entries(adds).forEach(([playerId, newRosterId]) => {
                players.push(details.player_names?.[playerId] || playerId);
                // Get team name and create abbreviation
                const newTeamName = details.team_names?.[newRosterId];
                const newTeamAbbr = newTeamName && newTeamName !== newRosterId ? createTeamAbbreviation(newTeamName) : `Team ${newRosterId}`;
                newTeams.push(newTeamAbbr);
                // Find if it was dropped from somewhere (in trade, it's from the other team)
                let oldRosterId = Object.entries(drops).find(([p]) => p === playerId)?.[1] || 'Traded';
                const oldTeamName = details.team_names?.[oldRosterId];
                const oldTeamAbbr = oldRosterId === 'Traded' ? 'Traded' : 
                    (oldTeamName && oldTeamName !== oldRosterId ? createTeamAbbreviation(oldTeamName) : `Team ${oldRosterId}`);
                oldTeams.push(oldTeamAbbr);
            });

            Object.entries(drops).forEach(([playerId, oldRosterId]) => {
                if (!players.includes(playerId)) {
                    players.push(details.player_names?.[playerId] || playerId);
                    const oldTeamName = details.team_names?.[oldRosterId];
                    const oldTeamAbbr = oldTeamName && oldTeamName !== oldRosterId ? createTeamAbbreviation(oldTeamName) : `Team ${oldRosterId}`;
                    oldTeams.push(oldTeamAbbr);
                    newTeams.push('Traded');
                }
            });
        } else if (type === 'waiver' || type === 'free_agent') {
            description = 'Waive';
            
            // For waive/free_agent, only include dropped players (assuming waive means drop)
            // But per user: "only include players who have an existing contract"
            // Note: Since we can't check contracts in frontend, we'll assume all drops are waives
            // TODO: Enhance backend to include 'has_contract' in details for drops
            const drops = details.drops || {};
            
            Object.entries(drops).forEach(([playerId, oldRosterId]) => {
                // Placeholder: Assume has_contract=true for now; replace with actual check if backend provides it
                const has_contract = true;  // TODO: Use details.has_contract[playerId] if added to backend
                
                if (has_contract) {
                    players.push(details.player_names?.[playerId] || playerId);
                    const oldTeamName = details.team_names?.[oldRosterId];
                    const oldTeamAbbr = oldTeamName && oldTeamName !== oldRosterId ? createTeamAbbreviation(oldTeamName) : `Team ${oldRosterId}`;
                    oldTeams.push(oldTeamAbbr);
                    newTeams.push('FA');
                }
            });
            
            // If there are adds without drops, perhaps treat as pickup, but per user focus on waive (drops)
        } else {
            // For other types, skip or use generic
            description = type.charAt(0).toUpperCase() + type.slice(1);
            return { description, players: [], oldTeams: [], newTeams: [] };
        }

        return { description, players, oldTeams, newTeams };
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'Unknown';
        
        try {
            // Add 'Z' to force UTC interpretation, then convert to local time
            const date = new Date(dateString + 'Z');
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
            {transactions.length === 0 ? (
                <div className="text-center py-3">
                    <p className="text-muted mb-0">
                        {selectedWeek === 'all' 
                            ? 'No transactions found for this league.' 
                            : `No transactions found for Week ${selectedWeek}.`
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
                            </tr>
                        </thead>
                        <tbody>
                            {transactions.map((transaction) => {
                                const { description, players, oldTeams, newTeams } = getTransactionDetails(transaction);
                                
                                if (players.length === 0) {
                                    return null;  // Skip transactions with no players
                                }

                                // Multi-row for multiple players
                                return players.map((player, index) => {
                                    const oldTeam = oldTeams[index];
                                    const newTeam = newTeams[index];
                                    
                                    // Team display is now already processed as abbreviations
                                    const getTeamDisplay = (teamValue) => {
                                        return teamValue || 'N/A';
                                    };
                                    
                                    return (
                                        <tr key={`${transaction.transaction_id}-${index}`}>
                                            <td>{formatDate(transaction.created_at)}</td>
                                            <td>{description}</td>
                                            <td>{player}</td>
                                            <td>{getTeamDisplay(oldTeam)}</td>
                                            <td>{getTeamDisplay(newTeam)}</td>
                                            <td>{transaction.week ? transaction.week : 'Unknown'}</td>
                                        </tr>
                                    );
                                });
                            })}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}

// Remove getStatusColor and getStatusBadgeColor if no longer needed, since Type is now normal text and Status column is removed

export default TransactionsTable;
