-- Drop existing tables
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS leagues;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS rosters;
DROP TABLE IF EXISTS contracts;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS traded_picks;
DROP TABLE IF EXISTS drafts;

-- Recreate tables
CREATE TABLE IF NOT EXISTS sessions (
    wallet_address TEXT PRIMARY KEY, 
    session_token TEXT
);

CREATE TABLE IF NOT EXISTS leagues (
    sleeper_league_id TEXT,
    sleeper_user_id TEXT,
    name TEXT,
    season TEXT,
    status TEXT,
    settings TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS users (
    sleeper_user_id TEXT UNIQUE,
    username TEXT,
    display_name TEXT,
    avatar TEXT,
    wallet_address TEXT UNIQUE,
    metadata TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS players (
    sleeper_player_id TEXT UNIQUE,
    name TEXT,
    position TEXT,
    team TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS rosters (
    sleeper_roster_id TEXT,
    league_id TEXT,
    owner_id TEXT,
    players TEXT,
    settings TEXT,
    metadata TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS contracts (
    player_id TEXT,
    team_id TEXT,
    sleeper_league_id TEXT,
    draft_amount REAL,
    contract_year INTEGER,
    duration INTEGER,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    UNIQUE (player_id, team_id, contract_year, sleeper_league_id),
    FOREIGN KEY (sleeper_league_id) REFERENCES LeagueMetadata(sleeper_league_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transactions (
    sleeper_transaction_id TEXT UNIQUE,
    league_id INTEGER,
    type TEXT,
    status TEXT,
    data TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS traded_picks (
    league_id INTEGER,
    draft_id TEXT,
    round INTEGER,
    roster_id TEXT,
    previous_owner_id TEXT,
    current_owner_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS drafts (
    sleeper_draft_id TEXT UNIQUE,
    league_id INTEGER,
    status TEXT,
    start_time DATETIME,
    data TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
); 