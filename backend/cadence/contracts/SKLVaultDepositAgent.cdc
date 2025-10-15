import FlowToken from 0x7e60df042a9c0868
import FungibleToken from 0x9a0766d93b6608b7
import FlowTransactionScheduler from 0x0 // TODO: Update with actual testnet address when available
import FlowTransactionSchedulerUtils from 0x0 // TODO: Update with actual testnet address when available

import SKLFeeCollectionSource from 0xdf978465ee6dcf32
import IncrementFiVaultSink from 0xdf978465ee6dcf32

/// SKL Vault Deposit Agent - Flow Agents Implementation
/// Implements TransactionHandler interface for automated vault deposits
///
/// This agent orchestrates the automated deposit of collected league fees
/// to IncrementFi yield vaults using Flow Actions (Source → Sink pattern)
///
/// Execution Flow:
/// 1. Check if all league fees are collected (via Source)
/// 2. If yes, aggregate fees from admin vault (Source)
/// 3. Deposit to IncrementFi Money Market (Sink)
/// 4. Record execution in database (via events)
///
/// Part of the Forte upgrade - Flow Actions & Agents automation

access(all) contract SKLVaultDepositAgent {

    /// Storage paths
    access(all) let AgentStoragePath: StoragePath
    access(all) let AgentPublicPath: PublicPath

    /// Event emitted when agent is created
    access(all) event AgentCreated(
        leagueId: String,
        agentId: String,
        scheduledTime: UFix64
    )

    /// Event emitted when agent executes successfully
    access(all) event AgentExecuted(
        leagueId: String,
        agentId: String,
        amountDeposited: UFix64,
        executionTime: UFix64
    )

    /// Event emitted when agent execution fails
    access(all) event AgentExecutionFailed(
        leagueId: String,
        agentId: String,
        reason: String,
        executionTime: UFix64
    )

    /// Public interface for the agent
    access(all) resource interface AgentPublic {
        access(all) let leagueId: String
        access(all) let agentId: String
        access(all) let poolAddress: Address
        access(all) var isExecuted: Bool
        access(all) var executionTime: UFix64?

        access(all) fun getAgentInfo(): {String: AnyStruct}
    }

    /// VaultDepositAgent resource - implements TransactionHandler for scheduled execution
    access(all) resource VaultDepositAgent: AgentPublic, FlowTransactionScheduler.TransactionHandler {

        /// League identifier
        access(all) let leagueId: String

        /// Unique agent identifier
        access(all) let agentId: String

        /// IncrementFi pool address for deposits
        access(all) let poolAddress: Address

        /// Capability to admin's FLOW vault
        access(self) let vaultCap: Capability<&{FungibleToken.Provider, FungibleToken.Balance}>

        /// Fee collection source
        access(self) var source: @SKLFeeCollectionSource.FeeCollectionSource?

        /// Vault sink
        access(self) var sink: @IncrementFiVaultSink.VaultSink?

        /// Execution status
        access(all) var isExecuted: Bool

        /// Execution timestamp
        access(all) var executionTime: UFix64?

        /// Maximum deposit capacity (0 = unlimited)
        access(self) let capacityLimit: UFix64

        init(
            leagueId: String,
            agentId: String,
            poolAddress: Address,
            vaultCap: Capability<&{FungibleToken.Provider, FungibleToken.Balance}>,
            capacityLimit: UFix64
        ) {
            self.leagueId = leagueId
            self.agentId = agentId
            self.poolAddress = poolAddress
            self.vaultCap = vaultCap
            self.capacityLimit = capacityLimit
            self.isExecuted = false
            self.executionTime = nil
            self.source <- nil
            self.sink <- nil
        }

        /// Initialize the agent with fee collection data
        /// Called by the scheduler transaction before scheduling
        access(all) fun initialize(
            totalTeams: Int,
            paidTeams: Int,
            collectedAmount: UFix64,
            supplierAddress: Address
        ) {
            pre {
                self.source == nil: "Agent already initialized"
                self.sink == nil: "Agent already initialized"
            }

            // Create Source connector
            self.source <-! SKLFeeCollectionSource.createSource(
                leagueId: self.leagueId,
                vaultCap: self.vaultCap,
                totalTeams: totalTeams,
                paidTeams: paidTeams,
                collectedAmount: collectedAmount
            )

            // Create Sink connector
            self.sink <-! IncrementFiVaultSink.createSink(
                leagueId: self.leagueId,
                poolAddress: self.poolAddress,
                supplierAddress: supplierAddress,
                capacityLimit: self.capacityLimit
            )

            log("Agent initialized for league: ".concat(self.leagueId))
        }

        /// Execute the scheduled transaction - TransactionHandler interface
        /// This is called automatically by Flow's scheduled transaction system
        access(FlowTransactionScheduler.Execute)
        fun executeTransaction(data: {String: AnyStruct}) {
            pre {
                !self.isExecuted: "Agent already executed"
                self.source != nil: "Agent not initialized - source is nil"
                self.sink != nil: "Agent not initialized - sink is nil"
            }

            let currentTime = getCurrentBlock().timestamp

            // Borrow references to source and sink
            let sourceRef = &self.source as &SKLFeeCollectionSource.FeeCollectionSource?
                ?? panic("Could not borrow source reference")
            let sinkRef = &self.sink as &IncrementFiVaultSink.VaultSink?
                ?? panic("Could not borrow sink reference")

            // Check if source is ready (all fees paid)
            if !sourceRef.isReady() {
                emit AgentExecutionFailed(
                    leagueId: self.leagueId,
                    agentId: self.agentId,
                    reason: "Not all league fees have been collected",
                    executionTime: currentTime
                )
                self.isExecuted = true
                self.executionTime = currentTime
                return
            }

            // Get the amount to deposit
            let amount = sourceRef.getAvailableAmount()

            if amount <= 0.0 {
                emit AgentExecutionFailed(
                    leagueId: self.leagueId,
                    agentId: self.agentId,
                    reason: "No fees available to deposit",
                    executionTime: currentTime
                )
                self.isExecuted = true
                self.executionTime = currentTime
                return
            }

            // Source tokens from collected fees
            let vault <- sourceRef.source(amount: amount)

            // Sink tokens to IncrementFi vault
            sinkRef.sink(vault: <- vault)

            // Mark as executed
            self.isExecuted = true
            self.executionTime = currentTime

            // Emit success event
            emit AgentExecuted(
                leagueId: self.leagueId,
                agentId: self.agentId,
                amountDeposited: amount,
                executionTime: currentTime
            )

            log("Agent executed successfully: "
                .concat(amount.toString())
                .concat(" FLOW deposited for league ")
                .concat(self.leagueId))
        }

        /// Get agent information
        access(all) fun getAgentInfo(): {String: AnyStruct} {
            var sourceInfo: {String: AnyStruct}? = nil
            var sinkInfo: {String: AnyStruct}? = nil

            if let sourceRef = &self.source as &SKLFeeCollectionSource.FeeCollectionSource? {
                sourceInfo = sourceRef.getLeagueInfo()
            }

            if let sinkRef = &self.sink as &IncrementFiVaultSink.VaultSink? {
                sinkInfo = sinkRef.getSinkInfo()
            }

            return {
                "leagueId": self.leagueId,
                "agentId": self.agentId,
                "poolAddress": self.poolAddress,
                "isExecuted": self.isExecuted,
                "executionTime": self.executionTime,
                "capacityLimit": self.capacityLimit,
                "source": sourceInfo,
                "sink": sinkInfo
            }
        }

        destroy() {
            destroy self.source
            destroy self.sink
        }
    }

    /// Create a new VaultDepositAgent
    access(all) fun createAgent(
        leagueId: String,
        agentId: String,
        poolAddress: Address,
        vaultCap: Capability<&{FungibleToken.Provider, FungibleToken.Balance}>,
        capacityLimit: UFix64
    ): @VaultDepositAgent {
        emit AgentCreated(
            leagueId: leagueId,
            agentId: agentId,
            scheduledTime: getCurrentBlock().timestamp
        )

        return <- create VaultDepositAgent(
            leagueId: leagueId,
            agentId: agentId,
            poolAddress: poolAddress,
            vaultCap: vaultCap,
            capacityLimit: capacityLimit
        )
    }

    init() {
        // Set storage paths
        self.AgentStoragePath = /storage/SKLVaultDepositAgent
        self.AgentPublicPath = /public/SKLVaultDepositAgent

        log("SKL Vault Deposit Agent contract initialized")
    }
}
