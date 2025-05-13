import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { TonConnectButton, useTonConnectUI, useTonAddress, TonConnectUIProvider } from '@tonconnect/ui-react';
import ErrorBoundary from './ErrorBoundary';

// Define the base API URL
const API_BASE_URL = "https://e17b-181-214-151-64.ngrok-free.app"; // Your ngrok URL

// Home Component
function Home({ walletAddress, logout, error }) {
    return (
        <div className="container p-4">
            <h1 className="display-4 fw-bold mb-4">Supreme Keeper League - Home</h1>
            {walletAddress ? (
                <div>
                    <p className="lead">Welcome, {walletAddress}!</p>
                    <button onClick={logout} className="btn btn-danger mt-2">
                        Logout
                    </button>
                </div>
            ) : (
                <TonConnectButton />
            )}
            {error && <p className="text-danger mt-2">{error}</p>}
        </div>
    );
}

// Leagues Component
function Leagues() {
    const [leagues, setLeagues] = useState([]);
    const [sleeperData, setSleeperData] = useState({});
    const [paymentStatus, setPaymentStatus] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [sleeperLeagueId, setSleeperLeagueId] = useState('');

    const tonConnectUI = useTonConnectUI()[0]; // Get the TonConnect UI instance
    const walletAddress = useTonAddress(); // Get the connected wallet address

    const syncSleeperLeague = async (localLeagueId) => {
        const sessionToken = localStorage.getItem('sessionToken');
        if (!sessionToken) {
            setError('Please log in to sync Sleeper data.');
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/sleeper/sync-league`, {
                method: 'POST',
                headers: {
                    'Authorization': sessionToken,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ sleeper_league_id: sleeperLeagueId, local_league_id: localLeagueId })
            });
            const data = await response.json();
            if (data.success) {
                const sleeperResponse = await fetch(`${API_BASE_URL}/sleeper/league/${localLeagueId}`, {
                    headers: { 'Authorization': sessionToken }
                });
                const sleeper = await sleeperResponse.json();
                if (sleeper.success) {
                    setSleeperData(prev => ({ ...prev, [localLeagueId]: sleeper.sleeper_league }));
                }
            } else {
                setError(data.error || 'Failed to sync Sleeper league');
            }
        } catch (err) {
            setError('Error syncing Sleeper league: ' + err.message);
        }
    };

    const payLeagueFee = async (leagueId) => {
        const sessionToken = localStorage.getItem('sessionToken');
        if (!sessionToken) {
            setError('Please log in to pay the league fee.');
            return;
        }

        if (!walletAddress) {
            setError('Please connect your wallet to pay the league fee.');
            return;
        }

        try {
            const amount = 5 * 1e9;
            const recipientAddress = "EQDcOm5plcC8Rc4BqWLV-O4-9NFbeX9_FgxiCkNpiRVMpJVB"; // Replace with actual address

            const transaction = {
                validUntil: Math.floor(Date.now() / 1000) + 60,
                messages: [
                    {
                        address: recipientAddress,
                        amount: amount.toString(),
                        payload: btoa(`League Fee for League ID: ${leagueId}`)
                    }
                ]
            };

            const result = await tonConnectUI.sendTransaction(transaction);
            if (result) {
                const response = await fetch(`${API_BASE_URL}/payments/initiate`, {
                    method: 'POST',
                    headers: {
                        'Authorization': sessionToken,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        league_id: leagueId,
                        transaction_hash: result.boc,
                        amount: amount / 1e9
                    })
                });
                const data = await response.json();
                if (data.success) {
                    alert('Payment initiated! Waiting for confirmation...');
                    checkPaymentStatus(leagueId);
                } else {
                    setError(data.error || 'Failed to initiate payment');
                }
            }
        } catch (err) {
            setError('Error processing payment: ' + err.message);
        }
    };

    const checkPaymentStatus = async (leagueId) => {
        const sessionToken = localStorage.getItem('sessionToken');
        if (!sessionToken) return;

        try {
            const response = await fetch(`${API_BASE_URL}/payments/status/${leagueId}`, {
                headers: { 'Authorization': sessionToken }
            });
            const data = await response.json();
            if (data.success) {
                setPaymentStatus(prev => ({ ...prev, [leagueId]: data }));
                if (data.status === 'pending') {
                    setTimeout(() => checkPaymentStatus(leagueId), 5000);
                }
            }
        } catch (err) {
            setError('Error checking payment status: ' + err.message);
        }
    };

    useEffect(() => {
        const sessionToken = localStorage.getItem('sessionToken');
        if (!sessionToken) {
            setError('Please log in to view leagues.');
            setLoading(false);
            return;
        }

        fetch(`${API_BASE_URL}/leagues`, {
            headers: { 'Authorization': sessionToken }
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    setLeagues(data.leagues);
                    Promise.all(data.leagues.map(league =>
                        Promise.all([
                            fetch(`${API_BASE_URL}/sleeper/league/${league.id}`, {
                                headers: { 'Authorization': sessionToken }
                            }).then(res => res.json()),
                            fetch(`${API_BASE_URL}/payments/status/${league.id}`, {
                                headers: { 'Authorization': sessionToken }
                            }).then(res => res.json())
                        ])
                            .then(([sleeper, payment]) => ({
                                leagueId: league.id,
                                sleeper,
                                payment: payment.success ? payment : null
                            }))
                    ))
                        .then(results => {
                            const sleeperMap = {};
                            const paymentMap = {};
                            results.forEach(result => {
                                if (result.sleeper.success) {
                                    sleeperMap[result.leagueId] = result.sleeper.sleeper_league;
                                }
                                if (result.payment) {
                                    paymentMap[result.leagueId] = result.payment;
                                }
                            });
                            setSleeperData(sleeperMap);
                            setPaymentStatus(paymentMap);
                            setLoading(false);
                        })
                        .catch(err => {
                            setError('Error fetching data: ' + err.message);
                            setLoading(false);
                        });
                } else {
                    setError(data.error || 'Failed to fetch leagues');
                    setLoading(false);
                }
            })
            .catch(err => {
                setError('Error fetching leagues: ' + err.message);
                setLoading(false);
            });
    }, []);

    if (loading) return <p className="text-center text-muted">Loading leagues...</p>;
    if (error) return <p className="text-center text-danger">{error}</p>;

    return (
        <div className="container p-4">
            <h1 className="display-4 fw-bold mb-4">Leagues</h1>
            <ul className="list-group">
                {leagues.map(league => (
                    <li key={league.id} className="list-group-item">
                        <div className="d-flex justify-content-between align-items-center">
                            <span className="fs-5 fw-semibold">
                                {league.name} (Created by user ID: {league.creator_id})
                            </span>
                            {paymentStatus[league.id] && paymentStatus[league.id].status === 'confirmed' ? (
                                <span className="text-success">Fee Paid ({paymentStatus[league.id].amount} TON)</span>
                            ) : (
                                <button
                                    onClick={() => payLeagueFee(league.id)}
                                    className="btn btn-success"
                                >
                                    {paymentStatus[league.id]?.status === 'pending' ? 'Payment Pending...' : 'Pay League Fee (5 TON)'}
                                </button>
                            )}
                        </div>
                        {sleeperData[league.id] ? (
                            <div className="mt-2">
                                <p><strong>Sleeper League:</strong> {sleeperData[league.id].name}</p>
                                <p><strong>Season:</strong> {sleeperData[league.id].season}</p>
                                <h3 className="mt-2 fw-semibold">Player Stats:</h3>
                                <ul className="list-group list-group-flush">
                                    {sleeperData[league.id].player_stats.map(stat => (
                                        <li key={stat.player_id} className="list-group-item">
                                            Player ID: {stat.player_id}, Points: {stat.points}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        ) : (
                            <div className="mt-2">
                                <p className="text-muted">No Sleeper data available.</p>
                                <div className="d-flex gap-2 mt-2">
                                    <input
                                        type="text"
                                        placeholder="Enter Sleeper League ID"
                                        value={sleeperLeagueId}
                                        onChange={(e) => setSleeperLeagueId(e.target.value)}
                                        className="form-control w-auto"
                                    />
                                    <button
                                        onClick={() => syncSleeperLeague(league.id)}
                                        className="btn btn-primary"
                                    >
                                        Sync Sleeper League
                                    </button>
                                </div>
                            </div>
                        )}
                    </li>
                ))}
            </ul>
        </div>
    );
}

// Profile Component
function Profile() {
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const sessionToken = localStorage.getItem('sessionToken');
        if (!sessionToken) {
            setError('Please log in to view your profile.');
            setLoading(false);
            return;
        }

        fetch(`${API_BASE_URL}/auth/verify`, {
            headers: { 'Authorization': sessionToken }
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    setProfile({ wallet_address: data.walletAddress });
                    setLoading(false);
                } else {
                    setError(data.error || 'Failed to fetch profile');
                    setLoading(false);
                }
            })
            .catch(err => {
                setError('Error fetching profile: ' + err.message);
                setLoading(false);
            });
    }, []);

    if (loading) return <p className="text-center text-muted">Loading profile...</p>;
    if (error) return <p className="text-center text-danger">{error}</p>;

    return (
        <div className="container p-4">
            <h1 className="display-4 fw-bold mb-4">Profile</h1>
            <p><strong>Wallet Address:</strong> {profile.wallet_address}</p>
            <p><strong>Username:</strong> {profile.username || 'Not set'}</p>
        </div>
    );
}

// Inner App Component to Delay Hook Usage
function InnerApp() {
  const [walletAddress, setWalletAddress] = useState(null);
  const [error, setError] = useState(null);

  const tonConnectUI = useTonConnectUI()[0];
  const address = useTonAddress();

  useEffect(() => {
      if (address) {
          setWalletAddress(address);
          const loginWithWallet = async () => {
            try {
                const nonce = Math.random().toString(36).substring(2);
                console.log('Sending POST to', `${API_BASE_URL}/auth/login`, { walletAddress: address, nonce });
                const response = await fetch(`${API_BASE_URL}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ walletAddress: address, nonce })
                });
        
                if (!response.ok) {
                    const text = await response.text();
                    throw new Error(`HTTP error ${response.status}: ${text || 'No response body'}`);
                }
        
                const data = await response.json();
                if (data.success) {
                    localStorage.setItem('sessionToken', data.sessionToken);
                    setError(null);
                } else {
                    setError('Login failed: ' + (data.error || 'Unknown error'));
                    localStorage.removeItem('sessionToken');
                    await tonConnectUI.disconnect();
                }
            } catch (err) {
                setError('Failed to authenticate wallet: ' + err.message);
                localStorage.removeItem('sessionToken');
                try {
                    await tonConnectUI.disconnect();
                } catch (disconnectErr) {
                    console.error('Failed to disconnect wallet:', disconnectErr);
                }
            }
        };

          if (!localStorage.getItem('sessionToken')) {
              loginWithWallet();
          }
      } else {
          setWalletAddress(null);
      }
  }, [address, tonConnectUI]);

  const logout = async () => {
      localStorage.removeItem('sessionToken');
      setWalletAddress(null);
      setError(null);
      try {
          await tonConnectUI.disconnect();
      } catch (err) {
          console.error('Failed to disconnect wallet:', err);
      }
  };

  useEffect(() => {
      const verifySession = async () => {
          const sessionToken = localStorage.getItem('sessionToken');
          if (sessionToken && !address) {
              try {
                  const res = await fetch(`${API_BASE_URL}/auth/verify`, {
                      headers: { 'Authorization': sessionToken }
                  });
                  const data = await res.json();
                  if (data.success) {
                      setWalletAddress(data.walletAddress);
                  } else {
                      localStorage.removeItem('sessionToken');
                      setWalletAddress(null);
                  }
              } catch (err) {
                  setError('Error verifying session: ' + err.message);
                  localStorage.removeItem('sessionToken');
                  setWalletAddress(null);
                  try {
                      await tonConnectUI.disconnect();
                  } catch (disconnectErr) {
                      console.error('Failed to disconnect wallet:', disconnectErr);
                  }
              }
          }
      };

      verifySession();
  }, [address]);

  return (
      <ErrorBoundary>
          <Router>
              <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
                  <div className="container">
                      <Link className="navbar-brand" to="/">SKL</Link>
                      <div className="navbar-nav">
                          <Link className="nav-link" to="/">Home</Link>
                          <Link className="nav-link" to="/leagues">Leagues</Link>
                          <Link className="nav-link" to="/profile">Profile</Link>
                      </div>
                  </div>
              </nav>
              <Routes>
                  <Route path="/" element={<Home walletAddress={walletAddress} logout={logout} error={error} />} />
                  <Route path="/leagues" element={<Leagues />} />
                  <Route path="/profile" element={<Profile />} />
              </Routes>
          </Router>
      </ErrorBoundary>
  );
}

// Main App Component
function App() {
    return (
        <TonConnectUIProvider manifestUrl={`${API_BASE_URL}/tonconnect-manifest.json`}>
            <InnerApp />
        </TonConnectUIProvider>
    );
}

export default App;