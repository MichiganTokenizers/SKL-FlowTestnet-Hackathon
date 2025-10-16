import FlowEpoch from 0x9eca2b38b18b5dfe
import DelegatorManager from 0xe45c64ecfe31e465
import FlowIDTableStaking from 0x9eca2b38b18b5dfe

/// Script to check if IncrementFi protocol epoch is synced with Flow chain epoch
/// This is the exact check that blocks staking in LiquidStaking.stake()
///
/// The pre-condition that's failing:
/// FlowEpoch.currentEpochCounter == DelegatorManager.quoteEpochCounter
///
/// Usage:
/// flow scripts execute check_epoch_sync.cdc --network testnet

access(all) fun main(): {String: AnyStruct} {
    // Get Flow blockchain's current epoch
    let flowChainEpoch = FlowEpoch.currentEpochCounter

    // Get IncrementFi protocol's current epoch
    let protocolEpoch = DelegatorManager.quoteEpochCounter

    // Check if they're synced
    let isSynced = flowChainEpoch == protocolEpoch

    // Check if staking is enabled on Flow blockchain
    let stakingEnabled = FlowIDTableStaking.stakingEnabled()

    // Get current epoch metadata
    let epochMetadata = FlowEpoch.getEpochMetadata(flowChainEpoch)

    return {
        "flowChainEpoch": flowChainEpoch,
        "protocolEpoch": protocolEpoch,
        "epochsMatch": isSynced,
        "epochDifference": flowChainEpoch > protocolEpoch ? flowChainEpoch - protocolEpoch : protocolEpoch - flowChainEpoch,
        "stakingEnabled": stakingEnabled,
        "currentEpochMetadata": epochMetadata,
        "status": isSynced && stakingEnabled ? "✅ Staking Available" : "❌ Staking Blocked",
        "blockingReason": isSynced ? (stakingEnabled ? "None" : "Flow staking not in auction period") : "Protocol epoch not synced with chain epoch"
    }
}