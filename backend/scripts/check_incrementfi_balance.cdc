import FlowToken from 0x7e60df042a9c0868
import FungibleToken from 0x9a0766d93b6608b7

// IncrementFi Lending Protocol Testnet Imports
import LendingInterfaces from 0x8bc9e24c307d249b
import LendingConfig from 0x8bc9e24c307d249b

/// Script to query the balance of FLOW tokens in IncrementFi Money Market
/// Returns the supplied balance (principal + accrued interest)
///
/// @param accountAddress: SKL admin wallet address
/// @param poolAddress: LendingPool contract address (0x8aaca41f09eb1e3d for FLOW on testnet)
/// @return UFix64: Total balance in the lending pool (principal + yield)
///
/// Example usage:
/// flow scripts execute backend/scripts/check_incrementfi_balance.cdc 0xdf978465ee6dcf32 0x8aaca41f09eb1e3d --network testnet

access(all) fun main(accountAddress: Address, poolAddress: Address): UFix64 {
    // Get reference to the LendingPool
    let poolRef = getAccount(poolAddress)
        .capabilities.get<&{LendingInterfaces.PoolPublic}>(/public/incrementLendingPool)
        .borrow()
        ?? panic("Could not borrow reference to LendingPool at address ".concat(poolAddress.toString()))

    // Get the supply balance for the account
    // This represents the total value (principal + interest) the account can redeem
    let supplyBalance = poolRef.getAccountSupplyBalance(account: accountAddress)

    return supplyBalance
}
