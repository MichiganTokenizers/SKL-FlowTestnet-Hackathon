import React, { useState, useEffect } from 'react';
import { Modal, Button, Form, Alert } from 'react-bootstrap';
import { API_BASE_URL } from '../../config';

function BudgetTradeModal({ show, onHide, teamId, leagueId, onTradeCreated }) {
    const [tradeData, setTradeData] = useState({
        recipient_team_id: '',
        budget_items: []
    });
    const [availableTeams, setAvailableTeams] = useState([]);
    const [loading, setLoading] = useState(false);
    const [fetchingTeams, setFetchingTeams] = useState(false);
    const [error, setError] = useState(null);
    
    useEffect(() => {
        if (show && leagueId) {
            fetchAvailableTeams();
            // Initialize with one empty budget item for better UX
            if (tradeData.budget_items.length === 0) {
                setTradeData(prev => ({
                    ...prev,
                    budget_items: [{ year: '', amount: '' }]
                }));
            }
        }
    }, [show, leagueId]);
    
    const fetchAvailableTeams = async () => {
        setFetchingTeams(true);
        setError(null);
        try {
            const sessionToken = localStorage.getItem('sessionToken');
            console.log('DEBUG: Fetching teams for league:', leagueId, 'Current team ID:', teamId);
            
            const response = await fetch(`${API_BASE_URL}/api/league/${leagueId}/teams`, {
                headers: { 'Authorization': sessionToken }
            });
            const data = await response.json();
            
            console.log('DEBUG: Teams response:', data);
            
            if (data.success) {
                // Filter out the current user's team
                const otherTeams = data.teams.filter(team => 
                    team.roster_id !== teamId
                );
                
                console.log('DEBUG: All teams:', data.teams);
                console.log('DEBUG: Other teams (filtered):', otherTeams);
                
                if (otherTeams.length === 0) {
                    setError('No other teams available for trading. You need at least one other team in the league to create trades.');
                } else {
                    setAvailableTeams(otherTeams);
                }
            } else {
                setError('Failed to fetch available teams');
            }
        } catch (error) {
            console.error('Error fetching teams:', error);
            setError('Error fetching available teams');
        } finally {
            setFetchingTeams(false);
        }
    };
    
    const handleAddBudgetItem = () => {
        setTradeData(prev => ({
            ...prev,
            budget_items: [...prev.budget_items, { year: '', amount: '' }]
        }));
    };
    
    const handleRemoveBudgetItem = (index) => {
        setTradeData(prev => ({
            ...prev,
            budget_items: prev.budget_items.filter((_, i) => i !== index)
        }));
    };
    
    const handleBudgetItemChange = (index, field, value) => {
        setTradeData(prev => ({
            ...prev,
            budget_items: prev.budget_items.map((item, i) => 
                i === index ? { ...item, [field]: value } : item
            )
        }));
    };
    
    const handleSubmit = async () => {
        setLoading(true);
        setError(null);
        
        try {
            const sessionToken = localStorage.getItem('sessionToken');
            const response = await fetch(`${API_BASE_URL}/api/trades/budget/create`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': sessionToken
                },
                body: JSON.stringify({
                    ...tradeData,
                    initiator_team_id: teamId,
                    league_id: leagueId
                })
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                alert('Trade created successfully! Waiting for commissioner approval.');
                onTradeCreated();
                onHide();
                // Reset form
                setTradeData({ recipient_team_id: '', budget_items: [{ year: '', amount: '' }] }); // Reset with initial empty item
            } else {
                setError(result.error || 'Failed to create trade');
            }
        } catch (error) {
            console.error('Error creating trade:', error);
            setError('Error creating trade. Please try again.');
        } finally {
            setLoading(false);
        }
    };
    
    const canSubmit = tradeData.recipient_team_id && 
                     tradeData.budget_items.length > 0 &&
                     tradeData.budget_items.every(item => item.year && item.amount > 0);
    
    const getCurrentYear = () => {
        return new Date().getFullYear();
    };
    
    const getFutureYears = () => {
        const currentYear = getCurrentYear();
        return [currentYear + 1, currentYear + 2, currentYear + 3, currentYear + 4];
    };
    
    return (
        <Modal show={show} onHide={onHide} size="xl" dialogClassName="modal-xl" style={{maxWidth: '90vw'}}>
            <Modal.Header closeButton>
                <Modal.Title className="fw-bold">Trade Future Budget Dollars</Modal.Title>
            </Modal.Header>
            <Modal.Body className="px-5">
                
                {error && <Alert variant="danger" className="mb-4">{error}</Alert>}
                
                {fetchingTeams ? (
                    <div className="text-center py-4">
                        <div className="spinner-border text-primary" role="status">
                            <span className="visually-hidden">Loading...</span>
                        </div>
                        <p className="mt-3 text-muted">Loading available teams...</p>
                    </div>
                ) : availableTeams.length === 0 ? (
                    <Alert variant="warning" className="mb-4">
                        <strong>No Trading Partners Available</strong>
                        <br />
                        You need at least one other team in the league to create budget trades. 
                        <br />
                        <small className="text-muted">
                            This usually happens when you're the only user in the league or when other teams haven't been imported yet.
                        </small>
                    </Alert>
                ) : (
                    <Form className="w-100">
                        <Form.Group className="mb-5">
                            <Form.Select
                                value={tradeData.recipient_team_id}
                                onChange={(e) => setTradeData(prev => ({...prev, recipient_team_id: e.target.value}))}
                                disabled={fetchingTeams}
                                className="form-control-lg w-100"
                            >
                                <option value="">Select Team</option>
                                {availableTeams.map(team => (
                                    <option key={team.roster_id} value={team.roster_id}>
                                        {team.team_name} (Manager: {team.manager_name})
                                    </option>
                                ))}
                            </Form.Select>
                        </Form.Group>
                        
                        <Form.Group className="mb-4">
                            {/* Header Row */}
                            <div className="row mb-3 fw-bold text-muted">
                                <div className="col-2">
                                    <span style={{fontSize: '0.9rem'}}>Year</span>
                                </div>
                                <div className="col-8">
                                    <span style={{fontSize: '0.9rem'}}>Amount ($)</span>
                                </div>
                                <div className="col-2 text-end">
                                    <span style={{fontSize: '0.9rem'}}>Action</span>
                                </div>
                            </div>
                            
                            {/* Budget Item Rows */}
                            {tradeData.budget_items.map((item, index) => (
                                <div key={index} className="row mb-3 align-items-center">
                                    <div className="col-2">
                                        <Form.Select
                                            value={item.year}
                                            onChange={(e) => handleBudgetItemChange(index, 'year', e.target.value)}
                                            className="form-select-sm"
                                        >
                                            <option value="">Select Year</option>
                                            {getFutureYears().map(year => (
                                                <option key={year} value={year}>{year}</option>
                                            ))}
                                        </Form.Select>
                                    </div>
                                    <div className="col-8">
                                        <Form.Control
                                            type="number"
                                            placeholder="0"
                                            min="1"
                                            value={item.amount}
                                            onChange={(e) => handleBudgetItemChange(index, 'amount', parseFloat(e.target.value) || '')}
                                            className="form-control-sm"
                                        />
                                    </div>
                                    <div className="col-2 d-flex justify-content-end">
                                        <Button 
                                            variant="outline-danger" 
                                            size="sm"
                                            onClick={() => handleRemoveBudgetItem(index)}
                                            className="btn-sm px-2 py-1"
                                        >
                                            ×
                                        </Button>
                                    </div>
                                </div>
                            ))}
                            
                            {/* Add Year Button */}
                            <div className="mt-4 mb-2">
                                <Button 
                                    variant="outline-secondary" 
                                    size="sm"
                                    onClick={handleAddBudgetItem}
                                    className="w-100 py-2"
                                >
                                    + Add Another Year
                                </Button>
                            </div>
                        </Form.Group>
                    </Form>
                )}
                
                {tradeData.recipient_team_id && (
                    <Alert variant="warning" className="mt-5">
                        <strong>Note:</strong> This trade will be sent to the commissioner for approval. 
                        You cannot cancel it once submitted.
                    </Alert>
                )}
            </Modal.Body>
            <Modal.Footer className="px-5 py-3">
                <Button variant="secondary" onClick={onHide} size="lg">Cancel</Button>
                <Button 
                    variant="primary" 
                    onClick={handleSubmit}
                    disabled={loading || !canSubmit || availableTeams.length === 0}
                    size="lg"
                >
                    {loading ? 'Creating...' : 'Submit Trade for Approval'}
                </Button>
            </Modal.Footer>
        </Modal>
    );
}

export default BudgetTradeModal;
