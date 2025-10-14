import FlowToken from 0x7e60df042a9c0868
import FungibleToken from 0x9a0766d93b6608b7

// IncrementFi Lending Protocol Testnet Imports
import LendingInterfaces from 0x8bc9e24c307d249b
import LendingConfig from 0x8bc9e24c307d249b
import LendingComptroller from 0xc15e75b5f6b95e54
import LendingPool from 0x8aaca41f09eb1e3d

/// Transaction to deposit FLOW tokens to IncrementFi Money Market (LendingPool)
/// Used by SKL admin wallet to earn yield on collected league fees
///
/// @param amount: Amount of FLOW to deposit
/// @param poolAddress: LendingPool contract address (0x8aaca41f09eb1e3d for FLOW on testnet)
/// @param leagueId: League identifier for tracking in database
///
/// Example:
/// amount: 500.0
/// poolAddress: 0x8aaca41f09eb1e3d
/// leagueId: "TEST_LEAGUE_001"

transaction(amount: UFix64, poolAddress: Address, leagueId: String) {

    let poolAddress: Address
    let signerAddress: Address
    let vaultRef: auth(FungibleToken.Withdraw) &FlowToken.Vault
    let depositVault: @{FungibleToken.Vault}

    prepare(signer: auth(BorrowValue, Storage) &Account) {
        // Store signer address for execute phase
        self.signerAddress = signer.address
        // Validate inputs
        if amount <= 0.0 {
            panic("Deposit amount must be greater than 0")
        }

        // Store pool address for execute phase
        self.poolAddress = poolAddress

        // Get reference to signer's FlowToken vault
        self.vaultRef = signer.storage.borrow<auth(FungibleToken.Withdraw) &FlowToken.Vault>(
            from: /storage/flowTokenVault
        ) ?? panic("Could not borrow reference to the signer's FlowToken Vault")

        // Verify signer has enough balance
        if self.vaultRef.balance < amount {
            panic("Insufficient balance. Required: ".concat(amount.toString()).concat(" FLOW, Available: ").concat(self.vaultRef.balance.toString()).concat(" FLOW"))
        }

        // Withdraw FLOW tokens to deposit
        self.depositVault <- self.vaultRef.withdraw(amount: amount)

        // Emit event for backend tracking
        log("SKL IncrementFi Deposit Started")
        log("League ID: ".concat(leagueId))
        log("Amount: ".concat(amount.toString()).concat(" FLOW"))
        log("Pool Address: ".concat(poolAddress.toString()))
    }

    execute {
        // Get reference to the LendingPool contract
        // IncrementFi deploys LendingPool as a contract at the pool address
        // We can access its public functions directly via contract import
        let poolContract = getAccount(self.poolAddress).contracts.borrow<&LendingPool>(name: "LendingPool")
            ?? panic("Could not borrow reference to LendingPool contract at address ".concat(self.poolAddress.toString()))

        // Supply the FLOW vault to the pool
        // IncrementFi's supply() method takes the supplier address and the vault
        poolContract.supply(supplierAddr: self.signerAddress, inUnderlyingVault: <- self.depositVault)

        log("SKL IncrementFi Deposit Completed Successfully")
        log("Tokens deposited to IncrementFi Money Market")
    }
}
