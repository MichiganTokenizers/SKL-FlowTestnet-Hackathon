# Testnet Wallet Reference for TEST_VAULT_001

## Your Testnet Wallet Addresses

| Wallet # | Address | Team Name | Regular Season | Playoff Result | Prize | Amount |
|----------|---------|-----------|----------------|----------------|-------|--------|
| **1** | `0xb647c8ffe7d05b51` | Regular Season Kings | 12-2 (1st) | Lost in playoffs | 🏅 Regular Season Winner | **100 FLOW** |
| **2** | `0x447414116f2e51ef` | Championship Champions | 11-3 (2nd) | **Won Championship!** | 🏆 1st Place | **500 FLOW** |
| **3** | `0xa9f313f3c175ebb5` | Runner-Up Rivals | 10-4 (3rd) | Lost in finals | 🥈 2nd Place | **300 FLOW** |
| **4** | `0x5bc0cf1d498be10b` | Third Place Threats | 9-5 (4th) | Won 3rd place game | 🥉 3rd Place | **100 FLOW** |
| **5** | `0xbfa776c05871e1d4` | Playoff Participants | 8-6 (5th) | Lost both playoff games | ❌ No Prize | **0 FLOW** |

## Prize Summary

**Total Prizes:** 1000 FLOW

| Prize Category | Winner | Address | Amount | Percentage |
|----------------|--------|---------|--------|------------|
| 1st Place | Wallet 2 | `0x447414116f2e51ef` | 500 FLOW | 50% |
| 2nd Place | Wallet 3 | `0xa9f313f3c175ebb5` | 300 FLOW | 30% |
| 3rd Place | Wallet 4 | `0x5bc0cf1d498be10b` | 100 FLOW | 10% |
| Regular Season | Wallet 1 | `0xb647c8ffe7d05b51` | 100 FLOW | 10% |
| **TOTAL** | **4 winners** | - | **1000 FLOW** | **100%** |

## Test Flow Actions Required

### 1. Pay League Fees (You do this via UI)
Connect each wallet and pay 100 FLOW:
- [ ] Wallet 1 (`0xb647c8ffe7d05b51`) - Pay 100 FLOW
- [ ] Wallet 2 (`0x447414116f2e51ef`) - Pay 100 FLOW
- [ ] Wallet 3 (`0xa9f313f3c175ebb5`) - Pay 100 FLOW
- [ ] Wallet 4 (`0x5bc0cf1d498be10b`) - Pay 100 FLOW
- [ ] Wallet 5 (`0xbfa776c05871e1d4`) - Pay 100 FLOW

**Total Collected:** 1000 FLOW (500 from real wallets + 500 from fake wallets)

### 2. Verify Prize Distribution (After payout executed)
Check balances on Flow testnet:
```bash
# Check Wallet 2 (should receive 500 FLOW)
flow scripts execute backend/scripts/check_balance.cdc 0x447414116f2e51ef --network testnet

# Check Wallet 3 (should receive 300 FLOW)
flow scripts execute backend/scripts/check_balance.cdc 0xa9f313f3c175ebb5 --network testnet

# Check Wallet 4 (should receive 100 FLOW)
flow scripts execute backend/scripts/check_balance.cdc 0x5bc0cf1d498be10b --network testnet

# Check Wallet 1 (should receive 100 FLOW)
flow scripts execute backend/scripts/check_balance.cdc 0xb647c8ffe7d05b51 --network testnet

# Check Wallet 5 (should receive 0 FLOW - no prize)
flow scripts execute backend/scripts/check_balance.cdc 0xbfa776c05871e1d4 --network testnet
```

### 3. View Transactions on Flowscan
After payout execution, view the prize distribution transaction:
- **Transaction URL:** `https://testnet.flowscan.io/tx/{transaction_id}`
- Should show 4 transfer events to your wallet addresses

## Database Roster IDs

| Wallet Address | Roster ID | Team Name |
|----------------|-----------|-----------|
| `0xb647c8ffe7d05b51` | `6` | Regular Season Kings |
| `0x447414116f2e51ef` | `7` | Championship Champions |
| `0xa9f313f3c175ebb5` | `8` | Runner-Up Rivals |
| `0x5bc0cf1d498be10b` | `9` | Third Place Threats |
| `0xbfa776c05871e1d4` | `10` | Playoff Participants |

## Expected Balance Changes

### Before Any Transactions
```
Wallet 1: X FLOW
Wallet 2: Y FLOW
Wallet 3: Z FLOW
Wallet 4: A FLOW
Wallet 5: B FLOW
```

### After Paying League Fees (Each pays 100 FLOW)
```
Wallet 1: X - 100 FLOW
Wallet 2: Y - 100 FLOW
Wallet 3: Z - 100 FLOW
Wallet 4: A - 100 FLOW
Wallet 5: B - 100 FLOW
```

### After Prize Distribution
```
Wallet 1: X - 100 + 100 = X (net 0)
Wallet 2: Y - 100 + 500 = Y + 400 FLOW (net +400) 🎉
Wallet 3: Z - 100 + 300 = Z + 200 FLOW (net +200) 🎉
Wallet 4: A - 100 + 100 = A (net 0)
Wallet 5: B - 100 + 0 = B - 100 FLOW (net -100)
```

**Net Winners:**
- Wallet 2: +400 FLOW profit 🏆
- Wallet 3: +200 FLOW profit 🥈

## Fake Wallets (No Interaction Required)

These wallets show as "paid" in the database but require no action from you:

| Fake Wallet | Status | Amount | Notes |
|-------------|--------|--------|-------|
| `0xFAKE1111...` | paid | 100 FLOW | Dynasty Duds (5-9) - No prize |
| `0xFAKE2222...` | paid | 100 FLOW | Mediocre Managers (4-10) - No prize |
| `0xFAKE3333...` | paid | 100 FLOW | Playoff Pretenders (3-11) - No prize |
| `0xFAKE4444...` | paid | 100 FLOW | Touchdown Turnovers (2-12) - No prize |
| `0xFAKE5555...` | paid | 100 FLOW | Fantasy Failures (1-13) - No prize |

All fake wallets are losers - they exist only for database testing!
