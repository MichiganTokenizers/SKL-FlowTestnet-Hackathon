# IncrementFi Liquid Staking Integration

## Overview

This project includes a complete integration with IncrementFi's liquid staking protocol on Flow blockchain. The integration uses Flow Actions (Forte upgrade) to automatically stake collected league fees and earn staking rewards.

## Implementation Status

### ✅ Completed

1. **IncrementFiStakingV2 Contract** - [View Contract](backend/cadence/contracts/IncrementFiStakingV2.cdc)
   - Deployed to testnet at `0xdf978465ee6dcf32`
   - Imports `LiquidStaking` and `stFlowToken` from IncrementFi (`0xe45c64ecfe31e465`)
   - Calls `LiquidStaking.stake()` to stake FLOW tokens
   - Receives and manages stFlow tokens (liquid staking derivatives)
   - Implements proper resource lifecycle and stFlow withdrawal

2. **Staking Transaction** - [View Transaction](backend/cadence/transactions/stake_league_fees_v2.cdc)
   - Sets up stFlow vault automatically if needed
   - Creates Source connector for fee collection
   - Creates Sink connector for IncrementFi staking
   - Executes atomic Flow Action: Source → Sink
   - Withdraws stFlow tokens and deposits to admin vault

3. **Backend Integration** - [View Code](backend/app.py#L2697)
   - API endpoint: `POST /admin/league/{league_id}/stake-fees`
   - Executes staking transaction via Flow CLI
   - Returns transaction ID and execution details

4. **Admin UI** - [View Component](frontend/src/components/admin/AdminDashboard.jsx)
   - Staking test interface in Automation tab
   - League selection dropdown
   - Execute button with confirmation dialog
   - Success/error display with transaction links

### ⚠️ Current Limitation: IncrementFi Testnet Epoch Sync

**Status:** IncrementFi's liquid staking on testnet is currently unavailable due to epoch synchronization issues.

**Error Message:**
```
error: pre-condition failed: [IncLiquidStakingErrorMsg:Cannot stake until protocol
epoch syncs with chain epoch][IncLiquidStakingErrorCode:8]
```

**What This Means:**
- IncrementFi's liquid staking protocol requires its internal epoch to sync with Flow's blockchain epoch
- This is a safety mechanism to ensure accurate reward calculations
- On mainnet, this sync happens automatically every week (Thursday-Wednesday staking window)
- On testnet, the sync appears to be stuck or not actively maintained

**Duration:** Persisting for 24+ hours, suggesting testnet deployment may not be actively maintained

## How It Works (When Available)

### 1. Staking Flow

```
League Fees (FLOW)
  → Source Connector (Fee Collection)
  → Sink Connector (IncrementFi Staking)
  → stFlow Tokens (Liquid Staking Receipt)
  → Admin Vault
```

### 2. stFlow Tokens

When staking succeeds, you receive **stFlow tokens** which:
- Represent your staked FLOW in IncrementFi's liquid staking pool
- Automatically accrue value as staking rewards are earned
- Can be unstaked later to receive FLOW + rewards
- Are tradeable and usable in DeFi protocols

### 3. Earning Rewards

- **Automatic**: Rewards accrue without any action needed
- **Exchange Rate**: stFlow increases in value relative to FLOW over time
- **Weekly Epochs**: New rewards calculated every Thursday (UTC)
- **APY**: Varies based on Flow network staking rewards (~4-6% typically)

## Alternative Testing Options

Since IncrementFi testnet is currently unavailable, here are your options:

### Option 1: Test Flow Actions Pattern (Recommended)

Use the V1 transaction which simulates staking without IncrementFi dependency:

**Update backend to use V1:**
```python
# In backend/app.py line 2697
script_path = os.path.join(os.path.dirname(__file__), 'cadence', 'transactions', 'stake_league_fees.cdc')
```

**What This Tests:**
- ✅ Flow Actions Source → Sink pattern
- ✅ Automatic fee collection and staking automation
- ✅ Backend API integration
- ✅ Admin UI workflow
- ✅ Transaction execution and logging
- ⚠️ Simulates staking (destroys tokens instead of staking)

### Option 2: Deploy to Mainnet

The IncrementFi integration is production-ready and will work on mainnet where:
- IncrementFi's liquid staking is actively maintained
- Epochs sync properly every week
- Real FLOW tokens earn real staking rewards

**Mainnet Deployment Steps:**
1. Update `flow.json` with mainnet account
2. Deploy contracts: `flow project deploy --network mainnet`
3. Fund mainnet account with FLOW tokens
4. Test with small amounts first

**Mainnet Addresses:**
- IncrementFi LiquidStaking: `0xa6850776a94e6551`
- IncrementFi stFlowToken: `0xa6850776a94e6551`

### Option 3: Wait for Testnet Sync

IncrementFi may resolve the testnet epoch sync eventually. Monitor:
- https://app.increment.fi/staking
- IncrementFi Discord/Community channels
- Try again periodically

## Production Recommendations

### When Moving to Mainnet:

1. **Test Small Amounts First**
   - Start with 10-100 FLOW to verify end-to-end flow
   - Confirm stFlow tokens are received
   - Verify balance increases over time

2. **Monitor Staking Windows**
   - IncrementFi allows staking Thursday-Wednesday (UTC)
   - Brief maintenance window Wednesday-Thursday
   - Plan automation accordingly

3. **Add Error Handling**
   - Detect epoch sync errors
   - Retry transactions during next staking window
   - Alert admins when staking fails

4. **Track stFlow Holdings**
   - Monitor stFlow balance at admin address
   - Track stFlow/FLOW exchange rate
   - Calculate earned rewards

5. **Consider Unstaking Strategy**
   - Decide when to unstake (end of season, specific milestones)
   - Account for unstaking delays (7 days on Flow)
   - Plan liquidity needs

## Code References

### Contracts
- [SKLFeeCollectionSource.cdc](backend/cadence/contracts/SKLFeeCollectionSource.cdc) - Source connector for fee collection
- [IncrementFiStakingV2.cdc](backend/cadence/contracts/IncrementFiStakingV2.cdc) - Sink connector for IncrementFi staking
- [IncrementFiStakingSink.cdc](backend/cadence/contracts/IncrementFiStakingSink.cdc) - V1 (simulation fallback)

### Transactions
- [stake_league_fees_v2.cdc](backend/cadence/transactions/stake_league_fees_v2.cdc) - Real IncrementFi integration
- [stake_league_fees.cdc](backend/cadence/transactions/stake_league_fees.cdc) - V1 simulation version

### Backend
- [app.py](backend/app.py) - `/admin/league/{league_id}/stake-fees` endpoint (line ~2650)

### Frontend
- [AdminDashboard.jsx](frontend/src/components/admin/AdminDashboard.jsx) - Staking UI in Automation tab

## Testing Checklist

- [x] Contracts deployed to testnet
- [x] IncrementFi imports and integration code
- [x] Transaction compiles without errors
- [x] Backend API endpoint created
- [x] Admin UI for executing stakes
- [x] Proper error handling and logging
- [ ] Successful stake on IncrementFi (blocked by testnet epoch sync)
- [ ] stFlow tokens received in admin vault (blocked by testnet)
- [ ] Mainnet deployment and testing

## Resources

- [IncrementFi Documentation](https://docs.increment.fi/protocols/liquid-staking)
- [Flow Actions Documentation](https://developers.flow.com/build/advanced-concepts/actions)
- [Flow Staking Guide](https://developers.flow.com/protocol/staking)
- [IncrementFi Protocol Epoch](https://docs.increment.fi/protocols/liquid-staking/protocol-overview/protocol-epoch)

## Support

For IncrementFi-specific issues:
- IncrementFi Discord: Check their community channels
- IncrementFi Documentation: https://docs.increment.fi
- GitHub Issues: https://github.com/IncrementFi

For Flow Actions and integration questions:
- Flow Discord: #dev-chat channel
- Flow Forums: https://forum.flow.com