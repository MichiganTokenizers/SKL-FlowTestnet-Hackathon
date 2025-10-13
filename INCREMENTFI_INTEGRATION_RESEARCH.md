# IncrementFi Integration Research & Testing Strategy

## Research Summary (2025-10-09)

### IncrementFi Overview
IncrementFi is an All-In-One DeFi platform on Flow blockchain providing:
- **Decentralized Exchange (DEX)** - Swap/trade tokens
- **Money Market (Increment Earn)** - Lend/borrow with algorithmic interest rates
- **Liquid Staking** - Stake FLOW tokens
- **Yield Strategies** - Automated yield optimization

### Contract Addresses Found

#### Mainnet (Cadence)
**DEX Contracts:**
- SwapFactory: `0xb063c16cac85dbd1`
- SwapPair: `0xecbda466e7f191c7`
- SwapConfig: `0xb78ef7afa52ff906`
- SwapRouter: `0xa6850776a94e6551`
- PublicPriceOracle: `0xec67451f8a58216a`

**StableSwap DEX:**
- StableSwapFactory: `0xb063c16cac85dbd1`
- SwapConfig: `0xb78ef7afa52ff906`

#### Testnet (Cadence)
**DEX Contracts:**
- PublicPriceOracle: `0x8232ce4a3aff4e94`

**StableSwap DEX:**
- StableSwapFactory: `0x6ca93d49c45a249f`
- SwapPair: `0x7afd587a5d5e2efe`
- SwapConfig: `0x8d5b9dd833e176da`

### ⚠️ Critical Finding: Money Market Contract Addresses Not Found

**Issue:** The specific contract addresses for IncrementFi's **Money Market (lending/borrowing)** protocol were **NOT** found in public documentation.

**What We Know:**
- Money Market exists at: https://app.increment.fi/dashboard
- GitHub repo: https://github.com/IncrementFi/Money-Market
- Documentation: https://docs.increment.fi/protocols/decentralized-money-market
- Testnet supposed to exist but URL returns `ENOTFOUND`

**What We Don't Know:**
- Actual contract addresses for deposits/withdrawals
- Supported tokens on testnet (FLOW, USDF, FUSD?)
- Cadence transaction signatures for supply/borrow
- Minimum deposit amounts
- Lock-up periods or withdrawal restrictions
- Current APY rates on testnet

### Official Documentation Links
- **Main Docs:** https://docs.increment.fi/
- **Money Market:** https://docs.increment.fi/protocols/decentralized-money-market
- **GitHub:** https://github.com/IncrementFi/Money-Market
- **Security Audit:** https://increment-audit.s3.us-west-1.amazonaws.com/Audit+Report+-+Increment+Finance.pdf

---

## Recommended Testing Strategy: Two-Phase Approach

### Phase 1: Direct Wallet Testing (Immediate - No External Dependencies)

**Skip IncrementFi integration initially** and focus on core functionality:

#### 1A. Fee Collection Testing
```
User Wallets → SKL Wallet (0xdf978465ee6dcf32)
```

**Implementation:**
- ✅ **COMPLETED** - Already working in LeagueFees.jsx
- ✅ **TESTED** - Multiple user wallets tested on mainnet
- ✅ **VERIFIED** - Backend recording in `LeaguePayments` table confirmed
- ✅ **TRACKED** - Transaction IDs verified on Flowscan

**Status:** Production-ready, no additional testing needed for fee collection flow

#### 1B. Prize Payout Testing (NEW)
```
SKL Wallet → Winner Wallets (4 recipients)
```

**What to Build:**
1. **Cadence Transaction:** `distribute_prizes.cdc` ✅ (Already created)

2. **Backend API Endpoint:** `/admin/league/<league_id>/payouts/execute`
   ```python
   @app.route('/admin/league/<league_id>/payouts/execute', methods=['POST'])
   @admin_required
   def execute_payout(league_id):
       # Get payout schedule
       # Calculate splits (50%/30%/10%/10%)
       # Call Flow transaction via fcl or flow-py-sdk
       # Record distributions in PayoutDistributions table
       # Return transaction IDs
   ```

3. **Admin Dashboard Component:** Prize distribution UI

**Prize Distribution Structure:**
```
Collected Fees: 10.0 FLOW
Prize Pool: 10.0 FLOW (principal only - interest stays in SKL wallet)
Payouts:
  - 1st Place: 5.0 FLOW (50%)
  - 2nd Place: 3.0 FLOW (30%)
  - 3rd Place: 1.0 FLOW (10%)
  - Regular Season Winner: 1.0 FLOW (10%)
```

**Note:** Yield/interest earned from IncrementFi vaults remains in SKL wallet as platform revenue. Only the original principal (total league fees collected) is distributed as prizes.

### Phase 2: IncrementFi Yield Integration (Future - After Research)

**Once we have Money Market addresses:**

#### 2A. Deposit to Yield Vault
```
SKL Wallet → IncrementFi Money Market → Earn Interest
```

**Requirements:**
- [ ] Money Market contract address on testnet
- [ ] Supply transaction Cadence code
- [ ] Confirm FLOW/USDF is supported
- [ ] Test with 1.0 FLOW minimum deposit

#### 2B. Withdraw + Payout
```
IncrementFi Vault (Principal + Yield) → SKL Wallet → Winners (Principal Only)
```

**Test:**
- Deposit 10 FLOW, wait for yield accrual
- Withdraw 10.05 FLOW (0.05 = yield)
- Distribute 10.0 FLOW to winners (principal only)
- **Keep 0.05 FLOW yield in SKL wallet** as platform revenue
- Track yield separately in `YieldVaults.yield_earned` field

**Important:** Prize pool = Original league fees only. Interest remains with SKL.

---

## Immediate Next Steps

### Step 1: Create Prize Payout Cadence Script ✅
**File:** `backend/scripts/distribute_prizes.cdc`

**Test Locally:**
```bash
flow transactions send backend/scripts/distribute_prizes.cdc \
  --arg Address:[0xwinner1,0xwinner2,0xwinner3,0xregseason] \
  --arg UFix64:[5.0,3.0,1.0,1.0] \
  --arg String:"TEST_LEAGUE_001" \
  --signer testnet-account \
  --network testnet
```

### Step 2: Backend API for Payout Execution ✅
**File:** `backend/payout_routes.py`

**Endpoints:**
- `POST /admin/league/<league_id>/payouts/create` - Schedule a payout
- `POST /admin/league/<league_id>/payouts/<payout_id>/execute` - Execute distributions
- `GET /admin/payouts` - List all payouts (already exists)

### Step 3: Test Database Records ✅
```sql
-- Create test payout
INSERT INTO PayoutSchedules (
    payout_id, sleeper_league_id, season_year,
    total_prize_pool, payout_status, payout_date
) VALUES (
    'test-payout-001', 'TEST_LEAGUE_001', 9999,
    10.0, 'ready', '2025-10-15'
);

-- Record distributions
INSERT INTO PayoutDistributions (
    distribution_id, payout_id, wallet_address,
    payout_type, amount, percentage, status
) VALUES
    ('dist-001', 'test-payout-001', '0xwinner1', '1st_place', 5.0, 50.0, 'pending'),
    ('dist-002', 'test-payout-001', '0xwinner2', '2nd_place', 3.0, 30.0, 'pending'),
    ('dist-003', 'test-payout-001', '0xwinner3', '3rd_place', 1.0, 10.0, 'pending'),
    ('dist-004', 'test-payout-001', '0xregseason', 'regular_season_winner', 1.0, 10.0, 'pending');
```

### Step 4: Create Admin UI Component ✅
**File:** `frontend/src/components/admin/PayoutExecution.jsx`

**Features:**
- Show pending payouts
- Display calculated splits
- "Execute Payout" button
- Show transaction progress
- Link to Flowscan for each payout

### Step 5: End-to-End Test ✅
```bash
# 1. Setup test league
# 2. Collect fees from 5 users (10 FLOW total)
# 3. Mark season complete
# 4. Create payout schedule
# 5. Execute payout via admin dashboard
# 6. Verify winners received FLOW
# 7. Check all records in database
# 8. Verify on Flowscan testnet
```

---

## Alternative Yield Strategies (If IncrementFi Unavailable)

### Option 1: Flow Liquid Staking
- **Protocol:** IncrementFi Liquid Staking (separate from Money Market)
- **Stake FLOW** → Receive **stFLOW** → Earn staking rewards
- **Contract:** Available at https://app.increment.fi/staking

### Option 2: Manual "Virtual Yield"
- Keep funds in SKL wallet
- Manually add 5% "yield bonus" to prize pool from SKL treasury
- Simpler for MVP, no smart contract dependencies

### Option 3: Wait for IncrementFi Support
- Contact IncrementFi team for testnet Money Market addresses
- Discord: Check Flow Discord for IncrementFi channel
- Twitter: @incrementfi

---

## Testing Budget (Testnet FLOW)

**Per Test Cycle:**
- User fees: 5 users × 2 FLOW = 10 FLOW
- Gas fees: ~5 transactions × 0.001 FLOW = 0.005 FLOW
- Payout distribution: ~4 recipients × 0.001 FLOW = 0.004 FLOW

**Total per cycle:** ~10.01 FLOW

**Recommended:** Get 50 FLOW from testnet faucet for 5 full test cycles

**Faucet:** https://testnet-faucet.onflow.org/

---

## Success Metrics

### Phase 1 Complete When:
- ✅ 5 test users pay league fees successfully (DONE - tested on mainnet)
- ✅ SKL wallet receives 10 FLOW (DONE - verified)
- ✅ Backend records all payments (DONE - LeaguePayments table working)
- ⏳ Admin can trigger payout execution (IN PROGRESS)
- ⏳ 4 winners receive correct FLOW amounts (50%/30%/10%/10%)
- ⏳ All payout transactions visible on Flowscan
- ⏳ Database shows completed payout status

### Phase 2 Complete When:
- ✅ Funds deposited to IncrementFi vault
- ✅ Yield accrual tracked over time in database
- ✅ Withdrawal + payout works end-to-end
- ✅ Yield amount **retained by SKL wallet** (not distributed to winners)
- ✅ `YieldVaults` table accurately tracks principal vs yield

---

## Open Questions for IncrementFi Team

1. What are Money Market contract addresses on testnet?
2. Which tokens are supported? (FLOW, USDF, FUSD?)
3. Is there a minimum deposit amount?
4. What are current APY rates on testnet?
5. Any lock-up periods or withdrawal restrictions?
6. Can we get example Cadence transactions?
7. Is there a Discord/Telegram for developer support?

---

## Resources

- **Flow Testnet Faucet:** https://testnet-faucet.onflow.org/
- **Flowscan Testnet:** https://testnet.flowscan.io/
- **IncrementFi Docs:** https://docs.increment.fi/
- **IncrementFi GitHub:** https://github.com/IncrementFi/Money-Market
- **Flow Developer Docs:** https://developers.flow.com/
- **Our Testnet Wallet:** 0xdf978465ee6dcf32

---

## Conclusion

**Recommended Approach:**
1. **Immediate:** Build Phase 1 (direct wallet payouts) - fully testable today
2. **Parallel:** Continue researching IncrementFi Money Market addresses
3. **Future:** Add Phase 2 (yield integration) once contracts confirmed

This gives us a **working prize payout system** while we investigate the yield component.
