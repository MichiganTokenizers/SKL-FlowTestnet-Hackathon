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
            const response = await fetch(`${API_BASE_URL}/api/league/${leagueId}/teams`, {
                headers: { 'Authorization': sessionToken }
            });
            const data = await response.json();
            
            if (data.success) {
                // Filter out the current user's team
                const otherTeams = data.teams.filter(team => 
                    team.roster_id !== teamId
                );
                setAvailableTeams(otherTeams);
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
                setTradeData({ recipient_team_id: '', budget_items: [] });
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
                <Alert variant="info" className="mb-4">
                    <strong>How it works:</strong> Select a team to trade with, specify which years and amounts, 
                    then submit for commissioner approval.
                </Alert>
                
                {error && <Alert variant="danger">{error}</Alert>}
                
                <Form>
                    <Form.Group className="mb-4">
                        <Form.Label className="fw-bold">Trade With:</Form.Label>
                        <Form.Select
                            value={tradeData.recipient_team_id}
                            onChange={(e) => setTradeData(prev => ({...prev, recipient_team_id: e.target.value}))}
                            disabled={fetchingTeams}
                            className="form-select-lg"
                        >
                            <option value="">{fetchingTeams ? 'Loading teams...' : 'Select Team'}</option>
                            {availableTeams.map(team => (
                                <option key={team.roster_id} value={team.roster_id}>
                                    {team.team_name} (Manager: {team.manager_name})
                                </option>
                            ))}
                        </Form.Select>
                    </Form.Group>
                    
                                         <Form.Group className="mb-3">
                         <Form.Label className="fw-bold">Budget Items:</Form.Label>
                         
                         {/* Header Row */}
                         <div className="row mb-3 fw-bold text-muted">
                             <div className="col-3">
                                 <span style={{fontSize: '0.9rem'}}>Year</span>
                             </div>
                             <div className="col-7">
                                 <span style={{fontSize: '0.9rem'}}>Amount ($)</span>
                             </div>
                             <div className="col-2">
                                 <span style={{fontSize: '0.9rem'}}>Action</span>
                             </div>
                         </div>
                         
                         {/* Budget Item Rows */}
                         {tradeData.budget_items.map((item, index) => (
                             <div key={index} className="row mb-3 align-items-center">
                                 <div className="col-3">
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
                                 <div className="col-7">
                                     <Form.Control
                                         type="number"
                                         placeholder="0"
                                         min="1"
                                         value={item.amount}
                                         onChange={(e) => handleBudgetItemChange(index, 'amount', parseFloat(e.target.value) || '')}
                                         className="form-control-sm"
                                     />
                                 </div>
                                 <div className="col-2">
                                     <Button 
                                         variant="outline-danger" 
                                         size="sm"
                                         onClick={() => handleRemoveBudgetItem(index)}
                                         className="btn-sm px-2"
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
                
                {tradeData.recipient_team_id && (
                    <Alert variant="warning">
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
