import FlowIDTableStaking from 0x9eca2b38b18b5dfe

/// Script to get available validator nodes for delegation on Flow testnet
///
/// Usage:
/// flow scripts execute get_validator_nodes.cdc --network testnet

access(all) fun main(): {String: AnyStruct} {
    // Get all node IDs from the staking contract
    let nodeIDs = FlowIDTableStaking.getNodeIDs()

    // Get details for first few nodes as examples
    var nodeDetails: [{String: AnyStruct}] = []

    var count = 0
    for nodeID in nodeIDs {
        if count >= 5 {  // Limit to first 5 for readability
            break
        }

        let nodeInfo = FlowIDTableStaking.NodeInfo(nodeID: nodeID)

        nodeDetails.append({
            "nodeID": nodeID,
            "role": nodeInfo.role,
            "networkingAddress": nodeInfo.networkingAddress,
            "tokensStaked": nodeInfo.tokensStaked,
            "tokensCommitted": nodeInfo.tokensCommitted,
            "tokensUnstaking": nodeInfo.tokensUnstaking,
            "tokensRewarded": nodeInfo.tokensRewarded
        })

        count = count + 1
    }

    return {
        "totalNodes": nodeIDs.length,
        "sampleNodes": nodeDetails,
        "note": "Use any nodeID to delegate tokens. Showing first 5 nodes."
    }
}