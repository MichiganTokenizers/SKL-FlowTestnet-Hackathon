# Flow Testnet Migration Guide

## Overview
This project has been migrated from Flow mainnet to Flow testnet to enable development and testing of Actions & Agents features.

## What Changed

### 1. Frontend Configuration ([frontend/src/config.js](frontend/src/config.js))
```javascript
// Updated to testnet endpoints
"accessNode.api": "https://rest-testnet.onflow.org"
"discovery.wallet": "https://fcl-discovery.onflow.org/testnet/authn"

// Updated SKL wallet address
SKL_PAYMENT_WALLET_ADDRESS = "0xdf978465ee6dcf32"
```

### 2. Flow Configuration ([flow.json](flow.json))
- Added `testnet-account` with address `0xdf978465ee6dcf32`
- Added testnet deployment configuration
- **IMPORTANT**: You need to create `testnet-account.pkey` file with your private key

### 3. Cadence Contracts ([backend/scripts/setup_account.cdc](backend/scripts/setup_account.cdc))
Updated contract addresses to testnet:
- **FlowToken**: `0x7e60df042a9c0868`
- **FungibleToken**: `0x9a0766d93b6608b7`
- **FUSD**: `0xe223d8a629e49c68`

## Setup Instructions

### Prerequisites
1. Flow CLI installed
2. Flow testnet wallet with test tokens
3. Private key for testnet account `0xdf978465ee6dcf32`

### Steps

#### 1. Create Private Key File
```bash
# Create the private key file for testnet account
# Replace YOUR_PRIVATE_KEY with actual private key
echo "YOUR_PRIVATE_KEY" > testnet-account.pkey
chmod 600 testnet-account.pkey
```

#### 2. Get Testnet Tokens
Visit the Flow testnet faucet to fund your wallet:
- https://testnet-faucet.onflow.org/
- Request FLOW tokens for `0xdf978465ee6dcf32`

#### 3. Setup Account Vaults
Run the account setup transaction to initialize FlowToken and FUSD vaults:
```bash
flow transactions send backend/scripts/setup_account.cdc \
  --signer testnet-account \
  --network testnet
```

#### 4. Test Wallet Connection
Start the frontend and test wallet authentication:
```bash
cd frontend
npm run dev
```
- Connect your Flow wallet
- Ensure it's set to testnet mode
- Verify connection to `0xdf978465ee6dcf32`

## Testnet Resources

### Network Endpoints
- **REST API**: `https://rest-testnet.onflow.org`
- **Access Node**: `access.devnet.nodes.onflow.org:9000`
- **Block Explorer**: https://testnet.flowscan.org/

### Contract Addresses (Testnet)
| Contract | Address |
|----------|---------|
| FlowToken | 0x7e60df042a9c0868 |
| FungibleToken | 0x9a0766d93b6608b7 |
| FUSD | 0xe223d8a629e49c68 |

### SKL Testnet Wallet
- **Address**: `0xdf978465ee6dcf32`
- **Usage**: League fee collection and payouts

## Flow Actions & Agents Development

### Official Documentation
Flow provides official Claude AI development guides:
- **AgentKit Guide**: https://developers.flow.com/tutorials/ai-plus-flow/agentkit-flow-guide
- **Claude Code for Flow**: https://developers.flow.com/blockchain-development-tutorials/use-AI-to-build-on-flow/llms/claude-code
- **Flow Actions Tutorial**: https://developers.flow.com/blockchain-development-tutorials/flow-actions

### AgentKit Setup (Optional)
For AI-powered development on Flow testnet:
```bash
npm create onchain-agent@latest
# Select: Langchain framework
# Select: EVM network
# Set Chain ID: 545 (Flow Testnet)
# Set RPC: https://testnet.evm.nodes.onflow.org
```

### Recommended LLM
- **Model**: `claude-3-5-haiku-20241022`
- Lightweight and affordable for blockchain interactions

## Next Steps: Actions & Agents

### Phase 1: League Fee Yield Strategy
1. Create Flow Agent to monitor fee deadlines
2. Implement Actions workflow:
   - Collect fees from user wallets
   - Swap to stablecoins if needed
   - Deploy to yield protocol
3. Track vault positions in database

### Phase 2: Automated Payouts
1. Create Flow Agent for season-end payouts
2. Implement Actions workflow:
   - Withdraw from yield vault
   - Calculate payout splits
   - Distribute to winners
3. Record transactions in database

## Troubleshooting

### Wallet Won't Connect
- Ensure wallet is set to testnet mode
- Clear browser cache and reconnect
- Verify testnet has sufficient FLOW tokens

### Transaction Fails
- Check account has enough FLOW for gas
- Verify contract addresses are correct
- Ensure vaults are initialized (run setup_account.cdc)

### Backend API Errors
- Backend currently doesn't use Flow SDK directly
- Payments recorded via transaction IDs in database
- No backend changes needed for testnet migration

## Reverting to Mainnet
To switch back to mainnet:
1. Update [frontend/src/config.js](frontend/src/config.js) to mainnet endpoints
2. Restore mainnet SKL wallet address: `0xa30279e4e80d4216`
3. Update contract imports to mainnet addresses

## Support
- Flow Discord: https://discord.gg/flow
- Flow Forum: https://forum.flow.com/
- Claude Code Issues: https://github.com/anthropics/claude-code/issues
