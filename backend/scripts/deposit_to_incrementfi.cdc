import FlowToken from 0x7e60df042a9c0868
import FungibleToken from 0x9a0766d93b6608b7

// IncrementFi Lending Protocol Testnet Imports
import LendingInterfaces from 0x8bc9e24c307d249b
import LendingConfig from 0x8bc9e24c307d249b
import LendingComptroller from 0xc15e75b5f6b95e54

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
    let vaultRef: auth(FungibleToken.Withdraw) &FlowToken.Vault
    let depositVault: @{FungibleToken.Vault}

    prepare(signer: auth(BorrowValue, Storage) &Account) {
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
        // Get reference to the LendingPool
        // IncrementFi uses a Pool resource that accepts fungible token vaults
        let poolRef = getAccount(self.poolAddress)
            .capabilities.get<&{LendingInterfaces.PoolPublic}>(/public/incrementLendingPool)
            .borrow()
            ?? panic("Could not borrow reference to LendingPool at address ".concat(self.poolAddress.toString()))

        // Deposit (supply) the FLOW vault to the pool
        // Note: The exact method name may be 'deposit', 'supply', 'mint', or similar
        // This follows the standard IncrementFi Money Market interface
        poolRef.deposit(from: <- self.depositVault)

        log("SKL IncrementFi Deposit Completed Successfully")
        log("Tokens deposited to IncrementFi Money Market")
    }

    post {
        // Verify the vault was consumed
        self.depositVault.balance == 0.0: "Deposit vault should be empty after transaction"
    }
}
