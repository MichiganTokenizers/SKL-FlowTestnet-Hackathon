import FlowToken from 0x1654653399040a61
import FungibleToken from 0xf233dcee88fe0abe
import FUSD from 0x3c5959b568896393

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