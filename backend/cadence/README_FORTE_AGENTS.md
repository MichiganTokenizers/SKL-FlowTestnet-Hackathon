# SKL Vault Deposit Automation with Flow Agents & Actions (Forte)

## Overview

This directory contains the Flow Actions and Agents implementation for automating SKL league fee deposits to IncrementFi yield vaults. This replaces the previous Python backend trigger system with fully decentralized, on-chain automation.

## Architecture

### Flow Actions (Composable Connectors)

**1. SKLFeeCollectionSource.cdc** - Source Action
- Implements the `Source` interface from Flow Actions
- Aggregates collected league fees from the admin vault
- Checks if all teams have paid their fees
- Provides FLOW tokens on-demand for deposit

**2. IncrementFiVaultSink.cdc** - Sink Action
- Implements the `Sink` interface from Flow Actions
- Accepts FLOW tokens and deposits to IncrementFi LendingPool
- Includes capacity limits and graceful no-op handling
- Emits events for backend tracking

### Flow Agent (Transaction Handler)

**3. SKLVaultDepositAgent.cdc** - Agent Resource
- Implements `FlowTransactionScheduler.TransactionHandler`
- Composes Source → Sink workflow
- Executes automatically at scheduled time
- Handles errors gracefully with event emissions

### Scheduling Transaction

**4. schedule_vault_deposit_agent.cdc** - Setup Transaction
- Creates the agent resource
- Initializes with league fee data
- Schedules execution via FlowTransactionScheduler
- Stores agent in account storage

## Execution Flow

```
1. Admin triggers scheduling transaction
   ↓
2. Agent created with league data
   ↓
3. Agent scheduled for future execution
   ↓
4. [TIME PASSES]
   ↓
5. Flow blockchain automatically executes agent
   ↓
6. Agent checks if all fees collected (Source)
   ↓
7. Agent withdraws fees from admin vault (Source)
   ↓
8. Agent deposits to IncrementFi (Sink)
   ↓
9. Events emitted for backend tracking
   ↓
10. Agent marks itself as executed
```

## Deployment

### Prerequisites

1. Flow CLI installed
2. Testnet account with FLOW tokens
3. Account configured in `flow.json`
4. Scheduled Transactions enabled on testnet (Forte upgrade)

### Contract Deployment

```bash
# Deploy Source connector
flow accounts add-contract SKLFeeCollectionSource \
  backend/cadence/contracts/SKLFeeCollectionSource.cdc \
  --signer testnet-account \
  --network testnet

# Deploy Sink connector
flow accounts add-contract IncrementFiVaultSink \
  backend/cadence/contracts/IncrementFiVaultSink.cdc \
  --signer testnet-account \
  --network testnet

# Deploy Agent handler
flow accounts add-contract SKLVaultDepositAgent \
  backend/cadence/contracts/SKLVaultDepositAgent.cdc \
  --signer testnet-account \
  --network testnet
```

### Scheduling an Agent

```bash
# Schedule vault deposit for a league
flow transactions send \
  backend/cadence/transactions/schedule_vault_deposit_agent.cdc \
  --args-json '[
    {
      "type": "String",
      "value": "TEST_VAULT_001"
    },
    {
      "type": "Address",
      "value": "0x8aaca41f09eb1e3d"
    },
    {
      "type": "Int",
      "value": "10"
    },
    {
      "type": "Int",
      "value": "10"
    },
    {
      "type": "UFix64",
      "value": "500.0"
    },
    {
      "type": "UFix64",
      "value": "3600.0"
    },
    {
      "type": "String",
      "value": "Medium"
    },
    {
      "type": "UInt64",
      "value": "1000"
    },
    {
      "type": "UFix64",
      "value": "1.0"
    },
    {
      "type": "UFix64",
      "value": "0.0"
    }
  ]' \
  --signer testnet-account \
  --network testnet
```

## Backend Integration

### Python Backend Changes

The Python backend (`app.py`) needs to:

1. **Remove immediate trigger** from fee payment endpoint
2. **Add agent scheduling endpoint** for admin use
3. **Listen for agent events** to update database
4. **Provide admin UI** to schedule agents

### Event Listening

Events to monitor:
- `SKLVaultDepositAgent.AgentCreated` - Agent scheduled
- `SKLVaultDepositAgent.AgentExecuted` - Agent completed successfully
- `SKLVaultDepositAgent.AgentExecutionFailed` - Agent failed
- `SKLFeeCollectionSource.FeesCollected` - Fees withdrawn
- `IncrementFiVaultSink.TokensDeposited` - Tokens deposited to vault

### Database Updates

`AgentExecutions` table should track:
- `execution_id`: Agent ID from Cadence
- `agent_type`: 'vault_deposit_scheduled'
- `status`: 'scheduled' → 'completed'/'failed'
- `trigger_time`: When scheduled
- `execution_time`: When executed
- `result_data`: JSON with amounts, transaction IDs, events

## Testing

### Test on Flow Emulator

```bash
# Start emulator
flow emulator

# Deploy contracts
flow project deploy --network emulator

# Run test transaction
flow transactions send \
  backend/cadence/transactions/schedule_vault_deposit_agent.cdc \
  --args-json '...' \
  --signer emulator-account \
  --network emulator
```

### Test on Testnet

1. Use `TEST_VAULT_001` league for testing
2. Schedule agent with 5-minute delay
3. Monitor Flow testnet explorer for execution
4. Verify IncrementFi balance increased
5. Check backend events were captured

## Benefits vs Python Trigger

| Aspect | Python Backend | Flow Agents (Forte) |
|--------|---------------|---------------------|
| Execution | Requires server running | Runs on Flow blockchain |
| Reliability | Server downtime breaks it | Guaranteed execution |
| Decentralization | Centralized | Fully decentralized |
| Composability | Tightly coupled | Reusable Actions |
| Gas Costs | Transaction per trigger | Single scheduled transaction |
| Monitoring | Backend logs | On-chain events |

## Important Notes

### Forte Development Status

⚠️ **Scheduled Transactions are under active development**
- Currently available on testnet only
- FLIP 330 and FLIP 339 may introduce breaking changes
- Test thoroughly before production use
- Monitor Flow developer docs for updates

### Contract Addresses

Update these addresses in the contracts once Forte contracts are deployed to testnet:
- `FlowTransactionScheduler`: TBD
- `FlowTransactionSchedulerUtils`: TBD

Check Flow docs for latest testnet addresses:
https://developers.flow.com/blockchain-development-tutorials/forte/scheduled-transactions

### Fee Management

Scheduled transactions require fees:
- Admin account must have sufficient FLOW
- Fees are deducted when scheduling
- Failed executions do not refund fees
- Budget ~1-5 FLOW per scheduled transaction

## Troubleshooting

### Agent Not Executing

1. Check scheduled time hasn't passed
2. Verify account has scheduled transaction capability
3. Check agent status via public capability
4. Review Flow testnet explorer for transaction logs

### Execution Failed

1. Check `AgentExecutionFailed` event for reason
2. Verify all teams have paid fees
3. Confirm admin vault has sufficient balance
4. Check IncrementFi pool is accepting deposits

### Cannot Schedule

1. Verify Forte upgrade is live on testnet
2. Check account has sufficient FLOW for fees
3. Confirm contracts are deployed correctly
4. Review transaction errors in Flow CLI

## Resources

- **Flow Actions**: https://developers.flow.com/blockchain-development-tutorials/flow-actions
- **Scheduled Transactions**: https://developers.flow.com/blockchain-development-tutorials/forte/scheduled-transactions
- **Flow Actions Scaffold**: https://github.com/onflow/flow-actions-scaffold
- **FLIP 330 (Scheduled Tx)**: https://github.com/onflow/flips/pull/331
- **FLIP 339 (Actions)**: https://github.com/onflow/flips/pull/339
- **IncrementFi Docs**: https://docs.incrementfi.org/

## Next Steps

1. Deploy contracts to testnet
2. Test with TEST_VAULT_001 league
3. Integrate Python backend scheduling endpoint
4. Build admin UI for agent management
5. Monitor agents in production
6. Gradually migrate from Python triggers

---

**Built with Flow Forte Upgrade** 🌊🤖
