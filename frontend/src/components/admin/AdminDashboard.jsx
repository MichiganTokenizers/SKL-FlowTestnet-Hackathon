import { useState, useEffect } from 'react';
import { API_BASE_URL } from '../../config';
import './AdminDashboard.css';

const AdminDashboard = ({ user }) => {
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [leagues, setLeagues] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');

  // Payout testing state
  const [selectedLeague, setSelectedLeague] = useState('');
  const [payoutPreview, setPayoutPreview] = useState(null);
  const [payoutLoading, setPayoutLoading] = useState(false);
  const [payoutError, setPayoutError] = useState(null);
  const [payoutSuccess, setPayoutSuccess] = useState(null);

  // Staking testing state
  const [stakingLeague, setStakingLeague] = useState('');
  const [stakingLoading, setStakingLoading] = useState(false);
  const [stakingError, setStakingError] = useState(null);
  const [stakingSuccess, setStakingSuccess] = useState(null);

  useEffect(() => {
    verifyAdmin();
  }, [user]);

  useEffect(() => {
    if (isAdmin) {
      fetchDashboardData();
    }
  }, [isAdmin, activeTab]);

  const verifyAdmin = async () => {
    try {
      const sessionToken = localStorage.getItem('sessionToken');
      const response = await fetch(`${API_BASE_URL}/admin/verify`, {
        headers: {
          'Authorization': sessionToken || ''
        }
      });
      const data = await response.json();
      console.log('Admin dashboard verification:', data);
      setIsAdmin(data.is_admin);
      setLoading(false);
    } catch (error) {
      console.error('Admin verification error:', error);
      setLoading(false);
    }
  };

  const fetchDashboardData = async () => {
    try {
      const sessionToken = localStorage.getItem('sessionToken');

      // Fetch stats
      const statsRes = await fetch(`${API_BASE_URL}/admin/dashboard/stats`, {
        headers: { 'Authorization': sessionToken || '' }
      });
      const statsData = await statsRes.json();
      if (statsData.success) {
        setStats(statsData.stats);
      }

      // Fetch leagues
      const leaguesRes = await fetch(`${API_BASE_URL}/admin/leagues`, {
        headers: { 'Authorization': sessionToken || '' }
      });
      const leaguesData = await leaguesRes.json();
      if (leaguesData.success) {
        setLeagues(leaguesData.leagues);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const handlePreviewPayouts = async () => {
    if (!selectedLeague) {
      setPayoutError('Please select a league');
      return;
    }

    setPayoutLoading(true);
    setPayoutError(null);
    setPayoutSuccess(null);

    try {
      const sessionToken = localStorage.getItem('sessionToken');
      const response = await fetch(`${API_BASE_URL}/admin/league/${selectedLeague}/payouts/preview`, {
        headers: {
          'Authorization': `Bearer ${sessionToken}`
        }
      });

      const data = await response.json();

      if (data.success) {
        setPayoutPreview(data);
      } else {
        setPayoutError(data.error || 'Failed to load payout preview');
      }
    } catch (error) {
      console.error('Error previewing payouts:', error);
      setPayoutError('Network error loading preview');
    } finally {
      setPayoutLoading(false);
    }
  };

  const handleExecutePayouts = async () => {
    if (!selectedLeague) {
      setPayoutError('Please select a league');
      return;
    }

    if (!window.confirm('⚠️ WARNING: This will execute REAL blockchain transactions and send FLOW tokens to winner wallets. Are you sure you want to continue?')) {
      return;
    }

    setPayoutLoading(true);
    setPayoutError(null);
    setPayoutSuccess(null);

    try {
      const sessionToken = localStorage.getItem('sessionToken');
      const response = await fetch(`${API_BASE_URL}/admin/league/${selectedLeague}/payouts/execute`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${sessionToken}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (data.success) {
        setPayoutSuccess({
          message: 'Prize distribution executed successfully!',
          transactionId: data.transaction_id,
          payoutId: data.payout_id,
          totalDistributed: data.total_distributed,
          distributions: data.distributions
        });
        setPayoutPreview(null);
      } else {
        setPayoutError(data.error || 'Failed to execute payouts');
      }
    } catch (error) {
      console.error('Error executing payouts:', error);
      setPayoutError('Network error executing payouts');
    } finally {
      setPayoutLoading(false);
    }
  };

  const handleExecuteStaking = async () => {
    if (!stakingLeague) {
      setStakingError('Please select a league');
      return;
    }

    if (!window.confirm('⚠️ WARNING: This will execute a REAL blockchain transaction to stake league fees to a Flow validator node. Are you sure you want to continue?')) {
      return;
    }

    setStakingLoading(true);
    setStakingError(null);
    setStakingSuccess(null);

    try {
      const sessionToken = localStorage.getItem('sessionToken');
      const response = await fetch(`${API_BASE_URL}/admin/league/${stakingLeague}/stake-fees`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${sessionToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          season_year: 2025
        })
      });

      const data = await response.json();

      if (data.success) {
        setStakingSuccess({
          message: 'Staking transaction executed successfully!',
          transactionId: data.transaction_id,
          executionId: data.execution_id,
          amount: data.amount,
          nodeId: data.node_id
        });
      } else {
        setStakingError(data.error || 'Failed to execute staking');
      }
    } catch (error) {
      console.error('Error executing staking:', error);
      setStakingError('Network error executing staking transaction');
    } finally {
      setStakingLoading(false);
    }
  };


  if (loading) {
    return <div className="admin-loading">Verifying admin access...</div>;
  }

  if (!isAdmin) {
    return (
      <div className="admin-unauthorized">
        <h2>Unauthorized</h2>
        <p>You do not have admin access to this dashboard.</p>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      <div className="admin-header">
        <h1>🏈 SKL Admin Dashboard</h1>
        <p className="admin-wallet">Admin: {user?.addr}</p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Leagues</h3>
            <div className="stat-value">{stats.total_leagues}</div>
          </div>
          <div className="stat-card">
            <h3>Fees Collected</h3>
            <div className="stat-value">{stats.total_fees_collected.toFixed(2)} FLOW</div>
            <div className="stat-subtitle">of {stats.total_fees_due.toFixed(2)} due</div>
          </div>
          <div className="stat-card">
            <h3>Active Agents</h3>
            <div className="stat-value">{stats.active_agents}</div>
          </div>
          <div className="stat-card">
            <h3>Total Yield Earned</h3>
            <div className="stat-value">{stats.total_yield_earned.toFixed(2)} FLOW</div>
            <div className="stat-subtitle">{stats.active_vaults} active vaults</div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="admin-tabs">
        <button
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={activeTab === 'fees' ? 'active' : ''}
          onClick={() => setActiveTab('fees')}
        >
          Fee Collection
        </button>
        <button
          className={activeTab === 'automation' ? 'active' : ''}
          onClick={() => setActiveTab('automation')}
        >
          Automation
        </button>
        <button
          className={activeTab === 'yield' ? 'active' : ''}
          onClick={() => setActiveTab('yield')}
        >
          Yield Management
        </button>
        <button
          className={activeTab === 'payouts' ? 'active' : ''}
          onClick={() => setActiveTab('payouts')}
        >
          Payouts
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'overview' && (
          <div className="overview-tab">
            <h2>All SKL Leagues</h2>
            <div className="leagues-table">
              <table>
                <thead>
                  <tr>
                    <th>League Name</th>
                    <th>Season</th>
                    <th>Status</th>
                    <th>Fee Amount</th>
                    <th>Collection Status</th>
                    <th>Teams Paid</th>
                    <th>Automated</th>
                  </tr>
                </thead>
                <tbody>
                  {leagues.length === 0 ? (
                    <tr>
                      <td colSpan="7" style={{textAlign: 'center'}}>No leagues found</td>
                    </tr>
                  ) : (
                    leagues.map(league => (
                      <tr key={league.sleeper_league_id}>
                        <td>{league.name}</td>
                        <td>{league.season}</td>
                        <td>
                          <span className={`status-badge ${league.status}`}>
                            {league.status}
                          </span>
                        </td>
                        <td>
                          {league.fee_amount ? `${league.fee_amount} ${league.fee_currency}` : 'Not set'}
                        </td>
                        <td>
                          <span className={`status-badge ${league.collection_status || 'pending'}`}>
                            {league.collection_status || 'pending'}
                          </span>
                        </td>
                        <td>
                          {league.teams_paid || 0} / {league.total_teams || 0}
                        </td>
                        <td>
                          {league.automated ? '✅ Yes' : '❌ No'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'fees' && (
          <div className="fees-tab">
            <h2>Fee Collection Management</h2>
            <p className="coming-soon">Coming soon: Fee collection monitoring and management tools</p>
          </div>
        )}

        {activeTab === 'automation' && (
          <div className="automation-tab">
            <h2>Automation & Agents</h2>

            <div className="staking-section">
              <h3>🎯 Test Native Flow Staking (Flow Actions)</h3>
              <p className="section-description">
                Test the automated staking of league fees to Flow validator nodes using Flow Actions connectors.
                This demonstrates the Source → Sink pattern for DeFi automation.
              </p>

              <div className="staking-controls">
                <div className="form-group">
                  <label htmlFor="staking-league-select">Select League:</label>
                  <select
                    id="staking-league-select"
                    value={stakingLeague}
                    onChange={(e) => {
                      setStakingLeague(e.target.value);
                      setStakingError(null);
                      setStakingSuccess(null);
                    }}
                    className="league-select"
                  >
                    <option value="">-- Select a league --</option>
                    {leagues.map(league => (
                      <option key={league.sleeper_league_id} value={league.sleeper_league_id}>
                        {league.name} ({league.sleeper_league_id}) - {league.teams_paid || 0}/{league.total_teams || 0} paid
                      </option>
                    ))}
                  </select>
                </div>

                <div className="button-group">
                  <button
                    onClick={handleExecuteStaking}
                    disabled={!stakingLeague || stakingLoading}
                    className="btn-execute"
                  >
                    {stakingLoading ? 'Staking...' : '🚀 Execute Staking Transaction'}
                  </button>
                </div>
              </div>

              {stakingError && (
                <div className="payout-error">
                  <strong>❌ Error:</strong> {stakingError}
                </div>
              )}

              {stakingSuccess && (
                <div className="payout-success">
                  <h3>✅ {stakingSuccess.message}</h3>
                  <div className="success-details">
                    <p><strong>Transaction ID:</strong> {stakingSuccess.transactionId}</p>
                    <p><strong>Execution ID:</strong> {stakingSuccess.executionId}</p>
                    <p><strong>Amount Staked:</strong> {stakingSuccess.amount} FLOW</p>
                    <p><strong>IncrementFi Pool ID:</strong> {stakingSuccess.poolId}</p>
                    <a
                      href={`https://testnet.flowscan.io/transaction/${stakingSuccess.transactionId}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="view-transaction"
                    >
                      View on Flow Testnet Explorer →
                    </a>
                  </div>

                  <div className="staking-info">
                    <h4>📊 What just happened:</h4>
                    <ul>
                      <li>✅ SKLFeeCollectionSource aggregated {stakingSuccess.amount} FLOW from league fees</li>
                      <li>✅ IncrementFiStakingSink received the tokens via Flow Actions</li>
                      <li>✅ Tokens staked to IncrementFi pool #{stakingSuccess.poolId}</li>
                      <li>✅ League treasury will now earn staking rewards!</li>
                    </ul>
                  </div>
                </div>
              )}
            </div>

            <div className="automation-info">
              <h4>📝 About Flow Actions Staking</h4>
              <p>
                This feature demonstrates the <strong>Flow Actions pattern</strong> from the Forte upgrade:
              </p>
              <ul>
                <li><strong>Source:</strong> SKLFeeCollectionSource - Aggregates collected league fees</li>
                <li><strong>Sink:</strong> IncrementFiStakingSink - Stakes tokens to IncrementFi</li>
                <li><strong>Composability:</strong> Single transaction combines both actions atomically</li>
                <li><strong>Automation:</strong> Can be triggered automatically when all fees are paid</li>
              </ul>
            </div>
          </div>
        )}

        {activeTab === 'yield' && (
          <div className="yield-tab">
            <h2>Yield Vault Management</h2>
            <p className="coming-soon">Coming soon: Increment Fi vault monitoring and management</p>
          </div>
        )}

        {activeTab === 'payouts' && (
          <div className="payouts-tab">
            <h2>Prize Distribution Testing</h2>

            <div className="payout-controls">
              <div className="form-group">
                <label htmlFor="league-select">Select League:</label>
                <select
                  id="league-select"
                  value={selectedLeague}
                  onChange={(e) => {
                    setSelectedLeague(e.target.value);
                    setPayoutPreview(null);
                    setPayoutError(null);
                    setPayoutSuccess(null);
                  }}
                  className="league-select"
                >
                  <option value="">-- Select a league --</option>
                  {leagues.map(league => (
                    <option key={league.sleeper_league_id} value={league.sleeper_league_id}>
                      {league.name} ({league.sleeper_league_id})
                    </option>
                  ))}
                </select>
              </div>

              <div className="button-group">
                <button
                  onClick={handlePreviewPayouts}
                  disabled={!selectedLeague || payoutLoading}
                  className="btn-preview"
                >
                  {payoutLoading ? 'Loading...' : 'Preview Payouts'}
                </button>

                <button
                  onClick={handleExecutePayouts}
                  disabled={!selectedLeague || payoutLoading || !payoutPreview}
                  className="btn-execute"
                >
                  {payoutLoading ? 'Executing...' : 'Execute Prize Distribution'}
                </button>
              </div>
            </div>

            {payoutError && (
              <div className="payout-error">
                <strong>❌ Error:</strong> {payoutError}
              </div>
            )}

            {payoutSuccess && (
              <div className="payout-success">
                <h3>✅ {payoutSuccess.message}</h3>
                <div className="success-details">
                  <p><strong>Transaction ID:</strong> {payoutSuccess.transactionId}</p>
                  <p><strong>Payout ID:</strong> {payoutSuccess.payoutId}</p>
                  <p><strong>Total Distributed:</strong> {payoutSuccess.totalDistributed} FLOW</p>
                  <a
                    href={`https://testnet.flowscan.org/transaction/${payoutSuccess.transactionId}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="view-transaction"
                  >
                    View on Flow Testnet Explorer →
                  </a>
                </div>

                <h4>Distributions:</h4>
                <table className="distributions-table">
                  <thead>
                    <tr>
                      <th>Winner</th>
                      <th>Wallet Address</th>
                      <th>Placement</th>
                      <th>Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {payoutSuccess.distributions.map((dist, index) => (
                      <tr key={index}>
                        <td>{dist.username}</td>
                        <td><code>{dist.wallet_address}</code></td>
                        <td>{dist.placement_type.replace('_', ' ')}</td>
                        <td><strong>{dist.amount} FLOW</strong></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {payoutPreview && !payoutSuccess && (
              <div className="payout-preview">
                <h3>Prize Distribution Preview</h3>
                <p className="preview-info">
                  <strong>Total Prize Pool:</strong> {payoutPreview.total_prize_pool} FLOW
                </p>
                <p className="preview-info">
                  <strong>Number of Winners:</strong> {payoutPreview.distributions.length}
                </p>

                <table className="distributions-table">
                  <thead>
                    <tr>
                      <th>Winner</th>
                      <th>Wallet Address</th>
                      <th>Placement</th>
                      <th>Percentage</th>
                      <th>Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {payoutPreview.distributions.map((dist, index) => (
                      <tr key={index}>
                        <td>{dist.username}</td>
                        <td><code>{dist.wallet_address}</code></td>
                        <td>{dist.placement_type.replace('_', ' ')}</td>
                        <td>{dist.percentage}%</td>
                        <td><strong>{dist.amount} FLOW</strong></td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <div className="preview-warning">
                  ⚠️ Click "Execute Prize Distribution" to send these payments on Flow Testnet
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
