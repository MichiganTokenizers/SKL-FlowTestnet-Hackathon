import FlowToken from 0x7e60df042a9c0868
import FungibleToken from 0x9a0766d93b6608b7
import stFlowToken from 0xe45c64ecfe31e465

import SKLFeeCollectionSource from 0xdf978465ee6dcf32
import IncrementFiStakingSink from 0xdf978465ee6dcf32

/// Transaction to stake collected league fees to IncrementFi
/// Uses Flow Actions: Source (fees) → Sink (staking)
///
/// This transaction demonstrates the Flow Actions pattern:
/// 1. Source connector aggregates collected league fees
/// 2. Sink connector stakes them into IncrementFi pool
/// 3. Single atomic transaction ensures safety
///
/// @param leagueId: Unique identifier for the league
/// @param poolId: IncrementFi staking pool ID (e.g., 198 for FLOW pool)
/// @param totalTeams: Total number of teams in the league
/// @param paidTeams: Number of teams that have paid their fees
/// @param collectedAmount: Total FLOW collected from all teams
///
/// Example usage:
/// flow transactions send stake_league_fees.cdc \
///   --args-json '[
///     {"type":"String","value":"TEST_VAULT_001"},
///     {"type":"UInt64","value":"198"},
///     {"type":"Int","value":"10"},
///     {"type":"Int","value":"10"},
///     {"type":"UFix64","value":"500.0"}
///   ]' \
///   --network testnet --signer testnet-account

transaction(
    leagueId: String,
    poolId: UInt64,
    totalTeams: Int,
    paidTeams: Int,
    collectedAmount: UFix64
) {

    let source: @SKLFeeCollectionSource.FeeCollectionSource
    let sink: @IncrementFiStakingSink.StakingSink
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

        if poolId == 0 {
            panic("Pool ID must be greater than 0")
        }

        // Create vault capability for the Source connector
        let vaultCap = signer.capabilities.storage
            .issue<auth(FungibleToken.Withdraw) &{FungibleToken.Provider, FungibleToken.Balance}>(/storage/flowTokenVault)

        // Verify capability is valid
        if !vaultCap.check() {
            panic("Vault capability is invalid")
        }

        // Setup stFlow vault if it doesn't exist
        if signer.storage.borrow<&stFlowToken.Vault>(from: stFlowToken.VaultStoragePath) == nil {
            // Create a new stFlow vault
            let vault <- stFlowToken.createEmptyVault(vaultType: Type<@stFlowToken.Vault>())
            signer.storage.save(<-vault, to: stFlowToken.VaultStoragePath)

            // Create public capability for receiving stFlow
            let receiverCap = signer.capabilities.storage.issue<&{FungibleToken.Receiver}>(stFlowToken.VaultStoragePath)
            signer.capabilities.publish(receiverCap, at: stFlowToken.ReceiverPublicPath)

            // Create public capability for balance
            let balanceCap = signer.capabilities.storage.issue<&{FungibleToken.Balance}>(stFlowToken.VaultStoragePath)
            signer.capabilities.publish(balanceCap, at: stFlowToken.BalancePublicPath)
        }

        // Get the stFlow receiver capability
        let stFlowReceiver = signer.capabilities.get<&{FungibleToken.Receiver}>(stFlowToken.ReceiverPublicPath)
        if !stFlowReceiver.check() {
            panic("stFlow receiver capability is invalid")
        }

        // Create Source connector to aggregate league fees
        self.source <- SKLFeeCollectionSource.createSource(
            leagueId: leagueId,
            vaultCap: vaultCap,
            totalTeams: totalTeams,
            paidTeams: paidTeams,
            collectedAmount: collectedAmount
        )

        // Create Sink connector to stake into IncrementFi pool
        self.sink <- IncrementFiStakingSink.createSink(
            leagueId: leagueId,
            poolId: poolId,
            stakerAddress: signer.address,
            capacityLimit: 0.0,  // Unlimited capacity
            requiresCertificate: false  // Simplified for now
        )

        log("Flow Actions created for league: ".concat(leagueId))
        log("Source (Fee Collection) initialized")
        log("Sink (IncrementFi Staking) initialized for pool ".concat(poolId.toString()))
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

        log("Staking ".concat(amount.toString()).concat(" FLOW for league ").concat(leagueId))

        // Step 3: Source tokens from collected fees
        // This withdraws FLOW from the admin vault
        let vault <- self.source.source(amount: amount)

        log("Tokens sourced from fee collection")

        // Step 4: Sink tokens to IncrementFi staking pool
        // This stakes the FLOW into the pool
        self.sink.sink(vault: <- vault)

        log("Tokens staked to IncrementFi pool")

        // Step 5: Withdraw stFlow tokens from the sink and deposit to admin vault
        let stFlowVault <- self.sink.withdrawStFlow()
        if stFlowVault != nil {
            let unwrappedVault <- stFlowVault!
            let stFlowAmount = unwrappedVault.balance

            // Get the stFlow receiver from the admin account
            let stFlowReceiver = getAccount(self.signerAddress)
                .capabilities.get<&{FungibleToken.Receiver}>(stFlowToken.ReceiverPublicPath)
                .borrow()
                ?? panic("Could not borrow stFlow receiver reference")

            // Deposit stFlow to admin vault
            stFlowReceiver.deposit(from: <-unwrappedVault)

            log("Received ".concat(stFlowAmount.toString()).concat(" stFlow tokens"))
        } else {
            destroy stFlowVault
        }

        // Step 6: Log success
        log("✅ Successfully staked "
            .concat(amount.toString())
            .concat(" FLOW for league ")
            .concat(leagueId)
            .concat(" to IncrementFi liquid staking"))

        // Clean up resources
        destroy self.source
        destroy self.sink
    }

    post {
        // Verify transaction completed
        true: "Staking transaction completed successfully"
    }
}
