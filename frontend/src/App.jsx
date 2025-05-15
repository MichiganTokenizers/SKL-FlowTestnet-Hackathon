import { BrowserRouter as Router, Route, Routes, Link, Navigate, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { TonConnectButton, useTonConnectUI, TonConnectUIProvider } from '@tonconnect/ui-react';
import ErrorBoundary from './ErrorBoundary';
import SleeperImport from './SleeperImport';
import AssociateSleeper from './components/auth/AssociateSleeper';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';
import { useTonConnect } from './hooks/useTonConnect';
import { useTonWallet } from '@tonconnect/ui-react';
import Home from './components/common/Home';
import Profile from './components/profile/Profile';
import League from './components/league/League';
import Team from './components/team/Team';

// Define the base API URL
const API_BASE_URL = "http://localhost:5000"; // Changed from ngrok URL to local development server

// League Connect Component
function LeagueConnect({ sessionToken, onSuccess }) {
    const { connected } = useTonConnect();
    const tonWallet = useTonWallet();

    useEffect(() => {
        if (connected && tonWallet && !sessionToken) {
            const login = async () => {
                try {
                    const nonce = Math.random().toString(36).substring(2);
                    const response = await fetch('http://localhost:5000/auth/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            walletAddress: tonWallet.account.address,
                            nonce: nonce
                        })
                    });

                    const data = await response.json();
                    if (data.success) {
                        localStorage.setItem('sessionToken', data.sessionToken);
                        onSuccess();
                    }
                } catch (error) {
                    console.error('Login error:', error);
                }
            };
            login();
        }
    }, [connected, tonWallet, sessionToken, onSuccess]);

    return (
        <div className="container p-4">
            <h1 className="display-4 fw-bold mb-4">League Connect</h1>
            <p>Connecting to the league...</p>
        </div>
    );
}

// App Content Component
function AppContent() {
    const { connected } = useTonConnect();
    const tonWallet = useTonWallet();
    const [sessionToken, setSessionToken] = useState(localStorage.getItem('sessionToken'));
    const [isNewUser, setIsNewUser] = useState(false);
    const tonConnectUI = useTonConnectUI()[0];
    const navigate = useNavigate();

    const logout = async () => {
        try {
            if (tonConnectUI.connected) {
                await tonConnectUI.disconnect();
            }
        } catch (error) {
            console.error('Error disconnecting wallet:', error);
        } finally {
            localStorage.removeItem('sessionToken');
            setSessionToken(null);
            setIsNewUser(false);
            navigate('/');
        }
    };

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

    useEffect(() => {
        if (connected && tonWallet && !sessionToken) {
            const login = async () => {
                try {
                    const nonce = Math.random().toString(36).substring(2);
                    const response = await fetch('http://localhost:5000/auth/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            walletAddress: tonWallet.account.address,
                            nonce: nonce
                        })
                    });

                    const data = await response.json();
                    if (data.success) {
                        localStorage.setItem('sessionToken', data.sessionToken);
                        setSessionToken(data.sessionToken);
                        setIsNewUser(data.isNewUser);
                        
                        // Fetch all Sleeper data after login
                        if (!data.isNewUser) {
                            await fetchAllSleeperData();
                        }
                        
                        // Redirect based on user status
                        if (data.isNewUser) {
                            navigate('/league-connect');
                        } else {
                            navigate('/league');
                        }
                    }
                } catch (error) {
                    console.error('Login error:', error);
                }
            };
            login();
        }
    }, [connected, tonWallet, sessionToken, navigate]);

    return (
        <div className="App min-vh-100 d-flex flex-column">
            <nav className="navbar navbar-expand-lg navbar-dark bg-primary">
                <div className="container-fluid px-4">
                    <Link className="navbar-brand" to="/">Supreme Keeper League</Link>
                    <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                        <span className="navbar-toggler-icon"></span>
                    </button>
                    <div className="collapse navbar-collapse" id="navbarNav">
                        <ul className="navbar-nav me-auto">
                            <li className="nav-item">
                                <Link className="nav-link" to="/">Home</Link>
                            </li>
                            {sessionToken && !isNewUser && (
                                <>
                                    <li className="nav-item">
                                        <Link className="nav-link" to="/league">My League</Link>
                                    </li>
                                    <li className="nav-item">
                                        <Link className="nav-link" to="/profile">Profile</Link>
                                    </li>
                                </>
                            )}
                        </ul>
                        <div className="d-flex align-items-center">
                            {sessionToken ? (
                                <button onClick={logout} className="btn btn-outline-light">Logout</button>
                            ) : (
                                <TonConnectButton className="btn btn-outline-light" />
                            )}
                        </div>
                    </div>
                </div>
            </nav>

            <main className="flex-grow-1 py-4">
                <Routes>
                    <Route path="/" element={
                        sessionToken ? (
                            isNewUser ? (
                                <Navigate to="/league-connect" replace />
                            ) : (
                                <Navigate to="/league" replace />
                            )
                        ) : (
                            <div className="text-center">
                                <h2>Welcome to Supreme Keeper League</h2>
                                <p>Please connect your TON wallet to continue</p>
                            </div>
                        )
                    } />
                    <Route path="/league" element={
                        sessionToken && !isNewUser ? (
                            <League />
                        ) : (
                            <Navigate to="/" replace />
                        )
                    } />
                    <Route path="/team/:teamId" element={
                        sessionToken && !isNewUser ? (
                            <Team />
                        ) : (
                            <Navigate to="/" replace />
                        )
                    } />
                    <Route path="/profile" element={
                        sessionToken && !isNewUser ? (
                            <Profile />
                        ) : (
                            <Navigate to="/" replace />
                        )
                    } />
                    <Route path="/sleeper-import" element={<SleeperImport />} />
                    <Route path="/associate-sleeper" element={<AssociateSleeper walletAddress={localStorage.getItem('walletAddress')} />} />
                    <Route path="/league-connect" element={
                        sessionToken && isNewUser ? (
                            <LeagueConnect sessionToken={sessionToken} onSuccess={() => setIsNewUser(false)} />
                        ) : (
                            <Navigate to="/" replace />
                        )
                    } />
                </Routes>
            </main>
        </div>
    );
}

// Main App Component
function App() {
    return (
        <TonConnectUIProvider manifestUrl="https://c724-193-43-135-218.ngrok-free.app/tonconnect-manifest.json">
            <Router>
                <AppContent />
            </Router>
        </TonConnectUIProvider>
    );
}

export default App;