// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

// Flow Configuration - TESTNET
export const FLOW_CONFIG = {
  "app.detail.title": "Supreme Keeper League",
  "app.detail.icon": "https://placekitten.com/g/200/200",
  "accessNode.api": "https://rest-testnet.onflow.org",
  "discovery.wallet": "https://fcl-discovery.onflow.org/testnet/authn",
  "walletconnect.projectId": "6703e7bf382e685009436a07efd63b22",
  "0xProfile": "0xPROFILE",
};

// SKL Payment wallet address - TESTNET
export const SKL_PAYMENT_WALLET_ADDRESS = "0xdf978465ee6dcf32"; 