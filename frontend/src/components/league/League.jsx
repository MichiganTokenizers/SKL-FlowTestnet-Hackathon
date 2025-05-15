import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const API_BASE_URL = "http://localhost:5000";

function League() {
    const [userData, setUserData] = useState({});
    const [teams, setTeams] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const sessionToken = localStorage.getItem('sessionToken');
        if (!sessionToken) {
            setError('Please log in to view league information.');
            setLoading(false);
            return;
        }

        fetch(`${API_BASE_URL}/league/local`, {
            headers: { 'Authorization': sessionToken }
        })
            .then(res => {
                if (!res.ok) {
                    if (res.status === 401) {
                        localStorage.removeItem('sessionToken');
                        window.location.href = '/login';
                        throw new Error('Session expired. Please log in again.');
                    }
                    throw new Error('Failed to fetch league data');
                }
                return res.json();
            })
            .then(data => {
                if (data.success) {
                    setUserData({
                        walletAddress: data.walletAddress || 'Unknown',
                        firstName: data.firstName || 'Unknown',
                        leagueName: data.leagueName || 'Unknown',
                        teamName: data.teamName || 'Unknown'
                    });
                    fetchTeamsData(sessionToken);
                    setLoading(false);
                } else {
                    setError(data.error || 'Failed to fetch league data');
                    setLoading(false);
                }
            })
            .catch(err => {
                setError(err.message);
                setLoading(false);
            });
    }, []);

    const fetchTeamsData = async (sessionToken) => {
        try {
            const response = await fetch(`${API_BASE_URL}/league/standings/local`, {
                headers: { 'Authorization': sessionToken }
            });
            const data = await response.json();
            if (data.success) {
                setTeams(data.teams || []);
            } else {
                setError(data.error || 'Failed to fetch standings');
            }
        } catch (err) {
            setError('Error fetching standings: ' + err.message);
        }
    };

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
        <div className="container p-4">
            <h1 className="display-4 fw-bold mb-4">Supreme Keeper League - {userData.leagueName}</h1>
            <p className="lead">Welcome, {userData.firstName} ({userData.walletAddress})</p>
            <p className="lead">Your Team: {userData.teamName}</p>
            <div className="mt-3">
                {teams.length > 0 ? (
                    <div>
                        <h3>League Standings</h3>
                        <ul className="list-group">
                            {teams.map(team => (
                                <li key={team.id} className="list-group-item">
                                    <Link to={`/team/${team.id}`}>{team.teamName}</Link> - Managed by {team.manager} - Record: {team.record}
                                </li>
                            ))}
                        </ul>
                    </div>
                ) : (
                    <p>No standings data available yet.</p>
                )}
            </div>
        </div>
    );
}

export default League; 