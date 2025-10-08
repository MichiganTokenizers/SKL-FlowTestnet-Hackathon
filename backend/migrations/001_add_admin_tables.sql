-- SKL Admin Dashboard Tables
-- Migration: 001_add_admin_tables
-- Created: 2025-10-08

-- Admin users table (only 0xdf978465ee6dcf32 for now)
CREATE TABLE IF NOT EXISTS AdminUsers (
    wallet_address TEXT PRIMARY KEY,
    role TEXT DEFAULT 'super_admin',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (wallet_address) REFERENCES Users(wallet_address)
);

-- Fee collection schedules and automation
CREATE TABLE IF NOT EXISTS FeeSchedules (
    schedule_id TEXT PRIMARY KEY,
    sleeper_league_id TEXT NOT NULL,
    season_year INTEGER NOT NULL,
    due_date TEXT NOT NULL,
    collection_status TEXT DEFAULT 'pending',
    total_expected REAL,
    total_collected REAL DEFAULT 0.0,
    agent_id TEXT,
    agent_status TEXT DEFAULT 'not_deployed',
    last_check DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (sleeper_league_id) REFERENCES LeagueMetadata(sleeper_league_id) ON DELETE CASCADE
);

-- Agent execution logs (tracking all automation)
CREATE TABLE IF NOT EXISTS AgentExecutions (
    execution_id TEXT PRIMARY KEY,
    agent_type TEXT NOT NULL,
    sleeper_league_id TEXT,
    season_year INTEGER,
    status TEXT DEFAULT 'scheduled',
    trigger_time TEXT,
    execution_time TEXT,
    transaction_ids TEXT,
    result_data TEXT,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (sleeper_league_id) REFERENCES LeagueMetadata(sleeper_league_id) ON DELETE CASCADE
);

-- Yield vault positions (Increment Fi integration)
CREATE TABLE IF NOT EXISTS YieldVaults (
    vault_id TEXT PRIMARY KEY,
    sleeper_league_id TEXT NOT NULL,
    season_year INTEGER NOT NULL,
    vault_protocol TEXT DEFAULT 'increment_fi',
    vault_address TEXT NOT NULL,
    principal_amount REAL NOT NULL,
    current_value REAL,
    yield_earned REAL DEFAULT 0.0,
    deposit_tx_id TEXT,
    deposit_date TEXT,
    withdrawal_tx_id TEXT,
    withdrawal_date TEXT,
    status TEXT DEFAULT 'active',
    agent_id TEXT,
    last_updated DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sleeper_league_id) REFERENCES LeagueMetadata(sleeper_league_id) ON DELETE CASCADE
);

-- Payout schedules (automated on standings finalization)
CREATE TABLE IF NOT EXISTS PayoutSchedules (
    payout_id TEXT PRIMARY KEY,
    sleeper_league_id TEXT NOT NULL,
    season_year INTEGER NOT NULL,
    payout_date TEXT NOT NULL,
    payout_status TEXT DEFAULT 'pending',
    total_prize_pool REAL,
    vault_id TEXT,
    standings_finalized INTEGER DEFAULT 0,
    agent_id TEXT,
    agent_status TEXT DEFAULT 'not_deployed',
    execution_date TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (sleeper_league_id) REFERENCES LeagueMetadata(sleeper_league_id) ON DELETE CASCADE,
    FOREIGN KEY (vault_id) REFERENCES YieldVaults(vault_id)
);

-- Payout distributions (individual winner payments)
CREATE TABLE IF NOT EXISTS PayoutDistributions (
    distribution_id TEXT PRIMARY KEY,
    payout_id TEXT NOT NULL,
    wallet_address TEXT NOT NULL,
    payout_type TEXT NOT NULL,
    amount REAL NOT NULL,
    percentage REAL,
    transaction_id TEXT,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (payout_id) REFERENCES PayoutSchedules(payout_id) ON DELETE CASCADE,
    FOREIGN KEY (wallet_address) REFERENCES Users(wallet_address)
);

-- Seed admin user
INSERT OR IGNORE INTO AdminUsers (wallet_address, role)
VALUES ('0xdf978465ee6dcf32', 'super_admin');
