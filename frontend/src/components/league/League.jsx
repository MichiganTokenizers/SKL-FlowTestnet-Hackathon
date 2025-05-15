import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

function League() {
    const [teams, setTeams] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [leagueInfo, setLeagueInfo] = useState(null);

    useEffect(() => {
        const fetchLeagueData = async () => {
            try {
                const sessionToken = localStorage.getItem('sessionToken');
                if (!sessionToken) {
                    throw new Error('No session token found');
                }

                // Fetch league information
                const leagueResponse = await fetch('http://localhost:5000/league', {
                    headers: {
                        'Authorization': sessionToken
                    }
                });

                if (!leagueResponse.ok) {
                    throw new Error('Failed to fetch league data');
                }

                const leagueData = await leagueResponse.json();
                setLeagueInfo(leagueData);

                // Fetch teams
                const teamsResponse = await fetch('http://localhost:5000/league/teams', {
                    headers: {
                        'Authorization': sessionToken
                    }
                });

                if (!teamsResponse.ok) {
                    throw new Error('Failed to fetch teams data');
                }

                const teamsData = await teamsResponse.json();
                setTeams(teamsData.teams || []);
            } catch (err) {
                console.error('Error fetching league data:', err);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchLeagueData();
    }, []);

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

    return (
        <div className="container py-4">
            <div className="row mb-4">
                <div className="col">
                    <h1 className="display-4 mb-3">{leagueInfo?.leagueName || 'Supreme Keeper League'}</h1>
                    {leagueInfo?.season && (
                        <p className="lead text-muted">Season {leagueInfo.season}</p>
                    )}
                </div>
            </div>

            <div className="row">
                <div className="col-md-8">
                    <div className="card shadow-sm">
                        <div className="card-header bg-primary text-white">
                            <h2 className="h4 mb-0">League Teams</h2>
                        </div>
                        <div className="card-body">
                            {teams.length > 0 ? (
                                <div className="list-group">
                                    {teams.map((team) => (
                                        <Link
                                            key={team.id}
                                            to={`/team/${team.id}`}
                                            className="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
                                        >
                                            <div>
                                                <h5 className="mb-1">{team.name}</h5>
                                                <small className="text-muted">
                                                    Manager: {team.manager}
                                                </small>
                                            </div>
                                            <div className="text-end">
                                                <span className="badge bg-primary rounded-pill">
                                                    {team.record || '0-0'}
                                                </span>
                                            </div>
                                        </Link>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-muted text-center my-4">No teams found in the league.</p>
                            )}
                        </div>
                    </div>
                </div>

                <div className="col-md-4">
                    <div className="card shadow-sm mb-4">
                        <div className="card-header bg-primary text-white">
                            <h3 className="h5 mb-0">League Info</h3>
                        </div>
                        <div className="card-body">
                            <ul className="list-group list-group-flush">
                                <li className="list-group-item d-flex justify-content-between align-items-center">
                                    Total Teams
                                    <span className="badge bg-primary rounded-pill">{teams.length}</span>
                                </li>
                                {leagueInfo?.draftDate && (
                                    <li className="list-group-item">
                                        Draft Date: {new Date(leagueInfo.draftDate).toLocaleDateString()}
                                    </li>
                                )}
                                {leagueInfo?.tradeDeadline && (
                                    <li className="list-group-item">
                                        Trade Deadline: {new Date(leagueInfo.tradeDeadline).toLocaleDateString()}
                                    </li>
                                )}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default League; 