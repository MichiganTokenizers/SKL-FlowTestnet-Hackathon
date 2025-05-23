import React, { useState, useEffect, useCallback } from 'react';
// import api from '../../services/api'; // No longer using a separate API service file
import './LeagueFees.css';

const API_BASE_URL = "http://localhost:5000"; // Define API_BASE_URL here

const LeagueFees = ({ leagueId, currentUser, sessionToken }) => {
    // const { leagueId } = useParams(); // Remove useParams, leagueId comes from props
    // const navigate = useNavigate(); // Commented out as it's not used yet
    const [leagueFeeSettings, setLeagueFeeSettings] = useState(null);
    const [rosterPaymentDetails, setRosterPaymentDetails] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isCommissioner, setIsCommissioner] = useState(false);
    const [queriedSeasonYear, setQueriedSeasonYear] = useState(null);
    const [showFeeForm, setShowFeeForm] = useState(false);

    // For commissioner form
    const [editFeeAmount, setEditFeeAmount] = useState('');
    const [editFeeCurrency, setEditFeeCurrency] = useState('USD');
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
                    setEditFeeCurrency(data.fee_settings.fee_currency || 'USD');
                    setEditNotes(data.fee_settings.notes || '');
                    // setShowFeeForm(false); // Ensures form is collapsed by default, even if fees are set
                    // If fees are not set (fee_amount is null) and user is commish, they still need to click to expand.
                } else { // If data.fee_settings is null (no record in LeagueFees table for the season)
                    setEditFeeAmount('');
                    setEditFeeCurrency('USD');
                    setEditNotes('');
                    // setShowFeeForm(false); // Ensures form is collapsed by default for commish to set initial fees
                }
                // Explicitly ensure showFeeForm is false after initial load to default to collapsed.
                setShowFeeForm(false);
            } else {
                setError(data.error || 'Failed to load league fee data.');
            }
        } catch (err) {
            console.error("Error fetching league fee data:", err);
            setError(err.message || 'An error occurred while fetching fee data.');
        } finally {
            setIsLoading(false);
        }
    }, [leagueId, currentUser, sessionToken]);

    useEffect(() => {
        if (leagueId && currentUser && sessionToken) { // Ensure sessionToken is present
            fetchLeagueFeeData();
        }
    }, [leagueId, currentUser, sessionToken, fetchLeagueFeeData]);

    const handleFeeSettingsSubmit = async (e) => {
        e.preventDefault();
        if (!isCommissioner || !sessionToken) return; // Check for token

        setIsSubmitting(true);
        setError(null);
        try {
            const payload = {
                fee_amount: parseFloat(editFeeAmount),
                fee_currency: editFeeCurrency,
                notes: editNotes,
                // season_year: could be added here if frontend allows selecting season
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
            console.error("Error updating league fees:", err);
            setError(err.message || 'An error occurred while updating fees.');
        } finally {
            setIsSubmitting(false);
        }
    };

    if (isLoading) {
        return <div className="league-fees-container"><p>Loading league fees...</p></div>;
    }

    if (error) {
        return <div className="league-fees-container alert alert-danger"><p>Error: {error}</p></div>;
    }

    return (
        <div className="league-fees-container card mb-4">
            <div className="card-header">
                <h4>League Fee Information</h4>
            </div>
            <div className="card-body">
                {/* Updated Fee Amount Display Section (handles both cases) */}
                <div className="fee-amount-section mb-3">
                    <h5>Required Fees</h5>
                    {leagueFeeSettings && leagueFeeSettings.fee_amount !== null ? (
                        <div>
                            <p className="mb-1">
                                <strong>{queriedSeasonYear} fee:</strong> 
                                {leagueFeeSettings.fee_currency === 'USD' && ' $'}{leagueFeeSettings.fee_amount}
                                {leagueFeeSettings.fee_currency === 'TON' && ` ${leagueFeeSettings.fee_currency}`}
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
                            <button 
                                className="btn btn-sm" 
                                style={{ backgroundColor: '#9966CC', color: 'white', border: 'none' }}
                                type="button" 
                                onClick={() => alert('Pay League Fee functionality to be implemented.')} // Placeholder action
                            >
                                Pay League Fee
                            </button>
                        </div>
                    )}
                </div>

                {/* Commissioner's Form - conditionally rendered and collapsible */} 
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
                                        <option value="USD">USD</option>
                                        <option value="TON">TON</option>
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
                                                {roster.payment_status.replace('_', ' ').toUpperCase()}
                                            </span>
                                        </td>
                                        <td>
                                            {leagueFeeSettings?.fee_currency === 'USD' && '$'}{roster.paid_amount}
                                            {leagueFeeSettings?.fee_currency === 'TON' && ` ${leagueFeeSettings.fee_currency}`}
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