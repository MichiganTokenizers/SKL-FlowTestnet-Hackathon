import { config } from "@onflow/fcl";

config({
  "app.detail.title": "Supreme Keeper League", // Name of your app
  "app.detail.icon": "https://placekitten.com/g/200/200", // URL to your app's icon
  "accessNode.api": "http://localhost:8888", // Endpoint for the Flow Emulator REST API
  "discovery.wallet": "http://localhost:8701/fcl/authn", // Endpoint for FCL Dev Wallet
  // Testnet configuration (can be uncommented later)
  // "accessNode.api": "https://rest-testnet.onflow.org",
  // "discovery.wallet": "https://fcl-discovery.onflow.org/testnet/authn",
  "0xProfile": "0xPROFILE", // Will be replaced by a real contract address later
  // Add other contract placeholders if known, e.g.:
  // "0xFungibleToken": "0xee82856bf20e2aa6", (Testnet FT)
  // "0xFlowToken": "0x7e60df042a9c0868" (Testnet FlowToken)
}); 