import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './AssociateSleeper.css';

const API_BASE_URL = "http://localhost:5000";

const AssociateSleeper = ({ onAssociationSuccess }) => {
  const [sleeperUsername, setSleeperUsername] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    if (!sleeperUsername.trim()) {
      setError('Sleeper username cannot be empty.');
      setIsLoading(false);
      return;
    }

    const sessionToken = localStorage.getItem('sessionToken');
    if (!sessionToken) {
      setError('No session token found. Please log in again.');
      setIsLoading(false);
      navigate('/'); // Or to a login page
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/complete_association`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': sessionToken 
        },
        body: JSON.stringify({ sleeperUsername })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `Server responded with ${response.status}`);
      }

      if (data.success) {
        console.log('Sleeper account associated successfully!');
        if (onAssociationSuccess) {
          onAssociationSuccess(); // This should trigger data refetch and navigation in App.jsx
        } else {
          navigate('/league'); // Fallback navigation
        }
      } else {
        setError(data.error || 'Failed to associate Sleeper account.');
      }
    } catch (err) {
      setError(err.message);
    }
    setIsLoading(false);
  };

  return (
    <div className="container py-5">
      <div className="row justify-content-center">
        <div className="col-md-6">
          <div className="card">
            <div className="card-body">
              <h2 className="card-title text-center mb-4">Link Your Sleeper Account</h2>
              <p className="text-center text-muted mb-4">
                To access your league data, please enter your Sleeper username.
              </p>
              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label htmlFor="sleeperUsername" className="form-label">Sleeper Username</label>
                  <input 
                    type="text" 
                    className="form-control"
                    id="sleeperUsername"
                    value={sleeperUsername}
                    onChange={(e) => setSleeperUsername(e.target.value)}
                    placeholder="Enter your Sleeper username"
                    disabled={isLoading}
                  />
                </div>

                {error && (
                  <div className="alert alert-danger" role="alert">
                    {error}
                  </div>
                )}

                <div className="d-grid">
                  <button 
                    type="submit" 
                    className="btn btn-primary btn-lg"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                        Linking...
                      </>
                    ) : (
                      'Link Sleeper Account'
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
};

export default AssociateSleeper; 