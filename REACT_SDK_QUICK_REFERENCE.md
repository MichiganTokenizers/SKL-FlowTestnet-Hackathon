# Flow React SDK - Quick Reference Guide

## Installation

```bash
npm install @onflow/react-sdk
```

---

## Setup

### 1. Wrap your app with FlowProvider

```javascript
import { FlowProvider } from '@onflow/react-sdk';

const config = {
  network: 'testnet',
  accessNode: 'https://access-testnet.onflow.org',
};

root.render(
  <FlowProvider config={config}>
    <App />
  </FlowProvider>
);
```

---

## Common Hooks

### Authentication

```javascript
import { useFlowCurrentUser, useFlowAuth } from '@onflow/react-sdk';

const MyComponent = () => {
  const { user, isLoading } = useFlowCurrentUser();
  const { logout } = useFlowAuth();

  return (
    <div>
      {user ? (
        <>
          <p>Address: {user.addr}</p>
          <button onClick={logout}>Logout</button>
        </>
      ) : (
        <p>Not logged in</p>
      )}
    </div>
  );
};
```

### Read Data (Query)

```javascript
import { useFlowQuery } from '@onflow/react-sdk';

const { data, isLoading, error, refetch } = useFlowQuery({
  cadence: `
    access(all) fun main(addr: Address): UFix64 {
      return getAccount(addr).balance
    }
  `,
  args: (arg, t) => [arg(address, t.Address)],
  staleTime: 60000, // Cache for 1 minute
});
```

### Send Transaction (Mutate)

```javascript
import { useFlowMutate } from '@onflow/react-sdk';

const { mutate, isLoading, error } = useFlowMutate({
  cadence: `
    transaction(amount: UFix64) {
      // Transaction code
    }
  `,
  args: (arg, t) => [arg(amount, t.UFix64)],
  onSuccess: (txId) => console.log('Success:', txId),
  onError: (error) => console.error('Error:', error),
});

// Trigger transaction
<button onClick={() => mutate()}>Send</button>
```

### Track Transaction Status

```javascript
import { useFlowTransactionStatus } from '@onflow/react-sdk';

const { status, isSealed, isFinalized } = useFlowTransactionStatus(txId);
```

### Listen to Events

```javascript
import { useFlowEvents } from '@onflow/react-sdk';

const { data: events } = useFlowEvents({
  eventType: 'A.0x123.Contract.Event',
  fromBlockHeight: 'latest',
  onEvent: (event) => console.log('New event:', event),
});
```

### Get Account Balance

```javascript
import { useFlowBalance } from '@onflow/react-sdk';

const { data: balance, isLoading } = useFlowBalance(address);
```

---

## UI Components

### Wallet Connect Button

```javascript
import { Connect } from '@onflow/react-sdk';

<Connect />
```

### Transaction Button

```javascript
import { TransactionButton } from '@onflow/react-sdk';

<TransactionButton
  cadence={transactionCode}
  args={(arg, t) => [arg(value, t.UFix64)]}
  onSuccess={(txId) => console.log('Done:', txId)}
>
  Execute Transaction
</TransactionButton>
```

### Transaction Dialog (Progress Modal)

```javascript
import { TransactionDialog } from '@onflow/react-sdk';

// Shows automatically when transaction is processing
<TransactionDialog />
```

### Transaction Link (Block Explorer)

```javascript
import { TransactionLink } from '@onflow/react-sdk';

<TransactionLink txId={transactionId}>
  View on Explorer
</TransactionLink>
```

---

## Migration from FCL

### Before (FCL)

```javascript
import * as fcl from "@onflow/fcl";

// Auth
useEffect(() => {
  fcl.currentUser.subscribe(setUser);
}, []);

// Logout
await fcl.unauthenticate();

// Query
const result = await fcl.query({
  cadence: script,
  args: (arg, t) => []
});

// Transaction
const txId = await fcl.mutate({
  cadence: transaction,
  args: (arg, t) => []
});
```

### After (React SDK)

```javascript
import {
  useFlowCurrentUser,
  useFlowAuth,
  useFlowQuery,
  useFlowMutate
} from '@onflow/react-sdk';

// Auth
const { user } = useFlowCurrentUser();
const { logout } = useFlowAuth();

// Query
const { data } = useFlowQuery({ cadence: script });

// Transaction
const { mutate } = useFlowMutate({ cadence: transaction });
```

---

## Real-World Examples for SKL

### Pay League Fee

```javascript
const PayFeeButton = ({ leagueId, amount }) => {
  const { mutate: payFee, isLoading } = useFlowMutate({
    cadence: `
      import FlowToken from 0x7e60df042a9c0868

      transaction(amount: UFix64, leagueId: String) {
        // Payment transaction
      }
    `,
    args: (arg, t) => [
      arg(amount, t.UFix64),
      arg(leagueId, t.String)
    ],
    onSuccess: async (txId) => {
      // Record in backend
      await fetch('/api/record-payment', {
        method: 'POST',
        body: JSON.stringify({ txId, leagueId, amount })
      });
    }
  });

  return (
    <button onClick={() => payFee()} disabled={isLoading}>
      {isLoading ? 'Processing...' : 'Pay Fee'}
    </button>
  );
};
```

### Monitor Agent Events

```javascript
const AgentMonitor = ({ leagueId }) => {
  const { data: events } = useFlowEvents({
    eventType: 'A.0xdf978465ee6dcf32.SKLVaultDepositAgent.AgentExecuted',
    fromBlockHeight: 'latest',
    onEvent: (event) => {
      toast.success(`Agent executed: ${event.data.amountDeposited} FLOW`);
    }
  });

  return (
    <div>
      <h3>Agent Activity</h3>
      {events?.map(event => (
        <div key={event.id}>
          {event.data.leagueId}: {event.data.amountDeposited} FLOW
        </div>
      ))}
    </div>
  );
};
```

### Schedule Agent (Admin)

```javascript
import { TransactionButton } from '@onflow/react-sdk';

const ScheduleAgentButton = ({ leagueId, delaySeconds }) => {
  return (
    <TransactionButton
      cadence={scheduleAgentTransaction}
      args={(arg, t) => [
        arg(leagueId, t.String),
        arg(delaySeconds, t.UFix64),
        // ... other args
      ]}
      onSuccess={(txId) => {
        console.log('Agent scheduled:', txId);
        // Refresh agent list
      }}
    >
      Schedule Agent ({delaySeconds}s delay)
    </TransactionButton>
  );
};
```

---

## TypeScript Support

```typescript
import { useFlowMutate } from '@onflow/react-sdk';
import type { TransactionResult } from '@onflow/react-sdk';

interface PaymentData {
  amount: string;
  leagueId: string;
}

const { mutate } = useFlowMutate<PaymentData>({
  cadence: paymentTransaction,
  args: (arg, t) => [
    arg(data.amount, t.UFix64),
    arg(data.leagueId, t.String)
  ]
});
```

---

## Caching Configuration

```javascript
const { data } = useFlowQuery({
  cadence: script,
  args: (arg, t) => [],

  // Cache for 5 minutes
  staleTime: 300000,

  // Refetch on window focus
  refetchOnWindowFocus: true,

  // Refetch every 30 seconds
  refetchInterval: 30000,

  // Keep data while refetching
  keepPreviousData: true,
});
```

---

## Error Handling

```javascript
const { mutate, error, isError } = useFlowMutate({
  cadence: transaction,
  onError: (error) => {
    if (error.message.includes('insufficient balance')) {
      toast.error('Not enough FLOW to pay fee');
    } else {
      toast.error('Transaction failed');
    }
  },
  retry: 3, // Retry 3 times on failure
});

if (isError) {
  return <ErrorMessage error={error} />;
}
```

---

## Dark Mode

```javascript
const config = {
  network: 'testnet',
  theme: {
    colorMode: 'dark', // 'light' | 'dark' | 'system'
  }
};
```

---

## Useful Links

- **Documentation**: https://developers.flow.com/build/tools/react-sdk
- **GitHub**: https://github.com/onflow/react-sdk
- **Examples**: https://github.com/onflow/flow-react-sdk-examples
- **Discord**: https://discord.gg/flow

---

**Quick Tip**: Start by migrating authentication first - it provides the biggest immediate benefit with minimal risk!
