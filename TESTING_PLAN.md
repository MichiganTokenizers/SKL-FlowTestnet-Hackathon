# SKL Automated Prize Payout Testing Plan

## Overview
Testing strategy for league fee collection and automated prize distribution on Flow testnet, **without** external yield vault dependency initially.

## Testing Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PHASE 1: CORE FLOWS                       │
│                (No IncrementFi Dependency)                   │
└─────────────────────────────────────────────────────────────┘

Flow 1: Fee Collection
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  User Wallet │ ───> │  SKL Wallet  │ ───> │   Database   │
│  (Test User) │ FLOW │ 0xdf978465.. │      │ LeaguePayments│
└──────────────┘      └──────────────┘      └──────────────┘
     Multiple              Aggregates            Tracks
     users pay             all fees              status

Flow 2: Prize Distribution
┌──────────────┐      ┌──────────────────────────────────────┐
│  SKL Wallet  │ ───> │        Winner Wallets                │
│ (Admin Only) │      │  1st: 60%  2nd: 30%  3rd: 10%       │
└──────────────┘      └──────────────────────────────────────┘
   Single Tx                Three deposits
   (atomic)                 via distribute_prizes.cdc

┌─────────────────────────────────────────────────────────────┐
│              PHASE 2: YIELD INTEGRATION                      │
│              (Future - After Research)                       │
└─────────────────────────────────────────────────────────────┘

Flow 3: Yield Strategy (To Be Implemented)
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  SKL Wallet  │ ───> │ IncrementFi  │ ───> │ SKL Wallet + │
│              │      │ Money Market │      │    Yield     │
└──────────────┘      └──────────────┘      └──────────────┘
   Deposit funds      Earn interest        Withdraw + payout
```

---

## Test Environment Setup

### Test Accounts Required

| Role | Wallet Address | Purpose | FLOW Balance Needed |
|------|---------------|---------|---------------------|
| **SKL Admin** | `0xdf978465ee6dcf32` | Receive fees, distribute prizes | 50 FLOW (for gas) |
| **Test User 1** | TBD | Pay league fee | 100 FLOW |
| **Test User 2** | TBD | Pay league fee | 100 FLOW |
| **Test User 3** | TBD | Pay league fee | 100 FLOW |
| **Test User 4** | TBD | Pay league fee | 100 FLOW |
| **Test User 5** | TBD | Pay league fee | 100 FLOW |
| **Total** | 6 wallets | | **500 FLOW** |

### Test League Setup

```sql
-- Create test league in database
INSERT INTO LeagueMetadata (sleeper_league_id, name, season, status)
VALUES ('TEST_LEAGUE_001', 'SKL Test League - Prize Flow', 9999, 'active');

-- Configure league fees (small amount for testing)
INSERT INTO LeagueFees (sleeper_league_id, season_year, fee_amount, fee_currency, automated)
VALUES ('TEST_LEAGUE_001', 9999, 2.0, 'FLOW', 1);

-- Create test rosters (5 teams)
INSERT INTO rosters (sleeper_roster_id, sleeper_league_id, sleeper_user_id, owner_id, settings)
VALUES
    ('roster_001', 'TEST_LEAGUE_001', 'user_001', 1, '{}'),
    ('roster_002', 'TEST_LEAGUE_001', 'user_002', 2, '{}'),
    ('roster_003', 'TEST_LEAGUE_001', 'user_003', 3, '{}'),
    ('roster_004', 'TEST_LEAGUE_001', 'user_004', 4, '{}'),
    ('roster_005', 'TEST_LEAGUE_001', 'user_005', 5, '{}');

-- Link users to wallets
INSERT INTO UserLeagueLinks (wallet_address, sleeper_league_id, sleeper_roster_id, role)
VALUES
    ('0xuser1...', 'TEST_LEAGUE_001', 'roster_001', 'member'),
    ('0xuser2...', 'TEST_LEAGUE_001', 'roster_002', 'member'),
    ('0xuser3...', 'TEST_LEAGUE_001', 'roster_003', 'member'),
    ('0xuser4...', 'TEST_LEAGUE_001', 'roster_004', 'member'),
    ('0xuser5...', 'TEST_LEAGUE_001', 'roster_005', 'commissioner');
```

---

## Test Scenarios

### Scenario 1: Happy Path - Full Fee Collection

**Objective:** Verify all 5 users can pay fees successfully

**Status:** ✅ ALREADY TESTED ON MAINNET - Fee collection is production-ready

**Steps:**
1. Start with clean test league (no payments)
2. Each user connects wallet via Flow wallet
3. Each user pays 2.0 FLOW league fee
4. Verify SKL wallet receives 10.0 FLOW total
5. Verify database records all 5 payments

**Expected Results:**
```
LeaguePayments table:
- 5 rows with status = 'paid'
- Total paid_amount = 10.0 FLOW
- Each has valid transaction_id

SKL Wallet balance:
- Initial: X FLOW
- Final: X + 10.0 FLOW
```

**Validation:**
```bash
# Check SKL wallet balance
flow scripts execute backend/scripts/check_balance.cdc 0xdf978465ee6dcf32 --network testnet

# Check database
sqlite3 keeper.db "SELECT COUNT(*), SUM(paid_amount) FROM LeaguePayments WHERE sleeper_league_id='TEST_LEAGUE_001' AND season_year=9999"
# Expected: 5 | 10.0
```

---

### Scenario 2: Partial Payment Recovery

**Objective:** Test user paying remaining fee after partial payment

**Steps:**
1. User 1 pays 1.0 FLOW (half of 2.0 FLOW fee)
2. Verify status = 'partially_paid'
3. User 1 pays remaining 1.0 FLOW
4. Verify status = 'paid'

**Expected Results:**
```
LeaguePayments table for User 1:
- First payment: paid_amount = 1.0, status = 'partially_paid'
- Second payment: paid_amount = 2.0, status = 'paid'
- Two transaction_ids recorded
```

---

### Scenario 3: Prize Distribution (4-Way Split)

**Objective:** Distribute collected fees as prizes to top finishers

**Setup:**
```
Collected Fees: 10.0 FLOW
Prize Pool: 10.0 FLOW (principal only - yield stays with SKL)
Distribution:
  1st Place (User 1): 5.0 FLOW (50%)
  2nd Place (User 3): 3.0 FLOW (30%)
  3rd Place (User 5): 1.0 FLOW (10%)
  Regular Season Winner (User 2): 1.0 FLOW (10%)
```

**Steps:**
1. Admin marks season as complete in dashboard
2. Admin creates payout schedule:
   ```sql
   INSERT INTO PayoutSchedules (
       payout_id, sleeper_league_id, season_year,
       total_prize_pool, payout_status, payout_date, standings_finalized
   ) VALUES (
       'payout_test_001', 'TEST_LEAGUE_001', 9999,
       10.0, 'ready', '2025-10-09', 1
   );
   ```
3. Admin creates payout distributions:
   ```sql
   INSERT INTO PayoutDistributions (
       distribution_id, payout_id, wallet_address, payout_type, amount, percentage, status
   ) VALUES
       ('dist_001', 'payout_test_001', '0xuser1...', '1st_place', 5.0, 50.0, 'pending'),
       ('dist_002', 'payout_test_001', '0xuser3...', '2nd_place', 3.0, 30.0, 'pending'),
       ('dist_003', 'payout_test_001', '0xuser5...', '3rd_place', 1.0, 10.0, 'pending'),
       ('dist_004', 'payout_test_001', '0xuser2...', 'regular_season_winner', 1.0, 10.0, 'pending');
   ```
4. Admin executes payout via dashboard (calls Cadence transaction)
5. Verify all 4 winners receive FLOW
6. Verify database updates status to 'completed'

**Expected Flow Transaction:**
```bash
flow transactions send backend/scripts/distribute_prizes.cdc \
  --arg Address:[0xuser1,0xuser3,0xuser5,0xuser2] \
  --arg UFix64:[5.0,3.0,1.0,1.0] \
  --arg String:"TEST_LEAGUE_001" \
  --signer testnet-account \
  --network testnet
```

**Expected Results:**
```
Winner Wallet Balances:
- User 1: +5.0 FLOW (1st Place)
- User 2: +1.0 FLOW (Regular Season Winner)
- User 3: +3.0 FLOW (2nd Place)
- User 5: +1.0 FLOW (3rd Place)

SKL Wallet Balance:
- Before: X + 10.0 FLOW
- After: X + 0.0 FLOW (all distributed)

PayoutDistributions table:
- All 4 distributions: status = 'completed'
- All have transaction_id
- All have updated_at timestamp

Flowscan:
- Single transaction with 4 deposit events
- All visible on testnet.flowscan.io
```

---

### Scenario 4: Multi-League Isolation

**Objective:** Verify payouts for League A don't affect League B

**Steps:**
1. Create TEST_LEAGUE_002 with different users
2. Collect 8.0 FLOW in fees (4 users × 2 FLOW)
3. Execute payout for TEST_LEAGUE_001 (10.0 FLOW)
4. Verify TEST_LEAGUE_002 funds untouched
5. Execute payout for TEST_LEAGUE_002 (8.0 FLOW)

**Expected Results:**
- Each league payout uses only its own collected fees
- Database records isolated by `sleeper_league_id`
- No cross-league contamination

---

### Scenario 5: Failed Transaction Recovery

**Objective:** Handle transaction failures gracefully

**Steps:**
1. Create payout with invalid recipient address
2. Attempt to execute payout
3. Verify transaction fails
4. Verify database status remains 'pending' (not 'completed')
5. Fix recipient address
6. Retry payout
7. Verify success

**Expected Results:**
```
PayoutDistributions:
- First attempt: status = 'pending', error_message = 'Could not borrow receiver...'
- Second attempt: status = 'completed', transaction_id = '0xabc...'
```

---

### Scenario 6: Insufficient Balance Protection

**Objective:** Prevent payout execution if SKL wallet has insufficient FLOW

**Steps:**
1. Create payout for 100.0 FLOW
2. SKL wallet has only 10.0 FLOW
3. Attempt to execute payout
4. Verify transaction fails with balance error
5. Verify no funds transferred
6. Verify database shows error status

**Expected Results:**
```
Transaction Error: "Insufficient balance. Required: 100.0 FLOW, Available: 10.0 FLOW"
PayoutSchedules.payout_status = 'failed'
No changes to winner wallet balances
```

---

## Test Data Cleanup

After each test cycle, clean up test data:

```sql
-- Remove test payments
DELETE FROM LeaguePayments WHERE season_year = 9999;

-- Remove test payouts
DELETE FROM PayoutDistributions WHERE payout_id IN (
    SELECT payout_id FROM PayoutSchedules WHERE season_year = 9999
);
DELETE FROM PayoutSchedules WHERE season_year = 9999;

-- Remove test leagues (optional - can reuse)
-- DELETE FROM LeagueMetadata WHERE season = 9999;
```

---

## Success Criteria

### Phase 1 Complete When:
- ✅ All 6 test scenarios pass
- ✅ No manual intervention needed for standard flows
- ✅ All transactions visible on Flowscan testnet
- ✅ Database accurately reflects all states
- ✅ Admin dashboard shows real-time updates
- ✅ Error messages are clear and actionable

### Performance Targets:
- Fee payment transaction: < 5 seconds
- Prize distribution (3 winners): < 10 seconds
- Database queries: < 100ms
- UI updates: Real-time (via polling or WebSocket)

---

## Monitoring & Logging

### Transaction Tracking
```javascript
// Frontend - Store all transaction IDs
const paymentTx = await fcl.mutate({ ... });
console.log(`Payment TX: https://testnet.flowscan.io/tx/${paymentTx}`);

// Backend - Log all Cadence calls
logger.info(f"Executing payout for league {league_id}, tx_id: {tx_id}")
```

### Database Auditing
```sql
-- Add audit trail
CREATE TABLE IF NOT EXISTS AuditLog (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    wallet_address TEXT,
    transaction_id TEXT,
    details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## Risk Mitigation

### Financial Risks
| Risk | Mitigation | Status |
|------|------------|--------|
| Incorrect prize splits | Pre-calculate and display for admin confirmation | ✅ Planned |
| Double payout | Check payout_status before execution | ✅ Planned |
| Lost transaction IDs | Store all tx_ids in database immediately | ✅ Planned |
| Wallet compromise | Admin wallet requires multi-sig (future) | ⚠️ Future |

### Technical Risks
| Risk | Mitigation | Status |
|------|------------|--------|
| Cadence transaction fails | Retry logic + error handling | ✅ Planned |
| Database corruption | Daily backups + transaction logs | ⚠️ TODO |
| Network congestion | Increase gas limit if needed | ✅ Configurable |
| Testnet reset | Use season_year=9999 for easy cleanup | ✅ Implemented |

---

## Test Execution Checklist

### Pre-Test Setup
- [ ] Fund SKL wallet with 50 FLOW from testnet faucet
- [ ] Create 5 test user wallets with 5 FLOW each
- [ ] Insert test league data into database
- [ ] Verify frontend connects to testnet (not mainnet!)
- [ ] Verify backend API is running
- [ ] Clear any existing test data

### During Testing
- [ ] Record all transaction IDs in spreadsheet
- [ ] Screenshot each step for documentation
- [ ] Monitor Flowscan for transaction status
- [ ] Check database after each action
- [ ] Note any errors or unexpected behavior

### Post-Test Validation
- [ ] Verify all wallet balances correct
- [ ] Verify database states match reality
- [ ] Export test results to CSV
- [ ] Document any bugs found
- [ ] Clean up test data

---

## Next Steps After Phase 1

Once Phase 1 testing is complete and stable:

1. **Contact IncrementFi** for Money Market testnet addresses
2. **Implement Phase 2** yield vault integration
3. **Test yield accrual** over time (deposit → wait → withdraw)
4. **Calculate yield bonus** added to prize pool
5. **Build automated agents** for fee collection and payouts
6. **Deploy to mainnet** (carefully!)

---

## Questions to Resolve

- [ ] What's the minimum FLOW needed for gas per transaction?
- [ ] Should we support USDF payouts in addition to FLOW?
- [ ] How to handle partial team payments (some pay, some don't)?
- [ ] When to trigger "season complete" status?
- [ ] Should payouts be atomic (all or nothing) or individual?
- [ ] How to handle tax reporting for prize winnings? (legal question)

---

## Resources

- **This Project:** [INCREMENTFI_INTEGRATION_RESEARCH.md](INCREMENTFI_INTEGRATION_RESEARCH.md)
- **Testnet Migration:** [TESTNET_MIGRATION.md](TESTNET_MIGRATION.md)
- **Admin Dashboard:** [ADMIN_DASHBOARD_SETUP.md](ADMIN_DASHBOARD_SETUP.md)
- **Testnet Faucet:** https://testnet-faucet.onflow.org/
- **Flowscan Testnet:** https://testnet.flowscan.io/
- **Flow Docs:** https://developers.flow.com/

---

## Test Results Template

```markdown
# Test Run: [Date]

**Tester:** [Name]
**Test Cycle:** #[Number]
**Duration:** [Time]

## Scenarios Tested
- [x] Scenario 1: Fee Collection - PASSED
- [x] Scenario 2: Partial Payment - PASSED
- [x] Scenario 3: Prize Distribution - PASSED
- [ ] Scenario 4: Multi-League - FAILED (see notes)
- [ ] Scenario 5: Failed TX Recovery - NOT TESTED
- [ ] Scenario 6: Insufficient Balance - NOT TESTED

## Issues Found
1. [Description of issue]
   - Severity: High/Medium/Low
   - Transaction ID: 0x...
   - Error message: "..."
   - Reproduction steps: ...

## Wallet Balances
| Wallet | Before | After | Expected | Status |
|--------|--------|-------|----------|--------|
| SKL | 50.0 | 40.0 | 40.0 | ✅ |
| User 1 | 5.0 | 9.0 | 9.0 | ✅ |
| User 2 | 5.0 | 3.0 | 3.0 | ✅ |

## Transaction IDs
- Fee payment 1: https://testnet.flowscan.io/tx/0x...
- Fee payment 2: https://testnet.flowscan.io/tx/0x...
- Prize payout: https://testnet.flowscan.io/tx/0x...

## Notes
[Any additional observations]
```

---

**Last Updated:** 2025-10-09
**Status:** Ready for Implementation
