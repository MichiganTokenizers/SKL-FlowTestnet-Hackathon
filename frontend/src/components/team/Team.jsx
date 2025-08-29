import React from 'react';
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { API_BASE_URL } from '../../config';
import BudgetTradeModal from '../league/BudgetTradeModal';

function Team() {
    console.log("Team.jsx DEPLOY TEST: TRADE_BUTTON_V3_LOADED");
    const { teamId, leagueId } = useParams();
    const [teamData, setTeamData] = useState(null);
    const [teamPositionRanks, setTeamPositionRanks] = useState(null);
    const [futureYearlyTotalRanks, setFutureYearlyTotalRanks] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [contractDurations, setContractDurations] = useState({});
    
    // Trade modal state
    const [showTradeModal, setShowTradeModal] = useState(false);

    const fetchTeamData = async (currentTeamId, currentLeagueId, token) => {
        if (!token) {
            setError('Please log in to view team information.');
            setLoading(false);
            return;
        }
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE_URL}/team/${currentTeamId}?league_id=${currentLeagueId}`, {
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
                    setTeamData(data);
                setTeamPositionRanks(data.team_position_spending_ranks || null);
                setFutureYearlyTotalRanks(data.future_yearly_total_ranks || null);
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
        fetchTeamData(teamId, leagueId, sessionToken);
    }, [teamId, leagueId]);

    const handleDurationChange = (playerId, duration) => {
        setContractDurations(prevDurations => ({
            ...prevDurations,
            [playerId]: duration
        }));
    };

    if (loading) return <div className="container p-4"><p>Loading team data...</p></div>;
    if (error) return <div className="container p-4"><p className="text-danger">{error}</p></div>;
    if (!teamData) return <div className="container p-4"><p>No team data available</p></div>;

    console.log("Team.jsx - is_offseason value:", teamData.is_offseason);

    const positionOrder = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF', 'DL', 'LB', 'DB'];

    const getSortableCost = (player, currentProcessingYearForCostFunc) => {
        let cost = null;
        if (player.contract_status === 'Pending Contract Setting' && currentProcessingYearForCostFunc === teamData.current_processing_year) {
            cost = player.draft_amount;
        } else if (player.projected_costs && currentProcessingYearForCostFunc) {
            const yearCostInfo = player.projected_costs.find(pc => pc.year === currentProcessingYearForCostFunc);
            if (yearCostInfo) {
                cost = yearCostInfo.cost;
            }
        }
        // For free agents, only show cost for current year, not future years
        if (cost === null && player.contract_status === "Free Agent" && currentProcessingYearForCostFunc === teamData.current_processing_year) {
            cost = 0;
        }
        return cost === null || cost === undefined ? -1 : Number(cost);
    };

    const allPlayersSorted = (teamData.players_by_position 
        ? Object.values(teamData.players_by_position).flat() 
        : []
    ).sort((a, b) => {
        const posA = a.position || 'Unknown';
        const posB = b.position || 'Unknown';
        const indexA = positionOrder.indexOf(posA);
        const indexB = positionOrder.indexOf(posB);

        if (indexA !== indexB) {
            if (indexA === -1) return 1;
            if (indexB === -1) return -1;
            return indexA - indexB;
        }

        const currentSortYear = teamData ? teamData.current_processing_year : null;
        const costA = getSortableCost(a, currentSortYear);
        const costB = getSortableCost(b, currentSortYear);

        if (costA !== costB) {
            return costB - costA;
        }
        return (a.name || '').localeCompare(b.name || ''); 
    });

    const yearlyCostColumnHeaders = [];
    if (teamData && teamData.current_processing_year) {
        for (let i = 0; i < 4; i++) {
            yearlyCostColumnHeaders.push(teamData.current_processing_year + i);
        }
    }

    const numDataColumns = 4 + yearlyCostColumnHeaders.length;

    const positionGroupTotals = {};
    if (teamData && teamData.current_processing_year) {
        allPlayersSorted.forEach(player => {
            const position = player.position || 'Unknown';
            const cost = getSortableCost(player, teamData.current_processing_year);
            if (!positionGroupTotals[position]) {
                positionGroupTotals[position] = 0;
            }
            if (cost > 0) {
                positionGroupTotals[position] += cost;
            }
        });
    }

    const getCostCellStyle = (cost) => {
        if (cost === null || cost === undefined || cost < 0) { // Handles '-' and ensures non-negative costs
            return {};
        }

        const normMin = 0;
        const normMax = 50;

        const effectiveCost = Math.min(cost, normMax);
        
        let normalized;
        if (normMax === normMin) { // Should not happen with normMax = 50, normMin = 0
            normalized = (effectiveCost >= normMax) ? 1 : 0;
        } else {
            normalized = (effectiveCost - normMin) / (normMax - normMin);
        }

        const lightness = 90 - (normalized * 50); // Scale from 90% (lightest) down to 40% (darkest)
        return { backgroundColor: `hsl(120, 70%, ${lightness}%)` };
    };

    const futureYearlyTotals = {};
    if (teamData && teamData.current_processing_year && yearlyCostColumnHeaders.length > 1) {
        yearlyCostColumnHeaders.slice(1).forEach(year => {
            let contractTotalForYear = 0;
            allPlayersSorted.forEach(p => { 
                let cost = null;
                if (p.projected_costs) {
                    const yearCostInfo = p.projected_costs.find(pc => pc.year === year);
                    if (yearCostInfo) { 
                        cost = yearCostInfo.cost;
                    }
                }
                if (cost !== null && cost !== undefined) {
                    contractTotalForYear += cost;
                }
            });

            const penaltyTotalForYear = (teamData.team_yearly_penalty_totals && teamData.team_yearly_penalty_totals[year])
                ? teamData.team_yearly_penalty_totals[year]
                : 0;

            futureYearlyTotals[year] = {
                contractTotal: contractTotalForYear,
                penaltyTotal: penaltyTotalForYear
            };
        });
    }

    const canSetContracts = teamData && 
                            teamData.is_contract_setting_period_active &&
                            allPlayersSorted.some(p => p.contract_status === 'Pending Contract Setting');
    
    // Debug logging for trade button visibility
    console.log("DEBUG TRADE BUTTON - teamData exists:", !!teamData);
    console.log("DEBUG TRADE BUTTON - is_contract_setting_period_active:", teamData?.is_contract_setting_period_active);
    console.log("DEBUG TRADE BUTTON - players with Pending Contract Setting:", allPlayersSorted.filter(p => p.contract_status === 'Pending Contract Setting').length);
    console.log("DEBUG TRADE BUTTON - canSetContracts result:", canSetContracts);

    const handleSaveContractDurations = async () => {
        if (!teamData || !teamData.league_id) {
            setError('League ID is missing. Cannot save contract durations.');
            return;
        }
        if (Object.keys(contractDurations).length === 0) {
            return;
        }

        setLoading(true);
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
                setContractDurations({}); 
                const currentToken = localStorage.getItem('sessionToken'); // Re-fetch token in case it changed
                await fetchTeamData(teamId, leagueId, currentToken);
            } else { // if result.success is false but response was ok (e.g. validation error from backend)
                setError(result.error || 'An unknown error occurred while saving.');
            }
        } catch (err) {
            setError(err.message);
        }
        setLoading(false);
    };

    // Console logs for debugging
    if (teamData && teamData.players_by_position) {
        console.log("Team.jsx - teamData (includes all context like fields):", teamData);
        console.log("Team.jsx - teamData.players_by_position:", teamData.players_by_position);
        allPlayersSorted.forEach(player => {
            console.log(`Team.jsx - Player ${player.id} (${player.name}) contract_status:`, player.contract_status, "draft_amount:", player.draft_amount, "projected_costs:", player.projected_costs);
        });
    }
    console.log("Team.jsx - canSetContracts variable value:", canSetContracts);

    return (
        <div className="wrapper">
            <div className="container p-4">
                <h1 className="display-4 fw-bold mb-4">{teamData.team_name}</h1>

                <div className="card mb-4">
                    <div className="card-body">
                        <div className="row">
                            <div className="col-md-6">
                                <span className="fw-bold">Manager:</span> {teamData.manager_name} <br />
                                <span className="fw-bold">League:</span> {teamData.league_name} ({teamData.league_id})
                            </div>
                            <div className="col-md-6 text-md-end">
                                {teamData.current_processing_year !== undefined && (
                        <p className="card-text">
                                        <strong>Current Season:</strong> {teamData.current_processing_year} ({teamData.is_offseason ? 'Off-season' : 'In-season'})
                                        {teamData.is_contract_setting_period_active && 
                                    <span className="badge ms-2" style={{ backgroundColor: '#9966CC', color: 'white' }}>
                                        Contract Setting Active
                                    </span>}
                            </p>
                        )}
                            </div>
                        </div>
                        {teamData.is_contract_setting_period_active && (
                            <div className="alert alert-info mt-3" role="alert">
                                Contract Setting Active! Set contract durations for newly acquired players below.
                            </div>
                        )}
                    </div>
                </div>

                {/* Future Spending & Roster Analysis Row */}
                <div className="row mt-4 mb-4">
                    {/* Current Year Roster Analysis Table Column (MOVED TO LEFT) */}
                    <div className="col-md-6">
                        <div className="card h-100">
                            <div className="card-body">
                                <h5 className="card-title">{teamData.current_processing_year} Roster Summary</h5>
                                {teamData && teamData.current_processing_year && teamData.players_by_position ? (
                                    <div className="table-responsive">
                                        <table className="table table-sm table-bordered">
                                            <thead>
                                                <tr>
                                                    <th className="text-start" style={{ backgroundColor: '#E77728', color: '#100B00' }}>Position</th>
                                                    <th className="text-center" style={{ backgroundColor: '#E77728', color: '#100B00' }}>Players</th>
                                                    <th className="text-center" style={{ backgroundColor: '#E77728', color: '#100B00' }}>Total Contract $</th>
                                                    <th className="text-center" style={{ backgroundColor: '#E77728', color: '#100B00' }}>Spending Rank</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {positionOrder.map(position => {
                                                    const playersInPosition = allPlayersSorted.filter(p => p.position === position);
                                                    const playerCount = playersInPosition.length;
                                                    const positionTotalCost = positionGroupTotals[position] || 0;
                                                    const rankData = teamPositionRanks && teamPositionRanks[position];

                                                    if (playerCount === 0 && positionTotalCost === 0 && (!rankData || rankData.total_teams === 0)) return null;

                                                    return (
                                                        <tr key={`roster-analysis-${position}`}>
                                                            <td className="text-start fw-bold">{position}</td>
                                                            <td className="text-center">{playerCount}</td>
                                                            <td className="text-center">
                                                                ${positionTotalCost.toFixed(0)}
                                                            </td>
                                                            <td className="text-center">
                                                                {rankData ? 
                                                                    <div className="text-muted" style={{fontSize: '0.8rem', marginTop: '0px'}}>
                                                                        <strong>{`(Rank ${rankData.rank}/${rankData.total_teams})`}</strong>
                                                                    </div> 
                                                                    : 'N/A'}
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                ) : (
                                    <p>No current year data available for roster analysis.</p>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Future Spending Table Column (MOVED TO RIGHT) */}
                    <div className="col-md-6">
                        <div className="card h-100">
                            <div className="card-body">
                                <h5 className="card-title">Future Budgets ($200/yr)</h5>
                                {(yearlyCostColumnHeaders.length > 1 && Object.keys(futureYearlyTotals).some(yr => futureYearlyTotals[yr] && (futureYearlyTotals[yr].contractTotal > 0 || futureYearlyTotals[yr].penaltyTotal > 0 || (futureYearlyTotalRanks && futureYearlyTotalRanks[yr])))) ? (
                                    <div className="table-responsive">
                                        <table className="table table-sm table-bordered text-center">
                                            <thead>
                                                <tr>
                                                    <th style={{ backgroundColor: '#E77728', color: '#100B00' }}></th>
                                                    {yearlyCostColumnHeaders.slice(1).map(year => (
                                                        <th key={`future-header-${year}`} style={{ backgroundColor: '#E77728', color: '#100B00' }}>{year}</th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <tr>
                                                    <td className="text-start fw-bold">- Contracts</td>
                                                    {yearlyCostColumnHeaders.slice(1).map(year => {
                                                        const yearData = futureYearlyTotals[year];
                                                        const contractTotal = yearData ? (yearData.contractTotal || 0) : 0;
                                                        return <td key={`contracts-${year}`}>${contractTotal.toFixed(0)}</td>;
                                                    })}
                                                </tr>
                                                <tr>
                                                    <td className="text-start fw-bold">- Penalties</td>
                                                    {yearlyCostColumnHeaders.slice(1).map(year => {
                                                        const yearData = futureYearlyTotals[year];
                                                        const penaltyTotal = yearData ? (yearData.penaltyTotal || 0) : 0;
                                                        return <td key={`penalties-${year}`}>${penaltyTotal.toFixed(0)}</td>;
                                                    })}
                                                </tr>
                                                <tr>
                                                    <td className="text-start fw-bold">- Trades</td>
                                                    {yearlyCostColumnHeaders.slice(1).map(year => {
                                                        const tradesTotal = teamData.team_yearly_trade_amounts && teamData.team_yearly_trade_amounts[year] 
                                                            ? teamData.team_yearly_trade_amounts[year] 
                                                            : 0;
                                                        return <td key={`trades-${year}`}>${tradesTotal.toFixed(0)}</td>;
                                                    })}
                                                </tr>

                                                <tr className="fw-bold table-group-divider">
                                                    <td className="text-start">Remaining Budget</td>
                                                    {yearlyCostColumnHeaders.slice(1).map(year => {
                                                        const yearData = futureYearlyTotals[year];
                                                        const rankInfo = futureYearlyTotalRanks && futureYearlyTotalRanks[year];
                                                        const contractTotal = yearData ? (yearData.contractTotal || 0) : 0;
                                                        const penaltyTotal = yearData ? (yearData.penaltyTotal || 0) : 0;
                                                        const tradesTotal = teamData.team_yearly_trade_amounts && teamData.team_yearly_trade_amounts[year] 
                                                            ? teamData.team_yearly_trade_amounts[year] 
                                                            : 0;
                                                        const overallTotalVal = contractTotal + penaltyTotal + tradesTotal; // Add trades (negative = received, positive = sent)
                                                        const remainingBudget = 200 - overallTotalVal;
                                                        return (
                                                            <td key={`remaining-budget-${year}`}>
                                                                ${remainingBudget.toFixed(0)}
                                                                {rankInfo && (
                                                                    <div className="text-muted" style={{fontSize: '0.8rem', marginTop: '0.25rem'}}>
                                                                        <strong>{`(Rank ${rankInfo.rank}/${rankInfo.total_teams})`}</strong>
                                                                    </div>
                                                                )}
                                                            </td>
                                                        );
                                                    })}
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                ) : (
                                    <p>No future spending data available.</p>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Team Roster Card */}
                <div className="card mb-4">
                    <div className="card-header d-flex justify-content-between align-items-center">
                        <h5 className="mb-0">Team Roster</h5>
                        <div className="ms-3">
                            <button 
                                onClick={() => setShowTradeModal(true)} 
                                className="btn btn-success btn-sm me-2"
                                style={{ backgroundColor: '#28a745', borderColor: '#28a745' }}
                            >
                                Trade Future Budget
                            </button>
                            {canSetContracts && (
                                <button 
                                    onClick={handleSaveContractDurations} 
                                    className="btn btn-primary btn-sm"
                                    style={{ backgroundColor: '#9966CC', borderColor: '#9966CC' }}
                                    disabled={Object.keys(contractDurations).length === 0 || loading}
                                >
                                    {loading ? 'Saving...' : 'Save Contracts'}
                                </button>
                            )}
                        </div>
                    </div>
                    <div className="card-body p-0">
                        {error && canSetContracts && <p className="text-danger p-3 mb-0">{error}</p>}
                        <div className="table-responsive">
                            <table className="table table-hover mb-0">
                                <thead className="table-light">
                                    <tr>
                                        <th>Name</th>
                                        <th>Team</th>
                                        <th>Draft $</th>
                                        <th>Yrs Rem</th>
                                        {yearlyCostColumnHeaders.map(year => (
                                            <th key={`header-cost-${year}`}>{year} $</th>
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
                                        const currentPositionTotal = positionGroupTotals[currentPosition] !== undefined ? positionGroupTotals[currentPosition] : 0;
                                        const positionRankData = teamPositionRanks && teamPositionRanks[currentPosition];

                                        return (
                                            <React.Fragment key={player.id}>
                                                {showPositionHeader && (
                                                    <tr className="position-group-header">
                                                        <td colSpan={numDataColumns}>
                                                            <h5 className="m-1" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                                                <span>{currentPosition || 'Unknown'}</span> 
                                                                {teamData.current_processing_year && (
                                                                    <span style={{ fontWeight: 'normal', fontSize: '0.9rem' }}>
                                                                        {teamData.current_processing_year} Total: ${currentPositionTotal.toFixed(0)}
                                                                        {positionRankData && (
                                                                            ` (Rank: ${positionRankData.rank}/${positionRankData.total_teams})`
                                                                        )}
                                                                    </span>
                                                                )}
                                                            </h5>
                                                        </td>
                                                    </tr>
                                                )}
                                                <tr className="player-data-row">
                                                    <td>
                                                        {player.name}
                                                        {player.status && player.status !== 'Active' && player.status !== 'Free Agent' && player.contract_status !== 'Pending Contract Setting' && (
                                                            <sup style={{ marginLeft: '4px', color: player.status === 'IR' ? 'red' : 'orange' }}>
                                                                {player.status.substring(0,2).toUpperCase()}
                                                            </sup>
                                                        )}
                                                    </td>
                                                    <td>{player.team_nfl}</td>
                                                    <td>${player.draft_amount !== null && player.draft_amount !== undefined ? player.draft_amount : 'N/A'}</td>
                                                    <td>
                                                        {teamData.is_contract_setting_period_active && player.contract_status === 'Pending Contract Setting' ? (
                                                            <select 
                                                                className="form-select form-select-sm" 
                                                                value={contractDurations[player.id] !== undefined ? contractDurations[player.id] : (player.contract_duration_db || 1)}
                                                                onChange={(e) => handleDurationChange(player.id, parseInt(e.target.value))}
                                                            >
                                                                {[1, 2, 3, 4].map(yearVal => (
                                                                    <option key={yearVal} value={yearVal}>{yearVal}</option>
                                                                ))}
                                                            </select>
                                                        ) : player.contract_duration_db && (player.contract_status === 'Active Contract' || player.contract_status === 'Pending Contract Setting') ? (
                                                            `${player.contract_duration_db}`
                                                        ) : (
                                                            player.years_remaining !== null && player.years_remaining !== undefined ? player.years_remaining : 'N/A'
                                                        )}
                                                    </td>
                                                    {yearlyCostColumnHeaders.map(year => {
                                                        const cellCost = getSortableCost(player, year);
                                                        const displayCost = cellCost === -1 ? null : cellCost;
                                                        
                                                        return (
                                                            <td key={`cost-${player.id}-${year}`} style={getCostCellStyle(displayCost)}>
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
                    </div>
                </div>
            </div>
            
            {/* Budget Trade Modal */}
            <BudgetTradeModal
                show={showTradeModal}
                onHide={() => setShowTradeModal(false)}
                teamId={teamId}
                leagueId={leagueId}
                onTradeCreated={() => {
                    // Optionally refresh team data to show updated budgets
                    const sessionToken = localStorage.getItem('sessionToken');
                    fetchTeamData(teamId, leagueId, sessionToken);
                }}
            />
        </div>
    );
}

export default Team; 