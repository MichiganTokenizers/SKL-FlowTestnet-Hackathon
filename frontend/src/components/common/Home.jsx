import { Link } from 'react-router-dom';
import { useState } from 'react';

function Home({ sessionToken, onLogout }) {
    // Collapsible state
    const [showInstructions, setShowInstructions] = useState(false);
    const [showRules, setShowRules] = useState(true);

    return (
        <div className="container-fluid px-4 py-5">
            {/* Welcome Title */}
            <div className="row justify-content-center mb-3">
                <div className="col-md-10 col-lg-8">
                    <h2 className="display-4 mb-4" style={{ color: 'white' }}>Welcome to Supreme Keeper League</h2>
                </div>
            </div>
            {/* Login Prompt Section */}
            <div className="row justify-content-center mb-4">
                <div className="col-md-10 col-lg-8">
                    <div className="alert alert-info text-start" role="alert">
                        <h5 className="mb-2">Access Your League</h5>
                        <p className="mb-0">To access your league(s) and manage your team, please <strong>log in with your FLOW wallet</strong> using the button at the top right.</p>
                    </div>
                </div>
            </div>
            {/* Collapsible Rules Section (now above instructions) */}
            <div className="row justify-content-center mb-2">
                <div className="col-md-10 col-lg-8">
                    <button
                        className="btn btn-outline-primary w-100 mb-2 text-start"
                        style={{ color: 'white', borderColor: 'white' }}
                        onClick={() => setShowRules((v) => !v)}
                        aria-expanded={showRules}
                        aria-controls="rules-section"
                    >
                        {showRules ? '▼' : '►'} Supreme Keeper League Custom Rules
                    </button>
                </div>
            </div>
            {showRules && (
                <div className="row justify-content-center mb-5" id="rules-section">
                    <div className="col-md-10 col-lg-8">
                        <div className="card shadow-sm border-0 text-start">
                            <div className="card-body" style={{ textAlign: 'left' }}>
                                <ul>
                                    <li>
                                        <strong>Contract Lengths:</strong> All drafted players must be signed to a contract of <b>1 to 4 years</b> in length after the draft.
                                    </li>
                                    <li>
                                        <strong>Contract Penalties:</strong> If a player is dropped or exits a contract early, a penalty of <b>10% of the contract value per remaining year</b> will be assessed. The penalty for each year is rounded up to the nearest dollar.
                                    </li>
                                    <li>
                                        <strong>Penalty Accrual:</strong> Penalties are not paid all at once. Instead, they accrue and are charged in each associated future year of the contract.
                                    </li>
                                    <li>
                                        <strong>Contract Escalation:</strong> Each year of a contract increases in cost by 10% over the previous year (rounded up).
                                    </li>
                                    <li>
                                        <strong>Franchise Tag:</strong> Each team may designate one player as a franchise player before the season. The franchise tag contract amount is set to the <b>greater of</b>:
                                        <ul>
                                            <li>The average of the top 5 contracts at the same position from the previous year</li>
                                            <li>10% greater than the player's previous year contract</li>
                                        </ul>
                                    </li>
                                    <li>
                                        <strong>Roster Configuration:</strong> 20 roster spots with starting positions: 1 QB, 2 RB, 3 WR, 1 RB/WR, 1 RB/TE, 1 TE, 1 RB/WR/TE, 1 QB/RB/WR/TE, 1 DEF.
                                    </li>
                                    <li>
                                        <strong>Waivers & Trades:</strong> Most roster moves (waivers, trades) are performed on Sleeper, but all contract and penalty management is handled on this platform.
                                    </li>
                                    <li>
                                        <strong>Transparency:</strong> All penalties, contracts, and league finances are tracked and viewable on the platform for full transparency.
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            )}
            {/* Collapsible Instructions Section (now below rules) */}
            <div className="row justify-content-center mb-2">
                <div className="col-md-10 col-lg-8">
                    <button
                        className="btn btn-outline-primary w-100 mb-2 text-start"
                        style={{ color: 'white', borderColor: 'white' }}
                        onClick={() => setShowInstructions((v) => !v)}
                        aria-expanded={showInstructions}
                        aria-controls="instructions-section"
                    >
                        {showInstructions ? '▼' : '►'} How to Create or Join a Supreme Keeper League
                    </button>
                </div>
            </div>
            {showInstructions && (
                <div className="row justify-content-center mb-4" id="instructions-section">
                    <div className="col-md-10 col-lg-8">
                        <div className="card shadow-sm border-0 text-start">
                            <div className="card-body" style={{ textAlign: 'left' }}>
                                <ol className="mb-0">
                                    <li className="mb-2">
                                        <strong>Create or Join a League on Sleeper</strong><br />
                                        If you are a <b>commissioner</b>: Go to the Sleeper fantasy football platform and create a new league.<br />
                                        <span className="text-danger">Important:</span> The league name must begin with <code>SKL</code> (for example, <code>SKL Supreme League 2024</code>). Only leagues with names starting with <code>SKL</code> will be recognized and imported into the Supreme Keeper League platform.<br />
                                        If you are <b>joining</b>: Ask your commissioner for the Sleeper invite link and join the league on Sleeper.
                                    </li>
                                    <li className="mb-2">
                                        <strong>Create a FLOW Wallet (if you don’t have one)</strong><br />
                                        You’ll need a FLOW-compatible wallet to use the Supreme Keeper League platform.<br />
                                        We recommend using <a href="https://nu.fi/" target="_blank" rel="noopener noreferrer">NuFi Wallet</a> or the official <a href="https://www.flow.com/" target="_blank" rel="noopener noreferrer">FLOW Wallet</a>.<br />
                                        <em>You may use either the browser extension or the phone version of your chosen wallet.</em><br />
                                        Follow the instructions on the wallet provider’s website to create and secure your wallet. Be sure to back up your recovery phrase in a safe place.
                                    </li>
                                    <li className="mb-2">
                                        <strong>Set Up Your Supreme Keeper League Account</strong><br />
                                        Visit the Supreme Keeper League website.<br />
                                        Connect your FLOW wallet (browser or phone version) to authenticate your account.
                                    </li>
                                    <li className="mb-2">
                                        <strong>Associate Your Sleeper Account</strong><br />
                                        After logging in with your FLOW wallet, you will be prompted to link your Sleeper account.<br />
                                        Enter your Sleeper username to complete the association.
                                    </li>
                                    <li className="mb-2">
                                        <strong>Import or Join Your League Data</strong><br />
                                        Once your Sleeper account is linked, the platform will automatically pull in all relevant data from your Sleeper league(s) (users, teams, rosters, standings, etc.) into the local system.<br />
                                        This is a one-time data pull; all future actions will use the local data for speed and reliability.
                                    </li>
                                    <li className="mb-2">
                                        <strong>Invite League Members or Join Your League</strong><br />
                                        If you are a <b>commissioner</b>: Share your league’s Sleeper invite link with other managers so they can join on Sleeper and then on this platform.<br />
                                        If you are a <b>manager</b>: Make sure you have joined the league on Sleeper and completed your account setup here.
                                    </li>
                                    <li className="mb-2">
                                        <strong>Manage Your League</strong><br />
                                        Use the Supreme Keeper League platform to view league details, manage contracts, track penalties, and handle league finances securely.<br />
                                        Most roster moves (waivers, trades) are still performed on Sleeper, but contract management and analytics are handled here.
                                    </li>
                                    <li className="mb-2">
                                        <strong>Set Contracts and Franchise Tags</strong><br />
                                        After your league draft, use the contract management tools to assign contracts to your players.<br />
                                        Designate a franchise player if desired, following the platform’s rules for franchise tags.
                                    </li>
                                    <li className="mb-2">
                                        <strong>Pay League Fees (if applicable)</strong><br />
                                        Use your FLOW wallet to pay league fees directly through the platform.<br />
                                        Track payment status and league treasury transparently.
                                    </li>
                                    <li className="mb-2">
                                        <strong>Enjoy Your Season!</strong><br />
                                        Use the analytics, penalty tracking, and contract management features to compete for the championship.
                                    </li>
                                </ol>
                            </div>
                        </div>
                    </div>
                </div>
            )}
            {/* REMOVE the Import Sleeper League and Logout buttons below */}
            {/* 
            {sessionToken ? (
                <div className="row justify-content-center">
                    <div className="col-md-8">
                        <p className="lead">Welcome!</p>
                        <div className="mt-3">
                            <Link to="/sleeper-import" className="btn btn-primary">Import Sleeper League</Link>
                        </div>
                    </div>
                </div>
            ) : null}
            {sessionToken && (
                <div className="mt-3">
                    <button onClick={onLogout} className="btn btn-outline-danger">Logout</button>
                </div>
            )}
            */}
        </div>
    );
}

export default Home; 