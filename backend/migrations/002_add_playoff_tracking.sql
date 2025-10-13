-- SKL Playoff Tracking Tables
-- Migration: 002_add_playoff_tracking
-- Created: 2025-10-13
-- Purpose: Track playoff brackets and final placements from Sleeper API

-- Table to store playoff bracket data from Sleeper
CREATE TABLE IF NOT EXISTS PlayoffBrackets (
    bracket_id TEXT PRIMARY KEY,
    sleeper_league_id TEXT NOT NULL,
    season_year INTEGER NOT NULL,
    bracket_type TEXT NOT NULL, -- 'winners_bracket' or 'losers_bracket'
    bracket_data TEXT NOT NULL, -- Full JSON from Sleeper API
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (sleeper_league_id) REFERENCES LeagueMetadata(sleeper_league_id) ON DELETE CASCADE
);

-- Table to store individual playoff matchups
CREATE TABLE IF NOT EXISTS PlayoffMatchups (
    matchup_id TEXT PRIMARY KEY,
    sleeper_league_id TEXT NOT NULL,
    season_year INTEGER NOT NULL,
    bracket_type TEXT NOT NULL, -- 'winners_bracket' or 'losers_bracket'
    round_number INTEGER NOT NULL, -- 1, 2, 3 (corresponds to 'r' in Sleeper API)
    match_number INTEGER NOT NULL, -- corresponds to 'm' in Sleeper API
    team1_roster_id TEXT, -- corresponds to 't1' in Sleeper API
    team2_roster_id TEXT, -- corresponds to 't2' in Sleeper API
    winner_roster_id TEXT, -- corresponds to 'w' in Sleeper API
    loser_roster_id TEXT, -- corresponds to 'l' in Sleeper API
    team1_from_match TEXT, -- corresponds to 't1_from' in Sleeper API
    team2_from_match TEXT, -- corresponds to 't2_from' in Sleeper API
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (sleeper_league_id) REFERENCES LeagueMetadata(sleeper_league_id) ON DELETE CASCADE,
    FOREIGN KEY (team1_roster_id, sleeper_league_id) REFERENCES rosters(sleeper_roster_id, sleeper_league_id),
    FOREIGN KEY (team2_roster_id, sleeper_league_id) REFERENCES rosters(sleeper_roster_id, sleeper_league_id),
    FOREIGN KEY (winner_roster_id, sleeper_league_id) REFERENCES rosters(sleeper_roster_id, sleeper_league_id)
);

-- Table to store final league placements
CREATE TABLE IF NOT EXISTS LeaguePlacements (
    placement_id TEXT PRIMARY KEY,
    sleeper_league_id TEXT NOT NULL,
    season_year INTEGER NOT NULL,
    roster_id TEXT NOT NULL,
    placement_type TEXT NOT NULL, -- '1st_place', '2nd_place', '3rd_place', 'regular_season_winner', '4th_place', etc.
    final_rank INTEGER, -- 1, 2, 3, 4, etc.
    determined_by TEXT, -- 'playoff_bracket', 'regular_season', 'consolation_match'
    notes TEXT, -- Additional context
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY (sleeper_league_id) REFERENCES LeagueMetadata(sleeper_league_id) ON DELETE CASCADE,
    FOREIGN KEY (roster_id, sleeper_league_id) REFERENCES rosters(sleeper_roster_id, sleeper_league_id),
    UNIQUE(sleeper_league_id, season_year, roster_id)
);

-- Add points_for column to rosters (for regular season tiebreakers)
ALTER TABLE rosters ADD COLUMN points_for REAL DEFAULT 0.0;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_playoff_matchups_league_season
    ON PlayoffMatchups(sleeper_league_id, season_year);

CREATE INDEX IF NOT EXISTS idx_playoff_matchups_round
    ON PlayoffMatchups(sleeper_league_id, season_year, round_number);

CREATE INDEX IF NOT EXISTS idx_league_placements_league_season
    ON LeaguePlacements(sleeper_league_id, season_year);

CREATE INDEX IF NOT EXISTS idx_league_placements_rank
    ON LeaguePlacements(sleeper_league_id, season_year, final_rank);
