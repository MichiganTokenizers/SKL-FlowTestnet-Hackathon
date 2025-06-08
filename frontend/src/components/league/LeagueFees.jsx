import React, { useState, useEffect, useCallback } from 'react';
import * as fcl from "@onflow/fcl";
// import api from '../../services/api'; // No longer using a separate API service file
import './LeagueFees.css';

// Enable FCL debug logging and configure discovery wallet
fcl.config({
    "fcl.limit": 9999,
    "debug.level": 5, // Set to 5 for maximum debug output
    "discovery.wallet": "https://fcl-discovery.onflow.org/api/v1/dapps/mainnet/authn", // Explicitly set Mainnet discovery
});

const API_BASE_URL = "http://localhost:5000"; // Define API_BASE_URL here

// SKL Payment wallet address - same for all leagues
const SKL_PAYMENT_WALLET_ADDRESS = "0xa30279e4e80d4216"; // Corrected to the actual SKL wallet address

const LeagueFees = ({ leagueId, currentUser, sessionToken }) => {
    // const { leagueId } = useParams(); // Remove useParams, leagueId comes from props
    // const navigate = useNavigate(); // Commented out as it's not used yet
    const [leagueFeeSettings, setLeagueFeeSettings] = useState(null);
    const [rosterPaymentDetails, setRosterPaymentDetails] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isCommissioner, setIsCommissioner] = useState(false);
    const [currentUserFeeDetails, setCurrentUserFeeDetails] = useState(null);
    const [queriedSeasonYear, setQueriedSeasonYear] = useState(null);
    const [showFeeForm, setShowFeeForm] = useState(false);
    const [isPaymentProcessing, setIsPaymentProcessing] = useState(false);
    const [showVaultSetupOption, setShowVaultSetupOption] = useState(false);

    // For commissioner form
    const [editFeeAmount, setEditFeeAmount] = useState('');
    const [editFeeCurrency, setEditFeeCurrency] = useState('FLOW');
    const [editNotes, setEditNotes] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const fetchLeagueFeeData = useCallback(async () => {
        if (!sessionToken) { // Don't fetch if no token
            setError('Session token not available. Cannot fetch fee data.');
            setIsLoading(false);
            return;
        }
        setIsLoading(true);
        setError(null);
        try {
            // Construct URL for GET request, assuming current season if not specified by backend logic
            const response = await fetch(`${API_BASE_URL}/league/${leagueId}/fees`, {
                headers: { 
                    'Authorization': sessionToken,
                    // 'Content-Type': 'application/json' // Not strictly needed for GET but good practice
                }
            });
            const data = await response.json();

            if (response.ok && data.success) {
                setLeagueFeeSettings(data.fee_settings);
                setRosterPaymentDetails(data.roster_payment_details || []);
                setQueriedSeasonYear(data.queried_season_year);
                
                const currentUserWallet = currentUser?.wallet_address;

                const commishEntry = (data.roster_payment_details || []).find(
                    roster => roster.wallet_address === currentUserWallet && roster.is_commissioner
                );
                
                const currentIsCommissioner = !!commishEntry;
                setIsCommissioner(currentIsCommissioner);

                if (data.fee_settings) {
                    setEditFeeAmount(data.fee_settings.fee_amount !== null ? String(data.fee_settings.fee_amount) : '');
                    setEditFeeCurrency(data.fee_settings.fee_currency || 'FLOW');
                    setEditNotes(data.fee_settings.notes || '');
                } else { 
                    setEditFeeAmount('');
                    setEditFeeCurrency('FLOW');
                    setEditNotes('');
                }
                setShowFeeForm(false);
            } else {
                setError(data.error || 'Failed to load league fee data.');
            }
        } catch (err) {
            // console.error("Error fetching league fee data:", err); // Keep this commented unless specific debug needed
            setError(err.message || 'An error occurred while fetching fee data.');
        } finally {
            setIsLoading(false);
        }
    }, [leagueId, currentUser, sessionToken]);

    useEffect(() => {
        if (leagueId && currentUser && sessionToken) { 
            fetchLeagueFeeData();
        }
    }, [leagueId, currentUser, sessionToken, fetchLeagueFeeData]);

    useEffect(() => {
        if (currentUser && rosterPaymentDetails.length > 0 && leagueFeeSettings) {
            const userWallet = currentUser.wallet_address;
            const userFeeRecord = rosterPaymentDetails.find(
                (roster) => roster.wallet_address === userWallet
            );

            if (userFeeRecord) {
                setCurrentUserFeeDetails({
                    status: userFeeRecord.payment_status, 
                    paid_amount: userFeeRecord.paid_amount, 
                    is_commissioner: userFeeRecord.is_commissioner 
                });
            } else {
                setCurrentUserFeeDetails(null); 
            }
        } else {
            setCurrentUserFeeDetails(null);
        }
    }, [currentUser, rosterPaymentDetails, leagueFeeSettings]);

    const handleFeeSettingsSubmit = async (e) => {
        e.preventDefault();
        if (!isCommissioner || !sessionToken) return; 

        setIsSubmitting(true);
        setError(null);
        try {
            const payload = {
                fee_amount: parseFloat(editFeeAmount),
                fee_currency: editFeeCurrency,
                notes: editNotes,
            };
            const response = await fetch(`${API_BASE_URL}/league/${leagueId}/fees`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': sessionToken, 
                },
                body: JSON.stringify(payload),
            });
            const data = await response.json();

            if (response.ok && data.success) {
                fetchLeagueFeeData(); 
            } else {
                setError(data.error || 'Failed to update league fees.');
            }
        } catch (err) {
            // console.error("Error updating league fees:", err); // Keep this commented unless specific debug needed
            setError(err.message || 'An error occurred while updating fees.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleSetupVaults = async () => {
        setError(null);

        console.log('handleSetupVaults: Initiating vault setup...');

        const fclUserSnapshot = await fcl.currentUser().snapshot();
        console.log('handleSetupVaults: FCL user snapshot:', fclUserSnapshot);

        if (!fclUserSnapshot.loggedIn) {
            console.log('handleSetupVaults: FCL user not logged in. Prompting for authentication...');
            setError('Please connect your Flow wallet using the main Login button to set up vaults.');
            return;
        }

        setIsPaymentProcessing(true);
        console.log('handleSetupVaults: isPaymentProcessing set to true.');

        try {
            console.log('handleSetupVaults: Preparing fcl.mutate call...');
            const transactionId = await fcl.mutate({
                cadence: `
                    import FlowToken from 0x1654653399040a61
                    import FungibleToken from 0xf233dcee88fe0abe
                    import EVMVMBridgedToken_2aabea2058b5ac2d339b163c6ab6f2b6d53aabed from 0x1e4aa0b87d10b141

                    transaction {
                        prepare(signer: auth(Storage, Capabilities) &Account) {
                            // Setup FlowToken Vault if not already set up
                            if signer.storage.borrow<&FlowToken.Vault>(from: /storage/flowTokenVault) == nil {
                                signer.storage.save(<- FlowToken.createEmptyVault(vaultType: Type<@FlowToken.Vault>()), to: /storage/flowTokenVault)
                            }
                            // Always publish or re-publish the FlowToken receiver capability
                            if signer.capabilities.get<&{FungibleToken.Receiver}>(/public/flowTokenReceiver).borrow() == nil {
                                signer.capabilities.publish(
                                    signer.capabilities.storage.issue<&FlowToken.Vault>(/storage/flowTokenVault),
                                    at: /public/flowTokenReceiver
                                )
                            }

                            // Setup USDF Vault if not already set up (replaces FUSD setup)
                            if signer.storage.borrow<&EVMVMBridgedToken_2aabea2058b5ac2d339b163c6ab6f2b6d53aabed.Vault>(from: /storage/EVMVMBridgedToken_2aabea2058b5ac2d339b163c6ab6f2b6d53aabedVault) == nil {
                                signer.storage.save(<- EVMVMBridgedToken_2aabea2058b5ac2d339b163c6ab6f2b6d53aabed.createEmptyVault(vaultType: Type<@EVMVMBridgedToken_2aabea2058b5ac2d339b163c6ab6f2b6d53aabed.Vault>()), to: /storage/EVMVMBridgedToken_2aabea2058b5ac2d339b163c6ab6f2b6d53aabedVault)
                            }
                            // Always publish or re-publish the USDF receiver capability
                            if signer.capabilities.get<&{FungibleToken.Receiver}>(/public/usdfReceiver).borrow() == nil {
                                signer.capabilities.publish(
                                    signer.capabilities.storage.issue<&EVMVMBridgedToken_2aabea2058b5ac2d339b163c6ab6f2b6d53aabed.Vault>(/storage/EVMVMBridgedToken_2aabea2058b5ac2d339b163c6ab6f2b6d53aabedVault),
                                    at: /public/usdfReceiver
                                )
                            }
                        }
                    }
                `,
                proposer: fcl.currentUser,
                payer: fcl.currentUser,
                authorizations: [fcl.currentUser],
                limit: 999
            });

            console.log('Vault setup transaction submitted:', transactionId);
            const transaction = await fcl.tx(transactionId).onceSealed();
            console.log('Vault setup transaction sealed:', transaction);

            if (transaction.status === 4) {
                alert('Flow and USDF vaults initialized successfully! Please try your payment again.');
                setShowVaultSetupOption(false); // Hide the button after success
                fetchLeagueFeeData(); // Refresh data in case something changed
            } else {
                throw new Error('Vault setup transaction failed.');
            }
        } catch (error) {
            console.error('Vault setup error:', error);
            setError(`Failed to set up vaults: ${error.message || 'Unknown error occurred'}. Please ensure your wallet is connected and has enough FLOW for transaction fees.`);
        } finally {
            // console.log('handleSetupVaults: finally block executed'); // Removed debug log
            setIsPaymentProcessing(false);
        }
    };

    const recordPaymentOnBackend = async (txId, amount, currency) => {
        try {
            const payload = {
                payer_wallet_address: currentUser.wallet_address,
                amount: amount,
                currency: currency,
                transaction_id: txId,
                league_id: leagueId, // Pass league_id to backend
            };
            const response = await fetch(`${API_BASE_URL}/league/${leagueId}/fees/record-payment`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': sessionToken,
                },
                body: JSON.stringify(payload),
            });
            const data = await response.json();

            if (response.ok && data.success) {
                console.log('Backend successfully recorded payment:', data);
                // Potentially refresh league data again to show immediate status update
                fetchLeagueFeeData(); 
            } else {
                console.error('Failed to record payment on backend:', data.error || 'Unknown error');
                setError(data.error || 'Failed to record payment on backend.');
            }
        } catch (err) {
            console.error('Error sending payment record to backend:', err);
            setError('Error sending payment record to backend: ' + (err.message || 'Unknown error'));
        }
    };

    const handlePaymentClick = async () => {
        console.log('handlePaymentClick triggered');
        // console.log('leagueFeeSettings:', leagueFeeSettings); // Removed debug log
        // console.log('currentUserFeeDetails:', currentUserFeeDetails); // Removed debug log

        // Ensure FCL user is logged in before proceeding with any transaction
        const fclUserSnapshot = await fcl.currentUser().snapshot(); // Await the snapshot
        console.log('FCL User Snapshot (resolved):', fclUserSnapshot); // New debug log

        if (!fclUserSnapshot.loggedIn) {
            console.log('handlePaymentClick: FCL user not logged in. Prompting for authentication...');
            setError('Please connect your Flow wallet using the main Login button to proceed with payment.');
            return; // Exit early if not authenticated
        }
        
        if (!leagueFeeSettings || !currentUserFeeDetails) {
            console.log('Early exit: Missing leagueFeeSettings or currentUserFeeDetails');
            // This condition should ideally not be hit if fetchLeagueFeeData is working correctly
            setError('Missing league fee data. Please refresh the page.');
            return;
        }
        
        setIsPaymentProcessing(true);
        console.log('isPaymentProcessing set to true (before mutate)'); // New debug log
        setError(null); // Clear previous errors
        setShowVaultSetupOption(false); // Hide setup option at the start of a new payment attempt
        // console.log('handlePaymentClick: fcl.currentUser snapshot:', fcl.currentUser.snapshot()); // Removed debug log
        try {
            let amountToPay;
            if (currentUserFeeDetails.status === 'partially_paid') {
                amountToPay = leagueFeeSettings.fee_amount - currentUserFeeDetails.paid_amount;
            } else {
                amountToPay = leagueFeeSettings.fee_amount;
            }

            console.log('Fee Currency to process:', leagueFeeSettings.fee_currency); // New debug log
            console.log('Amount to pay:', amountToPay); // New debug log

            if (leagueFeeSettings.fee_currency === 'FLOW') {
                console.log('Attempting FLOW payment fcl.mutate...'); // New debug log
                // For Flow token payments
                const transactionId = await fcl.mutate({
                    cadence: `
                        import FlowToken from 0x1654653399040a61
                        import FungibleToken from 0xf233dcee88fe0abe

                        transaction(amount: UFix64, recipient: Address) {
                            let sentVault: @{FungibleToken.Vault}

                            prepare(signer: auth(BorrowValue, Storage) &Account) {
                                let vaultRef = signer.storage.borrow<auth(FungibleToken.Withdraw) &FlowToken.Vault>(from: /storage/flowTokenVault)
                                    ?? panic("Could not borrow reference to the owner's Vault!")
                                
                                self.sentVault <- vaultRef.withdraw(amount: amount)
                            }

                            execute {
                                let recipientRef = getAccount(recipient)
                                    .capabilities.get<&{FungibleToken.Receiver}>(/public/flowTokenReceiver)
                                    .borrow()
                                    ?? panic("Could not borrow receiver reference to the recipient's Vault")

                                recipientRef.deposit(from: <-self.sentVault)
                            }
                        }
                    `,
                    args: (arg, t) => [
                        arg(amountToPay.toFixed(8), t.UFix64),
                        arg(SKL_PAYMENT_WALLET_ADDRESS, t.Address)
                    ],
                    proposer: fcl.currentUser,
                    payer: fcl.currentUser,
                    authorizations: [fcl.currentUser],
                    limit: 999
                });

                console.log('FLOW payment transaction submitted:', transactionId);
                
                const transaction = await fcl.tx(transactionId).onceSealed();
                console.log('FLOW payment transaction sealed:', transaction);

                if (transaction.status === 4) {
                    alert(`Payment of ${amountToPay} FLOW sent successfully! Transaction ID: ${transactionId}`);
                    await recordPaymentOnBackend(transactionId, amountToPay, 'FLOW'); // Notify backend
                } else {
                    throw new Error('Transaction failed');
                }
            } else if (leagueFeeSettings.fee_currency === 'USDF') {
                console.log('Attempting USDF payment fcl.mutate...'); // Updated debug log
                // For USDF payments - using correct mainnet contract
                const transactionId = await fcl.mutate({
                    cadence: `
                        import FungibleToken from 0xf233dcee88fe0abe
                        import EVMVMBridgedToken_2aabea2058b5ac2d339b163c6ab6f2b6d53aabed from 0x1e4aa0b87d10b141

                        transaction(amount: UFix64, recipient: Address) {
                            let sentVault: @{FungibleToken.Vault}

                            prepare(signer: auth(BorrowValue, Storage) &Account) {
                                let vaultRef = signer.storage.borrow<auth(FungibleToken.Withdraw) &EVMVMBridgedToken_2aabea2058b5ac2d339b163c6ab6f2b6d53aabed.Vault>(from: /storage/EVMVMBridgedToken_2aabea2058b5ac2d339b163c6ab6f2b6d53aabedVault)
                                    ?? panic("Could not borrow reference to the owner's USDF Vault!")
                                
                                self.sentVault <- vaultRef.withdraw(amount: amount)
                            }

                            execute {
                                let recipientRef = getAccount(recipient)
                                    .capabilities.get<&{FungibleToken.Receiver}>(/public/usdfReceiver)
                                    .borrow()
                                    ?? panic("Could not borrow receiver reference to the recipient's USDF Vault")

                                recipientRef.deposit(from: <-self.sentVault)
                            }
                        }
                    `,
                    args: (arg, t) => [
                        arg(amountToPay.toFixed(8), t.UFix64),
                        arg(SKL_PAYMENT_WALLET_ADDRESS, t.Address)
                    ],
                    proposer: fcl.currentUser,
                    payer: fcl.currentUser,
                    authorizations: [fcl.currentUser],
                    limit: 999
                });

                console.log('USDF payment transaction submitted:', transactionId);
                
                const transaction = await fcl.tx(transactionId).onceSealed();
                console.log('USDF payment transaction sealed:', transaction);

                if (transaction.status === 4) {
                    alert(`Payment of ${amountToPay} USDF sent successfully! Transaction ID: ${transactionId}`);
                    await recordPaymentOnBackend(transactionId, amountToPay, 'USDF'); // Notify backend
                } else {
                    throw new Error('Transaction failed');
                }
            } else {
                console.log('Payment skipped: Invalid fee currency or amount.'); // New debug log
            }
        } catch (error) {
            console.error('Payment error:', error);
            const errorMessage = error.message || 'Unknown error occurred';
            setError(`Payment failed: ${errorMessage}`);
            // Check for specific error indicating vault setup is needed
            if (errorMessage.includes('Could not borrow reference to the owner\'s USDF Vault!') ||
                errorMessage.includes('cannot access `withdraw`: function requires `Withdraw` authorization')) {
                setShowVaultSetupOption(true);
            }
        } finally {
            // console.log('handlePaymentClick: finally block executed'); // Removed debug log
            setIsPaymentProcessing(false);
        }
    };

    if (isLoading) {
        return <div className="league-fees-container"><p>Loading league fees...</p></div>;
    }

    if (error) {
        return (
            <div className="league-fees-container alert alert-danger">
                <p>Error: {error}</p>
                {showVaultSetupOption && (
                    <div className="mt-3">
                        <p>It looks like your wallet might need to set up its Flow and USDF token vaults. Please click the button below to initialize them.</p>
                        <button
                            className="btn btn-sm"
                            style={{ backgroundColor: '#9966CC', color: 'white', border: 'none' }}
                            type="button"
                            onClick={handleSetupVaults}
                            disabled={isPaymentProcessing}
                        >
                            {isPaymentProcessing ? 'Setting Up Vaults...' : 'Setup Flow/USDF Vaults'}
                        </button>
                    </div>
                )}
            </div>
        );
    }

    const shouldShowPayButton = currentUserFeeDetails &&
                                leagueFeeSettings &&
                                leagueFeeSettings.fee_amount > 0 &&
                                (currentUserFeeDetails.status === 'unpaid' || 
                                 (currentUserFeeDetails.status === 'partially_paid' && currentUserFeeDetails.paid_amount < leagueFeeSettings.fee_amount));

    const payButtonText = currentUserFeeDetails?.status === 'partially_paid' ? 'Pay Remaining Fees' : 'Pay League Fee';
    // console.log('Rendering button - shouldShowPayButton:', shouldShowPayButton, ', payButtonText:', payButtonText, ', isPaymentProcessing:', isPaymentProcessing); // Removed debug log

    return (
        <div className="league-fees-container card mb-4">
            <div className="card-header">
                <h4>League Fee Information</h4>
            </div>
            <div className="card-body">
                <div className="fee-amount-section mb-3">
                    <h5>Required Fees</h5>
                    {leagueFeeSettings && leagueFeeSettings.fee_amount !== null ? (
                        <div>
                            <p className="mb-1">
                                <strong>{queriedSeasonYear} fee:</strong> 
                                {leagueFeeSettings.fee_amount} {leagueFeeSettings.fee_currency}
                                {leagueFeeSettings.notes && <span className="text-muted small ms-2">({leagueFeeSettings.notes})</span>} 
                            </p>
                        </div>
                    ) : (
                        <p>{queriedSeasonYear ? `${queriedSeasonYear} fee not yet set.` : 'Fee not yet set.'}</p>
                    )}
                    {isCommissioner && (
                        <div className="mt-1">
                            <button 
                                className="btn btn-sm me-2" 
                                style={{ backgroundColor: '#9966CC', color: 'white', border: 'none' }}
                                onClick={() => setShowFeeForm(!showFeeForm)}
                                type="button"
                                data-bs-toggle="collapse"
                                data-bs-target="#feeFormCollapseArea"
                                aria-expanded={showFeeForm}
                                aria-controls="feeFormCollapseArea"
                            >
                                {showFeeForm ? 'Cancel' : (leagueFeeSettings && leagueFeeSettings.fee_amount !== null ? 'Update Fee' : 'Set Fee')}
                            </button>
                        </div>
                    )}
                    {shouldShowPayButton && !isCommissioner && (
                         <div className="mt-2">
                            <button 
                                className="btn btn-sm" 
                                style={{ backgroundColor: '#28a745', color: 'white', border: 'none' }} 
                                type="button" 
                                onClick={handlePaymentClick}
                                disabled={isPaymentProcessing}
                            >
                                {isPaymentProcessing ? 'Processing...' : payButtonText}
                            </button>
                        </div>
                    )}
                    {shouldShowPayButton && isCommissioner && (
                         <div className="mt-2">
                             <p className="small text-muted fst-italic">
                                 As commissioner, your fee status is: {currentUserFeeDetails.status}. 
                                 You can pay your fee if applicable, or it might be considered waived.
                             </p>
                             <button
                                 className="btn btn-sm"
                                 style={{ backgroundColor: '#28a745', color: 'white', border: 'none' }}
                                 type="button"
                                 onClick={handlePaymentClick}
                                 disabled={isPaymentProcessing}
                             >
                                 {isPaymentProcessing ? 'Processing...' : `${payButtonText} (My Fee)`}
                             </button>
                         </div>
                    )}
                </div>

                {isCommissioner && (
                    <div 
                        className={`commissioner-form mt-3 mb-3 p-3 border rounded collapse ${showFeeForm ? 'show' : ''}`}
                        id="feeFormCollapseArea"
                    >
                        <h5>
                            {(leagueFeeSettings && leagueFeeSettings.fee_amount !== null ? 'Update' : 'Set')} League Fees {queriedSeasonYear ? `for ${queriedSeasonYear}` : ''}
                        </h5>
                        <form onSubmit={handleFeeSettingsSubmit}>
                            <div className="row mb-2">
                                <label htmlFor="feeAmount" className="col-sm-3 col-form-label">Amount</label>
                                <div className="col-sm-9">
                                    <input 
                                        type="number" 
                                        className="form-control" 
                                        id="feeAmount"
                                        value={editFeeAmount}
                                        onChange={(e) => setEditFeeAmount(e.target.value)}
                                        placeholder="e.g., 20"
                                        step="0.01"
                                        required 
                                    />
                                </div>
                            </div>
                            <div className="row mb-2">
                                <label htmlFor="feeCurrency" className="col-sm-3 col-form-label">Currency</label>
                                <div className="col-sm-9">
                                    <select 
                                        className="form-select" 
                                        id="feeCurrency"
                                        value={editFeeCurrency}
                                        onChange={(e) => setEditFeeCurrency(e.target.value)}
                                        required
                                    >
                                        <option value="FLOW">FLOW</option>
                                        <option value="USDF">USDF</option>
                                    </select>
                                </div>
                            </div>
                            <div className="row mb-3">
                                <label htmlFor="feeNotes" className="col-sm-3 col-form-label">Notes (Optional)</label>
                                <div className="col-sm-9">
                                    <textarea 
                                        className="form-control" 
                                        id="feeNotes" 
                                        rows="2"
                                        value={editNotes}
                                        onChange={(e) => setEditNotes(e.target.value)}
                                        placeholder="e.g., Due by Week 1"
                                    ></textarea>
                                </div>
                            </div>
                            <div className="row">
                                <div className="col-sm-9 offset-sm-3">
                                    <button 
                                        type="submit" 
                                        className="btn btn-sm" 
                                        disabled={isSubmitting}
                                        style={{ backgroundColor: '#9966CC', color: 'white', border: 'none' }}
                                    >
                                        {isSubmitting ? 'Saving...' : (leagueFeeSettings && leagueFeeSettings.fee_amount !== null ? 'Update Fees' : 'Set Fees')}
                                    </button>
                                </div>
                            </div>
                        </form>
                    </div>
                )}

                <h5>Payment Status</h5>
                {rosterPaymentDetails.length > 0 ? (
                    <div className="table-responsive">
                        <table className="table table-sm table-striped table-hover">
                            <thead>
                                <tr>
                                    <th>Team</th>
                                    <th>Manager</th>
                                    <th>Status</th>
                                    <th>Amount Paid</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rosterPaymentDetails.map(roster => (
                                    <tr key={roster.roster_id || roster.wallet_address || Math.random()}>
                                        <td>{roster.team_name}</td>
                                        <td>
                                            {roster.manager_display_name}
                                        </td>
                                        <td>
                                            <span className={`badge bg-${roster.payment_status === 'paid' ? 'success' : (roster.payment_status === 'partially_paid' ? 'warning' : 'danger')}`}>
                                                {roster.payment_status ? roster.payment_status.replace('_', ' ').toUpperCase() : 'N/A'}
                                            </span>
                                        </td>
                                        <td>
                                            {roster.paid_amount} {leagueFeeSettings?.fee_currency || 'FLOW'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <p>No roster payment details available for this league.</p>
                )}
            </div>
        </div>
    );
};

export default LeagueFees; 