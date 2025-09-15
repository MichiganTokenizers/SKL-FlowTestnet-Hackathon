# Supreme Keeper League

**Built on Flow** - A decentralized fantasy football platform that revolutionizes keeper league management through blockchain technology and seamless Sleeper API integration.

## 🏈 Overview

Supreme Keeper League is a cutting-edge fantasy football platform that combines the excitement of keeper leagues with the transparency and security of blockchain technology. Built on the Flow blockchain, it provides a decentralized, user-friendly environment for managing fantasy football leagues with smart contracts, secure transactions, and comprehensive league analytics.

## 🔗 Flow Blockchain Integration

This project is **Built on Flow** and leverages the Flow ecosystem for:

- **Secure Transactions**: All league fees and payouts processed through Flow blockchain
- **Smart Contracts**: Automated contract management and penalty systems
- **FlowConnect Integration**: Seamless wallet authentication and user experience
- **Transparent Operations**: All league activities recorded on-chain for complete transparency

### Flow Components Used
- **@onflow/fcl**: Flow Client Library for blockchain interactions
- **@onflow/types**: TypeScript definitions for Flow
- **Cadence Smart Contracts**: Custom contracts for account setup and token management
- **Flow Wallet Integration**: Secure user authentication and transaction signing

### Contract Addresses
- **Flow Network**: Mainnet (`access.mainnet.nodes.onflow.org:9000`)
- **Testnet**: Devnet (`access.devnet.nodes.onflow.org:9000`)
- **Account Setup Contract**: See `setup_account.cdc`
- **Flow Configuration**: See `flow.json`

## ✨ Key Features

### 🏆 League Management
- **Keeper League Support**: Multi-year player contracts with escalating costs
- **Franchise Tag System**: Designate one player per team with calculated tag values
- **Penalty System**: Automated penalties for waived players with active contracts
- **Real-time Analytics**: Positional spending ranks and future contract projections

### 💰 Financial Transparency
- **Blockchain Payments**: League fees processed through Flow blockchain
- **Automated Payouts**: Smart contract-based prize distribution
- **Contract Escalation**: 10% annual cost increases for multi-year contracts
- **Budget Tracking**: Real-time salary cap management and future projections

### 🔄 Sleeper Integration
- **One-time Data Sync**: Efficient data pull from Sleeper API
- **Local Database**: SQLite storage for fast, reliable data access
- **Roster Management**: Seamless integration with Sleeper's roster system
- **League Filtering**: Automatic import of SKL-prefixed leagues

### 🎯 User Experience
- **Flow Wallet Login**: Secure authentication via Flow blockchain
- **Responsive Design**: Modern UI built with React and Bootstrap
- **Real-time Updates**: Live league standings and transaction tracking
- **Mobile Friendly**: Optimized for all device sizes

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

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/[your-username]/supremekeeperleague-Flow.git
   cd supremekeeperleague-Flow
   ```

2. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   ```

3. **Install backend dependencies**
   ```bash
   cd ../backend
   pip install -r requirements.txt
   ```

4. **Configure Flow**
   - Update `flow.json` with your network configuration
   - Deploy smart contracts using Flow CLI

5. **Start the application**
   ```bash
   # Backend (Terminal 1)
   cd backend
   python app.py
   
   # Frontend (Terminal 2)
   cd frontend
   npm run dev
   ```

## 📊 Database Schema

The application uses SQLite with the following key tables:
- **Users**: Wallet addresses and Sleeper associations
- **Leagues**: League metadata and settings
- **Rosters**: Team compositions and records
- **Contracts**: Player contracts with escalation logic
- **Transactions**: All league activities and trades
- **Penalties**: Automated penalty tracking

## 🎮 Usage

1. **Connect Wallet**: Authenticate using your Flow wallet
2. **Associate Sleeper**: Link your Sleeper account for league data
3. **Join League**: Connect to SKL-prefixed leagues
4. **Manage Contracts**: Set up multi-year player contracts
5. **Track Analytics**: Monitor spending and future commitments
6. **Process Transactions**: Handle trades and league fees

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

### Testing
```bash
# Run backend tests
cd backend
python -m pytest

# Run frontend tests
cd frontend
npm test
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines and submit pull requests for any improvements.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Links

- **Flow Documentation**: https://docs.onflow.org/
- **Sleeper API**: https://docs.sleeper.com/
- **Project Planning**: See `planning.md` for detailed architecture

## 🏆 ReWTF Program

This project is participating in the Flow ReWTF (Reward the Flow) program, building in public and contributing to the Flow ecosystem. Follow our progress with `#ReWTF` and `@flow_blockchain`!

---

**Built with ❤️ on Flow Blockchain**
