import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

const API_BASE_URL = "http://localhost:5000";

function Team() {
    const { teamId } = useParams();
    const [teamData, setTeamData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const sessionToken = localStorage.getItem('sessionToken');
        if (!sessionToken) {
            setError('Please log in to view team information.');
            setLoading(false);
            return;
        }

        fetch(`${API_BASE_URL}/team/${teamId}`, {
            headers: { 'Authorization': sessionToken }
        })
            .then(res => {
                if (!res.ok) {
                    if (res.status === 401) {
                        localStorage.removeItem('sessionToken');
                        window.location.href = '/login';
                        throw new Error('Session expired. Please log in again.');
                    }
                    throw new Error('Failed to fetch team data');
                }
                return res.json();
            })
            .then(data => {
                if (data.success) {
                    setTeamData(data.team);
                } else {
                    setError(data.error || 'Failed to load team data');
                }
                setLoading(false);
            })
            .catch(err => {
                setError(err.message);
                setLoading(false);
            });
    }, [teamId]);

    if (loading) return <div className="container p-4"><p>Loading team data...</p></div>;
    if (error) return <div className="container p-4"><p className="text-danger">{error}</p></div>;
    if (!teamData) return <div className="container p-4"><p>No team data available</p></div>;

    const playersByPosition = teamData.roster.reduce((acc, player) => {
        const position = player.position;
        if (!acc[position]) {
            acc[position] = [];
        }
        acc[position].push(player);
        return acc;
    }, {});

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

            <div className="row">
                <div className="col-md-8">
                    <h2 className="mb-3">Active Roster</h2>
                    {Object.entries(playersByPosition).map(([position, players]) => (
                        <div key={position} className="card mb-3">
                            <div className="card-header">
                                <h5 className="mb-0">{position}</h5>
                            </div>
                            <div className="card-body">
                                <div className="table-responsive">
                                    <table className="table table-hover">
                                        <thead>
                                            <tr>
                                                <th>Name</th>
                                                <th>Team</th>
                                                <th>Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {players.map(player => (
                                                <tr key={player.id}>
                                                    <td>{player.name}</td>
                                                    <td>{player.team}</td>
                                                    <td>
                                                        <span className={`badge ${player.status === 'Active' ? 'bg-success' : 'bg-warning'}`}>
                                                            {player.status}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="col-md-4">
                    <div className="card mb-3">
                        <div className="card-header">
                            <h5 className="mb-0">Taxi Squad</h5>
                        </div>
                        <div className="card-body">
                            {teamData.taxi_squad.length > 0 ? (
                                <ul className="list-group list-group-flush">
                                    {teamData.taxi_squad.map(playerId => {
                                        const player = teamData.roster.find(p => p.id === playerId);
                                        return player ? (
                                            <li key={playerId} className="list-group-item">
                                                {player.name} ({player.position})
                                            </li>
                                        ) : null;
                                    })}
                                </ul>
                            ) : (
                                <p className="text-muted">No players on taxi squad</p>
                            )}
                        </div>
                    </div>

                    <div className="card">
                        <div className="card-header">
                            <h5 className="mb-0">Reserve</h5>
                        </div>
                        <div className="card-body">
                            {teamData.reserve.length > 0 ? (
                                <ul className="list-group list-group-flush">
                                    {teamData.reserve.map(playerId => {
                                        const player = teamData.roster.find(p => p.id === playerId);
                                        return player ? (
                                            <li key={playerId} className="list-group-item">
                                                {player.name} ({player.position})
                                            </li>
                                        ) : null;
                                    })}
                                </ul>
                            ) : (
                                <p className="text-muted">No players on reserve</p>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Team; 