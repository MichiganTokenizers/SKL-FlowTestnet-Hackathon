// TESTNET CONTRACT ADDRESSES
import FlowToken from 0x7e60df042a9c0868
import FungibleToken from 0x9a0766d93b6608b7
import FUSD from 0xe223d8a629e49c68

transaction {
    prepare(signer: auth(Storage, Capabilities) &Account) {
        // Setup FlowToken Vault if not already set up
        if signer.storage.borrow<&FlowToken.Vault>(from: /storage/flowTokenVault) == nil {
            // Create a new FlowToken Vault and save it to storage
            signer.storage.save(<- FlowToken.createEmptyVault(), to: /storage/flowTokenVault)

            // Create a public capability to the Vault that only exposes the deposit function
            signer.capabilities.publish(
                signer.capabilities.storage.issue<&FlowToken.Vault>(/storage/flowTokenVault),
                at: /public/flowTokenReceiver
            )
        }

        // Setup FUSD Vault if not already set up
        if signer.storage.borrow<&FUSD.Vault>(from: /storage/fusdVault) == nil {
            // Create a new FUSD Vault and save it to storage
            signer.storage.save(<- FUSD.createEmptyVault(), to: /storage/fusdVault)

            // Create a public capability to the Vault that only exposes the deposit function
            signer.capabilities.publish(
                signer.capabilities.storage.issue<&FUSD.Vault>(/storage/fusdVault),
                at: /public/fusdReceiver
            )
        }
    }
} 