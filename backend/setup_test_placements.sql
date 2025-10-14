-- Setup test placements for TEST_VAULT_001 league
-- This SQL script creates the necessary placement records for prize distribution testing

-- First, let's see what rosters exist in the test league
SELECT '=== Existing Rosters in TEST_VAULT_001 ===' as info;
SELECT
    r.sleeper_roster_id,
    r.team_name,
    r.owner_id,
    u.username,
    u.wallet_address,
    r.wins,
    r.losses,
    r.points_for
FROM rosters r
LEFT JOIN Users u ON r.owner_id = u.sleeper_user_id
WHERE r.sleeper_league_id = 'TEST_VAULT_001'
ORDER BY r.wins DESC, r.points_for DESC;

-- Check current season year
SELECT '=== Current Season ===' as info;
SELECT current_year, IsOffSeason FROM season_curr LIMIT 1;

-- Delete any existing placements for this league (for clean testing)
SELECT '=== Cleaning Existing Placements ===' as info;
DELETE FROM LeaguePlacements WHERE sleeper_league_id = 'TEST_VAULT_001';

-- Insert placements for the test league
-- IMPORTANT: Update the roster_id values to match your actual roster IDs from the query above
SELECT '=== Inserting Test Placements ===' as info;

-- Replace 'roster_1', 'roster_2', etc. with actual roster IDs from your league
INSERT INTO LeaguePlacements (
    sleeper_league_id,
    season_year,
    roster_id,
    placement_type,
    final_rank,
    created_at
) VALUES
    -- 1st Place - Gets 50% of prize pool
    ('TEST_VAULT_001', 2025, 'roster_1', '1st_place', 1, datetime('now')),

    -- 2nd Place - Gets 30% of prize pool
    ('TEST_VAULT_001', 2025, 'roster_2', '2nd_place', 2, datetime('now')),

    -- 3rd Place - Gets 10% of prize pool
    ('TEST_VAULT_001', 2025, 'roster_3', '3rd_place', 3, datetime('now')),

    -- Regular Season Winner - Gets 10% of prize pool
    ('TEST_VAULT_001', 2025, 'roster_4', 'regular_season_winner', 4, datetime('now'));

-- Verify the insertions
SELECT '=== Verification: Placements with Team Info ===' as info;
SELECT
    lp.placement_type,
    lp.final_rank,
    lp.roster_id,
    r.team_name,
    u.username,
    u.wallet_address,
    lp.created_at
FROM LeaguePlacements lp
LEFT JOIN rosters r ON lp.roster_id = r.sleeper_roster_id
    AND lp.sleeper_league_id = r.sleeper_league_id
LEFT JOIN Users u ON r.owner_id = u.sleeper_user_id
WHERE lp.sleeper_league_id = 'TEST_VAULT_001'
ORDER BY lp.final_rank;

-- Check if we have all required placements
SELECT '=== Placement Summary ===' as info;
SELECT
    CASE
        WHEN COUNT(*) = 4 THEN '✅ All 4 placements recorded'
        ELSE '❌ Missing placements (need 4, have ' || COUNT(*) || ')'
    END as status
FROM LeaguePlacements
WHERE sleeper_league_id = 'TEST_VAULT_001';

-- Show prize distribution preview
SELECT '=== Prize Distribution Preview ===' as info;
WITH VaultDeposit AS (
    SELECT json_extract(result_data, '$.amount') as total_pool
    FROM AgentExecutions
    WHERE agent_type = 'vault_deposit'
    AND execution_id LIKE 'vault_deposit_TEST_VAULT_001%'
    AND status = 'completed'
    ORDER BY created_at DESC
    LIMIT 1
)
SELECT
    lp.placement_type,
    r.team_name,
    u.username,
    u.wallet_address,
    CASE lp.placement_type
        WHEN '1st_place' THEN vd.total_pool * 0.50
        WHEN '2nd_place' THEN vd.total_pool * 0.30
        WHEN '3rd_place' THEN vd.total_pool * 0.10
        WHEN 'regular_season_winner' THEN vd.total_pool * 0.10
    END as prize_amount,
    CASE lp.placement_type
        WHEN '1st_place' THEN '50%'
        WHEN '2nd_place' THEN '30%'
        WHEN '3rd_place' THEN '10%'
        WHEN 'regular_season_winner' THEN '10%'
    END as percentage
FROM LeaguePlacements lp
CROSS JOIN VaultDeposit vd
LEFT JOIN rosters r ON lp.roster_id = r.sleeper_roster_id
    AND lp.sleeper_league_id = r.sleeper_league_id
LEFT JOIN Users u ON r.owner_id = u.sleeper_user_id
WHERE lp.sleeper_league_id = 'TEST_VAULT_001'
ORDER BY lp.final_rank;

-- Instructions for manual editing
SELECT '=== INSTRUCTIONS ===' as info;
SELECT
'To use this script:
1. First run the SELECT query to see existing rosters
2. Update the INSERT statements with actual roster_id values
3. Run the INSERT statements
4. Verify with the final SELECT queries
5. Run: python check_payout_prerequisites.py' as instructions;