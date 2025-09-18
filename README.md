# Supreme Keeper League

**Built on Flow** - A decentralized fantasy football platform that revolutionizes keeper league management through blockchain technology and seamless Sleeper API integration.

## 🏈 Overview

Supreme Keeper League is a cutting-edge fantasy football platform that combines the excitement of keeper leagues with the transparency and security of blockchain technology. Built on the Flow blockchain, it provides a decentralized, user-friendly environment for managing fantasy football leagues with smart contracts, secure transactions, and comprehensive league analytics.

## 🔗 Flow Blockchain Integration

This project is **Built on Flow** and leverages the Flow ecosystem for:

- **Secure Transactions**: All league fees and payouts processed through Flow blockchain
- **Automated Sleeper Integration**: Automated penalty systems and user controlled contract management
- **FlowConnect Integration**: Seamless wallet authentication for account functions 


### Flow Components Used
- **@onflow/fcl**: Flow Client Library for blockchain interactions
- **@onflow/types**: TypeScript definitions for Flow
- **Cadence Smart Contracts**: Custom contracts for account setup and token management
- **Flow Wallet Integration**: Secure user authentication and transaction signing

### Contract Addresses
- **Flow Network**: Mainnet (`access.mainnet.nodes.onflow.org:9000`)
- **Account Setup Contract**: See `setup_account.cdc`
- **Flow Configuration**: See `flow.json`

## ✨ Key Features

### 🏆 League Management
- **Supreme Keeper League Support**: Multi-year player contracts with escalating costs
- **Franchise Tag System**: Designate one player per team with calculated tag values
- **Penalty System**: Automated penalties for waived players with active contracts
- **Real-time Analytics**: Positional spending ranks and future contract projections

### 💰 Financial Transparency
- **Blockchain Payments**: League fees processed through Flow blockchain, links to transactions posted
- **Automated Payouts**: Smart contract-based prize distribution
- **Budget Tracking**: Real-time auction budget management for team management over 4 years

### 🔄 Sleeper Integration
- **One-time Data Sync**: Efficient data pull from Sleeper API
- **Local Database**: SQLite storage for fast, reliable data access
- **Roster Management**: Seamless integration with Sleeper's roster system
- **League Filtering**: Automatic import of SKL-prefixed leagues

### 🎯 User Experience
- **Flow Wallet Login**: Secure authentication via Flow blockchain
- **Responsive Design**: Modern UI built with React and Bootstrap
- **Real-time Updates**: Live league standings and transaction tracking


## 🛠️ Technology Stack

### Frontend
- **React.js**: Modern, component-based UI framework
- **FlowConnect**: Flow blockchain integration
- **Bootstrap**: Responsive design and styling
- **React Router**: Client-side navigation

### Backend
- **Flask**: Lightweight Python web framework
- **SQLite**: Local database for efficient data storage
- **Sleeper API**: Fantasy football data integration
- **Flow SDK**: Blockchain transaction processing

### Blockchain
- **Flow Network**: Scalable, developer-friendly blockchain
- **Cadence**: Resource-oriented smart contract language
- **FlowToken & FUSD**: Native and stable token support

## 🚀 Getting Started

### Prerequisites
- Node.js (v16 or higher)
- Python 3.8+
- Flow CLI
- Flow wallet (Blocto, Ledger, or other compatible wallet)


## 📊 Database Schema

The application uses SQLite with the following key tables:
- **Users**: Wallet addresses and Sleeper associations
- **Leagues**: League metadata and settings
- **Rosters**: Team compositions and records
- **Contracts**: Player contracts with escalation logic
- **Transactions**: All league activities and trades
- **Penalties**: Automated penalty tracking


## 🔧 Development

### Project Structure
```
supremekeeperleague-Flow/
├── frontend/          # React.js frontend
├── backend/           # Flask API backend
├── cadence/           # Smart contracts
├── tests/             # Unit tests
├── flow.json          # Flow configuration
└── setup_account.cdc  # Account setup contract
```
## 🔗 Links

- **Flow Documentation**: https://docs.onflow.org/
- **Sleeper API**: https://docs.sleeper.com/
- **Project Planning**: See `planning.md` for detailed architecture

## 🏆 ReWTF Program

This project is participating in the Flow ReWTF (Reward the Flow) program, building in public and contributing to the Flow ecosystem. Follow our progress with `#ReWTF` and `@flow_blockchain`!

---


