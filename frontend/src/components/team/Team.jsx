import React from 'react';
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

const API_BASE_URL = "http://localhost:5000";

function Team() {
    const { teamId } = useParams();
    const [teamData, setTeamData] = useState(null);
    const [leagueContext, setLeagueContext] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [contractDurations, setContractDurations] = useState({});

    const fetchTeamData = async (currentTeamId, token) => {
        if (!token) {
            setError('Please log in to view team information.');
            setLoading(false);
            return;
        }
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/team/${currentTeamId}`, {
                headers: { 'Authorization': token }
            });
            if (!response.ok) {
                if (response.status === 401) {
                        localStorage.removeItem('sessionToken');
                        window.location.href = '/login';
                        throw new Error('Session expired. Please log in again.');
                    }
                    throw new Error('Failed to fetch team data');
                }
            const data = await response.json();
                if (data.success) {
                    setTeamData(data.team);
                setLeagueContext(data.league_context);
                } else {
                    setError(data.error || 'Failed to load team data');
                }
        } catch (err) {
                setError(err.message);
        }
                setLoading(false);
    };

    useEffect(() => {
        const sessionToken = localStorage.getItem('sessionToken');
        fetchTeamData(teamId, sessionToken);
    }, [teamId]);

    const handleDurationChange = (playerId, duration) => {
        setContractDurations(prevDurations => ({
            ...prevDurations,
            [playerId]: duration
        }));
    };

    if (loading) return <div className="container p-4"><p>Loading team data...</p></div>;
    if (error) return <div className="container p-4"><p className="text-danger">{error}</p></div>;
    if (!teamData) return <div className="container p-4"><p>No team data available</p></div>;

    const positionOrder = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF', 'DL', 'LB', 'DB'];

    const getSortableCost = (player, currentSeasonYear) => {
        let cost = null;
        if (player.yearly_costs && currentSeasonYear && player.yearly_costs[currentSeasonYear] !== null && player.yearly_costs[currentSeasonYear] !== undefined) {
            cost = player.yearly_costs[currentSeasonYear];
        } else if (player.player_contract_context && player.player_contract_context.status === 'pending_setting' &&
                   player.player_contract_context.recent_auction_value !== null && 
                   player.player_contract_context.recent_auction_value !== undefined) {
            cost = player.player_contract_context.recent_auction_value;
        }
        // Return a very low number for null/undefined costs if sorting descending, or handle as needed
        // For descending sort (b-a), a higher value means earlier. So nulls should be effectively smallest.
        return cost === null || cost === undefined ? -1 : Number(cost);
    };

    const allPlayersSorted = [...teamData.roster].sort((a, b) => {
        const posA = a.position || 'Unknown';
        const posB = b.position || 'Unknown';
        const indexA = positionOrder.indexOf(posA);
        const indexB = positionOrder.indexOf(posB);

        if (indexA !== indexB) { // Sort by position group first
            if (indexA === -1) return 1; // 'Unknown' or unlisted goes to the end
            if (indexB === -1) return -1;
            return indexA - indexB;
        }

        // Within the same position group, sort by contract cost (descending)
        const currentSeasonYear = leagueContext ? leagueContext.current_season_year : null;
        const costA = getSortableCost(a, currentSeasonYear);
        const costB = getSortableCost(b, currentSeasonYear);

        if (costA !== costB) {
            return costB - costA; // Descending order for cost (higher cost comes first)
        }

        // If costs are equal, sort by name (ascending)
        return (a.name || '').localeCompare(b.name || ''); 
    });

    const yearlyCostColumnHeaders = [];
    if (leagueContext && leagueContext.current_season_year) {
        for (let i = 0; i < 4; i++) {
            yearlyCostColumnHeaders.push(leagueContext.current_season_year + i);
        }
    }

    const numDataColumns = 4 + yearlyCostColumnHeaders.length; // Name, Team, Draft Amount, Yrs Rem + yearly costs

    // Calculate min/max costs for each year for shading
    const costRangesByYear = {};
    if (teamData && teamData.roster && leagueContext && leagueContext.current_season_year) {
        yearlyCostColumnHeaders.forEach(year => {
            const costsForYear = teamData.roster.map(p => {
                let cost = p.yearly_costs && p.yearly_costs[year];
                // Consider recent_auction_value for the current year if actual cost is null (as per display logic)
                if (p.player_contract_context && p.player_contract_context.status === 'pending_setting' &&
                    year === leagueContext.current_season_year &&
                    (cost === null || cost === undefined) &&
                    p.player_contract_context.recent_auction_value !== null &&
                    p.player_contract_context.recent_auction_value !== undefined) {
                    cost = p.player_contract_context.recent_auction_value;
                }
                return cost;
            }).filter(c => c !== null && c !== undefined);

            if (costsForYear.length > 0) {
                costRangesByYear[year] = {
                    min: Math.min(...costsForYear),
                    max: Math.max(...costsForYear)
                };
            } else {
                costRangesByYear[year] = { min: 0, max: 0 }; // Default if no costs
            }
        });
    }

    const getCostCellStyle = (cost, year) => {
        if (cost === null || cost === undefined || !costRangesByYear[year]) {
            return {};
        }
        const range = costRangesByYear[year];
        if (range.min === range.max) { // All costs are the same for this year, or only one player
            return { backgroundColor: 'hsl(120, 70%, 65%)' }; // A medium green
        }
        const normalized = (cost - range.min) / (range.max - range.min);
        const lightness = 90 - (normalized * 50); // Range from 90% (light) to 40% (dark)
        return { backgroundColor: `hsl(120, 70%, ${lightness}%)` };
    };

    // Calculate yearly totals for future years (years 2, 3, 4 of display)
    const futureYearlyTotals = {};
    if (teamData && teamData.roster && leagueContext && leagueContext.current_season_year && yearlyCostColumnHeaders.length > 1) {
        yearlyCostColumnHeaders.slice(1).forEach(year => { // Start from the second year
            let totalForYear = 0;
            teamData.roster.forEach(p => {
                let cost = p.yearly_costs && p.yearly_costs[year];
                // This logic is for display in player rows; for totals, we sum actual contract costs for future years.
                // If it's a 'pending_setting' player, their future year costs are likely null initially unless already set.
                // We should sum based on what their contract implies, which vw_contractByYear would provide.
                // The p.yearly_costs should already reflect this from the backend.
                if (cost !== null && cost !== undefined) {
                    totalForYear += cost;
                }
            });
            futureYearlyTotals[year] = totalForYear;
        });
    }

    const canSetContracts = leagueContext && 
                            leagueContext.is_contract_setting_period_active &&
                            teamData && 
                            teamData.roster.some(p => p.player_contract_context && p.player_contract_context.status === 'pending_setting');

    const handleSaveContractDurations = async () => {
        if (!teamData || !teamData.league_id) {
            setError('League ID is missing. Cannot save contract durations.');
            return;
        }
        if (Object.keys(contractDurations).length === 0) {
            // setError('No contract durations have been changed.'); // Or just let the button be disabled
            return;
        }

        setLoading(true); // Indicate loading state
        setError(null);

        try {
            const sessionToken = localStorage.getItem('sessionToken');
            const response = await fetch(`${API_BASE_URL}/api/team/${teamId}/contracts/durations`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': sessionToken
                },
                body: JSON.stringify({
                    player_durations: contractDurations,
                    league_id: teamData.league_id
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || `Failed to save contract durations. Status: ${response.status}`);
            }

            if (result.success) {
                alert(result.message || 'Contract durations saved successfully!');
                setContractDurations({}); // Clear selections
                // Re-fetch team data to reflect changes immediately
                const sessionToken = localStorage.getItem('sessionToken');
                await fetchTeamData(teamId, sessionToken);
            } else {
                setError(result.error || 'An unknown error occurred while saving.');
            }
        } catch (err) {
            setError(err.message);
        }
        setLoading(false);
    };

    return (
        <div className="container p-4">
            <h1 className="display-4 fw-bold mb-4">{teamData.name}</h1>
            <div className="card mb-4">
                <div className="card-body">
                    <h5 className="card-title">Manager Information</h5>
                    <p className="card-text">
                        <strong>Name:</strong> {teamData.manager.name}<br />
                        <strong>Sleeper Username:</strong> {teamData.manager.sleeper_username}
                    </p>
                </div>
            </div>

            {leagueContext && (
                <div className="card mb-4">
                    <div className="card-body">
                        <h5 className="card-title">League Status</h5>
                        <p className="card-text">
                            <strong>Current Season:</strong> {leagueContext.current_season_year}<br />
                            <strong>Status:</strong> {leagueContext.is_offseason ? "Off-season" : "In-season"}<br />
                            {leagueContext.is_contract_setting_period_active && (
                                <strong className="text-success">Contract setting period is active.</strong>
                            )}
                        </p>
                    </div>
                </div>
            )}

            {canSetContracts && (
                <div className="card mb-4">
                    <div className="card-body text-end">
                        <button 
                            className="btn btn-primary" 
                            onClick={handleSaveContractDurations}
                            disabled={Object.keys(contractDurations).length === 0}
                        >
                            Save Contract Durations
                        </button>
                    </div>
                </div>
            )}

            {/* Display Future Yearly Totals */}
            {yearlyCostColumnHeaders.length > 1 && (
                <div className="card mb-4">
                    <div className="card-body">
                        <h5 className="card-title">Projected Future Yearly Contract Totals</h5>
                        <div className="row">
                            {yearlyCostColumnHeaders.slice(1).map(year => (
                                <div key={`total-${year}`} className="col-md-4">
                                    <strong>{year}:</strong> ${futureYearlyTotals[year] !== undefined ? futureYearlyTotals[year].toFixed(2) : '0.00'}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            <div className="row">
                <div className="col-md-12">
                    <h2 className="mb-3">Active Roster</h2>
                    {allPlayersSorted.length > 0 ? (
                                <div className="table-responsive">
                            <table className="table table-hover table-sm">
                                        <thead>
                                            <tr>
                                                <th>Name</th>
                                                <th>Team</th>
                                        <th>Draft Amount</th>
                                        <th>Yrs Rem</th>
                                        {yearlyCostColumnHeaders.map(year => (
                                            <th key={`header-cost-${year}`}>{year} Cost</th>
                                        ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                    {(() => {
                                        let currentPosition = null;
                                        return allPlayersSorted.map(player => {
                                            const showPositionHeader = player.position !== currentPosition;
                                            if (showPositionHeader) {
                                                currentPosition = player.position;
                                            }
                                            return (
                                                <React.Fragment key={`player-fragment-${player.id}`}>
                                                    {showPositionHeader && (
                                                        <tr className="position-group-header">
                                                            <td colSpan={numDataColumns}>
                                                                <h5 className="m-1">{currentPosition || 'Unknown'}</h5>
                                                    </td>
                                                </tr>
                                                    )}
                                                    <tr key={player.id} className="player-data-row">
                                                        <td>
                                                            {player.name}
                                                            {player.status && player.status !== 'Active' && (
                                                                <sup style={{ marginLeft: '4px', color: player.status === 'IR' ? 'red' : 'orange' }}>
                                                                    {player.status.substring(0,2).toUpperCase()}
                                                                </sup>
                                                            )}
                                                        </td>
                                                        <td>{player.team}</td>
                                                        <td>${player.draft_amount !== null && player.draft_amount !== undefined ? player.draft_amount : 'N/A'}</td>
                                                        <td>
                                                            {leagueContext && leagueContext.is_contract_setting_period_active && player.player_contract_context && player.player_contract_context.status === 'pending_setting' ? (
                                                                <select 
                                                                    className="form-select form-select-sm" 
                                                                    value={contractDurations[player.id] !== undefined ? contractDurations[player.id] : (player.years_remaining || 1)}
                                                                    onChange={(e) => handleDurationChange(player.id, parseInt(e.target.value))}
                                                                >
                                                                    {[1, 2, 3, 4].map(yearVal => (
                                                                        <option key={yearVal} value={yearVal}>{yearVal}</option>
                                                                    ))}
                                                                </select>
                                                            ) : (
                                                                player.years_remaining !== null && player.years_remaining !== undefined ? player.years_remaining : 'N/A'
                                                            )}
                                                        </td>
                                                        {yearlyCostColumnHeaders.map(year => {
                                                            const cost = player.yearly_costs && player.yearly_costs[year];
                                                            let displayCost = cost;
                                                            if (player.player_contract_context && player.player_contract_context.status === 'pending_setting' && 
                                                                year === leagueContext.current_season_year && 
                                                                (cost === null || cost === undefined) && 
                                                                player.player_contract_context.recent_auction_value !== null && 
                                                                player.player_contract_context.recent_auction_value !== undefined) {
                                                                displayCost = player.player_contract_context.recent_auction_value;
                                                            }
                                                            return (
                                                                <td key={`cost-${player.id}-${year}`} style={getCostCellStyle(displayCost, year)}>
                                                                    {displayCost !== null && displayCost !== undefined ? `$${displayCost}` : '-'}
                                                                </td>
                                                            );
                                                        })}
                                                    </tr>
                                                </React.Fragment>
                                            );
                                        });
                                    })()}
                                        </tbody>
                                    </table>
                        </div>
                    ) : (
                        <p>No active players on this roster.</p>
                    )}
                </div>
            </div>
        </div>
    );
}

export default Team; 