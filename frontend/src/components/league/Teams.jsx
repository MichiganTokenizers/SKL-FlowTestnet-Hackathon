import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { API_BASE_URL } from '../../config';

function Teams() {
    const { leagueId } = useParams();
    const [teams, setTeams] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [currentUserTeam, setCurrentUserTeam] = useState(null);

    useEffect(() => {
        const fetchTeams = async () => {
            try {
                const sessionToken = localStorage.getItem('sessionToken');
                const response = await fetch(`${API_BASE_URL}/api/league/${leagueId}/teams`, {
                    headers: { 'Authorization': sessionToken }
                });

                if (!response.ok) {
                    throw new Error('Failed to fetch teams');
                }

                const data = await response.json();
                if (data.success) {
                    setTeams(data.teams);
                    
                    // Find current user's team to highlight it
                    const currentUser = JSON.parse(localStorage.getItem('currentUserDetails'));
                    if (currentUser?.sleeper_user_id) {
                        const userTeam = data.teams.find(team => 
                            team.sleeper_user_id === currentUser.sleeper_user_id
                        );
                        setCurrentUserTeam(userTeam);
                    }
                } else {
                    setError(data.error || 'Failed to load teams');
                }
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchTeams();
    }, [leagueId]);

    if (loading) return <div className="container p-4"><p>Loading teams...</p></div>;
    if (error) return <div className="container p-4"><p className="text-danger">{error}</p></div>;

    return (
        <div className="container p-4">
            <div className="row mb-4">
                <div className="col">
                    <h2 className="mb-3">League Teams</h2>
                    <p className="text-muted">Click on a team to view their roster and contracts</p>
                </div>
            </div>

            <div className="row">
                {teams.map((team) => (
                    <div key={team.roster_id} className="col-md-6 col-lg-4 mb-3">
                        <div className={`card h-100 ${currentUserTeam?.roster_id === team.roster_id ? 'border-primary' : ''}`}>
                            <div className="card-body">
                                <h5 className="card-title">
                                    {team.team_name}
                                    {currentUserTeam?.roster_id === team.roster_id && (
                                        <span className="badge bg-primary ms-2">Your Team</span>
                                    )}
                                </h5>
                                <p className="card-text">
                                    <strong>Manager:</strong> {team.manager_name}<br/>
                                    <strong>Record:</strong> {team.record}
                                </p>
                                <Link 
                                    to={`/league/${leagueId}/team/${team.roster_id}`}
                                    className="btn btn-outline-primary btn-sm"
                                >
                                    View Team
                                </Link>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default Teams;
