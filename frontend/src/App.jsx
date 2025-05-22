import { BrowserRouter as Router, Route, Routes, Link, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { useState, useEffect, useCallback } from 'react';
import { TonConnectButton, useTonConnectUI, TonConnectUIProvider } from '@tonconnect/ui-react';
import ErrorBoundary from './ErrorBoundary';
import SleeperImport from './SleeperImport';
import AssociateSleeper from './components/auth/AssociateSleeper';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';
import './App.css';
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
    const [leagues, setLeagues] = useState([]);
    const [selectedLeagueId, setSelectedLeagueId] = useState(null);
    const [currentUserDetails, setCurrentUserDetails] = useState(null);
    const [loginProcessJustCompleted, setLoginProcessJustCompleted] = useState(false);
    const [isAppReady, setIsAppReady] = useState(false);
    const tonConnectUI = useTonConnectUI()[0];
    const navigate = useNavigate();
    const location = useLocation();

    const logout = useCallback(async () => {
        try {
            if (tonConnectUI && tonConnectUI.connected) {
                await tonConnectUI.disconnect();
            }
        } catch (error) {
            console.error('Error disconnecting wallet programmatically:', error);
        } finally {
            localStorage.removeItem('sessionToken');
            setSessionToken(null);
            setIsNewUser(false);
            setLeagues([]);
            setSelectedLeagueId(null);
            setCurrentUserDetails(null);
            setIsAppReady(false);
            if (location.pathname !== '/') {
                navigate('/');
            }
        }
    }, [tonConnectUI, navigate, location.pathname]);

    const fetchUserLeagues = async (token) => {
        if (!token) return { success: false, leagues: [], error: 'No token for fetchUserLeagues' };
        try {
            const response = await fetch(`${API_BASE_URL}/league/local`, {
                headers: { 'Authorization': token }
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Failed to fetch leagues and parse error JSON' }));
                console.error('Failed to fetch user leagues:', response.status, errorData.error);
                if (response.status === 401) logout();
                setCurrentUserDetails(null);
                return { success: false, leagues: [], error: errorData.error || `HTTP error ${response.status}` };
            }
            const data = await response.json();
            if (data.success) {
                setLeagues(data.leagues || []);
                setCurrentUserDetails(data.user_info || null);
                if ((data.leagues || []).length > 0) {
                    if (!selectedLeagueId || !data.leagues.some(l => l.league_id === selectedLeagueId)) {
                        setSelectedLeagueId(data.leagues[0].league_id);
                    }
                } else {
                    setSelectedLeagueId(null);
                }
                return { success: true, leagues: data.leagues || [], user_info: data.user_info };
            } else {
                setCurrentUserDetails(null);
                return { success: false, leagues: [], error: data.error || 'Fetching leagues was not successful' };
            }
        } catch (error) {
            console.error('Error in fetchUserLeagues:', error);
            setCurrentUserDetails(null);
            return { success: false, leagues: [], error: error.message };
        }
    };

    // Verification Effect: Handles existing token on app load
    useEffect(() => {
        if (loginProcessJustCompleted) {
            setLoginProcessJustCompleted(false); // Reset the flag
            return; // Skip this run, let states settle from login effect
        }

        const currentToken = localStorage.getItem('sessionToken');
        if (currentToken) {
            setSessionToken(currentToken); 

            const verifyAndSetStates = async () => {
                await fetchUserLeagues(currentToken); 
                try {
                    const res = await fetch(`${API_BASE_URL}/auth/check_association`, { headers: { 'Authorization': currentToken }});
                    if (res.ok) {
                        const checkData = await res.json();
                        if (checkData.success) {
                            setIsNewUser(checkData.needs_association);
                        } else {
                            setIsNewUser(true); 
                        }
                    } else {
                        if (res.status === 401) logout();
                        setIsNewUser(true); 
                    }
                } catch {
                    setIsNewUser(true); 
                }
                setIsAppReady(true); // Set app ready after all states are set
            };
            verifyAndSetStates();
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [loginProcessJustCompleted, logout]); // Dependencies: loginProcessJustCompleted, logout. fetchUserLeagues/setIsNewUser are stable.

    // Login Effect: Handles new wallet connection via TonConnect
    useEffect(() => {
        if (connected && tonWallet && !sessionToken && !localStorage.getItem('sessionToken')) {
            const login = async () => {
                try {
                    const nonce = Math.random().toString(36).substring(2);
                    const response = await fetch(`${API_BASE_URL}/auth/login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
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
                        setLoginProcessJustCompleted(true); // Signal that login just completed

                        if (!loginData.isNewUser) {
                            await fetchUserLeagues(newSessionToken); // Fetch leagues for existing user
                        }
                        setIsAppReady(true); // Set app ready after all states are set
                    } else {
                        console.error("Login failed:", loginData.error);
                        setIsAppReady(false); // Ensure app is not ready on login failure
                    }
                } catch (error) {
                    console.error('Login process error:', error);
                    setIsAppReady(false); // Ensure app is not ready on error
                }
            };
            login();
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [connected, tonWallet]); // Dependencies: connected, tonWallet. Setters & fetchUserLeagues are stable. navigate removed.

    // Wallet Disconnection Effect
    useEffect(() => {
        if (!tonConnectUI) {
            return;
        }
        const unsubscribe = tonConnectUI.onStatusChange(
            (walletInfo) => {
                const currentSessionToken = localStorage.getItem('sessionToken');
                if (!walletInfo && currentSessionToken) {
                    console.log('Wallet disconnected, triggering app logout.');
                    logout();
                }
            }
        );
        return () => {
            unsubscribe();
        };
    }, [tonConnectUI, logout]);

    const handleLeagueNavChange = (leagueId) => {
        setSelectedLeagueId(leagueId);
        navigate('/league'); // Restore navigation to the league page
    };

    const handleMyTeamClick = async () => {
        console.log("DEBUG_MY_TEAM_CLICK: Attempting to navigate. Selected League ID is:", selectedLeagueId);
        if (!selectedLeagueId) {
            alert("Please select a league first.");
            return;
        }
        if (!currentUserDetails || !currentUserDetails.sleeper_user_id) {
            alert("User details not available. Cannot determine your team.");
            return;
        }
        if (!sessionToken) {
            alert("Session token not available. Please log in again.");
            logout(); // Or navigate to login
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/api/user/roster?league_id=${selectedLeagueId}`, {
                headers: { 'Authorization': sessionToken }
            });
            const data = await response.json();
            if (response.ok && data.success && data.roster_id) {
                navigate(`/league/${selectedLeagueId}/team/${data.roster_id}`);
            } else {
                alert(data.error || "Could not find your team in the selected league.");
            }
        } catch (error) {
            console.error('Error fetching roster ID for My Team click:', error);
            alert('An error occurred while trying to find your team.');
        }
    };

    const handleAssociationSuccess = async () => {
        // ... existing code ...
    };

    return (
        <div className="App min-vh-100 d-flex flex-column">
            <nav className="navbar navbar-expand-lg navbar-dark navbar-custom">
                <div className="container-fluid px-4">
                    <Link className="navbar-brand" to="/">Supreme Keeper League</Link>
                    {/* <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                        <span className="navbar-toggler-icon"></span>
                    </button> */}
                    <div className="collapse navbar-collapse" id="navbarNav">
                        <ul className="navbar-nav me-auto">
                            {sessionToken && !isNewUser && leagues.length > 0 && (
                                <li className="nav-item dropdown">
                                    <a className="nav-link dropdown-toggle" href="#" id="myLeaguesDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                                        My Leagues
                                    </a>
                                    <ul className="dropdown-menu" aria-labelledby="myLeaguesDropdown">
                                        {leagues.map(league => (
                                            <li key={league.league_id}>
                                                <button 
                                                    className={`dropdown-item ${league.league_id === selectedLeagueId ? 'active' : ''}`}
                                                    onClick={() => handleLeagueNavChange(league.league_id)}
                                                >
                                                    {league.name}
                                                </button>
                                            </li>
                                        ))}
                                    </ul>
                                </li>
                            )}
                            {sessionToken && !isNewUser && currentUserDetails && selectedLeagueId && (
                                <>
                                    <li className="nav-item">
                                        <button className="nav-link btn btn-link" onClick={handleMyTeamClick}>
                                            My Team
                                        </button>
                                    </li>
                                    <li className="nav-item">
                                        <Link className="nav-link" to="/trade-desk">Trade Desk</Link>
                                    </li>
                                </>
                            )}
                        </ul>
                        <div className="d-flex align-items-center">
                            <TonConnectButton className="btn btn-outline-light" />
                        </div>
                    </div>
                </div>
            </nav>

            <main className="flex-grow-1 py-4">
                <Routes>
                    <Route path="/" element={
                        sessionToken && isAppReady ? (
                            isNewUser ? (
                                <Navigate to="/associate-sleeper" replace />
                            ) : (
                                <Navigate to="/league" replace />
                            )
                        ) : (
                            sessionToken && !isAppReady ? (
                                <div className="text-center py-5">
                                    <div className="spinner-border text-primary" role="status">
                                        <span className="visually-hidden">Loading...</span>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center">
                                    <h2>Welcome to Supreme Keeper League</h2>
                                    <p>Please connect your TON wallet to continue</p>
                                </div>
                            )
                        )
                    } />
                    <Route path="/league" element={
                        sessionToken && isAppReady && !isNewUser ? (
                            <League leagues={leagues} selectedLeagueId={selectedLeagueId} sessionToken={sessionToken} currentUserDetails={currentUserDetails} />
                        ) : (
                            <Navigate to="/" replace />
                        )
                    } />
                    <Route path="/league/:leagueId/team/:teamId" element={
                        sessionToken && isAppReady && !isNewUser ? (
                            <Team />
                        ) : (
                            <Navigate to="/" replace />
                        )
                    } />
                    <Route path="/sleeper-import" element={<SleeperImport />} />
                    <Route path="/associate-sleeper" element={
                        sessionToken && isAppReady ? /* Also protect association route if needed, or handle differently */ 
                        <AssociateSleeper onAssociationSuccess={handleAssociationSuccess} /> : <Navigate to="/" replace />
                    } />
                    <Route path="/league-connect" element={
                        sessionToken && isAppReady && isNewUser ? (
                            <LeagueConnect sessionToken={sessionToken} onSuccess={() => {
                                setIsNewUser(false); 
                                setIsAppReady(false); // Will re-evaluate and navigate to /associate-sleeper or /league
                                navigate('/'); // Go to root to re-trigger routing logic after this action
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
        <TonConnectUIProvider manifestUrl="https://29d4-193-43-135-7.ngrok-free.app/tonconnect-manifest.json">
            <Router>
                <AppContent />
            </Router>
        </TonConnectUIProvider>
    );
}

export default App;