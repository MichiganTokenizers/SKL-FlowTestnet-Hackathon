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

    const fetchAllSleeperData = async (tokenToUse) => {
        if (!tokenToUse) {
            console.error('fetchAllSleeperData called without a token.');
            return { success: false, error: 'No token provided to fetchAllSleeperData' };
        }
        try {
            const response = await fetch('http://localhost:5000/sleeper/fetchAll', {
                method: 'POST',
                headers: {
                    'Authorization': tokenToUse
                }
            });
            const data = await response.json(); // Always parse JSON to get error message
            if (!response.ok) { // Check if response status is not OK (2xx)
                console.error('Failed to fetch all Sleeper data:', data.error || response.statusText);
                return { success: false, error: data.error || response.statusText, needsAssociation: (response.status === 404 && data.error && data.error.includes("No Sleeper user ID associated")) };
            }
            if (data.success) {
                console.log('All Sleeper data fetched and stored successfully.');
                return { success: true };
            } else {
                // This case might be redundant if !response.ok covers it
                console.error('Failed to fetch all Sleeper data (data.success false):', data.error);
                return { success: false, error: data.error, needsAssociation: (data.error && data.error.includes("No Sleeper user ID associated")) };
            }
        } catch (error) {
            console.error('Error fetching all Sleeper data (catch block):', error);
            return { success: false, error: error.message };
        }
    };

    // New function to handle successful association
    const handleAssociationSuccess = async () => {
        console.log('Sleeper association successful, backend has fetched data. Navigating to league.');
        setIsNewUser(false); // User is no longer "new"
        navigate('/league'); // Directly navigate to league
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

                    const loginData = await response.json();
                    if (loginData.success) {
                        const newSessionToken = loginData.sessionToken;
                        localStorage.setItem('sessionToken', newSessionToken);
                        setSessionToken(newSessionToken);
                        setIsNewUser(loginData.isNewUser);
                        
                        let associationNeeded = loginData.isNewUser;
                        if (!loginData.isNewUser) {
                            const fetchResult = await fetchAllSleeperData(newSessionToken);
                            if (!fetchResult.success && fetchResult.needsAssociation) {
                                associationNeeded = true;
                            }
                        }
                        
                        if (associationNeeded) {
                            navigate('/associate-sleeper'); // Or your league-connect route if that handles association
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
                                <Navigate to="/associate-sleeper" replace />
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
                    <Route path="/associate-sleeper" element={<AssociateSleeper onAssociationSuccess={handleAssociationSuccess} />} />
                    <Route path="/league-connect" element={
                        sessionToken && isNewUser ? (
                            <LeagueConnect sessionToken={sessionToken} onSuccess={() => {
                                // After LeagueConnect (if it only creates a user record without sleeper_id)
                                // we might still need to go to association or directly fetch if it now has sleeper_id
                                setIsNewUser(false); // Assumption: LeagueConnect makes them not a new user
                                navigate('/associate-sleeper'); // Or directly to /league if association is handled by LeagueConnect
                            }} />
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
        <TonConnectUIProvider manifestUrl="https://1e4c-193-43-135-215.ngrok-free.app/tonconnect-manifest.json">
            <Router>
                <AppContent />
            </Router>
        </TonConnectUIProvider>
    );
}

export default App;