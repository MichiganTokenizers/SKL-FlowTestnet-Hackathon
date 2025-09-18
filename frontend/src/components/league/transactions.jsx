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
    const [penalties, setPenalties] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [teamMap, setTeamMap] = useState({});
    const [playerMap, setPlayerMap] = useState({});

    useEffect(() => {
        if (leagueId && sessionToken) {
            fetchTeamMap();
            fetchPlayerMap();
            fetchPenalties();
        }
    }, [leagueId, sessionToken]);


    const fetchTeamMap = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/league/${leagueId}/teams`, {
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
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch(`${API_BASE_URL}/league/${leagueId}/penalties`, {
                headers: { 'Authorization': sessionToken }
            });
            const data = await response.json();
            
            if (data.success) {
                setPenalties(data.penalties || []);
            } else {
                setError(data.error || 'Failed to fetch penalties');
                setPenalties([]);
            }
        } catch (err) {
            setError('Error fetching penalties: ' + err.message);
            setPenalties([]);
        } finally {
            setLoading(false);
        }
    };



    // Group penalties by player to calculate totals
    const groupPenaltiesByPlayer = () => {
        const grouped = {};
        
        penalties.forEach(penalty => {
            const playerId = penalty.player_id;
            if (!grouped[playerId]) {
                grouped[playerId] = {
                    player_id: playerId,
                    player_name: playerMap[playerId] || playerId,
                    penalties: [],
                    total_amount: 0,
                    penalty_created_at: penalty.penalty_created_at,
                    draft_amount: penalty.draft_amount,
                    contract_year: penalty.contract_year,
                    duration: penalty.duration,
                    team_id: penalty.team_id,
                    team_name: penalty.team_name
                };
            }
            
            grouped[playerId].penalties.push(penalty);
            grouped[playerId].total_amount += penalty.amount;
        });
        
        return Object.values(grouped);
    };

    const formatDate = (timestamp) => {
        if (!timestamp) return 'Unknown';
        
        try {
            const date = new Date(timestamp);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
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
                    <span className="visually-hidden">Loading penalties...</span>
                </div>
                <span className="ms-2">Loading penalties...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="alert alert-warning" role="alert">
                <strong>Warning:</strong> {error}
                <button 
                    className="btn btn-sm btn-outline-warning ms-2"
                    onClick={fetchPenalties}
                >
                    Retry
                </button>
            </div>
        );
    }

    // Group penalties by player
    const penaltyGroups = groupPenaltiesByPlayer();

    return (
        <div>
            {/* Penalties Table */}
            {penaltyGroups.length === 0 ? (
                <div className="text-center py-3">
                    <p className="text-muted mb-0">
                        No waived players with penalties found for this league.
                    </p>
                </div>
            ) : (
                <div className="table-responsive">
                    <table className="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th>Date Waived</th>
                                <th>Team</th>
                                <th>Player</th>
                                <th>Contract Details</th>
                                <th>Penalty Years</th>
                                <th>Total Penalties</th>
                            </tr>
                        </thead>
                        <tbody>
                            {penaltyGroups.map((group, index) => (
                                <tr key={index}>
                                    <td>{formatDate(group.penalty_created_at)}</td>
                                    <td>
                                        {group.team_name ? createTeamAbbreviation(group.team_name) : `Team ${group.team_id}`
                                    </td>
                                    <td>{group.player_name}</td>
                                    <td>
                                        <small>
                                            ${group.draft_amount} for {group.duration} years<br/>
                                            Started: {group.contract_year}
                                        </small>
                                    </td>
                                    <td>
                                        <small>
                                            {group.penalties.map(p => p.penalty_year).join(', ')}
                                        </small>
                                    </td>
                                    <td className="fw-bold text-danger">
                                        {formatCurrency(group.total_amount)}
                                    </td>
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
