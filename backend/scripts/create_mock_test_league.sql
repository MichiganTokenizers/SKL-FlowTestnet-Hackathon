-- Mock Test League for IncrementFi Vault Testing
-- Created: 2025-10-13
-- Purpose: 10-team league with mixed fake/real wallets for end-to-end testing

-- League ID: TEST_VAULT_001
-- Season: 9999 (easy to identify and clean up)
-- 10 teams total:
--   - Teams 1-5: Fake wallets (pre-paid league fees)
--   - Teams 6-10: Real Flow testnet wallets (will pay via UI)

-- =============================================================================
-- STEP 1: Create League Metadata
-- =============================================================================

INSERT INTO LeagueMetadata (
    sleeper_league_id,
    name,
    season,
    status,
    settings,
    scoring_settings,
    roster_positions,
    created_at,
    updated_at
) VALUES (
    'TEST_VAULT_001',
    'SKL Testnet Vault League',
    '9999',
    'complete',
    '{"num_teams": 10, "playoff_teams": 4, "playoff_week_start": 15, "playoff_rounds": 3, "best_ball": 0, "type": 1, "max_keepers": 3, "waiver_type": 2}',
    '{"pass_yd": 0.04, "pass_td": 4.0, "rush_yd": 0.1, "rush_td": 6.0, "rec": 0.5, "rec_yd": 0.1, "rec_td": 6.0}',
    '["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "SUPER_FLEX", "BN", "BN", "BN", "BN"]',
    datetime('now'),
    datetime('now')
);

-- =============================================================================
-- STEP 2: Configure League Fees (100 FLOW per team)
-- =============================================================================

INSERT INTO LeagueFees (
    sleeper_league_id,
    season_year,
    fee_amount,
    fee_currency,
    fee_due_date,
    collection_deadline,
    automated,
    created_at,
    updated_at
) VALUES (
    'TEST_VAULT_001',
    9999,
    100.0,
    'FLOW',
    '2025-10-20',
    '2025-10-25',
    1,
    datetime('now'),
    datetime('now')
);

-- =============================================================================
-- STEP 3: Create 10 Rosters (5 fake + 5 real)
-- =============================================================================

-- Regular season standings (determines who makes playoffs and regular season winner)
-- FAKE WALLETS (Teams 1-5): All non-winners, no prizes
-- Team 1: 5-9 (fake - misses playoffs)
-- Team 2: 4-10 (fake - misses playoffs)
-- Team 3: 3-11 (fake - misses playoffs)
-- Team 4: 2-12 (fake - misses playoffs)
-- Team 5: 1-13 (fake - worst record)

-- REAL WALLETS (Teams 6-10): All 4 prize winners!
-- Team 6: 12-2 (REAL WALLET 1 - Best regular season, regular season winner prize)
-- Team 7: 11-3 (REAL WALLET 2 - Championship winner, 1st place)
-- Team 8: 10-4 (REAL WALLET 3 - Championship loser, 2nd place)
-- Team 9: 9-5 (REAL WALLET 4 - 3rd place game winner)
-- Team 10: 8-6 (REAL WALLET 5 - Makes playoffs but loses, no prize)

INSERT INTO rosters (sleeper_roster_id, sleeper_league_id, owner_id, team_name, wins, losses, ties, points_for, players, created_at, updated_at)
VALUES
    -- Fake wallets (pre-paid) - ALL LOSERS, NO PRIZES
    -- Mock Sleeper User IDs: 9001XXXXXXXX format (fake IDs starting with 9001)
    ('1', 'TEST_VAULT_001', '900111111111111111', 'Dynasty Duds', 5, 9, 0, 1437.3, '[]', datetime('now'), datetime('now')),
    ('2', 'TEST_VAULT_001', '900122222222222222', 'Mediocre Managers', 4, 10, 0, 1491.9, '[]', datetime('now'), datetime('now')),
    ('3', 'TEST_VAULT_001', '900133333333333333', 'Playoff Pretenders', 3, 11, 0, 1546.5, '[]', datetime('now'), datetime('now')),
    ('4', 'TEST_VAULT_001', '900144444444444444', 'Touchdown Turnovers', 2, 12, 0, 1601.1, '[]', datetime('now'), datetime('now')),
    ('5', 'TEST_VAULT_001', '900155555555555555', 'Fantasy Failures', 1, 13, 0, 1655.7, '[]', datetime('now'), datetime('now')),

    -- Real Flow testnet wallets (will pay via UI) - ALL 4 PRIZE WINNERS!
    -- Mock Sleeper User IDs: 9002XXXXXXXX format (real wallet IDs starting with 9002)
    ('6', 'TEST_VAULT_001', '900266666666666666', 'Regular Season Kings', 12, 2, 0, 1950.8, '[]', datetime('now'), datetime('now')),  -- Reg season winner
    ('7', 'TEST_VAULT_001', '900277777777777777', 'Championship Champions', 11, 3, 0, 1875.2, '[]', datetime('now'), datetime('now')),  -- 1st place
    ('8', 'TEST_VAULT_001', '900288888888888888', 'Runner-Up Rivals', 10, 4, 0, 1820.5, '[]', datetime('now'), datetime('now')),  -- 2nd place
    ('9', 'TEST_VAULT_001', '900299999999999999', 'Third Place Threats', 9, 5, 0, 1765.9, '[]', datetime('now'), datetime('now')),  -- 3rd place
    ('10', 'TEST_VAULT_001', '900210101010101010', 'Playoff Participants', 8, 6, 0, 1710.3, '[]', datetime('now'), datetime('now'));  -- Makes playoffs, no prize

-- =============================================================================
-- STEP 4: Create Users (Link Wallet Addresses to Sleeper User IDs)
-- =============================================================================

-- Fake wallet users
INSERT INTO Users (wallet_address, sleeper_user_id, username, display_name, created_at, updated_at)
VALUES
    ('0xFAKE1111111111111111111111111111', '900111111111111111', 'fake_user_001', 'Fake User 1', datetime('now'), datetime('now')),
    ('0xFAKE2222222222222222222222222222', '900122222222222222', 'fake_user_002', 'Fake User 2', datetime('now'), datetime('now')),
    ('0xFAKE3333333333333333333333333333', '900133333333333333', 'fake_user_003', 'Fake User 3', datetime('now'), datetime('now')),
    ('0xFAKE4444444444444444444444444444', '900144444444444444', 'fake_user_004', 'Fake User 4', datetime('now'), datetime('now')),
    ('0xFAKE5555555555555555555555555555', '900155555555555555', 'fake_user_005', 'Fake User 5 (Commissioner)', datetime('now'), datetime('now'));

-- Real testnet wallet users
INSERT INTO Users (wallet_address, sleeper_user_id, username, display_name, created_at, updated_at)
VALUES
    ('0xb647c8ffe7d05b51', '900266666666666666', 'SKLtest1', 'SKLtest1 (Wallet 1)', datetime('now'), datetime('now')),
    ('0x447414116f2e51ef', '900277777777777777', 'SKLtest2', 'SKLtest2 (Wallet 2)', datetime('now'), datetime('now')),
    ('0xa9f313f3c175ebb5', '900288888888888888', 'SKLtest3', 'SKLtest3 (Wallet 3)', datetime('now'), datetime('now')),
    ('0x5bc0cf1d498be10b', '900299999999999999', 'SKLtest4', 'SKLtest4 (Wallet 4)', datetime('now'), datetime('now')),
    ('0xbfa776c05871e1d4', '900210101010101010', 'SKLtest5', 'SKLtest5 (Wallet 5)', datetime('now'), datetime('now'));

-- =============================================================================
-- STEP 5: Link Wallets to League (UserLeagueLinks)
-- =============================================================================

-- Fake wallets - already paid (for testing vault deposit immediately)
INSERT INTO UserLeagueLinks (wallet_address, sleeper_league_id, is_commissioner, fee_paid_amount, fee_payment_status, updated_at)
VALUES
    ('0xFAKE1111111111111111111111111111', 'TEST_VAULT_001', 0, 100.0, 'paid', datetime('now')),
    ('0xFAKE2222222222222222222222222222', 'TEST_VAULT_001', 0, 100.0, 'paid', datetime('now')),
    ('0xFAKE3333333333333333333333333333', 'TEST_VAULT_001', 0, 100.0, 'paid', datetime('now')),
    ('0xFAKE4444444444444444444444444444', 'TEST_VAULT_001', 0, 100.0, 'paid', datetime('now')),
    ('0xFAKE5555555555555555555555555555', 'TEST_VAULT_001', 1, 100.0, 'paid', datetime('now')); -- Commissioner

-- Real Flow testnet wallets - PAID (simulating all 10 teams paid)
-- Your actual testnet wallet addresses - showing as paid for 1000 FLOW total prize pool
INSERT INTO UserLeagueLinks (wallet_address, sleeper_league_id, is_commissioner, fee_paid_amount, fee_payment_status, updated_at)
VALUES
    ('0xb647c8ffe7d05b51', 'TEST_VAULT_001', 0, 100.0, 'paid', datetime('now')),  -- Wallet 1 - Regular Season Winner (100 FLOW prize)
    ('0x447414116f2e51ef', 'TEST_VAULT_001', 0, 100.0, 'paid', datetime('now')),  -- Wallet 2 - 1st Place Champion (500 FLOW prize) 🏆
    ('0xa9f313f3c175ebb5', 'TEST_VAULT_001', 0, 100.0, 'paid', datetime('now')),  -- Wallet 3 - 2nd Place (300 FLOW prize) 🥈
    ('0x5bc0cf1d498be10b', 'TEST_VAULT_001', 0, 100.0, 'paid', datetime('now')),  -- Wallet 4 - 3rd Place (100 FLOW prize) 🥉
    ('0xbfa776c05871e1d4', 'TEST_VAULT_001', 0, 100.0, 'paid', datetime('now'));  -- Wallet 5 - No prize

-- =============================================================================
-- STEP 5: Record Fake Wallet Payments in LeaguePayments
-- =============================================================================

INSERT INTO LeaguePayments (
    sleeper_league_id,
    season_year,
    wallet_address,
    amount,
    currency,
    transaction_id,
    created_at,
    updated_at
) VALUES
    -- Fake wallet payments
    ('TEST_VAULT_001', 9999, '0xFAKE1111111111111111111111111111', 100.0, 'FLOW', '0xfaketx001', datetime('now'), datetime('now')),
    ('TEST_VAULT_001', 9999, '0xFAKE2222222222222222222222222222', 100.0, 'FLOW', '0xfaketx002', datetime('now'), datetime('now')),
    ('TEST_VAULT_001', 9999, '0xFAKE3333333333333333333333333333', 100.0, 'FLOW', '0xfaketx003', datetime('now'), datetime('now')),
    ('TEST_VAULT_001', 9999, '0xFAKE4444444444444444444444444444', 100.0, 'FLOW', '0xfaketx004', datetime('now'), datetime('now')),
    ('TEST_VAULT_001', 9999, '0xFAKE5555555555555555555555555555', 100.0, 'FLOW', '0xfaketx005', datetime('now'), datetime('now')),

    -- Real wallet payments (simulated)
    ('TEST_VAULT_001', 9999, '0xb647c8ffe7d05b51', 100.0, 'FLOW', '0xrealtx001', datetime('now'), datetime('now')),
    ('TEST_VAULT_001', 9999, '0x447414116f2e51ef', 100.0, 'FLOW', '0xrealtx002', datetime('now'), datetime('now')),
    ('TEST_VAULT_001', 9999, '0xa9f313f3c175ebb5', 100.0, 'FLOW', '0xrealtx003', datetime('now'), datetime('now')),
    ('TEST_VAULT_001', 9999, '0x5bc0cf1d498be10b', 100.0, 'FLOW', '0xrealtx004', datetime('now'), datetime('now')),
    ('TEST_VAULT_001', 9999, '0xbfa776c05871e1d4', 100.0, 'FLOW', '0xrealtx005', datetime('now'), datetime('now'));

-- =============================================================================
-- STEP 6: Mock Playoff Bracket Results
-- =============================================================================

-- Playoff Teams (top 4 make playoffs based on regular season):
-- ALL REAL WALLETS MAKE PLAYOFFS!
-- Seed 1: Team 6 (Regular Season Kings - 12-2) - REAL WALLET 1
-- Seed 2: Team 7 (Championship Champions - 11-3) - REAL WALLET 2
-- Seed 3: Team 8 (Runner-Up Rivals - 10-4) - REAL WALLET 3
-- Seed 4: Team 9 (Third Place Threats - 9-5) - REAL WALLET 4

-- Playoff Results (ALL real wallets):
-- Round 1:
--   - Team 7 (REAL 2) defeats Team 10 (REAL 5 - no prize)
--   - Team 8 (REAL 3) defeats Team 9 (REAL 4)
-- Championship:
--   - Team 7 (REAL 2 - Championship Champions) defeats Team 8 (REAL 3) - WINS CHAMPIONSHIP!
-- 3rd Place Game:
--   - Team 9 (REAL 4 - Third Place Threats) defeats Team 10 (REAL 5)

-- Store playoff matchups (simulating Sleeper API winners_bracket)
INSERT INTO PlayoffMatchups (
    matchup_id,
    sleeper_league_id,
    season_year,
    bracket_type,
    round_number,
    match_number,
    team1_roster_id,
    team2_roster_id,
    winner_roster_id,
    loser_roster_id,
    created_at,
    updated_at
) VALUES
    -- Round 1, Match 1: Team 7 (REAL 2) vs Team 10 (REAL 5)
    ('TEST_VAULT_001_9999_W_R1_M1', 'TEST_VAULT_001', 9999, 'winners_bracket', 1, 1, '7', '10', '7', '10', datetime('now'), datetime('now')),

    -- Round 1, Match 2: Team 8 (REAL 3) vs Team 9 (REAL 4)
    ('TEST_VAULT_001_9999_W_R1_M2', 'TEST_VAULT_001', 9999, 'winners_bracket', 1, 2, '8', '9', '8', '9', datetime('now'), datetime('now')),

    -- Championship: Team 7 (REAL 2) vs Team 8 (REAL 3)
    ('TEST_VAULT_001_9999_W_R2_M1', 'TEST_VAULT_001', 9999, 'winners_bracket', 2, 1, '7', '8', '7', '8', datetime('now'), datetime('now')),

    -- 3rd Place Game: Team 9 (REAL 4) vs Team 10 (REAL 5)
    ('TEST_VAULT_001_9999_L_R2_M1', 'TEST_VAULT_001', 9999, 'losers_bracket', 2, 1, '9', '10', '9', '10', datetime('now'), datetime('now'));

-- =============================================================================
-- STEP 7: Final League Placements (for prize distribution)
-- =============================================================================

-- PRIZE DISTRIBUTION (50% / 30% / 10% / 10%) of 1000 FLOW:
-- ALL PRIZES GO TO REAL WALLETS!
-- 1st Place: Team 7 "Championship Champions" (REAL WALLET 2) - 500 FLOW (50%)
-- 2nd Place: Team 8 "Runner-Up Rivals" (REAL WALLET 3) - 300 FLOW (30%)
-- 3rd Place: Team 9 "Third Place Threats" (REAL WALLET 4) - 100 FLOW (10%)
-- Regular Season Winner: Team 6 "Regular Season Kings" (REAL WALLET 1) - 100 FLOW (10%)
-- Team 10 (REAL WALLET 5) makes playoffs but gets no prize
-- TOTAL PRIZE POOL: 1000 FLOW (10 teams × 100 FLOW each)

INSERT INTO LeaguePlacements (
    placement_id,
    sleeper_league_id,
    season_year,
    roster_id,
    placement_type,
    final_rank,
    determined_by,
    notes,
    created_at,
    updated_at
) VALUES
    -- 1st Place: REAL WALLET 2 WINS CHAMPIONSHIP!
    ('TEST_VAULT_001_9999_7', 'TEST_VAULT_001', 9999, '7', '1st_place', 1, 'playoff_bracket', 'Championship Champions - Championship Winner', datetime('now'), datetime('now')),

    -- 2nd Place: REAL WALLET 3
    ('TEST_VAULT_001_9999_8', 'TEST_VAULT_001', 9999, '8', '2nd_place', 2, 'playoff_bracket', 'Runner-Up Rivals - Championship Runner-up', datetime('now'), datetime('now')),

    -- 3rd Place: REAL WALLET 4
    ('TEST_VAULT_001_9999_9', 'TEST_VAULT_001', 9999, '9', '3rd_place', 3, 'consolation_match', 'Third Place Threats - 3rd Place Game Winner', datetime('now'), datetime('now')),

    -- Regular Season Winner: REAL WALLET 1
    ('TEST_VAULT_001_9999_6_rs', 'TEST_VAULT_001', 9999, '6', 'regular_season_winner', 0, 'regular_season', 'Regular Season Kings - Best Regular Season Record (12-2)', datetime('now'), datetime('now'));

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Check league created
SELECT 'League Created:' as status, sleeper_league_id, name, status FROM LeagueMetadata WHERE sleeper_league_id = 'TEST_VAULT_001';

-- Check all 10 rosters
SELECT 'Rosters Created:' as status, COUNT(*) as total_rosters FROM rosters WHERE sleeper_league_id = 'TEST_VAULT_001';

-- Check wallet links (5 paid fake + 5 unpaid real)
SELECT 'Wallet Links:' as status,
    SUM(CASE WHEN fee_payment_status = 'paid' THEN 1 ELSE 0 END) as paid_count,
    SUM(CASE WHEN fee_payment_status = 'unpaid' THEN 1 ELSE 0 END) as unpaid_count
FROM UserLeagueLinks WHERE sleeper_league_id = 'TEST_VAULT_001';

-- Check total fees collected so far (should be 500 FLOW from fake wallets)
SELECT 'Fees Collected:' as status,
    COUNT(*) as payment_count,
    SUM(amount) as total_collected
FROM LeaguePayments WHERE sleeper_league_id = 'TEST_VAULT_001' AND season_year = 9999;

-- Check playoff placements
SELECT 'Playoff Placements:' as status,
    placement_type,
    roster_id,
    determined_by
FROM LeaguePlacements
WHERE sleeper_league_id = 'TEST_VAULT_001' AND season_year = 9999
ORDER BY final_rank;

-- =============================================================================
-- CLEANUP SCRIPT (run this to remove test league)
-- =============================================================================

-- UNCOMMENT TO DELETE TEST LEAGUE:
-- DELETE FROM LeaguePayments WHERE sleeper_league_id = 'TEST_VAULT_001';
-- DELETE FROM LeaguePlacements WHERE sleeper_league_id = 'TEST_VAULT_001';
-- DELETE FROM PlayoffMatchups WHERE sleeper_league_id = 'TEST_VAULT_001';
-- DELETE FROM PlayoffBrackets WHERE sleeper_league_id = 'TEST_VAULT_001';
-- DELETE FROM UserLeagueLinks WHERE sleeper_league_id = 'TEST_VAULT_001';
-- DELETE FROM LeagueFees WHERE sleeper_league_id = 'TEST_VAULT_001';
-- DELETE FROM rosters WHERE sleeper_league_id = 'TEST_VAULT_001';
-- DELETE FROM LeagueMetadata WHERE sleeper_league_id = 'TEST_VAULT_001';
