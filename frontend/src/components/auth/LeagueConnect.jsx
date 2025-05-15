import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function LeagueConnect({ sessionToken, onSuccess }) {
    const [sleeperLeagueId, setSleeperLeagueId] = useState('');
    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    const fetchAllSleeperData = async () => {
        try {
            const response = await fetch('http://localhost:5000/sleeper/fetchAll', {
                method: 'GET',
                headers: {
                    'Authorization': sessionToken
                }
            });
            const data = await response.json();
            if (data.success) {
                console.log('All Sleeper data fetched and stored successfully.');
            } else {
                console.error('Failed to fetch all Sleeper data:', data.error);
            }
        } catch (error) {
            console.error('Error fetching all Sleeper data:', error);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch('http://localhost:5000/league/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': sessionToken
                },
                body: JSON.stringify({
                    sleeperLeagueId
                })
            });

            const data = await response.json();
            if (data.success) {
                await fetchAllSleeperData(); // Fetch all data after successful connection
                onSuccess();
                navigate('/league');
            } else {
                setError(data.error || 'Failed to connect league');
            }
        } catch (err) {
            console.error('Error connecting league:', err);
            setError('Failed to connect to server');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="container">
            <div className="row justify-content-center">
                <div className="col-md-8 col-lg-6">
                    <div className="card shadow-sm">
                        <div className="card-body p-4">
                            <h2 className="card-title text-center mb-4">Welcome to Supreme Keeper League!</h2>
                            <p className="text-muted text-center mb-4">
                                To get started, please connect your Sleeper league
                            </p>
                            
                            <form onSubmit={handleSubmit}>
                                <div className="mb-3">
                                    <label htmlFor="sleeperLeagueId" className="form-label">
                                        Sleeper League ID
                                    </label>
                                    <input
                                        type="text"
                                        className="form-control"
                                        id="sleeperLeagueId"
                                        value={sleeperLeagueId}
                                        onChange={(e) => setSleeperLeagueId(e.target.value)}
                                        placeholder="Enter your Sleeper league ID"
                                        required
                                    />
                                    <div className="form-text">
                                        You can find your league ID in your Sleeper league URL. 
                                        For example, in "https://sleeper.com/leagues/1234567890", 
                                        the league ID is "1234567890"
                                    </div>
                                </div>

                                {error && (
                                    <div className="alert alert-danger" role="alert">
                                        {error}
                                    </div>
                                )}

                                <div className="d-grid">
                                    <button
                                        type="submit"
                                        className="btn btn-primary"
                                        disabled={isLoading}
                                    >
                                        {isLoading ? (
                                            <>
                                                <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                                                Connecting...
                                            </>
                                        ) : (
                                            'Connect League'
                                        )}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default LeagueConnect; 