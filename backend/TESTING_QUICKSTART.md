# Quick Start Guide: Testing Vault Withdrawal & Prize Distribution

## TL;DR - Test in 3 Steps

```bash
# 1. Check if ready to test
python check_payout_prerequisites.py

# 2. Safe preview (no blockchain transactions)
python test_payout_preview.py

# 3. Full test (executes real transactions)
python test_vault_payouts.py
```

## What These Scripts Do

### 1. `check_payout_prerequisites.py`
**Checks if system is ready for testing**

Verifies:
- ✅ Vault deposit completed
- ✅ No prior withdrawal
- ✅ Placements recorded (1st, 2nd, 3rd, regular season)
- ✅ No prior payouts

```bash
python check_payout_prerequisites.py
```

**Example output:**
```
============================================================
  Summary
============================================================

✅ Vault deposit completed
✅ No prior withdrawal
✅ Placements recorded
✅ No prior payouts

✅ All prerequisites met!
```

### 2. `test_payout_preview.py`
**Preview payouts WITHOUT executing transactions (SAFE)**

- Logs in as admin
- Shows prize distribution breakdown
- No blockchain transactions

```bash
python test_payout_preview.py
```

**Example output:**
```
💰 Total Prize Pool: 100.0 FLOW
🏆 Number of Winners: 4

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

### 3. `test_vault_payouts.py`
**Complete flow with REAL blockchain transactions**

Steps through:
1. Login as admin
2. Withdraw from IncrementFi vault
3. Preview distributions
4. Execute payouts (with confirmation prompt)

```bash
python test_vault_payouts.py
```

⚠️ **WARNING**: Executes real testnet transactions!

## Testing Workflow

```
Start Here
    ↓
┌─────────────────────────────────────┐
│ check_payout_prerequisites.py       │
│ (Verify system is ready)            │
└───────────┬─────────────────────────┘
            ↓
      Prerequisites OK?
            ↓
           Yes
            ↓
┌─────────────────────────────────────┐
│ test_payout_preview.py              │
│ (Preview - Safe, no transactions)   │
└───────────┬─────────────────────────┘
            ↓
    Data looks correct?
            ↓
           Yes
            ↓
┌─────────────────────────────────────┐
│ test_vault_payouts.py               │
│ (Full test - EXECUTES TX)           │
└───────────┬─────────────────────────┘
            ↓
        Success!
```

## Prize Distribution

| Placement | % | Example (100 FLOW) |
|-----------|---|--------------------|
| 1st Place | 50% | 50 FLOW |
| 2nd Place | 30% | 30 FLOW |
| 3rd Place | 10% | 10 FLOW |
| Regular Season | 10% | 10 FLOW |

## Requirements

- Backend server running (`python app.py`)
- Admin wallet: 0xdf978465ee6dcf32
- League: TEST_VAULT_001
- Database: `/var/data/keeper.db`
- Flow CLI configured for testnet

## Troubleshooting

**Backend not running:**
```bash
cd backend
python app.py
```

**Prerequisites not met:**
```bash
# Run check to see what's missing
python check_payout_prerequisites.py

# Follow the action items shown
```

**Connection failed:**
- Check backend is running on localhost:5000
- Check database path in environment variables

## View Transactions

After executing, view on Flow Testnet:
- Explorer: https://testnet.flowscan.org/
- Search by transaction ID

## More Details

See [TESTING_VAULT_PAYOUTS.md](TESTING_VAULT_PAYOUTS.md) for:
- Manual testing with cURL
- Database verification queries
- Detailed troubleshooting
- Production considerations