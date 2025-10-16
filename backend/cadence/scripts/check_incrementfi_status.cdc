import LiquidStaking from 0xe45c64ecfe31e465

/// Script to check IncrementFi liquid staking status
/// Returns information about whether staking is currently available
///
/// Usage:
/// flow scripts execute check_incrementfi_status.cdc --network testnet

access(all) fun main(): {String: AnyStruct} {
    // Get the epoch info from IncrementFi
    let epochInfo = LiquidStaking.getEpochInfo()

    return {
        "epochInfo": epochInfo,
        "message": "Check if protocol epoch matches chain epoch to determine if staking is available"
    }
}