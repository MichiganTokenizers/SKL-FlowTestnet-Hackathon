import FlowToken from 0x7e60df042a9c0868
import FungibleToken from 0x9a0766d93b6608b7

/// SKL Fee Collection Source - Flow Actions Connector
/// Implements the Source interface to provide collected league fees for vault deposit
///
/// This connector checks if all teams in a league have paid their fees,
/// and if so, provides the total collected amount as a FungibleToken vault
/// for further processing (typically depositing to IncrementFi yield vault)
///
/// Part of the Forte upgrade - Flow Actions & Agents automation

access(all) contract SKLFeeCollectionSource {

    /// Event emitted when fees are successfully collected
    access(all) event FeesCollected(
        leagueId: String,
        amount: UFix64,
        totalTeams: Int,
        paidTeams: Int
    )

    /// Event emitted when fee collection fails
    access(all) event FeeCollectionFailed(
        leagueId: String,
        reason: String
    )

    /// Source interface implementation for Flow Actions
    /// Provides tokens on demand by aggregating collected league fees
    access(all) resource interface SourceInterface {
        /// Get the available amount that can be sourced
        access(all) fun getAvailableAmount(): UFix64

        /// Check if the source is ready to provide tokens
        access(all) fun isReady(): Bool

        /// Source tokens from collected fees
        access(all) fun source(amount: UFix64): @{FungibleToken.Vault}
    }

    /// FeeCollectionSource resource that holds league fee collection logic
    access(all) resource FeeCollectionSource: SourceInterface {

        /// The league ID this source is collecting fees for
        access(all) let leagueId: String

        /// Reference to the SKL admin vault where fees are collected
        access(self) let vaultCap: Capability<&{FungibleToken.Provider, FungibleToken.Balance}>

        /// Total number of teams in the league
        access(self) var totalTeams: Int

        /// Number of teams that have paid
        access(self) var paidTeams: Int

        /// Total collected amount
        access(self) var collectedAmount: UFix64

        /// Whether all fees have been collected
        access(self) var allFeesPaid: Bool

        init(
            leagueId: String,
            vaultCap: Capability<&{FungibleToken.Provider, FungibleToken.Balance}>,
            totalTeams: Int,
            paidTeams: Int,
            collectedAmount: UFix64
        ) {
            self.leagueId = leagueId
            self.vaultCap = vaultCap
            self.totalTeams = totalTeams
            self.paidTeams = paidTeams
            self.collectedAmount = collectedAmount
            self.allFeesPaid = (totalTeams > 0 && paidTeams == totalTeams)
        }

        /// Get the total amount available to source
        access(all) fun getAvailableAmount(): UFix64 {
            if !self.isReady() {
                return 0.0
            }
            return self.collectedAmount
        }

        /// Check if all fees are collected and ready to source
        access(all) fun isReady(): Bool {
            return self.allFeesPaid && self.collectedAmount > 0.0
        }

        /// Source the specified amount from collected fees
        /// @param amount: Amount to withdraw (must be <= collectedAmount)
        /// @return FungibleToken vault containing the sourced tokens
        access(all) fun source(amount: UFix64): @{FungibleToken.Vault} {
            pre {
                self.isReady(): "Fee collection not ready: not all teams have paid"
                amount > 0.0: "Amount must be greater than 0"
                amount <= self.collectedAmount: "Requested amount exceeds collected fees"
            }

            // Borrow reference to the vault
            let vaultRef = self.vaultCap.borrow()
                ?? panic("Could not borrow reference to admin vault")

            // Verify vault has sufficient balance
            if vaultRef.balance < amount {
                panic("Insufficient balance in admin vault. Required: "
                    .concat(amount.toString())
                    .concat(", Available: ")
                    .concat(vaultRef.balance.toString()))
            }

            // Withdraw the amount
            let withdrawn <- vaultRef.withdraw(amount: amount)

            // Update collected amount
            self.collectedAmount = self.collectedAmount - amount

            // Emit success event
            emit FeesCollected(
                leagueId: self.leagueId,
                amount: amount,
                totalTeams: self.totalTeams,
                paidTeams: self.paidTeams
            )

            return <- withdrawn
        }

        /// Update fee collection status (called by backend after database checks)
        access(all) fun updateStatus(totalTeams: Int, paidTeams: Int, collectedAmount: UFix64) {
            self.totalTeams = totalTeams
            self.paidTeams = paidTeams
            self.collectedAmount = collectedAmount
            self.allFeesPaid = (totalTeams > 0 && paidTeams == totalTeams)
        }

        /// Get league information
        access(all) fun getLeagueInfo(): {String: AnyStruct} {
            return {
                "leagueId": self.leagueId,
                "totalTeams": self.totalTeams,
                "paidTeams": self.paidTeams,
                "collectedAmount": self.collectedAmount,
                "allFeesPaid": self.allFeesPaid,
                "isReady": self.isReady()
            }
        }
    }

    /// Create a new FeeCollectionSource for a league
    access(all) fun createSource(
        leagueId: String,
        vaultCap: Capability<&{FungibleToken.Provider, FungibleToken.Balance}>,
        totalTeams: Int,
        paidTeams: Int,
        collectedAmount: UFix64
    ): @FeeCollectionSource {
        return <- create FeeCollectionSource(
            leagueId: leagueId,
            vaultCap: vaultCap,
            totalTeams: totalTeams,
            paidTeams: paidTeams,
            collectedAmount: collectedAmount
        )
    }

    init() {
        // Contract initialization
        log("SKL Fee Collection Source initialized")
    }
}
