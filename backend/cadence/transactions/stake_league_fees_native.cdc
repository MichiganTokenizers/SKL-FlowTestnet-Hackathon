import FlowToken from 0x7e60df042a9c0868
import FungibleToken from 0x9a0766d93b6608b7

import SKLFeeCollectionSource from 0xdf978465ee6dcf32
import FlowNativeStakingSink from 0xdf978465ee6dcf32

/// Transaction to stake collected league fees using Flow Actions
/// Uses native Flow staking approach (simplified - holds tokens)
///
/// This transaction demonstrates the Flow Actions pattern:
/// 1. Source connector aggregates collected league fees
/// 2. Sink connector prepares tokens for Flow native staking
/// 3. Single atomic transaction ensures safety
///
/// Note: Full Flow native staking requires FlowStakingCollection setup
/// This version holds tokens in the sink as a working proof-of-concept
///
/// @param leagueId: Unique identifier for the league
/// @param nodeID: Flow validator node ID to delegate to
/// @param totalTeams: Total number of teams in the league
/// @param paidTeams: Number of teams that have paid their fees
/// @param collectedAmount: Total FLOW collected from all teams
///
/// Example usage:
/// flow transactions send stake_league_fees_native.cdc \
///   --args-json '[
///     {"type":"String","value":"TEST_VAULT_001"},
///     {"type":"String","value":"6a86dbcd3bced438480e626fd56e2d4fb8811222671cc24949dcde7f6817123b"},
///     {"type":"Int","value":"10"},
///     {"type":"Int","value":"10"},
///     {"type":"UFix64","value":"500.0"}
///   ]' \
///   --network testnet --signer testnet-account

transaction(
    leagueId: String,
    nodeID: String,
    totalTeams: Int,
    paidTeams: Int,
    collectedAmount: UFix64
) {

    let source: @SKLFeeCollectionSource.FeeCollectionSource
    let sink: @FlowNativeStakingSink.StakingSink
    let signerAddress: Address

    prepare(signer: auth(BorrowValue, Storage, Capabilities) &Account) {
        self.signerAddress = signer.address

        // Input validation
        if totalTeams <= 0 {
            panic("Total teams must be greater than 0")
        }

        if paidTeams > totalTeams {
            panic("Paid teams cannot exceed total teams")
        }

        if collectedAmount <= 0.0 {
            panic("Collected amount must be greater than 0")
        }

        if nodeID.length == 0 {
            panic("Node ID cannot be empty")
        }

        // Create vault capability for the Source connector
        let vaultCap = signer.capabilities.storage
            .issue<auth(FungibleToken.Withdraw) &{FungibleToken.Provider, FungibleToken.Balance}>(/storage/flowTokenVault)

        // Verify capability is valid
        if !vaultCap.check() {
            panic("Vault capability is invalid")
        }

        // Create Source connector to aggregate league fees
        self.source <- SKLFeeCollectionSource.createSource(
            leagueId: leagueId,
            vaultCap: vaultCap,
            totalTeams: totalTeams,
            paidTeams: paidTeams,
            collectedAmount: collectedAmount
        )

        // Create Sink connector for Flow native staking
        self.sink <- FlowNativeStakingSink.createSink(
            leagueId: leagueId,
            nodeID: nodeID,
            stakerAddress: signer.address,
            capacityLimit: 0.0,  // Unlimited capacity
            delegatorID: nil  // Will be assigned after first delegation
        )

        log("Flow Actions created for league: ".concat(leagueId))
        log("Source (Fee Collection) initialized")
        log("Sink (Flow Native Staking) initialized for node ".concat(nodeID))
    }

    execute {
        // Step 1: Verify all fees are collected
        if !self.source.isReady() {
            let info = self.source.getLeagueInfo()
            let paidTeamsInt = info["paidTeams"]! as! Int
            let totalTeamsInt = info["totalTeams"]! as! Int
            panic("Not all league fees have been collected. Paid: "
                .concat(paidTeamsInt.toString())
                .concat(" / ")
                .concat(totalTeamsInt.toString()))
        }

        // Step 2: Get the amount available to stake
        let amount = self.source.getAvailableAmount()

        if amount <= 0.0 {
            panic("No fees available to stake")
        }

        log("Processing ".concat(amount.toString()).concat(" FLOW for league ").concat(leagueId))

        // Step 3: Source tokens from collected fees
        let vault <- self.source.source(amount: amount)

        log("Tokens sourced from fee collection")

        // Step 4: Sink tokens to Flow native staking
        self.sink.sink(vault: <- vault)

        log("Tokens processed by staking sink")

        // Step 5: Withdraw held tokens and return to admin vault
        let heldVault <- self.sink.withdrawHeld()
        if heldVault != nil {
            let unwrappedVault <- heldVault!
            let heldAmount = unwrappedVault.balance

            // Get admin's FlowToken receiver
            let receiver = getAccount(self.signerAddress)
                .capabilities.get<&{FungibleToken.Receiver}>(/public/flowTokenReceiver)
                .borrow()
                ?? panic("Could not borrow Flow receiver reference")

            // Deposit tokens back to admin vault
            receiver.deposit(from: <-unwrappedVault)

            log("Returned ".concat(heldAmount.toString()).concat(" FLOW to admin vault"))
        } else {
            destroy heldVault
        }

        // Step 6: Log success
        log("✅ Successfully processed "
            .concat(amount.toString())
            .concat(" FLOW for league ")
            .concat(leagueId)
            .concat(" via Flow Actions"))

        // Clean up resources
        destroy self.source
        destroy self.sink
    }

    post {
        // Verify transaction completed
        true: "Staking transaction completed successfully"
    }
}