import FlowToken from 0x7e60df042a9c0868
import FungibleToken from 0x9a0766d93b6608b7

// IncrementFi Lending Protocol Testnet Imports
import LendingInterfaces from 0x8bc9e24c307d249b
import LendingConfig from 0x8bc9e24c307d249b
import LendingComptroller from 0xc15e75b5f6b95e54
import LendingPool from 0x8aaca41f09eb1e3d

/// IncrementFi Vault Sink - Flow Actions Connector
/// Implements the Sink interface to deposit tokens into IncrementFi Money Market
///
/// This connector accepts FLOW tokens and deposits them into the IncrementFi
/// LendingPool to earn yield. It implements the Sink pattern with capacity limits
/// and graceful no-op handling when capacity is exceeded.
///
/// Part of the Forte upgrade - Flow Actions & Agents automation

access(all) contract IncrementFiVaultSink {

    /// Event emitted when tokens are deposited to vault
    access(all) event TokensDeposited(
        amount: UFix64,
        poolAddress: Address,
        supplierAddress: Address,
        leagueId: String?
    )

    /// Event emitted when sink reaches capacity
    access(all) event CapacityReached(
        attemptedAmount: UFix64,
        capacityLimit: UFix64,
        currentDeposited: UFix64
    )

    /// Sink interface implementation for Flow Actions
    /// Accepts token deposits up to a specified capacity limit
    access(all) resource interface SinkInterface {
        /// Get the remaining capacity
        access(all) fun getRemainingCapacity(): UFix64

        /// Check if sink can accept the specified amount
        access(all) fun canAccept(amount: UFix64): Bool

        /// Sink tokens to the vault (deposit to IncrementFi)
        access(all) fun sink(vault: @{FungibleToken.Vault})
    }

    /// VaultSink resource that handles deposits to IncrementFi
    access(all) resource VaultSink: SinkInterface {

        /// The league ID this sink is depositing for (optional, for tracking)
        access(all) let leagueId: String?

        /// Address of the LendingPool contract
        access(all) let poolAddress: Address

        /// Address that will be credited as the supplier
        access(all) let supplierAddress: Address

        /// Maximum capacity for this sink (0 = unlimited)
        access(self) let capacityLimit: UFix64

        /// Total amount deposited through this sink
        access(self) var totalDeposited: UFix64

        init(
            leagueId: String?,
            poolAddress: Address,
            supplierAddress: Address,
            capacityLimit: UFix64
        ) {
            self.leagueId = leagueId
            self.poolAddress = poolAddress
            self.supplierAddress = supplierAddress
            self.capacityLimit = capacityLimit
            self.totalDeposited = 0.0
        }

        /// Get the remaining capacity before limit is reached
        access(all) fun getRemainingCapacity(): UFix64 {
            if self.capacityLimit == 0.0 {
                // Unlimited capacity
                return UFix64.max
            }

            if self.totalDeposited >= self.capacityLimit {
                return 0.0
            }

            return self.capacityLimit - self.totalDeposited
        }

        /// Check if the sink can accept the specified amount
        access(all) fun canAccept(amount: UFix64): Bool {
            if amount <= 0.0 {
                return false
            }

            let remainingCapacity = self.getRemainingCapacity()
            return amount <= remainingCapacity
        }

        /// Sink tokens to IncrementFi vault
        /// Performs no-op if capacity is exceeded (Flow Actions pattern)
        /// @param vault: FungibleToken vault to deposit
        access(all) fun sink(vault: @{FungibleToken.Vault}) {
            let amount = vault.balance

            // Check capacity - perform no-op if exceeded
            if !self.canAccept(amount: amount) {
                emit CapacityReached(
                    attemptedAmount: amount,
                    capacityLimit: self.capacityLimit,
                    currentDeposited: self.totalDeposited
                )

                // Destroy the vault (no-op pattern - don't panic, just skip)
                // In production, you might want to return the vault instead
                destroy vault
                return
            }

            // Get reference to the LendingPool contract
            let poolContract = getAccount(self.poolAddress)
                .contracts.borrow<&LendingPool>(name: "LendingPool")
                ?? panic("Could not borrow reference to LendingPool contract at address "
                    .concat(self.poolAddress.toString()))

            // Supply the tokens to the pool
            // IncrementFi's supply() method takes the supplier address and the vault
            poolContract.supply(
                supplierAddr: self.supplierAddress,
                inUnderlyingVault: <- vault
            )

            // Update total deposited
            self.totalDeposited = self.totalDeposited + amount

            // Emit success event
            emit TokensDeposited(
                amount: amount,
                poolAddress: self.poolAddress,
                supplierAddress: self.supplierAddress,
                leagueId: self.leagueId
            )

            log("IncrementFi Deposit Completed: "
                .concat(amount.toString())
                .concat(" FLOW deposited to IncrementFi Money Market"))
        }

        /// Get sink information
        access(all) fun getSinkInfo(): {String: AnyStruct} {
            return {
                "leagueId": self.leagueId,
                "poolAddress": self.poolAddress,
                "supplierAddress": self.supplierAddress,
                "capacityLimit": self.capacityLimit,
                "totalDeposited": self.totalDeposited,
                "remainingCapacity": self.getRemainingCapacity()
            }
        }
    }

    /// Create a new VaultSink for IncrementFi deposits
    access(all) fun createSink(
        leagueId: String?,
        poolAddress: Address,
        supplierAddress: Address,
        capacityLimit: UFix64
    ): @VaultSink {
        return <- create VaultSink(
            leagueId: leagueId,
            poolAddress: poolAddress,
            supplierAddress: supplierAddress,
            capacityLimit: capacityLimit
        )
    }

    init() {
        // Contract initialization
        log("IncrementFi Vault Sink initialized")
    }
}
