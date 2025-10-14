# SKL IncrementFi Vault Integration - Testing Plan

## Overview
End-to-end testing strategy for league fee collection, IncrementFi vault deposit, yield generation, and automated prize distribution on Flow testnet.

## Testing Architecture

```
┌─────────────────────────────────────────────────────────────┐
│           COMPLETE VAULT INTEGRATION FLOW                    │
│         (IncrementFi Money Market on Testnet)                │
└─────────────────────────────────────────────────────────────┘

Flow 1: Fee Collection
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  User Wallet │ ───> │  SKL Wallet  │ ───> │   Database   │
│   (5 Real)   │ FLOW │ 0xdf978465.. │      │ LeaguePayments│
└──────────────┘      └──────────────┘      └──────────────┘
  5 × 100 FLOW          Aggregates            Tracks status
  = 500 FLOW           + 500 (fake)           (10 teams)

Flow 2: Vault Deposit (Automatic on Full Payment)
┌──────────────┐      ┌──────────────────┐      ┌──────────────┐
│  SKL Wallet  │ ───> │  IncrementFi     │ ───> │  YieldVaults │
│              │      │  Money Market    │      │   (Database) │
└──────────────┘      └──────────────────┘      └──────────────┘
  Deposit 1000 FLOW    0x8aaca41f09eb1e3d       Track deposit
  via deposit_to_      Earn yield on FLOW       timestamp + amount
  incrementfi.cdc

Flow 3: Yield Accrual & Monitoring
┌──────────────────┐      ┌──────────────┐
│  IncrementFi     │ ───> │ Check Balance│
│  Vault Balance   │      │    Script    │
└──────────────────┘      └──────────────┘
  1000 + yield            check_incrementfi_
  (monitored daily)       balance.cdc

Flow 4: Vault Withdrawal (Manual Trigger After Season)
┌──────────────────┐      ┌──────────────┐      ┌──────────────┐
│  IncrementFi     │ ───> │  SKL Wallet  │ ───> │  Database    │
│  Vault           │      │              │      │  Update      │
└──────────────────┘      └──────────────┘      └──────────────┘
  Redeem 1000 FLOW        Receive funds +       Record withdrawal
  via withdraw_from_      yield earned          + yield amount
  incrementfi.cdc

Flow 5: Prize Distribution (Playoff-Based)
┌──────────────┐      ┌──────────────────────────────────────┐
│  SKL Wallet  │ ───> │        Winner Wallets (Real Testnet) │
│ (Admin Only) │      │  1st: 500  2nd: 300  3rd: 100 RS: 100│
└──────────────┘      └──────────────────────────────────────┘
  Distribute prizes        via distribute_prizes.cdc
  based on LeaguePlacements table
```

---

## Test Environment Setup

### Test Accounts (Actual Testnet Wallets)

| Role | Wallet Address | Username | Team | Prize | Balance Needed |
|------|---------------|----------|------|-------|----------------|
| **SKL Admin** | `0xdf978465ee6dcf32` | - | - | - | 1000+ FLOW (for distribution) |
| **Commissioner** | `0xb647c8ffe7d05b51` | SKLtest1 | Regular Season Kings | 100 FLOW | 100 FLOW |
| **Champion** | `0x447414116f2e51ef` | SKLtest2 | Championship Champions | 500 FLOW | 100 FLOW |
| **Runner-Up** | `0xa9f313f3c175ebb5` | SKLtest3 | Runner-Up Rivals | 300 FLOW | 100 FLOW |
| **3rd Place** | `0x5bc0cf1d498be10b` | SKLtest4 | Third Place Threats | 100 FLOW | 100 FLOW |
| **Participant** | `0xbfa776c05871e1d4` | SKLtest5 | Playoff Participants | 0 FLOW | 100 FLOW |
| **Total** | 6 wallets | - | - | - | **~600 FLOW** |

**Note:** All 5 test wallets will be funded with 100,000 FLOW from testnet faucet to track exact net profit/loss.

### Mock Sleeper User IDs

To bypass Sleeper authentication for testing:

| Wallet | Sleeper User ID | Username | Purpose |
|--------|----------------|----------|---------|
| 0xb647c8ffe7d05b51 | 900266666666666666 | SKLtest1 | Commissioner + Regular Season Winner |
| 0x447414116f2e51ef | 900277777777777777 | SKLtest2 | Champion (1st Place) |
| 0xa9f313f3c175ebb5 | 900288888888888888 | SKLtest3 | Runner-Up (2nd Place) |
| 0x5bc0cf1d498be10b | 900299999999999999 | SKLtest4 | 3rd Place Winner |
| 0xbfa776c05871e1d4 | 900210101010101010 | SKLtest5 | No Prize |
| 0xFAKE1111... (×5) | 9001xxxxxxxxxx | fake_user_00X | Pre-paid fake wallets (500 FLOW) |

### Test League Setup

**League:** TEST_VAULT_001
**Season:** 9999 (easy to identify and clean up)
**Teams:** 10 total (5 fake pre-paid + 5 real unpaid)
**Fee:** 100 FLOW per team
**Total Prize Pool:** 1000 FLOW (when all 10 teams paid)

**Database Configuration:**
```sql
-- League already created in keeper.db via create_mock_test_league.sql
-- Key tables populated:
-- - LeagueMetadata: TEST_VAULT_001
-- - LeagueFees: 100 FLOW per team
-- - rosters: 10 teams with mock Sleeper user IDs
-- - Users: Wallet addresses linked to Sleeper IDs
-- - UserLeagueLinks: 5 fake paid, 5 real unpaid
-- - LeaguePlacements: Pre-configured playoff results
-- - PlayoffBrackets: Mock playoff bracket structure
```

---

## Test Scenarios

### Scenario 1: League Fee Payment (5 Real Wallets)

**Objective:** Collect 500 FLOW from 5 real testnet wallets

**Initial State:**
- 5 fake wallets: paid (500 FLOW)
- 5 real wallets: unpaid (0 FLOW)
- Total collected: 500/1000 FLOW

**Steps:**
1. Fund each real wallet with 100,000 FLOW from testnet faucet
2. Log in with wallet 1 (SKLtest1 - Commissioner)
3. Navigate to league page for TEST_VAULT_001
4. Pay 100 FLOW league fee via UI
5. Verify transaction on Flowscan
6. Repeat for wallets 2-5 (SKLtest2 through SKLtest5)

**Expected Results:**
```
UserLeagueLinks table:
- All 10 wallets: fee_payment_status = 'paid'
- All 10 wallets: fee_paid_amount = 100.0

LeaguePayments table:
- 10 rows total (5 fake + 5 real)
- All have valid transaction_id
- Total amount: 1000.0 FLOW

SKL Wallet balance:
- Initial: X FLOW
- After all payments: X + 1000.0 FLOW
```

**Validation:**
```bash
# Check database
sqlite3 keeper.db "SELECT COUNT(*), SUM(fee_paid_amount) FROM UserLeagueLinks WHERE sleeper_league_id='TEST_VAULT_001' AND fee_payment_status='paid'"
# Expected: 10 | 1000.0

# Check SKL wallet balance
flow scripts execute backend/scripts/check_balance.cdc 0xdf978465ee6dcf32 --network testnet
```

---

### Scenario 2: Automatic Vault Deposit ✅ COMPLETED

**Objective:** Automatically deposit 1000 FLOW to IncrementFi vault when last wallet pays

**Trigger:** When 10th wallet (last of 5 real wallets) pays fee

**Implementation:** Fully automated via `execute_vault_deposit_transaction()` in backend/app.py

**Steps:**
1. ✅ Backend detects all 10 teams paid via payment record endpoint
2. ✅ Backend automatically triggers vault deposit execution
3. ✅ Execute Cadence transaction via subprocess: `deposit_to_incrementfi.cdc`
   - Uses Flow CLI with `--args-json` for proper type formatting
   - Transaction signed by testnet-account (SKL wallet)
   - Calls LendingPool.supply() method directly on IncrementFi contract
4. ✅ Transaction succeeds and is sealed on testnet
5. ✅ Database records execution in AgentExecutions table with status "completed"

**Test Results (2025-10-14):**
```
Transaction ID: bf0e40585fc53983b9e60298a512c57fc3e6b05b41fbffa83f0b085032177ff5
Block Height: 284850625
Status: SEALED ✅
Amount: 1000.0 FLOW
From: 0xdf978465ee6dcf32 (SKL Admin)
To: 0x8aaca41f09eb1e3d (IncrementFi FLOW Money Market)
LP Tokens Minted: 826,729,875,758,667,531,243 (scaled)

Flowscan: https://testnet.flowscan.io/tx/bf0e40585fc53983b9e60298a512c57fc3e6b05b41fbffa83f0b085032177ff5
```

**Expected Results:**
```
AgentExecutions table:
- execution_id: vault_deposit_TEST_VAULT_001_2025_1760449332
- agent_type: vault_deposit
- status: completed
- result_data: Contains transaction_id, amount, vault details

IncrementFi Pool Balance:
- Before: 2,002,526.98 FLOW
- After: 2,003,526.98 FLOW (+1000 FLOW confirmed)

SKL Wallet Balance:
- Before: ~100,500 FLOW
- After: 99,499 FLOW (-1000 FLOW confirmed)
```

**Key Technical Details:**
- **Flow CLI Configuration:** Added explicit key parameters in flow.json (index, signatureAlgorithm, hashAlgorithm)
- **Cadence Script:** Uses direct contract access via `getAccount().contracts.borrow<&LendingPool>()`
- **Method Called:** `supply(supplierAddr: Address, inUnderlyingVault: @{FungibleToken.Vault})`
- **Transaction Time:** ~7.4 seconds from trigger to sealed

**Validation:**
```bash
# Check AgentExecutions status
sqlite3 keeper.db "SELECT execution_id, status FROM AgentExecutions WHERE execution_id LIKE 'vault_deposit_TEST_VAULT_001%'"

# Check SKL wallet balance
flow accounts get 0xdf978465ee6dcf32 --network testnet | grep Balance

# View transaction on Flowscan
open https://testnet.flowscan.io/tx/bf0e40585fc53983b9e60298a512c57fc3e6b05b41fbffa83f0b085032177ff5
```

---

### Scenario 3: Yield Monitoring

**Objective:** Monitor vault balance growth over time

**Duration:** 24-48 hours (or longer for measurable yield)

**Steps:**
1. Record initial vault balance after deposit
2. Wait 24 hours
3. Check vault balance via `check_incrementfi_balance.cdc`
4. Calculate yield earned
5. Update database with yield snapshot

**Expected Results:**
```
Initial Balance: 1000.0 FLOW
After 24h: 1000.0 + X FLOW (yield rate depends on IncrementFi APY)
After 48h: 1000.0 + Y FLOW

Note: Testnet yield rates may differ from mainnet
```

**Monitoring Script:**
```bash
# Run daily to track yield
while true; do
  echo "=== Vault Balance Check $(date) ==="
  flow scripts execute backend/scripts/check_incrementfi_balance.cdc \
    0xdf978465ee6dcf32 \
    0x8aaca41f09eb1e3d \
    --network testnet
  sleep 86400  # 24 hours
done
```

---

### Scenario 4: Vault Withdrawal

**Objective:** Withdraw funds + yield from IncrementFi vault

**Trigger:** Manual admin action after season ends

**Steps:**
1. Admin marks season as complete in dashboard
2. Check final vault balance
3. Execute withdrawal transaction: `withdraw_from_incrementfi.cdc`
   ```bash
   flow transactions send backend/scripts/withdraw_from_incrementfi.cdc \
     --arg UFix64:[full_balance] \
     --arg Address:0x8aaca41f09eb1e3d \
     --arg String:"TEST_VAULT_001" \
     --signer testnet-account \
     --network testnet
   ```
4. Verify SKL wallet receives funds
5. Update database with withdrawal details

**Expected Results:**
```
YieldVaults table:
- vault_status: withdrawn
- withdrawal_amount: 1000.0 + yield
- withdrawal_tx_id: 0x...
- withdrawal_date: [timestamp]
- yield_earned: [calculated difference]

SKL Wallet Balance:
- Before withdrawal: Y FLOW
- After withdrawal: Y + 1000.0 + yield FLOW
```

---

### Scenario 5: Prize Distribution (Playoff-Based)

**Objective:** Distribute 1000 FLOW prize pool to 4 winners based on playoff results

**Prize Distribution (ALL REAL WALLETS!):**
- 🏆 **1st Place: Team 7 (SKLtest2 - 0x447414116f2e51ef) - 500 FLOW (50%)**
- 🥈 **2nd Place: Team 8 (SKLtest3 - 0xa9f313f3c175ebb5) - 300 FLOW (30%)**
- 🥉 **3rd Place: Team 9 (SKLtest4 - 0x5bc0cf1d498be10b) - 100 FLOW (10%)**
- 🏅 **Regular Season: Team 6 (SKLtest1 - 0xb647c8ffe7d05b51) - 100 FLOW (10%)**

**Steps:**
1. Admin creates payout schedule in dashboard
2. System reads LeaguePlacements table for winners
3. Admin confirms prize distribution breakdown
4. Execute Cadence transaction: `distribute_prizes.cdc`
   ```bash
   flow transactions send backend/scripts/distribute_prizes.cdc \
     --arg Address:[0x447414116f2e51ef,0xa9f313f3c175ebb5,0x5bc0cf1d498be10b,0xb647c8ffe7d05b51] \
     --arg UFix64:[500.0,300.0,100.0,100.0] \
     --arg String:"TEST_VAULT_001" \
     --signer testnet-account \
     --network testnet
   ```
5. Verify all 4 winners receive prizes
6. Update database with distribution records

**Expected Results:**
```
Winner Wallet Balances (Net P&L from 100,000 FLOW starting balance):
- SKLtest1: 100,000 - 100 + 100 = 100,000 FLOW (break even) ➡️
- SKLtest2: 100,000 - 100 + 500 = 100,400 FLOW (+400 profit) 🎉
- SKLtest3: 100,000 - 100 + 300 = 100,200 FLOW (+200 profit) 🎉
- SKLtest4: 100,000 - 100 + 100 = 100,000 FLOW (break even) ➡️
- SKLtest5: 100,000 - 100 + 0 = 99,900 FLOW (-100 loss) ❌

PayoutDistributions table:
- 4 rows (one per winner)
- All status = 'completed'
- All have transaction_id
- Total distributed: 1000.0 FLOW

PayoutSchedules table:
- payout_status: completed
- total_prize_pool: 1000.0 FLOW
- yield_bonus: [if any yield earned]
```

**Validation:**
```bash
# Check each winner's balance
for addr in 0x447414116f2e51ef 0xa9f313f3c175ebb5 0x5bc0cf1d498be10b 0xb647c8ffe7d05b51; do
  echo "Balance for $addr:"
  flow scripts execute backend/scripts/check_balance.cdc $addr --network testnet
done

# Verify on Flowscan
# Single transaction should show 4 deposit events
```

---

## Admin Dashboard Endpoints

New endpoints for vault management (added to [admin_routes.py](backend/admin_routes.py)):

### Vault Operations
```
POST /admin/league/<league_id>/vault/deposit
POST /admin/league/<league_id>/vault/withdraw
GET  /admin/league/<league_id>/vault/balance
GET  /admin/league/<league_id>/vault/history
```

### Playoff & Prize Calculation
```
POST /admin/league/<league_id>/playoff-bracket/sync
GET  /admin/league/<league_id>/playoff-bracket
POST /admin/league/<league_id>/payouts/calculate
GET  /admin/league/<league_id>/payouts/preview
```

### Execution
```
POST /admin/league/<league_id>/payouts/execute
GET  /admin/league/<league_id>/payouts/status
```

---

## Database Schema Updates

### New Tables (from [002_add_playoff_tracking.sql](backend/migrations/002_add_playoff_tracking.sql))

**PlayoffBrackets:** Store full playoff bracket JSON from Sleeper API
**PlayoffMatchups:** Individual playoff games with winners/losers
**LeaguePlacements:** Final rankings (1st, 2nd, 3rd, regular_season_winner)

**Updated Tables:**
- `rosters`: Added `points_for` column for tiebreakers
- `YieldVaults`: Track vault deposits/withdrawals
- `PayoutSchedules`: Link to vault withdrawals
- `PayoutDistributions`: Individual prize payments

---

## Test Data Cleanup

```bash
# Clean up TEST_VAULT_001 completely
cd backend
sqlite3 keeper.db <<EOF
DELETE FROM LeaguePayments WHERE sleeper_league_id = 'TEST_VAULT_001';
DELETE FROM LeaguePlacements WHERE sleeper_league_id = 'TEST_VAULT_001';
DELETE FROM PlayoffMatchups WHERE sleeper_league_id = 'TEST_VAULT_001';
DELETE FROM PlayoffBrackets WHERE sleeper_league_id = 'TEST_VAULT_001';
DELETE FROM PayoutDistributions WHERE payout_id IN (
    SELECT payout_id FROM PayoutSchedules WHERE sleeper_league_id = 'TEST_VAULT_001'
);
DELETE FROM PayoutSchedules WHERE sleeper_league_id = 'TEST_VAULT_001';
DELETE FROM YieldVaults WHERE sleeper_league_id = 'TEST_VAULT_001';
DELETE FROM UserLeagueLinks WHERE sleeper_league_id = 'TEST_VAULT_001';
DELETE FROM LeagueFees WHERE sleeper_league_id = 'TEST_VAULT_001';
DELETE FROM rosters WHERE sleeper_league_id = 'TEST_VAULT_001';
DELETE FROM Users WHERE wallet_address LIKE '0xFAKE%' OR sleeper_user_id LIKE '9001%' OR sleeper_user_id LIKE '9002%';
DELETE FROM LeagueMetadata WHERE sleeper_league_id = 'TEST_VAULT_001';
EOF

# Re-run mock league setup
sqlite3 keeper.db < scripts/create_mock_test_league.sql
```

---

## Success Criteria

### ✅ Complete Integration Test Passes When:
- [x] All 5 real wallets can pay league fees via UI
- [x] Vault deposit triggers automatically when 10th wallet pays ✅ **COMPLETED**
- [x] IncrementFi vault receives exactly 1000 FLOW ✅ **VERIFIED**
- [ ] Vault balance can be monitored via script
- [ ] Yield accrues over time (measurable after 24-48h)
- [ ] Vault withdrawal succeeds and funds return to SKL wallet
- [ ] Prize distribution sends correct amounts to 4 winners
- [x] All transactions visible on Flowscan testnet ✅ **VERIFIED**
- [x] Database accurately tracks all states (AgentExecutions) ✅ **VERIFIED**
- [ ] Admin dashboard shows real-time updates
- [ ] Net P&L matches expectations for all 5 wallets

### Performance Targets:
- Fee payment transaction: < 10 seconds ✅
- Vault deposit transaction: < 15 seconds ✅ **7.4 seconds achieved**
- Vault withdrawal transaction: < 15 seconds
- Prize distribution (4 winners): < 15 seconds
- Balance check script: < 5 seconds
- Database queries: < 100ms ✅

---

## Risk Mitigation

### Financial Risks
| Risk | Mitigation | Status |
|------|------------|--------|
| Incorrect prize splits | Pre-calculate and display for admin confirmation | ✅ Implemented |
| Vault deposit fails | Check balance before deposit, retry logic | ✅ Planned |
| Vault withdrawal fails | Verify vault balance first, error handling | ✅ Planned |
| Double payout | Check payout_status before execution | ✅ Implemented |
| Lost transaction IDs | Store all tx_ids in database immediately | ✅ Implemented |

### Technical Risks
| Risk | Mitigation | Status |
|------|------------|--------|
| IncrementFi vault unavailable | Graceful degradation, manual fallback | ⚠️ Monitor |
| Cadence transaction fails | Retry logic + detailed error messages | ✅ Implemented |
| Network congestion | Increase gas limit if needed | ✅ Configurable |
| Testnet reset | Use season_year=9999 for easy cleanup | ✅ Implemented |

---

## Test Execution Checklist

### Pre-Test Setup
- [x] Create TEST_VAULT_001 league in keeper.db
- [x] Configure 10 rosters with mock Sleeper user IDs
- [x] Link 5 real testnet wallets to Sleeper IDs
- [x] Set SKLtest1 as commissioner
- [x] Mark 5 fake wallets as paid (500 FLOW)
- [x] Mark 5 real wallets as unpaid (0 FLOW)
- [ ] Fund all 5 real wallets with 100,000 FLOW from testnet faucet
- [ ] Verify frontend connects to testnet (not mainnet!)
- [x] Verify backend API running on localhost:5000
- [x] Verify frontend running on localhost:5173

### During Testing
- [ ] Record all transaction IDs in spreadsheet
- [ ] Screenshot each step for documentation
- [ ] Monitor Flowscan for transaction status
- [ ] Check database after each action
- [ ] Track exact FLOW balances for P&L calculation
- [ ] Note any errors or unexpected behavior

### Post-Test Validation
- [ ] Verify all 5 wallet balances match expected P&L
- [ ] Verify database states match reality
- [ ] Export test results to CSV
- [ ] Document any bugs found
- [ ] Calculate actual yield earned (if any)
- [ ] Clean up test data for next run

---

## Resources

- **Integration Research:** [INCREMENTFI_INTEGRATION_RESEARCH.md](INCREMENTFI_INTEGRATION_RESEARCH.md)
- **Testnet Migration:** [TESTNET_MIGRATION.md](TESTNET_MIGRATION.md)
- **Admin Dashboard:** [ADMIN_DASHBOARD_SETUP.md](ADMIN_DASHBOARD_SETUP.md)
- **Wallet Reference:** [backend/scripts/TESTNET_WALLET_REFERENCE.md](backend/scripts/TESTNET_WALLET_REFERENCE.md)
- **Mock League SQL:** [backend/scripts/create_mock_test_league.sql](backend/scripts/create_mock_test_league.sql)
- **Testnet Faucet:** https://testnet-faucet.onflow.org/
- **Flowscan Testnet:** https://testnet.flowscan.io/
- **Flow Docs:** https://developers.flow.com/
- **IncrementFi Docs:** https://docs.increment.fi/

---

## IncrementFi Contract Addresses (Testnet)

- **LendingPool:** `0x8aaca41f09eb1e3d`
- **FlowToken Vault:** Standard Flow vault path (`/storage/flowTokenVault`)

---

**Last Updated:** 2025-10-14
**Status:** Automated Vault Deposit COMPLETED ✅
**Current Step:** Vault deposit automation working. Ready for vault withdrawal and prize distribution testing.
**Completed Milestones:**
- ✅ Automatic vault deposit on final fee payment (Scenario 2)
- ✅ Flow CLI integration with proper signing
- ✅ IncrementFi LendingPool integration (supply method)
- ✅ 1000 FLOW successfully deposited to testnet
- ✅ Transaction verified on Flowscan: [bf0e4058...](https://testnet.flowscan.io/tx/bf0e40585fc53983b9e60298a512c57fc3e6b05b41fbffa83f0b085032177ff5)
