# Testing Vault Withdrawal & Prize Distribution

This guide explains how to test the vault withdrawal and prize distribution system for demo purposes.

## Overview

The system has three main endpoints:

1. **POST** `/admin/league/<league_id>/vault/withdraw` - Withdraw funds from IncrementFi vault
2. **GET** `/admin/league/<league_id>/payouts/preview` - Preview prize distributions (safe, no blockchain TX)
3. **POST** `/admin/league/<league_id>/payouts/execute` - Execute prize distributions (sends real transactions)

## Prerequisites

Before testing, ensure:

1. **Backend server is running**:
   ```bash
   cd backend
   python app.py
   ```

2. **Test league setup** (`TEST_VAULT_001`):
   - All fees collected from teams
   - Vault deposit completed (funds in IncrementFi)
   - Placements recorded in `LeaguePlacements` table

3. **Admin wallet**: 0xdf978465ee6dcf32 (SKL testnet account)

4. **Flow CLI configured** with testnet account in `flow.json`

## Test Scripts

### 1. Quick Preview Test (Recommended First)

**Safe to run - NO blockchain transactions**

```bash
python test_payout_preview.py
```

This script:
- ✅ Logs in as admin
- ✅ Previews payout distributions
- ✅ Shows breakdown of prize splits
- ❌ Does NOT execute any blockchain transactions

**Example output:**
```
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
  Wallet:     0x1234...
  Amount:     50.00 FLOW (50%)

2ND PLACE
  Username:   TeamBeta
  Wallet:     0x5678...
  Amount:     30.00 FLOW (30%)
...
```

### 2. Full Test (Executes Blockchain Transactions)

**⚠️ WARNING: This sends REAL testnet transactions**

```bash
python test_vault_payouts.py
```

This script performs the complete flow:

1. **Login** as admin (0xdf978465ee6dcf32)
2. **Withdraw** from IncrementFi vault
3. **Preview** prize distributions
4. **Execute** prize distributions (with confirmation prompt)

**Steps:**

```bash
# The script will walk through each step
============================================================
  STEP 1: Admin Login
============================================================

✅ Logged in successfully!

============================================================
  STEP 2: Withdraw from Vault
============================================================

✅ Vault withdrawal successful!
ℹ️  Amount withdrawn: 100.0 FLOW
ℹ️  Transaction ID: 0xabc123...
ℹ️  View on Flow Testnet: https://testnet.flowscan.org/transaction/0xabc123...

============================================================
  STEP 3: Preview Prize Distributions
============================================================

✅ Preview loaded successfully!
...

============================================================
  STEP 4: Execute Prize Distributions
============================================================

⚠️  WARNING: This will execute REAL blockchain transactions!
Type 'YES' to continue with payout execution: YES

✅ Prize distribution executed successfully!
ℹ️  Transaction ID: 0xdef456...
```

## Manual Testing with cURL

### 1. Login as Admin

```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"walletAddress": "0xdf978465ee6dcf32"}'
```

Save the `sessionToken` from the response.

### 2. Preview Payouts (Safe)

```bash
curl -X GET http://localhost:5000/admin/league/TEST_VAULT_001/payouts/preview \
  -H "Authorization: YOUR_SESSION_TOKEN_HERE"
```

### 3. Withdraw from Vault

```bash
curl -X POST http://localhost:5000/admin/league/TEST_VAULT_001/vault/withdraw \
  -H "Content-Type: application/json" \
  -H "Authorization: YOUR_SESSION_TOKEN_HERE"
```

### 4. Execute Payouts

```bash
curl -X POST http://localhost:5000/admin/league/TEST_VAULT_001/payouts/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: YOUR_SESSION_TOKEN_HERE"
```

## Database Verification

After running tests, check the database:

```sql
-- Check vault withdrawal record
SELECT * FROM AgentExecutions
WHERE agent_type = 'vault_withdrawal'
ORDER BY created_at DESC LIMIT 1;

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

## Prize Distribution Logic

The system distributes prizes as follows:

| Placement | Percentage | Example (100 FLOW) |
|-----------|------------|-------------------|
| 1st Place | 50% | 50 FLOW |
| 2nd Place | 30% | 30 FLOW |
| 3rd Place | 10% | 10 FLOW |
| Regular Season Winner | 10% | 10 FLOW |

## Troubleshooting

### "Admin access required"
- Ensure you're logged in with wallet 0xdf978465ee6dcf32
- Check that session token is valid

### "No completed vault deposit found"
- Verify vault deposit exists in `AgentExecutions` table
- Ensure status is 'completed'

### "Vault already withdrawn for this league"
- Each league can only be withdrawn once
- Check `AgentExecutions` for existing 'vault_withdrawal' records

### "No placements found for this league"
- Populate `LeaguePlacements` table with winner data
- Ensure records exist for 1st, 2nd, 3rd place, and regular season winner

### "Prizes already distributed for this league"
- Each league can only execute payouts once
- Check `PayoutSchedules` for existing 'completed' records

## Flow Testnet Explorer

View your transactions on Flow Testnet:
- Testnet Explorer: https://testnet.flowscan.org/
- Search by transaction ID to see details

## Next Steps

1. **Test Preview** - Run `test_payout_preview.py` first to verify data
2. **Check Database** - Ensure all prerequisites are met
3. **Test Withdrawal** - Run `test_vault_payouts.py` for full flow
4. **Verify on Chain** - Check Flow Testnet explorer for transactions
5. **Admin Dashboard** - Add UI buttons to trigger these endpoints

## Production Considerations

For production deployment:

1. **Automated Triggers**: Replace manual endpoints with scheduled jobs
2. **Multi-sig Approval**: Require multiple admin approvals for large payouts
3. **Notification System**: Alert winners when prizes are distributed
4. **Audit Trail**: Log all operations with timestamps and admin IDs
5. **Rollback Plan**: Implement emergency procedures for failed transactions