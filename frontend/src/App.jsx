import { BrowserRouter as Router, Route, Routes, Link, Navigate, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
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
    const [leagues, setLeagues] = useState([]); // Added for managing user's leagues
    const [selectedLeagueId, setSelectedLeagueId] = useState(null); // Added for selected league
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
            setLeagues([]); // Clear leagues on logout
            setSelectedLeagueId(null); // Clear selected league on logout
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
        console.log('Sleeper association successful, backend has fetched data.');
        setIsNewUser(false); // User is no longer "new"
        // After association, fetch leagues and navigate
        if (sessionToken) { // sessionToken should be set by now
            const userLeaguesData = await fetchUserLeagues(sessionToken);
            if (userLeaguesData.success && userLeaguesData.leagues.length > 0) {
                navigate('/league');
            } else if (userLeaguesData.success) { // Has leagues but list is empty
                navigate('/league'); // Navigate to league page, it will show "no leagues"
            } else {
                // Handle error in fetching leagues post-association if necessary
                navigate('/associate-sleeper'); // Or back to a relevant page
            }
        } else {
             navigate('/associate-sleeper'); // Fallback if session token issue
        }
    };

    const fetchUserLeagues = async (token) => {
        if (!token) return { success: false, leagues: [], error: 'No token for fetchUserLeagues' };
        try {
            const response = await fetch(`${API_BASE_URL}/league/local`, {
                headers: { 'Authorization': token }
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Failed to fetch leagues and parse error JSON' }));
                console.error('Failed to fetch user leagues:', response.status, errorData.error);
                if (response.status === 401) { // Unauthorized
                    logout(); // Perform logout if session is invalid
                }
                return { success: false, leagues: [], error: errorData.error || `HTTP error ${response.status}` };
            }
            const data = await response.json();
            if (data.success) {
                setLeagues(data.leagues || []);
                if ((data.leagues || []).length > 0) {
                    setSelectedLeagueId(data.leagues[0].league_id);
                } else {
                    setSelectedLeagueId(null); // No leagues, so no selected league
                }
                return { success: true, leagues: data.leagues || [] };
            } else {
                return { success: false, leagues: [], error: data.error || 'Fetching leagues was not successful' };
            }
        } catch (error) {
            console.error('Error in fetchUserLeagues:', error);
            return { success: false, leagues: [], error: error.message };
        }
    };

    useEffect(() => {
        const currentToken = localStorage.getItem('sessionToken');
        if (currentToken) {
            setSessionToken(currentToken);
            // Verify token and fetch initial data if token exists
            const verifyAndFetch = async () => {
                // This verification could be a dedicated endpoint or part of fetchUserLeagues
                // For now, assume fetchUserLeagues handles auth errors (like 401)
                const leagueData = await fetchUserLeagues(currentToken);
                if (!leagueData.success) {
                    // If fetching leagues fails (e.g. bad token), logout might have been called
                    // If not, ensure user is redirected or state is cleared
                    if (localStorage.getItem('sessionToken')) { // check if logout was called
                       // setError('Failed to verify session or fetch initial data.');
                       // Potentially navigate to login or show error
                    }
                }
                 // Determine if association is needed based on user state (isNewUser could be set by login)
                const userNeedsAssociation = async () => {
                    try {
                        const res = await fetch(`${API_BASE_URL}/auth/check_association`, { headers: { 'Authorization': currentToken }});
                        if (!res.ok) return true; // Assume needs association on error
                        const checkData = await res.json();
                        return checkData.success ? checkData.needs_association : true;
                    } catch {
                        return true;
                    }
                };

                if (await userNeedsAssociation()) {
                    navigate('/associate-sleeper');
                } else if (leagueData.leagues.length > 0) {
                    navigate('/league');
                } else {
                    // User is associated but has no leagues, stay on a page or redirect to league import/search
                    navigate('/league'); // League page will show "no leagues"
                }

            };
            verifyAndFetch();
        }

        // This effect primarily handles initial login via TonConnect
        if (connected && tonWallet && !sessionToken && !localStorage.getItem('sessionToken')) { // Ensure we only run this for a new wallet connection without an existing session
            const login = async () => {
                try {
                    const nonce = Math.random().toString(36).substring(2); // Consider a more secure nonce
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
                        setIsNewUser(loginData.isNewUser); // Set based on login response

                        if (loginData.isNewUser) {
                            navigate('/associate-sleeper');
                        } else {
                            // For existing user, fetch their leagues
                            const userLeaguesData = await fetchUserLeagues(newSessionToken);
                            if (userLeaguesData.success && userLeaguesData.leagues.length > 0) {
                                navigate('/league');
                            } else if (userLeaguesData.success) { // Successfully fetched but no leagues
                                navigate('/league'); // League page will show "no leagues"
                            } else {
                                // Error fetching leagues for existing user, potentially back to login or error page
                                // For now, let's assume they might need to associate if fetchAllData implies it
                                const fetchResult = await fetchAllSleeperData(newSessionToken);
                                if (!fetchResult.success && fetchResult.needsAssociation) {
                                     navigate('/associate-sleeper');
                                } else {
                                     navigate('/'); // Or an error page
                                }
                            }
                        }
                    } else {
                        // Handle login failure
                        console.error("Login failed:", loginData.error);
                    }
                } catch (error) {
                    console.error('Login process error:', error);
                }
            };
            login();
        }
    // }, [connected, tonWallet, sessionToken, navigate]); // Original dependencies
    // eslint-disable-next-line react-hooks/exhaustive-deps 
    }, [connected, tonWallet, navigate]); // Removed sessionToken from deps to avoid re-running on its own change from localStorage hydration

    const handleLeagueNavChange = (leagueId) => {
        setSelectedLeagueId(leagueId);
        navigate('/league'); // Navigate to league page when a league is selected from navbar
    };

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
                            {sessionToken && !isNewUser && ( // Keep other nav items
                                <>
                                    <li className="nav-item">
                                        <Link className="nav-link" to="/my-team">My Team</Link>
                                    </li>
                                    <li className="nav-item">
                                        <Link className="nav-link" to="/trade-desk">Trade Desk</Link>
                                    </li>
                                </>
                            )}
                        </ul>
                        <div className="d-flex align-items-center">
                            {sessionToken ? (
                                <div className="nav-item dropdown">
                                    <a className="nav-link text-white" href="#" id="userDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" className="bi bi-list" viewBox="0 0 16 16">
                                            <path fillRule="evenodd" d="M2.5 12a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h10a.5.5 0 0 1 0 1H3a.5.5 0 0 1-.5-.5z"/>
                                        </svg>
                                    </a>
                                    <ul className="dropdown-menu dropdown-menu-end" aria-labelledby="userDropdown">
                                        <li><Link className="dropdown-item" to="/account">Account</Link></li>
                                        <li><Link className="dropdown-item" to="/change-team-name">Change Team Name</Link></li>
                                        <li><hr className="dropdown-divider" /></li>
                                        <li><button onClick={logout} className="dropdown-item btn btn-link">Logout</button></li>
                                    </ul>
                                </div>
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
                            <League leagues={leagues} selectedLeagueId={selectedLeagueId} sessionToken={sessionToken} />
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
        <TonConnectUIProvider manifestUrl="https://10bf-193-43-135-254.ngrok-free.app/tonconnect-manifest.json">
            <Router>
                <AppContent />
            </Router>
        </TonConnectUIProvider>
    );
}

export default App;