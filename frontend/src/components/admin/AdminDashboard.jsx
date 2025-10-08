import { useState, useEffect } from 'react';
import { API_BASE_URL } from '../../config';
import './AdminDashboard.css';

const AdminDashboard = ({ user }) => {
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [leagues, setLeagues] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');

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
            <p className="coming-soon">Coming soon: Create and manage Flow Agents for automated tasks</p>
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
            <h2>Payout Scheduling</h2>
            <p className="coming-soon">Coming soon: Automated payout distribution tools</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
