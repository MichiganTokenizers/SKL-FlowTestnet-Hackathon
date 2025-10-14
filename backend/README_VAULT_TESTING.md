# Vault Withdrawal & Prize Distribution - Testing Suite

Complete testing suite for the IncrementFi vault withdrawal and prize distribution system.

## 📁 Files Created

| File | Purpose |
|------|---------|
| `test_vault_payouts.py` | Full test script (executes blockchain transactions) |
| `test_payout_preview.py` | Safe preview script (no transactions) |
| `check_payout_prerequisites.py` | Verify system readiness |
| `setup_test_placements.sql` | SQL script to setup test data |
| `TESTING_QUICKSTART.md` | Quick start guide |
| `TESTING_VAULT_PAYOUTS.md` | Detailed testing documentation |

## 🚀 Quick Start

```bash
# 1. Check prerequisites
python check_payout_prerequisites.py

# 2. Preview payouts (safe - no blockchain transactions)
python test_payout_preview.py

# 3. Execute full test (includes real transactions)
python test_vault_payouts.py
```

## 📋 System Overview

### Endpoints Implemented

1. **Vault Withdrawal** - `POST /admin/league/<league_id>/vault/withdraw`
   - Withdraws funds from IncrementFi Money Market to SKL wallet
   - Admin-only (requires wallet 0xdf978465ee6dcf32)
   - Idempotent (prevents double-withdrawal)

2. **Payout Preview** - `GET /admin/league/<league_id>/payouts/preview`
   - Shows prize distribution breakdown
   - Safe to call repeatedly
   - No blockchain transactions

3. **Payout Execution** - `POST /admin/league/<league_id>/payouts/execute`
   - Executes prize distributions to winners
   - Creates blockchain transaction
   - Records in PayoutSchedules and PayoutDistributions tables

### Prize Distribution

| Placement | Percentage | Example (100 FLOW) |
|-----------|------------|--------------------|
| 1st Place | 50% | 50.00 FLOW |
| 2nd Place | 30% | 30.00 FLOW |
| 3rd Place | 10% | 10.00 FLOW |
| Regular Season Winner | 10% | 10.00 FLOW |

## 🔧 Setup

### Prerequisites

1. **Backend running:**
   ```bash
   cd backend
   python app.py
   ```

2. **Database tables exist:**
   - AgentExecutions
   - PayoutSchedules
   - PayoutDistributions
   - LeaguePlacements

3. **Test data:**
   - League: TEST_VAULT_001
   - Vault deposit completed
   - 4 placements recorded
   - Admin wallet: 0xdf978465ee6dcf32

### Setup Test Data

1. **Check existing rosters:**
   ```bash
   sqlite3 /var/data/keeper.db "SELECT sleeper_roster_id, team_name FROM rosters WHERE sleeper_league_id='TEST_VAULT_001';"
   ```

2. **Setup placements:**
   ```bash
   sqlite3 /var/data/keeper.db < setup_test_placements.sql
   ```

3. **Verify setup:**
   ```bash
   python check_payout_prerequisites.py
   ```

## 📊 Testing Workflow

```
┌──────────────────────────────────────────┐
│  1. Check Prerequisites                  │
│  python check_payout_prerequisites.py    │
└────────────────┬─────────────────────────┘
                 ↓
          All checks pass?
                 ↓ Yes
┌──────────────────────────────────────────┐
│  2. Preview Payouts (Safe)               │
│  python test_payout_preview.py           │
└────────────────┬─────────────────────────┘
                 ↓
        Data looks correct?
                 ↓ Yes
┌──────────────────────────────────────────┐
│  3. Execute Full Test                    │
│  python test_vault_payouts.py            │
│                                          │
│  Steps:                                  │
│  • Login as admin                        │
│  • Withdraw from vault                   │
│  • Preview distributions                 │
│  • Execute payouts (with confirmation)   │
└────────────────┬─────────────────────────┘
                 ↓
              Success!
```

## 🧪 Example Test Run

### 1. Check Prerequisites

```bash
$ python check_payout_prerequisites.py

============================================================
  Vault Withdrawal & Prize Distribution Prerequisites
============================================================

League: TEST_VAULT_001
Database: /var/data/keeper.db

============================================================
  Checking Vault Deposit
============================================================

✅ Vault deposit completed
   Execution ID: vault_deposit_TEST_VAULT_001_2025_1234567890
   Amount: 100.0 FLOW
   Transaction ID: 0xabc123...
   Created: 2025-01-15 10:30:00

============================================================
  Summary
============================================================

✅ Vault deposit completed
✅ No prior withdrawal
✅ Placements recorded
✅ No prior payouts

✅ All prerequisites met!
```

### 2. Preview Payouts

```bash
$ python test_payout_preview.py

============================================================
  Payout Preview Test (Safe - No Blockchain Transactions)
============================================================

🔐 Logging in as admin...
✅ Logged in! Token: Ab3dF9...

🔍 Previewing payouts for league: TEST_VAULT_001

✅ Preview loaded successfully!

💰 Total Prize Pool: 100.0 FLOW
🏆 Number of Winners: 4

Distribution Breakdown:
============================================================

1ST PLACE
  Username:   TeamAlpha
  Wallet:     0x1234567890abcdef
  Amount:     50.00 FLOW (50%)

2ND PLACE
  Username:   TeamBeta
  Wallet:     0x234567890abcdef1
  Amount:     30.00 FLOW (30%)

3RD PLACE
  Username:   TeamGamma
  Wallet:     0x34567890abcdef12
  Amount:     10.00 FLOW (10%)

REGULAR SEASON WINNER
  Username:   TeamDelta
  Wallet:     0x4567890abcdef123
  Amount:     10.00 FLOW (10%)

============================================================

✅ Total to be distributed: 100.00 FLOW
✅ Distribution amounts match prize pool
```

### 3. Execute Full Test

```bash
$ python test_vault_payouts.py

============================================================
  Vault Withdrawal & Prize Distribution Test
============================================================

Testing league: TEST_VAULT_001
Admin wallet: 0xdf978465ee6dcf32
Backend URL: http://localhost:5000

============================================================
  STEP 1: Admin Login
============================================================

✅ Logged in successfully!

============================================================
  STEP 2: Withdraw from Vault
============================================================

✅ Vault withdrawal successful!
ℹ️  Amount withdrawn: 100.0 FLOW
ℹ️  Transaction ID: 0xdef456...
ℹ️  View on Flow Testnet: https://testnet.flowscan.org/transaction/0xdef456...

============================================================
  STEP 3: Preview Prize Distributions
============================================================

✅ Preview loaded successfully!
💰 Total prize pool: 100.0 FLOW
[... distribution details ...]

============================================================
  STEP 4: Execute Prize Distributions
============================================================

⚠️  WARNING: This will execute REAL blockchain transactions!
Type 'YES' to continue with payout execution: YES

✅ Prize distribution executed successfully!
ℹ️  Transaction ID: 0xghi789...
ℹ️  View on Flow Testnet: https://testnet.flowscan.org/transaction/0xghi789...

============================================================
  All Operations Completed Successfully! 🎉
============================================================

✅ Vault withdrawal completed
✅ Prize distributions executed
```

## 🔍 Verification

### Database Checks

```sql
-- Check vault withdrawal
SELECT * FROM AgentExecutions
WHERE agent_type = 'vault_withdrawal'
AND execution_id LIKE 'vault_withdrawal_TEST_VAULT_001%';

-- Check payout schedule
SELECT * FROM PayoutSchedules
WHERE sleeper_league_id = 'TEST_VAULT_001';

-- Check individual distributions
SELECT * FROM PayoutDistributions
WHERE payout_id IN (
    SELECT payout_id FROM PayoutSchedules
    WHERE sleeper_league_id = 'TEST_VAULT_001'
);
```

### Blockchain Verification

View transactions on Flow Testnet:
- **Explorer:** https://testnet.flowscan.org/
- Search by transaction ID from test output

## ❓ Troubleshooting

### Common Issues

| Error | Solution |
|-------|----------|
| "Connection refused" | Start backend: `python app.py` |
| "Admin access required" | Login with wallet 0xdf978465ee6dcf32 |
| "No vault deposit found" | Ensure all fees collected and deposited |
| "Vault already withdrawn" | Can only withdraw once per league |
| "No placements found" | Run `setup_test_placements.sql` |
| "Prizes already distributed" | Can only execute once per league |

### Reset Test League

To reset and test again:

```sql
-- Clear withdrawal records
DELETE FROM AgentExecutions
WHERE agent_type = 'vault_withdrawal'
AND execution_id LIKE 'vault_withdrawal_TEST_VAULT_001%';

-- Clear payout records
DELETE FROM PayoutDistributions
WHERE payout_id IN (
    SELECT payout_id FROM PayoutSchedules
    WHERE sleeper_league_id = 'TEST_VAULT_001'
);

DELETE FROM PayoutSchedules
WHERE sleeper_league_id = 'TEST_VAULT_001';
```

## 📚 Additional Resources

- **Quick Start:** [TESTING_QUICKSTART.md](TESTING_QUICKSTART.md)
- **Detailed Guide:** [TESTING_VAULT_PAYOUTS.md](TESTING_VAULT_PAYOUTS.md)
- **Flow Testnet:** https://testnet.flowscan.org/
- **IncrementFi Docs:** https://docs.increment.fi/

## 🎯 Next Steps

1. ✅ Test vault withdrawal system
2. ✅ Test prize distribution system
3. 🔄 Add UI buttons to admin dashboard
4. 🔄 Implement automated triggers (production)
5. 🔄 Add multi-sig approval (production)

## 📝 Notes

- All tests use Flow Testnet (no real money)
- Admin wallet: 0xdf978465ee6dcf32
- Test league: TEST_VAULT_001
- IncrementFi pool: 0x8aaca41f09eb1e3d