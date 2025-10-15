import FlowToken from 0x7e60df042a9c0868
import FungibleToken from 0x9a0766d93b6608b7
import FlowTransactionScheduler from 0x0 // TODO: Update with actual testnet address when available
import FlowTransactionSchedulerUtils from 0x0 // TODO: Update with actual testnet address when available

import SKLVaultDepositAgent from 0xdf978465ee6dcf32

/// Transaction to schedule an automated vault deposit agent
/// This creates and schedules a Flow Agent that will automatically
/// deposit collected league fees to IncrementFi when executed
///
/// @param leagueId: Unique identifier for the league
/// @param poolAddress: IncrementFi LendingPool address (0x8aaca41f09eb1e3d for FLOW on testnet)
/// @param totalTeams: Total number of teams in the league
/// @param paidTeams: Number of teams that have paid their fees
/// @param collectedAmount: Total FLOW collected from all teams
/// @param executionDelaySeconds: Seconds until agent executes (e.g., 3600 for 1 hour)
/// @param priority: Execution priority (High/Medium/Low)
/// @param executionEffort: Gas limit for execution
/// @param feeAmount: FLOW amount to pay for scheduled transaction fees
/// @param capacityLimit: Maximum deposit capacity (0 for unlimited)
///
/// Example:
/// leagueId: "TEST_VAULT_001"
/// poolAddress: 0x8aaca41f09eb1e3d
/// totalTeams: 10
/// paidTeams: 10
/// collectedAmount: 500.0
/// executionDelaySeconds: 3600
/// priority: "Medium"
/// executionEffort: 1000
/// feeAmount: 1.0
/// capacityLimit: 0.0

transaction(
    leagueId: String,
    poolAddress: Address,
    totalTeams: Int,
    paidTeams: Int,
    collectedAmount: UFix64,
    executionDelaySeconds: UFix64,
    priority: String,
    executionEffort: UInt64,
    feeAmount: UFix64,
    capacityLimit: UFix64
) {

    let signerAddress: Address
    let vaultRef: auth(FungibleToken.Withdraw) &FlowToken.Vault
    let agent: @SKLVaultDepositAgent.VaultDepositAgent
    let manager: &FlowTransactionSchedulerUtils.Manager
    let agentId: String

    prepare(signer: auth(BorrowValue, SaveValue, Storage, Capabilities) &Account) {
        self.signerAddress = signer.address

        // Validate inputs
        if totalTeams <= 0 {
            panic("Total teams must be greater than 0")
        }

        if collectedAmount <= 0.0 {
            panic("Collected amount must be greater than 0")
        }

        if executionDelaySeconds < 60.0 {
            panic("Execution delay must be at least 60 seconds")
        }

        if feeAmount <= 0.0 {
            panic("Fee amount must be greater than 0")
        }

        // Generate unique agent ID
        self.agentId = leagueId
            .concat("_agent_")
            .concat(getCurrentBlock().timestamp.toString())

        // Get reference to signer's FlowToken vault
        self.vaultRef = signer.storage.borrow<auth(FungibleToken.Withdraw) &FlowToken.Vault>(
            from: /storage/flowTokenVault
        ) ?? panic("Could not borrow reference to signer's FlowToken Vault")

        // Create vault capability for the agent
        let vaultCap = signer.capabilities.storage
            .issue<&{FungibleToken.Provider, FungibleToken.Balance}>(/storage/flowTokenVault)

        // Verify capability is valid
        if !vaultCap.check() {
            panic("Vault capability is invalid")
        }

        // Create the agent
        self.agent <- SKLVaultDepositAgent.createAgent(
            leagueId: leagueId,
            agentId: self.agentId,
            poolAddress: poolAddress,
            vaultCap: vaultCap,
            capacityLimit: capacityLimit
        )

        // Initialize the agent with league data
        self.agent.initialize(
            totalTeams: totalTeams,
            paidTeams: paidTeams,
            collectedAmount: collectedAmount,
            supplierAddress: signer.address
        )

        // Get or create transaction scheduler manager
        if signer.storage.borrow<&FlowTransactionSchedulerUtils.Manager>(
            from: FlowTransactionSchedulerUtils.ManagerStoragePath
        ) == nil {
            // Create new manager
            let manager <- FlowTransactionSchedulerUtils.createManager()
            signer.storage.save(<-manager, to: FlowTransactionSchedulerUtils.ManagerStoragePath)

            // Create public capability
            let managerCap = signer.capabilities.storage.issue<&FlowTransactionSchedulerUtils.Manager>(
                FlowTransactionSchedulerUtils.ManagerStoragePath
            )
            signer.capabilities.publish(managerCap, at: FlowTransactionSchedulerUtils.ManagerPublicPath)
        }

        // Borrow manager reference
        self.manager = signer.storage.borrow<&FlowTransactionSchedulerUtils.Manager>(
            from: FlowTransactionSchedulerUtils.ManagerStoragePath
        ) ?? panic("Could not borrow Manager reference")

        log("Agent created for league: ".concat(leagueId))
        log("Agent ID: ".concat(self.agentId))
        log("Execution delay: ".concat(executionDelaySeconds.toString()).concat(" seconds"))
    }

    execute {
        // Calculate execution timestamp
        let currentTime = getCurrentBlock().timestamp
        let executionTimestamp = currentTime + executionDelaySeconds

        // Convert priority string to enum
        let priorityEnum: FlowTransactionScheduler.Priority
        switch priority {
            case "High":
                priorityEnum = FlowTransactionScheduler.Priority.High
            case "Low":
                priorityEnum = FlowTransactionScheduler.Priority.Low
            default:
                priorityEnum = FlowTransactionScheduler.Priority.Medium
        }

        // Withdraw fees for scheduled transaction
        let fees <- self.vaultRef.withdraw(amount: feeAmount)

        // Create handler capability
        let handlerCap = Capability<&{FlowTransactionScheduler.TransactionHandler}>(
            &self.agent as &{FlowTransactionScheduler.TransactionHandler}
        )

        // Schedule the transaction
        let transactionData: {String: AnyStruct} = {
            "leagueId": leagueId,
            "agentId": self.agentId,
            "scheduledAt": currentTime,
            "executeAt": executionTimestamp
        }

        self.manager.schedule(
            handlerCap: handlerCap,
            data: transactionData,
            timestamp: executionTimestamp,
            priority: priorityEnum,
            executionEffort: executionEffort,
            fees: <-fees
        )

        // Store the agent in signer's storage
        let agentStoragePath = StoragePath(identifier: "SKLAgent_".concat(leagueId))!
        let agentPublicPath = PublicPath(identifier: "SKLAgent_".concat(leagueId))!

        // Save agent to storage
        signer.storage.save(<-self.agent, to: agentStoragePath)

        // Create and publish public capability
        let agentCap = signer.capabilities.storage.issue<&SKLVaultDepositAgent.VaultDepositAgent>(
            agentStoragePath
        )
        signer.capabilities.publish(agentCap, at: agentPublicPath)

        log("Agent scheduled successfully!")
        log("Execution time: ".concat(executionTimestamp.toString()))
        log("Agent will execute at: ".concat(executionTimestamp.toString()))
        log("Current time: ".concat(currentTime.toString()))
        log("Agent storage path: ".concat(agentStoragePath.toString()))
    }

    post {
        self.agentId.length > 0: "Agent ID was not set properly"
    }
}
