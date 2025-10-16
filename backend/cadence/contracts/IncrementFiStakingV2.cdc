import FlowToken from 0x7e60df042a9c0868
import FungibleToken from 0x9a0766d93b6608b7
import LiquidStaking from 0xe45c64ecfe31e465
import stFlowToken from 0xe45c64ecfe31e465

/// IncrementFi Staking Sink - Flow Actions Connector
/// Stakes FLOW tokens into IncrementFi staking pools
///
/// This connector accepts FLOW tokens and stakes them into IncrementFi
/// staking pools to earn yield. It implements the Sink pattern with capacity
/// limits and graceful no-op handling when capacity is exceeded.
///
/// Part of the Forte upgrade - Flow Actions & Agents automation
/// Uses IncrementFi Staking (production-ready on testnet)

access(all) contract IncrementFiStakingV2 {

    /// Storage path for user certificate
    access(all) let UserCertificateStoragePath: StoragePath

    /// Event emitted when tokens are staked
    access(all) event TokensStaked(
        amount: UFix64,
        poolId: UInt64,
        stakerAddress: Address,
        leagueId: String?
    )

    /// Event emitted when sink reaches capacity
    access(all) event CapacityReached(
        attemptedAmount: UFix64,
        capacityLimit: UFix64,
        currentStaked: UFix64
    )

    /// Event emitted when staking fails
    access(all) event StakingFailed(
        reason: String,
        amount: UFix64,
        poolId: UInt64
    )

    /// Sink interface implementation for Flow Actions
    /// Accepts token deposits up to a specified capacity limit
    access(all) resource interface SinkInterface {
        /// Get the remaining capacity
        access(all) fun getRemainingCapacity(): UFix64

        /// Check if sink can accept the specified amount
        access(all) fun canAccept(amount: UFix64): Bool

        /// Sink tokens to the staking pool
        access(all) fun sink(vault: @{FungibleToken.Vault})
    }

    /// StakingSink resource that handles staking to IncrementFi pools
    access(all) resource StakingSink: SinkInterface {

        /// The league ID this sink is staking for (optional, for tracking)
        access(all) let leagueId: String?

        /// IncrementFi pool ID to stake into
        access(all) let poolId: UInt64

        /// Address that will be credited as the staker
        access(all) let stakerAddress: Address

        /// Maximum capacity for this sink (0 = unlimited)
        access(self) let capacityLimit: UFix64

        /// Total amount staked through this sink
        access(self) var totalStaked: UFix64

        /// Whether to require user certificate (for some pools)
        access(self) let requiresCertificate: Bool

        /// Holds the stFlow tokens received from staking
        access(self) var stFlowVault: @{FungibleToken.Vault}?

        init(
            leagueId: String?,
            poolId: UInt64,
            stakerAddress: Address,
            capacityLimit: UFix64,
            requiresCertificate: Bool
        ) {
            self.leagueId = leagueId
            self.poolId = poolId
            self.stakerAddress = stakerAddress
            self.capacityLimit = capacityLimit
            self.totalStaked = 0.0
            self.requiresCertificate = requiresCertificate
            self.stFlowVault <- nil
        }

        /// Get the remaining capacity before limit is reached
        access(all) fun getRemainingCapacity(): UFix64 {
            if self.capacityLimit == 0.0 {
                // Unlimited capacity
                return UFix64.max
            }

            if self.totalStaked >= self.capacityLimit {
                return 0.0
            }

            return self.capacityLimit - self.totalStaked
        }

        /// Check if the sink can accept the specified amount
        access(all) fun canAccept(amount: UFix64): Bool {
            if amount <= 0.0 {
                return false
            }

            let remainingCapacity = self.getRemainingCapacity()
            return amount <= remainingCapacity
        }

        /// Sink tokens to IncrementFi staking pool
        /// Performs no-op if capacity is exceeded (Flow Actions pattern)
        /// @param vault: FungibleToken vault to stake
        access(all) fun sink(vault: @{FungibleToken.Vault}) {
            let amount = vault.balance

            // Check capacity - perform no-op if exceeded
            if !self.canAccept(amount: amount) {
                emit CapacityReached(
                    attemptedAmount: amount,
                    capacityLimit: self.capacityLimit,
                    currentStaked: self.totalStaked
                )

                // Destroy the vault (no-op pattern - don't panic, just skip)
                destroy vault
                return
            }

            // Validate pool ID
            if self.poolId == 0 {
                emit StakingFailed(
                    reason: "Invalid pool ID: must be greater than 0",
                    amount: amount,
                    poolId: self.poolId
                )
                destroy vault
                return
            }

            // Cast the vault to FlowToken.Vault
            let flowVault <- vault as! @FlowToken.Vault

            // Stake FLOW tokens to IncrementFi Liquid Staking
            // This will return stFlow tokens at the current exchange rate
            let newStFlowVault <- LiquidStaking.stake(flowVault: <-flowVault)
            let stFlowAmount = newStFlowVault.balance

            // Store or merge the stFlow tokens
            if self.stFlowVault == nil {
                self.stFlowVault <-! newStFlowVault
            } else {
                let existingVault <- self.stFlowVault <- nil
                let unwrappedVault <- existingVault!
                unwrappedVault.deposit(from: <-newStFlowVault)
                self.stFlowVault <-! unwrappedVault
            }

            // Update total staked
            self.totalStaked = self.totalStaked + amount

            // Emit success event
            emit TokensStaked(
                amount: amount,
                poolId: self.poolId,
                stakerAddress: self.stakerAddress,
                leagueId: self.leagueId
            )

            log("IncrementFi Liquid Staking Completed: "
                .concat(amount.toString())
                .concat(" FLOW staked, received ")
                .concat(stFlowAmount.toString())
                .concat(" stFlow"))
        }

        /// Withdraw all stFlow tokens from this sink
        access(all) fun withdrawStFlow(): @{FungibleToken.Vault}? {
            let vault <- self.stFlowVault <- nil
            return <- vault
        }

        /// Get sink information
        access(all) fun getStakingInfo(): {String: AnyStruct} {
            return {
                "leagueId": self.leagueId,
                "poolId": self.poolId,
                "stakerAddress": self.stakerAddress,
                "capacityLimit": self.capacityLimit,
                "totalStaked": self.totalStaked,
                "remainingCapacity": self.getRemainingCapacity(),
                "requiresCertificate": self.requiresCertificate
            }
        }
    }

    /// Create a new StakingSink for IncrementFi staking
    access(all) fun createSink(
        leagueId: String?,
        poolId: UInt64,
        stakerAddress: Address,
        capacityLimit: UFix64,
        requiresCertificate: Bool
    ): @StakingSink {
        return <- create StakingSink(
            leagueId: leagueId,
            poolId: poolId,
            stakerAddress: stakerAddress,
            capacityLimit: capacityLimit,
            requiresCertificate: requiresCertificate
        )
    }

    init() {
        // Set storage paths
        self.UserCertificateStoragePath = /storage/IncrementFiUserCertificate

        log("IncrementFi Staking Sink initialized")
    }
}
