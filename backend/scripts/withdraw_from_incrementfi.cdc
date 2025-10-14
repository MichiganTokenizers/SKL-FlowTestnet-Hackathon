import FlowToken from 0x7e60df042a9c0868
import FungibleToken from 0x9a0766d93b6608b7

// IncrementFi Lending Protocol Testnet Imports
import LendingInterfaces from 0x8bc9e24c307d249b
import LendingConfig from 0x8bc9e24c307d249b
import LendingComptroller from 0xc15e75b5f6b95e54
import LendingPool from 0x8aaca41f09eb1e3d

/// Transaction to withdraw FLOW tokens from IncrementFi Money Market (LendingPool)
/// Used by SKL admin wallet to retrieve principal + yield for prize distribution
///
/// @param amount: Amount of FLOW to withdraw (can be partial or full balance)
/// @param poolAddress: LendingPool contract address (0x8aaca41f09eb1e3d for FLOW on testnet)
/// @param leagueId: League identifier for tracking in database
///
/// Example:
/// amount: 500.123456
/// poolAddress: 0x8aaca41f09eb1e3d
/// leagueId: "TEST_LEAGUE_001"

transaction(amount: UFix64, poolAddress: Address, leagueId: String) {

    let poolAddress: Address
    let signerAddress: Address
    let receiverRef: &{FungibleToken.Receiver}
    let balanceBefore: UFix64

    prepare(signer: auth(BorrowValue, Storage) &Account) {
        // Store signer address for execute phase
        self.signerAddress = signer.address
        // Validate inputs
        if amount <= 0.0 {
            panic("Withdrawal amount must be greater than 0")
        }

        // Store pool address for execute phase
        self.poolAddress = poolAddress

        // Get reference to signer's FlowToken vault for receiving
        self.receiverRef = signer.storage.borrow<&{FungibleToken.Receiver}>(
            from: /storage/flowTokenVault
        ) ?? panic("Could not borrow reference to the signer's FlowToken Vault receiver")

        // Get current balance for verification
        let vaultRef = signer.storage.borrow<&FlowToken.Vault>(
            from: /storage/flowTokenVault
        ) ?? panic("Could not borrow reference to check balance")

        self.balanceBefore = vaultRef.balance

        // Emit event for backend tracking
        log("SKL IncrementFi Withdrawal Started")
        log("League ID: ".concat(leagueId))
        log("Amount: ".concat(amount.toString()).concat(" FLOW"))
        log("Pool Address: ".concat(poolAddress.toString()))
        log("Wallet Balance Before: ".concat(self.balanceBefore.toString()).concat(" FLOW"))
    }

    execute {
        // Get reference to the LendingPool contract
        // IncrementFi deploys LendingPool as a contract at the pool address
        // We can access its public functions directly via contract import
        let poolContract = getAccount(self.poolAddress).contracts.borrow<&LendingPool>(name: "LendingPool")
            ?? panic("Could not borrow reference to LendingPool contract at address ".concat(self.poolAddress.toString()))

        // Redeem underlying FLOW from the pool
        // IncrementFi's redeemUnderlying() method withdraws the underlying token (FLOW)
        // It takes the redeemer's address and the amount to withdraw
        let withdrawnVault <- poolContract.redeemUnderlying(
            redeemer: self.signerAddress,
            amount: amount
        )

        // Deposit the withdrawn tokens back to signer's vault
        self.receiverRef.deposit(from: <- withdrawnVault)

        log("SKL IncrementFi Withdrawal Completed Successfully")
        log("Tokens withdrawn from IncrementFi Money Market to SKL wallet")
    }
}
