# Flow React SDK Upgrade Plan

## Project: SKL Fantasy Football - Frontend Modernization
## Date: October 15, 2025
## Status: Planning Phase

---

## Executive Summary

Upgrade the SKL frontend from using `@onflow/fcl` directly to the modern `@onflow/react-sdk`, which provides React-native hooks, components, and automatic optimizations. This will reduce code complexity, improve performance, and provide a better developer experience.

---

## Current State Analysis

### Existing Dependencies
```json
{
  "@onflow/fcl": "^1.18.0",
  "@onflow/types": "^1.4.1"
}
```

### Current Implementation Patterns

#### 1. **Authentication** (App.jsx)
```javascript
// Lines 79-82: Manual FCL subscription
useEffect(() => {
  fcl.currentUser.subscribe(setFlowUser);
}, []);

// Line 89: Manual logout
await fcl.unauthenticate();
```

**Issues:**
- Manual state management
- No automatic cleanup
- No loading states
- No error handling

#### 2. **Transaction Handling** (LeagueFees.jsx)
- Custom transaction construction
- Manual loading/error states
- No automatic retries
- No caching
- Complex status tracking

#### 3. **Wallet Connection**
- Custom UI implementation
- Manual wallet detection
- No mobile optimization

### Files Using FCL Directly
- `frontend/src/App.jsx` - Main authentication
- `frontend/src/components/league/LeagueFees.jsx` - Fee payments
- `frontend/src/components/common/Home.jsx` - User info display
- `frontend/src/config.js` - FCL configuration
- `frontend/src/flow/config.js` - Flow network config

---

## Target State: @onflow/react-sdk

### New Dependency
```json
{
  "@onflow/react-sdk": "^1.0.0"  // Add this
}
```

### Key Features We'll Gain

#### 1. **React Hooks**
- `useFlowCurrentUser()` - User authentication state
- `useFlowAuth()` - Login/logout actions
- `useFlowQuery()` - Read blockchain data
- `useFlowMutate()` - Send transactions
- `useFlowTransactionStatus()` - Track transaction status
- `useFlowEvents()` - Subscribe to on-chain events
- `useFlowBalance()` - Get account balance
- `useFlowAccount()` - Get account details

#### 2. **UI Components**
- `<Connect />` - Wallet connection button
- `<TransactionButton />` - Transaction execution
- `<TransactionDialog />` - Transaction progress modal
- `<TransactionLink />` - Block explorer links

#### 3. **Built-in Features**
- TypeScript type safety
- Automatic caching (@tanstack/react-query)
- Background refetching
- Optimistic updates
- Error retry logic
- Loading states
- Dark mode support
- Mobile responsive

---

## Implementation Plan

### Phase 1: Setup & Configuration (Day 1)

#### Step 1.1: Install Dependencies
```bash
cd frontend
npm install @onflow/react-sdk
```

#### Step 1.2: Create FlowProvider Configuration
**New File**: `frontend/src/flow/provider-config.js`
```javascript
export const flowProviderConfig = {
  network: 'testnet', // or 'mainnet'
  accessNode: 'https://access-testnet.onflow.org',
  discovery: {
    wallet: 'https://fcl-discovery.onflow.org/testnet/authn',
  },
  // Optional: Custom wallet discovery
  wallets: [
    // Add specific wallet configurations
  ],
  // Optional: Theme customization
  theme: {
    colorMode: 'light', // 'light' | 'dark' | 'system'
  }
};
```

#### Step 1.3: Wrap App with FlowProvider
**File**: `frontend/src/main.jsx` or `index.jsx`
```javascript
import { FlowProvider } from '@onflow/react-sdk';
import { flowProviderConfig } from './flow/provider-config';

root.render(
  <StrictMode>
    <FlowProvider config={flowProviderConfig}>
      <Router>
        <App />
      </Router>
    </FlowProvider>
  </StrictMode>
);
```

**Estimated Time**: 1 hour

---

### Phase 2: Authentication Migration (Day 1-2)

#### Step 2.1: Update App.jsx Authentication
**Current Code** (Lines 66, 79-82):
```javascript
const [flowUser, setFlowUser] = useState(null);

useEffect(() => {
  fcl.currentUser.subscribe(setFlowUser);
}, []);
```

**New Code**:
```javascript
import { useFlowCurrentUser, useFlowAuth } from '@onflow/react-sdk';

// In component
const { user, isLoading: userLoading } = useFlowCurrentUser();
const { logout: flowLogout } = useFlowAuth();
```

**Changes Required**:
- Replace `flowUser` state with `user` from hook
- Remove `useEffect` subscription
- Update all references to `flowUser` → `user`
- Replace `fcl.unauthenticate()` with `flowLogout()`

**Files to Modify**:
- `frontend/src/App.jsx` (Lines 66, 79-82, 89)

**Estimated Time**: 2 hours

#### Step 2.2: Add Pre-built Connect Component
**Current**: Custom wallet connection logic

**New**: Use built-in component
```javascript
import { Connect } from '@onflow/react-sdk';

// In your navigation/header
<Connect />
```

**Customization Options**:
```javascript
<Connect
  theme="light" // or "dark"
  className="custom-wallet-button"
  onConnect={(user) => console.log('Connected:', user)}
  onDisconnect={() => console.log('Disconnected')}
/>
```

**Files to Modify**:
- `frontend/src/App.jsx` (Header/Nav section)
- `frontend/src/components/common/Home.jsx` (Wallet button)

**Estimated Time**: 1 hour

---

### Phase 3: Transaction Migration (Day 2-3)

#### Step 3.1: Update Fee Payment Transactions
**File**: `frontend/src/components/league/LeagueFees.jsx`

**Current Pattern**:
```javascript
// Manual transaction construction
const sendTransaction = async () => {
  const txId = await fcl.mutate({
    cadence: transactionCode,
    args: (arg, t) => [...]
  });
  // Manual status tracking
};
```

**New Pattern**:
```javascript
import { useFlowMutate, useFlowTransactionStatus } from '@onflow/react-sdk';

const PayFeeButton = ({ amount, leagueId }) => {
  const { mutate: payFee, data: txId, isLoading, error } = useFlowMutate({
    cadence: `
      import FlowToken from 0x7e60df042a9c0868

      transaction(amount: UFix64, leagueId: String) {
        // Your payment transaction code
      }
    `,
    args: (arg, t) => [
      arg(amount, t.UFix64),
      arg(leagueId, t.String)
    ],
    onSuccess: (txId) => {
      console.log('Transaction submitted:', txId);
      // Call backend to record payment
    },
    onError: (error) => {
      console.error('Transaction failed:', error);
    }
  });

  // Automatic transaction status tracking
  const { status, isSealed, isFinalized } = useFlowTransactionStatus(txId);

  return (
    <button
      onClick={() => payFee()}
      disabled={isLoading}
    >
      {isLoading ? 'Processing...' : 'Pay Fee'}
    </button>
  );
};
```

**Benefits**:
- Automatic retries on network errors
- Built-in loading/error states
- Transaction status tracking
- Type safety for arguments

**Estimated Time**: 3 hours

#### Step 3.2: Use TransactionButton Component
**Alternative Approach**: Pre-built component

```javascript
import { TransactionButton, TransactionDialog } from '@onflow/react-sdk';

<TransactionButton
  cadence={paymentTransaction}
  args={(arg, t) => [
    arg(amount, t.UFix64),
    arg(leagueId, t.String)
  ]}
  onSuccess={(txId) => {
    // Record payment in backend
  }}
>
  Pay League Fee
</TransactionButton>

{/* Shows automatic progress dialog */}
<TransactionDialog />
```

**Files to Modify**:
- `frontend/src/components/league/LeagueFees.jsx`

**Estimated Time**: 2 hours

---

### Phase 4: Admin Dashboard Enhancement (Day 3-4)

#### Step 4.1: Add Agent Event Monitoring
**File**: `frontend/src/components/admin/AdminDashboard.jsx`

**New Feature**: Real-time agent execution monitoring

```javascript
import { useFlowEvents } from '@onflow/react-sdk';

const AdminDashboard = () => {
  // Monitor agent scheduled events
  const { data: scheduledEvents } = useFlowEvents({
    eventType: 'A.0xdf978465ee6dcf32.SKLVaultDepositAgent.AgentCreated',
    fromBlockHeight: 'latest',
    onEvent: (event) => {
      console.log('Agent scheduled:', event);
      // Update UI automatically
      toast.success('New agent scheduled!');
    }
  });

  // Monitor agent execution events
  const { data: executedEvents } = useFlowEvents({
    eventType: 'A.0xdf978465ee6dcf32.SKLVaultDepositAgent.AgentExecuted',
    fromBlockHeight: 'latest',
    onEvent: (event) => {
      console.log('Agent executed:', event);
      // Update dashboard automatically
      toast.success(`Vault deposit completed: ${event.data.amountDeposited} FLOW`);
    }
  });

  // Monitor agent failures
  const { data: failedEvents } = useFlowEvents({
    eventType: 'A.0xdf978465ee6dcf32.SKLVaultDepositAgent.AgentExecutionFailed',
    fromBlockHeight: 'latest',
    onEvent: (event) => {
      console.error('Agent failed:', event);
      toast.error(`Agent failed: ${event.data.reason}`);
    }
  });

  return (
    <div className="admin-dashboard">
      {/* Display events in real-time */}
      <AgentEventsTimeline events={[...scheduledEvents, ...executedEvents, ...failedEvents]} />
    </div>
  );
};
```

**Benefits**:
- Real-time UI updates
- No polling needed
- Automatic reconnection
- Event history

**Estimated Time**: 3 hours

#### Step 4.2: Add Agent Scheduling with TransactionButton
```javascript
import { TransactionButton } from '@onflow/react-sdk';

const ScheduleAgentButton = ({ leagueId, delaySeconds }) => {
  return (
    <TransactionButton
      cadence={scheduleAgentTransaction}
      args={(arg, t) => [
        arg(leagueId, t.String),
        arg(poolAddress, t.Address),
        arg(totalTeams, t.Int),
        arg(paidTeams, t.Int),
        arg(collectedAmount, t.UFix64),
        arg(delaySeconds, t.UFix64),
        arg("Medium", t.String),
        arg("1000", t.UInt64),
        arg("1.0", t.UFix64),
        arg("0.0", t.UFix64)
      ]}
      onSuccess={(txId) => {
        console.log('Agent scheduled:', txId);
        // Refresh agent list
      }}
    >
      Schedule Agent
    </TransactionButton>
  );
};
```

**Files to Modify**:
- `frontend/src/components/admin/AdminDashboard.jsx`

**Estimated Time**: 2 hours

---

### Phase 5: Query Optimization (Day 4-5)

#### Step 5.1: Replace Backend API Calls with On-Chain Queries
**Current**: Fetching league data from Python backend

**New**: Query directly from blockchain with caching

```javascript
import { useFlowQuery } from '@onflow/react-sdk';

const useLeagueFees = (leagueId) => {
  return useFlowQuery({
    cadence: `
      import SKLFeeCollectionSource from 0xdf978465ee6dcf32

      access(all) fun main(leagueId: String): {String: AnyStruct} {
        // Query league fee data from contracts
        return {
          "totalCollected": 500.0,
          "totalTeams": 10,
          "paidTeams": 8
        }
      }
    `,
    args: (arg, t) => [arg(leagueId, t.String)],
    // Automatic caching
    staleTime: 60000, // 1 minute
    refetchOnWindowFocus: true,
    refetchInterval: 30000 // Refresh every 30 seconds
  });
};

// In component
const { data: leagueFees, isLoading, error, refetch } = useLeagueFees(leagueId);
```

**Benefits**:
- 70-90% reduction in RPC calls
- Automatic background refetching
- Optimistic updates
- Error retry logic
- Loading states

**Files to Consider**:
- `frontend/src/components/league/League.jsx`
- `frontend/src/components/admin/AdminDashboard.jsx`

**Estimated Time**: 4 hours

---

### Phase 6: TypeScript Migration (Optional - Day 5-6)

#### Step 6.1: Add TypeScript
```bash
npm install --save-dev typescript @types/react @types/react-dom
```

#### Step 6.2: Create tsconfig.json
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

#### Step 6.3: Rename Files .jsx → .tsx
- Start with new components
- Gradually migrate existing components

**Benefits**:
- Full type safety
- Better IDE autocomplete
- Catch errors at compile time
- React SDK is TypeScript-first

**Estimated Time**: 2 days (optional)

---

## Testing Strategy

### Unit Tests
- Test custom hooks with React Testing Library
- Test component rendering
- Test transaction flows

### Integration Tests
- Test authentication flow
- Test fee payment flow
- Test agent scheduling
- Test event subscriptions

### Manual Testing Checklist
- [ ] Connect wallet successfully
- [ ] Disconnect wallet
- [ ] Pay league fee
- [ ] View transaction status
- [ ] Schedule agent from admin dashboard
- [ ] Monitor agent events in real-time
- [ ] View transaction in block explorer
- [ ] Dark mode toggle works
- [ ] Mobile responsive

---

## Migration Checklist

### Pre-Migration
- [ ] Backup current codebase
- [ ] Document current FCL usage patterns
- [ ] Review React SDK documentation
- [ ] Test React SDK on demo project

### Phase 1: Setup
- [ ] Install @onflow/react-sdk
- [ ] Create FlowProvider configuration
- [ ] Wrap app with FlowProvider
- [ ] Test basic setup

### Phase 2: Authentication
- [ ] Replace fcl.currentUser with useFlowCurrentUser
- [ ] Replace fcl.unauthenticate with useFlowAuth
- [ ] Add <Connect /> component
- [ ] Test wallet connection flow
- [ ] Verify logout works

### Phase 3: Transactions
- [ ] Migrate fee payment to useFlowMutate
- [ ] Add TransactionButton components
- [ ] Add TransactionDialog
- [ ] Test transaction submission
- [ ] Verify transaction tracking

### Phase 4: Admin Dashboard
- [ ] Add useFlowEvents for agent monitoring
- [ ] Add TransactionButton for agent scheduling
- [ ] Create real-time event timeline
- [ ] Test event subscriptions
- [ ] Verify automatic UI updates

### Phase 5: Optimization
- [ ] Replace API calls with useFlowQuery
- [ ] Configure caching strategy
- [ ] Test query performance
- [ ] Monitor RPC call reduction

### Phase 6: Polish
- [ ] Add loading skeletons
- [ ] Add error boundaries
- [ ] Add toast notifications
- [ ] Test dark mode
- [ ] Mobile optimization

### Post-Migration
- [ ] Performance testing
- [ ] User acceptance testing
- [ ] Documentation updates
- [ ] Deployment

---

## Risk Assessment

### Low Risk
- ✅ React SDK is production-ready
- ✅ Backward compatible with FCL
- ✅ Well-documented
- ✅ Active maintenance

### Medium Risk
- ⚠️ Learning curve for new API
- ⚠️ Potential breaking changes in future versions
- ⚠️ Need to test all transaction flows thoroughly

### Mitigation Strategies
1. **Gradual migration**: Migrate one component at a time
2. **Keep FCL as fallback**: Don't remove FCL until fully tested
3. **Comprehensive testing**: Test all critical flows
4. **Feature flags**: Use flags to enable/disable new features

---

## Performance Expectations

### Before (FCL)
- Manual state management: ~150 lines of code
- No caching: 100% RPC calls
- Manual error handling
- No optimistic updates

### After (React SDK)
- Automatic state management: ~50 lines of code
- Smart caching: 70-90% reduction in RPC calls
- Built-in error handling
- Optimistic updates

### Metrics to Track
- Bundle size change
- RPC call frequency
- Time to first interaction
- Transaction success rate
- User satisfaction

---

## Resources

### Documentation
- **React SDK Docs**: https://developers.flow.com/build/tools/react-sdk
- **FCL Migration Guide**: TBD (check Flow docs)
- **@tanstack/react-query**: https://tanstack.com/query/latest

### Examples
- **Flow React SDK Examples**: https://github.com/onflow/flow-react-sdk-examples
- **FCL Quickstart**: https://developers.flow.com/build/getting-started/fcl-quickstart

### Support
- **Flow Discord**: https://discord.gg/flow
- **GitHub Issues**: https://github.com/onflow/react-sdk/issues

---

## Timeline Summary

| Phase | Duration | Description |
|-------|----------|-------------|
| Phase 1: Setup | 1 day | Install and configure FlowProvider |
| Phase 2: Authentication | 1-2 days | Migrate auth logic to hooks |
| Phase 3: Transactions | 2-3 days | Migrate transactions to useFlowMutate |
| Phase 4: Admin Dashboard | 1-2 days | Add agent monitoring and scheduling |
| Phase 5: Optimization | 1-2 days | Add caching and query optimization |
| Phase 6: TypeScript (Optional) | 2 days | Add TypeScript support |
| **Total** | **6-12 days** | Depends on TypeScript inclusion |

---

## Success Criteria

### Functional
- ✅ All authentication flows work
- ✅ All transactions execute successfully
- ✅ Agent monitoring works in real-time
- ✅ No regression in existing features

### Non-Functional
- ✅ 70%+ reduction in RPC calls
- ✅ 50%+ reduction in code complexity
- ✅ Improved loading states and error handling
- ✅ Better mobile experience

### Developer Experience
- ✅ Cleaner, more maintainable code
- ✅ Better TypeScript support
- ✅ Easier to add new features
- ✅ Better documentation

---

## Next Steps

1. **Review this plan** with team
2. **Create feature branch**: `feature/react-sdk-upgrade`
3. **Start with Phase 1**: Setup and configuration
4. **Test incrementally**: Don't break existing features
5. **Document changes**: Keep this plan updated

---

## Notes

- React SDK is built on top of FCL, so both can coexist during migration
- Start with authentication (biggest immediate benefit)
- Event monitoring will be perfect for your new Flow Agents
- TypeScript is optional but highly recommended
- Keep the old code as reference during migration

---

**Status**: Ready to begin
**Priority**: Medium-High
**Estimated Effort**: 6-12 days
**Expected Impact**: Significant improvement in code quality and UX

---

**Created by**: Claude Code
**Date**: October 15, 2025
**Last Updated**: October 15, 2025
