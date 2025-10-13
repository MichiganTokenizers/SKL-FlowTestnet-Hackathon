import FlowToken from 0x7e60df042a9c0868
import FungibleToken from 0x9a0766d93b6608b7

/// Transaction to distribute prize money to multiple winners
/// Used by SKL admin wallet to send league prizes after season ends
///
/// @param recipients: Array of winner wallet addresses
/// @param amounts: Array of prize amounts (must match recipients length)
/// @param leagueId: League identifier for tracking
///
/// Example:
/// recipients: [0xwinner1, 0xwinner2, 0xwinner3]
/// amounts: [6.0, 3.0, 1.0] (FLOW tokens)
/// leagueId: "123456789"

transaction(recipients: [Address], amounts: [UFix64], leagueId: String) {

    let paymentVaults: @[{FungibleToken.Vault}]
    let senderRef: &FlowToken.Vault

    prepare(signer: auth(BorrowValue, Storage) &Account) {
        // Validate inputs
        if recipients.length != amounts.length {
            panic("Recipients and amounts arrays must have the same length")
        }

        if recipients.length == 0 {
            panic("Must have at least one recipient")
        }

        // Get reference to signer's FlowToken vault
        self.senderRef = signer.storage.borrow<auth(FungibleToken.Withdraw) &FlowToken.Vault>(
            from: /storage/flowTokenVault
        ) ?? panic("Could not borrow reference to the signer's FlowToken Vault")

        // Calculate total amount needed
        var totalAmount: UFix64 = 0.0
        var i = 0
        while i < amounts.length {
            totalAmount = totalAmount + amounts[i]
            i = i + 1
        }

        // Verify signer has enough balance
        if self.senderRef.balance < totalAmount {
            panic("Insufficient balance. Required: ".concat(totalAmount.toString()).concat(" FLOW, Available: ").concat(self.senderRef.balance.toString()).concat(" FLOW"))
        }

        // Withdraw individual amounts for each recipient
        self.paymentVaults <- []
        var j = 0
        while j < amounts.length {
            let vault <- self.senderRef.withdraw(amount: amounts[j])
            self.paymentVaults.append(<- vault)
            j = j + 1
        }

        // Emit event for backend tracking
        log("SKL Prize Distribution Started")
        log("League ID: ".concat(leagueId))
        log("Total Amount: ".concat(totalAmount.toString()).concat(" FLOW"))
        log("Number of Recipients: ".concat(recipients.length.toString()))
    }

    execute {
        var k = 0
        while k < recipients.length {
            // Get recipient's FlowToken receiver capability
            let recipientCap = getAccount(recipients[k])
                .capabilities.get<&{FungibleToken.Receiver}>(/public/flowTokenReceiver)

            // Borrow the receiver reference
            let receiverRef = recipientCap.borrow()
                ?? panic("Could not borrow receiver reference for address ".concat(recipients[k].toString()))

            // Deposit the payment
            let payment <- self.paymentVaults.remove(at: 0)

            log("Distributing ".concat(amounts[k].toString()).concat(" FLOW to ").concat(recipients[k].toString()))

            receiverRef.deposit(from: <- payment)

            k = k + 1
        }

        // Destroy the empty array
        destroy self.paymentVaults

        log("SKL Prize Distribution Completed Successfully")
    }
}
