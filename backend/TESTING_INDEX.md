# Testing Tools Index

Complete reference for all vault withdrawal and prize distribution testing tools.

## 🎯 Quick Commands

```bash
# View current status
python view_league_status.py

# Check if ready to test
python check_payout_prerequisites.py

# Safe preview (no transactions)
python test_payout_preview.py

# Full test (executes transactions)
python test_vault_payouts.py
```

## 📁 All Testing Files

### Python Scripts

| Script | Purpose | Safe? |
|--------|---------|-------|
| **view_league_status.py** | View current league status | ✅ Yes |
| **check_payout_prerequisites.py** | Verify system readiness | ✅ Yes |
| **test_payout_preview.py** | Preview payouts only | ✅ Yes |
| **test_vault_payouts.py** | Full test with blockchain TX | ⚠️ No |

### SQL Scripts

| Script | Purpose |
|--------|---------|
| **setup_test_placements.sql** | Setup placement test data |

### Documentation

| Document | Content |
|----------|---------|
| **TESTING_QUICKSTART.md** | Quick start guide |
| **TESTING_VAULT_PAYOUTS.md** | Detailed testing guide |
| **README_VAULT_TESTING.md** | Complete testing suite overview |
| **TESTING_INDEX.md** | This file |

## 🔍 Script Details

### 1. view_league_status.py

**Quick status viewer for TEST_VAULT_001**

Shows:
- Vault deposit status and amount
- Withdrawal status and transaction ID
- All placements with team/user info
- Payout status and distributions
- Next action recommendation

```bash
python view_league_status.py
```

**Output:**
```
💰 VAULT DEPOSIT
✅ Status: completed
   Amount: 100.0 FLOW
   TX ID: 0xabc123...

🏦 VAULT WITHDRAWAL
✅ No withdrawal yet (ready to withdraw)

🏆 PLACEMENTS
#1 1ST PLACE
   Team: TeamAlpha
   ...

📊 SUMMARY
✅ Ready to withdraw from vault
   Run: python test_vault_payouts.py
```

### 2. check_payout_prerequisites.py

**Comprehensive prerequisite checker**

Verifies:
- ✅ Vault deposit completed
- ✅ No prior withdrawal
- ✅ All 4 placements recorded
- ✅ No prior payouts

```bash
python check_payout_prerequisites.py
```

Returns exit code 0 if all checks pass, 1 if any fail.

### 3. test_payout_preview.py

**Safe preview - NO blockchain transactions**

- Authenticates as admin
- Fetches payout preview
- Displays distribution breakdown
- Validates totals

```bash
python test_payout_preview.py
```

**Safe to run repeatedly** - no state changes.

### 4. test_vault_payouts.py

**Full test suite - EXECUTES blockchain transactions**

4-step process:
1. Login as admin
2. Withdraw from IncrementFi vault
3. Preview distributions
4. Execute payouts (with confirmation)

```bash
python test_vault_payouts.py
```

**⚠️ WARNING**: Executes real testnet transactions!

## 🛠️ Setup Workflow

```bash
# 1. Check existing data
python view_league_status.py

# 2. Setup placements if needed
sqlite3 /var/data/keeper.db < setup_test_placements.sql

# 3. Verify prerequisites
python check_payout_prerequisites.py

# 4. Preview (safe)
python test_payout_preview.py

# 5. Execute (real transactions)
python test_vault_payouts.py
```

## 🧪 Testing Matrix

| Scenario | Command | Blockchain TX? | Idempotent? |
|----------|---------|----------------|-------------|
| View status | `view_league_status.py` | No | Yes |
| Check ready | `check_payout_prerequisites.py` | No | Yes |
| Preview payouts | `test_payout_preview.py` | No | Yes |
| Withdraw vault | Part of `test_vault_payouts.py` | Yes | No |
| Execute payouts | Part of `test_vault_payouts.py` | Yes | No |

## 📊 Database Tables Used

| Table | Purpose |
|-------|---------|
| **AgentExecutions** | Tracks vault deposits and withdrawals |
| **LeaguePlacements** | Stores final rankings for prize distribution |
| **PayoutSchedules** | Records payout execution metadata |
| **PayoutDistributions** | Tracks individual prize distributions |

## 🎭 Test Scenarios

### Scenario 1: First Time Test (Happy Path)

```bash
# 1. Fresh state
python view_league_status.py
# Shows: Deposit complete, no withdrawal, no payouts

# 2. Check prerequisites
python check_payout_prerequisites.py
# Shows: All checks pass

# 3. Preview
python test_payout_preview.py
# Shows: 4 distributions, 100 FLOW total

# 4. Execute
python test_vault_payouts.py
# Executes: Withdrawal + Payouts
```

### Scenario 2: Already Withdrawn

```bash
python view_league_status.py
# Shows: Withdrawal complete, ready for payouts

python test_vault_payouts.py
# Will skip withdrawal, proceed to payouts
```

### Scenario 3: Already Completed

```bash
python view_league_status.py
# Shows: All operations completed

python test_vault_payouts.py
# Will fail: "Vault already withdrawn" or "Prizes already distributed"
```

## 🔄 Reset for Re-testing

To test multiple times:

```sql
-- Clear withdrawal
DELETE FROM AgentExecutions
WHERE agent_type = 'vault_withdrawal'
AND execution_id LIKE 'vault_withdrawal_TEST_VAULT_001%';

-- Clear payouts
DELETE FROM PayoutDistributions
WHERE payout_id IN (
    SELECT payout_id FROM PayoutSchedules
    WHERE sleeper_league_id = 'TEST_VAULT_001'
);

DELETE FROM PayoutSchedules
WHERE sleeper_league_id = 'TEST_VAULT_001';
```

Then run tests again.

## 🌐 Flow Testnet Links

After executing transactions:

- **Explorer**: https://testnet.flowscan.org/
- **Transaction search**: Search by TX ID from script output
- **Account view**: View admin wallet 0xdf978465ee6dcf32
- **IncrementFi pool**: 0x8aaca41f09eb1e3d

## 📝 Common Tasks

### Check if ready to test
```bash
python check_payout_prerequisites.py && echo "Ready!"
```

### Quick status check
```bash
python view_league_status.py
```

### Safe preview without asking
```bash
python test_payout_preview.py 2>/dev/null | grep -E "(FLOW|✅|❌)"
```

### View transaction on explorer
```bash
# After test_vault_payouts.py, get TX ID and:
# https://testnet.flowscan.org/transaction/<TX_ID>
```

## 🐛 Debugging

Enable verbose output:

```bash
# Set environment variable
export DEBUG=1

# Run scripts
python test_vault_payouts.py
```

Check logs:
```bash
# Backend logs
tail -f backend.log

# Or if running in terminal
python app.py  # See real-time logs
```

## 📞 Support

If tests fail:

1. **Check status first**: `python view_league_status.py`
2. **Verify prerequisites**: `python check_payout_prerequisites.py`
3. **Check backend logs**: Look for errors in app.py output
4. **Verify database**: Check tables have correct data
5. **Check Flow CLI**: Ensure flow.json is configured correctly

## 🎯 Success Criteria

All tests pass when:

- ✅ `check_payout_prerequisites.py` exits with code 0
- ✅ `test_payout_preview.py` shows 4 distributions
- ✅ `test_vault_payouts.py` completes all 4 steps
- ✅ Transactions visible on Flow testnet explorer
- ✅ Database updated with completed status
- ✅ `view_league_status.py` shows "All operations completed!"

---

**Last Updated**: 2025-01-15
**Test League**: TEST_VAULT_001
**Admin Wallet**: 0xdf978465ee6dcf32