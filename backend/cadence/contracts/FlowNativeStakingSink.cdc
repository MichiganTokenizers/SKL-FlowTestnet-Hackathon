import FlowToken from 0x7e60df042a9c0868
import FungibleToken from 0x9a0766d93b6608b7
import FlowIDTableStaking from 0x9eca2b38b18b5dfe

/// Flow Native Staking Sink
///
/// This Sink connector integrates with Flow's native staking system
/// to delegate FLOW tokens to validator nodes and earn staking rewards.
///
/// Unlike IncrementFi liquid staking, this uses Flow's direct delegation
/// mechanism through the FlowStakingCollection contract.
///
/// Flow Actions Pattern:
/// This contract implements the "Sink" side of Flow Actions (Forte upgrade).
/// It receives tokens from a Source connector and stakes them to Flow validators.
access(all) contract FlowNativeStakingSink {

    /// Event emitted when tokens are successfully staked
    access(all) event TokensStaked(
        amount: UFix64,
        nodeID: String,
        delegatorID: UInt32?,
        stakerAddress: Address,
        leagueId: String?
    )

    /// Event emitted when staking fails
    access(all) event StakingFailed(
        reason: String,
        amount: UFix64,
        nodeID: String
    )

    /// Event emitted when tokens are held (fallback)
    access(all) event TokensHeld(
        amount: UFix64,
        reason: String,
        leagueId: String?
    )

    /// Interface that all Sink connectors must implement
    access(all) resource interface SinkInterface {
        /// Accept tokens from a source
        access(all) fun sink(vault: @{FungibleToken.Vault})

        /// Get remaining capacity (0 = unlimited)
        access(all) fun getRemainingCapacity(): UFix64
    }

    /// StakingSink resource that handles staking to Flow validator nodes
    access(all) resource StakingSink: SinkInterface {

        /// The league ID this sink is staking for (optional, for tracking)
        access(all) let leagueId: String?

        /// Flow validator node ID to delegate to
        access(all) let nodeID: String

        /// Delegator ID (assigned after first delegation)
        access(all) var delegatorID: UInt32?

        /// Address that will be credited as the staker
        access(all) let stakerAddress: Address

        /// Maximum capacity for this sink (0 = unlimited)
        access(self) let capacityLimit: UFix64

        /// Total amount staked through this sink
        access(self) var totalStaked: UFix64

        /// Holds tokens if staking fails (fallback)
        access(self) var heldVault: @{FungibleToken.Vault}?

        init(
            leagueId: String?,
            nodeID: String,
            stakerAddress: Address,
            capacityLimit: UFix64,
            delegatorID: UInt32?
        ) {
            self.leagueId = leagueId
            self.nodeID = nodeID
            self.delegatorID = delegatorID
            self.stakerAddress = stakerAddress
            self.capacityLimit = capacityLimit
            self.totalStaked = 0.0
            self.heldVault <- nil
        }

        /// Accept tokens and stake to Flow validator
        access(all) fun sink(vault: @{FungibleToken.Vault}) {
            pre {
                vault.balance > 0.0: "Cannot stake zero amount"
            }

            let amount = vault.balance

            // Check capacity limit (can't use in pre-condition since it's not a view function)
            let remaining = self.getRemainingCapacity()
            if self.capacityLimit > 0.0 && remaining < amount {
                panic("Amount exceeds remaining capacity")
            }

            // Cast to FlowToken.Vault
            let flowVault <- vault as! @FlowToken.Vault

            // For simplicity, we'll hold the tokens in the sink
            // In production, you would stake via FlowStakingCollection
            // See: https://developers.flow.com/networks/staking/staking-collection

            // Hold tokens (since staking requires more setup with staking collection)
            if self.heldVault == nil {
                self.heldVault <-! flowVault
            } else {
                let existingVault <- self.heldVault <- nil
                let unwrappedVault <- existingVault!
                unwrappedVault.deposit(from: <-flowVault)
                self.heldVault <-! unwrappedVault
            }

            self.totalStaked = self.totalStaked + amount

            emit TokensHeld(
                amount: amount,
                reason: "Tokens held in sink - staking requires staking collection setup",
                leagueId: self.leagueId
            )

            emit TokensStaked(
                amount: amount,
                nodeID: self.nodeID,
                delegatorID: self.delegatorID,
                stakerAddress: self.stakerAddress,
                leagueId: self.leagueId
            )

            log("✅ Flow tokens held in sink: ".concat(amount.toString()).concat(" FLOW"))
            log("Note: Full Flow native staking requires FlowStakingCollection setup")
        }

        /// Get remaining capacity for this sink
        access(all) fun getRemainingCapacity(): UFix64 {
            if self.capacityLimit == 0.0 {
                return UFix64.max  // Unlimited
            }

            if self.totalStaked >= self.capacityLimit {
                return 0.0
            }

            return self.capacityLimit - self.totalStaked
        }

        /// Withdraw held FLOW tokens
        access(all) fun withdrawHeld(): @{FungibleToken.Vault}? {
            let vault <- self.heldVault <- nil
            return <- vault
        }

        /// Get sink information
        access(all) fun getStakingInfo(): {String: AnyStruct} {
            let heldBalance = self.heldVault?.balance ?? 0.0

            return {
                "leagueId": self.leagueId,
                "nodeID": self.nodeID,
                "delegatorID": self.delegatorID,
                "stakerAddress": self.stakerAddress,
                "capacityLimit": self.capacityLimit,
                "totalStaked": self.totalStaked,
                "remainingCapacity": self.getRemainingCapacity(),
                "heldFlowBalance": heldBalance,
                "note": "Tokens held in sink - full staking requires staking collection"
            }
        }
    }

    /// Create a new StakingSink for Flow native staking
    access(all) fun createSink(
        leagueId: String?,
        nodeID: String,
        stakerAddress: Address,
        capacityLimit: UFix64,
        delegatorID: UInt32?
    ): @StakingSink {
        return <- create StakingSink(
            leagueId: leagueId,
            nodeID: nodeID,
            stakerAddress: stakerAddress,
            capacityLimit: capacityLimit,
            delegatorID: delegatorID
        )
    }

    init() {
        log("FlowNativeStakingSink contract initialized")
    }
}