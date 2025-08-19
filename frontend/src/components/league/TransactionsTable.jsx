import { useState, useEffect } from 'react';
import { API_BASE_URL } from '../../config';

function TransactionsTable({ leagueId, sessionToken }) {
    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [currentWeek, setCurrentWeek] = useState(null);
    const [selectedWeek, setSelectedWeek] = useState('all');
    const [availableWeeks, setAvailableWeeks] = useState([]);

    useEffect(() => {
        if (leagueId && sessionToken) {
            fetchCurrentWeek();
            fetchTransactions();
        }
    }, [leagueId, sessionToken]);

    useEffect(() => {
        if (selectedWeek !== 'all') {
            fetchTransactionsByWeek(selectedWeek);
        } else {
            fetchTransactions();
        }
    }, [selectedWeek, leagueId, sessionToken]);

    const fetchCurrentWeek = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/nfl/current-week`);
            const data = await response.json();
            
            if (data.success && !data.is_offseason) {
                setCurrentWeek(data.week);
                // Generate available weeks (1-18 for regular season, 19+ for playoffs)
                const weeks = [];
                for (let i = 1; i <= Math.max(data.week || 18, 18); i++) {
                    weeks.push(i);
                }
                setAvailableWeeks(weeks);
            }
        } catch {
            console.error('Error fetching current week');
        }
    };

    const fetchTransactions = async () => {
        if (!leagueId || !sessionToken) return;
        
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch(`${API_BASE_URL}/league/${leagueId}/transactions/recent`, {
                headers: { 'Authorization': sessionToken }
            });
            
            const data = await response.json();
            
            if (data.success) {
                setTransactions(data.transactions || []);
            } else {
                setError(data.error || 'Failed to fetch transactions');
                setTransactions([]);
            }
        } catch (err) {
            setError('Error fetching transactions: ' + err.message);
            setTransactions([]);
        } finally {
            setLoading(false);
        }
    };

    const fetchTransactionsByWeek = async (week) => {
        if (!leagueId || !sessionToken || week === 'all') return;
        
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch(`${API_BASE_URL}/league/${leagueId}/transactions/week/${week}`, {
                headers: { 'Authorization': sessionToken }
            });
            
            const data = await response.json();
            
            if (data.success) {
                setTransactions(data.transactions || []);
            } else {
                setError(data.error || 'Failed to fetch transactions');
                setTransactions([]);
            }
        } catch (err) {
            setError('Error fetching transactions: ' + err.message);
            setTransactions([]);
        } finally {
            setLoading(false);
        }
    };

    const formatTransactionType = (type) => {
        const typeMap = {
            'trade': 'Trade',
            'waiver': 'Waiver',
            'free_agent': 'Free Agent',
            'draft': 'Draft',
            'commissioner': 'Commissioner'
        };
        return typeMap[type] || type;
    };

    const formatTransactionDetails = (transaction) => {
        const { type, details } = transaction;
        
        if (type === 'trade') {
            // Handle trade transactions
            if (details.adds && details.drops) {
                const adds = Object.keys(details.adds).length;
                const drops = Object.keys(details.drops).length;
                return `Trade: ${adds} players added, ${drops} players dropped`;
            }
            return 'Trade transaction';
        } else if (type === 'waiver') {
            // Handle waiver transactions
            if (details.adds && details.drops) {
                const adds = Object.keys(details.adds).length;
                const drops = Object.keys(details.drops).length;
                if (adds > 0 && drops > 0) {
                    return `Waiver: ${adds} players added, ${drops} players dropped`;
                } else if (adds > 0) {
                    return `Waiver: ${adds} players added`;
                } else if (drops > 0) {
                    return `Waiver: ${drops} players dropped`;
                }
            }
            return 'Waiver transaction';
        } else if (type === 'free_agent') {
            // Handle free agent transactions
            if (details.adds && details.drops) {
                const adds = Object.keys(details.adds).length;
                const drops = Object.keys(details.drops).length;
                if (adds > 0 && drops > 0) {
                    return `Free Agent: ${adds} players added, ${drops} players dropped`;
                } else if (adds > 0) {
                    return `Free Agent: ${adds} players added`;
                } else if (drops > 0) {
                    return `Free Agent: ${drops} players dropped`;
                }
            }
            return 'Free Agent transaction';
        }
        
        return 'Transaction';
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'Unknown';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return 'Invalid date';
        }
    };

    if (loading) {
        return (
            <div className="text-center py-3">
                <div className="spinner-border spinner-border-sm text-primary" role="status">
                    <span className="visually-hidden">Loading transactions...</span>
                </div>
                <span className="ms-2">Loading transactions...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="alert alert-warning" role="alert">
                <strong>Warning:</strong> {error}
                <button 
                    className="btn btn-sm btn-outline-warning ms-2"
                    onClick={() => selectedWeek === 'all' ? fetchTransactions() : fetchTransactionsByWeek(selectedWeek)}
                >
                    Retry
                </button>
            </div>
        );
    }

    return (
        <div>
            {/* Week Filter */}
            {availableWeeks.length > 0 && (
                <div className="mb-3">
                    <label htmlFor="weekFilter" className="form-label">Filter by Week:</label>
                    <select 
                        id="weekFilter" 
                        className="form-select form-select-sm" 
                        style={{ maxWidth: '200px' }}
                        value={selectedWeek}
                        onChange={(e) => setSelectedWeek(e.target.value)}
                    >
                        <option value="all">All Weeks</option>
                        {availableWeeks.map(week => (
                            <option key={week} value={week}>
                                Week {week} {week === currentWeek ? '(Current)' : ''}
                            </option>
                        ))}
                    </select>
                </div>
            )}

            {/* Transactions Table */}
            {transactions.length === 0 ? (
                <div className="text-center py-3">
                    <p className="text-muted mb-0">
                        {selectedWeek === 'all' 
                            ? 'No transactions found for this league.' 
                            : `No transactions found for Week ${selectedWeek}.`
                        }
                    </p>
                </div>
            ) : (
                <div className="table-responsive">
                    <table className="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Type</th>
                                <th>Description</th>
                                <th>Status</th>
                                {selectedWeek === 'all' && <th>Week</th>}
                            </tr>
                        </thead>
                        <tbody>
                            {transactions.map((transaction) => (
                                <tr key={transaction.transaction_id}>
                                    <td>{formatDate(transaction.created_at)}</td>
                                    <td>
                                        <span className={`badge bg-${getStatusColor(transaction.type)}`}>
                                            {formatTransactionType(transaction.type)}
                                        </span>
                                    </td>
                                    <td>{formatTransactionDetails(transaction)}</td>
                                    <td>
                                        <span className={`badge bg-${getStatusBadgeColor(transaction.status)}`}>
                                            {transaction.status}
                                        </span>
                                    </td>
                                    {selectedWeek === 'all' && (
                                        <td>
                                            {transaction.week ? `Week ${transaction.week}` : 'Unknown'}
                                        </td>
                                    )}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}

// Helper function to get status colors for transaction types
function getStatusColor(type) {
    const colorMap = {
        'trade': 'primary',
        'waiver': 'warning',
        'free_agent': 'success',
        'draft': 'info',
        'commissioner': 'secondary'
    };
    return colorMap[type] || 'secondary';
}

// Helper function to get status badge colors
function getStatusBadgeColor(status) {
    const colorMap = {
        'complete': 'success',
        'processed': 'info',
        'pending': 'warning',
        'failed': 'danger',
        'cancelled': 'secondary'
    };
    return colorMap[status] || 'secondary';
}

export default TransactionsTable;
