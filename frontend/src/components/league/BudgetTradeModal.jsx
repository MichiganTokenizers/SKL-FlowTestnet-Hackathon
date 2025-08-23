import React, { useState, useEffect } from 'react';
import { Modal, Button, Form, Alert } from 'react-bootstrap';
import { API_BASE_URL } from '../../config';

function BudgetTradeModal({ show, onHide, teamId, leagueId, onTradeCreated }) {
    const [tradeData, setTradeData] = useState({
        recipient_team_id: '',
        budget_items: [{ year: '', amount: '' }]
    });
    const [availableTeams, setAvailableTeams] = useState([]);
    const [loading, setLoading] = useState(false);
    const [fetchingTeams, setFetchingTeams] = useState(false);
    const [error, setError] = useState(null);
    
    useEffect(() => {
        if (show && leagueId) {
            fetchAvailableTeams();
        }
    }, [show, leagueId]);
    
    const fetchAvailableTeams = async () => {
        setFetchingTeams(true);
        setError(null);
        try {
            const sessionToken = localStorage.getItem('sessionToken');
            const response = await fetch(`${API_BASE_URL}/api/league/${leagueId}/teams`, {
                headers: { 'Authorization': sessionToken }
            });
            const data = await response.json();
            
            if (data.success) {
                const otherTeams = data.teams.filter(team => team.roster_id !== teamId);
                if (otherTeams.length === 0) {
                    setError('No other teams available for trading.');
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
        if (tradeData.budget_items.length > 1) {
            setTradeData(prev => ({
                ...prev,
                budget_items: prev.budget_items.filter((_, i) => i !== index)
            }));
        }
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
                setTradeData({ recipient_team_id: '', budget_items: [{ year: '', amount: '' }] });
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
    
    const getFutureYears = () => {
        const currentYear = new Date().getFullYear();
        return [currentYear + 1, currentYear + 2, currentYear + 3, currentYear + 4];
    };
    
    return (
        <Modal show={show} onHide={onHide} size="lg">
            <Modal.Header closeButton>
                <Modal.Title>Trade Future Budget Dollars</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                {error && <Alert variant="danger" className="mb-3">{error}</Alert>}
                
                {fetchingTeams ? (
                    <div className="text-center py-3">
                        <div className="spinner-border text-primary" role="status">
                            <span className="visually-hidden">Loading...</span>
                        </div>
                        <p className="mt-2">Loading teams...</p>
                    </div>
                ) : availableTeams.length === 0 ? (
                    <Alert variant="warning">
                        No other teams available for trading.
                    </Alert>
                ) : (
                    <div>
                        {/* Team Selection */}
                        <div className="mb-4">
                            <Form.Select
                                value={tradeData.recipient_team_id}
                                onChange={(e) => setTradeData(prev => ({...prev, recipient_team_id: e.target.value}))}
                                className="form-select-lg"
                            >
                                <option value="">Select Team to Trade With</option>
                                {availableTeams.map(team => (
                                    <option key={team.roster_id} value={team.roster_id}>
                                        {team.team_name} (Manager: {team.manager_name})
                                    </option>
                                ))}
                            </Form.Select>
                        </div>
                        
                        {/* Budget Items */}
                        <div className="mb-4">
                            {tradeData.budget_items.map((item, index) => (
                                <div key={index} className="row mb-3 align-items-center">
                                    <div className="col-4">
                                        <Form.Select
                                            value={item.year}
                                            onChange={(e) => handleBudgetItemChange(index, 'year', e.target.value)}
                                            className="form-select"
                                        >
                                            <option value="">Select Year</option>
                                            {getFutureYears().map(year => (
                                                <option key={year} value={year}>{year}</option>
                                            ))}
                                        </Form.Select>
                                    </div>
                                    <div className="col-6">
                                        <Form.Control
                                            type="number"
                                            placeholder="Amount ($)"
                                            min="1"
                                            value={item.amount}
                                            onChange={(e) => handleBudgetItemChange(index, 'amount', parseFloat(e.target.value) || '')}
                                            className="form-control"
                                        />
                                    </div>
                                    <div className="col-2 d-flex justify-content-center">
                                        <Button 
                                            variant="outline-danger" 
                                            size="sm"
                                            onClick={() => handleRemoveBudgetItem(index)}
                                            disabled={tradeData.budget_items.length === 1}
                                            className="px-2"
                                        >
                                            ×
                                        </Button>
                                    </div>
                                </div>
                            ))}
                            
                            <Button 
                                variant="outline-secondary" 
                                size="sm"
                                onClick={handleAddBudgetItem}
                                className="w-100"
                            >
                                + Add Another Year
                            </Button>
                        </div>
                    </div>
                )}
            </Modal.Body>
            <Modal.Footer>
                <Button variant="secondary" onClick={onHide}>Cancel</Button>
                <Button 
                    variant="primary" 
                    onClick={handleSubmit}
                    disabled={loading || !canSubmit || availableTeams.length === 0}
                >
                    {loading ? 'Creating...' : 'Submit Trade'}
                </Button>
            </Modal.Footer>
        </Modal>
    );
}

export default BudgetTradeModal;
