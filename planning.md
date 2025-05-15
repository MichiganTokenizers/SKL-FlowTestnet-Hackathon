# Supreme Keeper League - Project Plan

## Overview
Supreme Keeper League is a fantasy football platform integrated with the TON blockchain for secure transactions and the Sleeper API for league management. The goal is to create a decentralized, transparent, and user-friendly environment for managing keeper leagues.

## Data Pull Strategy
- **One-Time Data Pull**: All Sleeper API data will be pulled once during user login or after a new league association. This pull will update the local database (`keeper.db`) with the latest information on users, leagues, teams, rosters, standings, and other relevant data.
- **Local Data Usage**: After the initial data pull, the application will use data stored in `keeper.db` for all subsequent requests, minimizing repeated calls to Sleeper APIs.
- **Refresh Mechanism**: A manual refresh option or scheduled task may be implemented to update `keeper.db` when necessary, but this will be an exception rather than the norm.
- **Backend Endpoints**: New endpoints will be created or existing ones updated to fetch data from `keeper.db` (e.g., `/league/local`, `/league/standings/local`). A specific endpoint `/sleeper/fetchAll` will handle the full data pull from Sleeper APIs.

## Architecture
### Frontend
- **React.js**: For building a dynamic and responsive user interface.
- **React Router**: For navigation and routing within the single-page application.
- **TonConnect**: For integrating TON wallet functionalities.
- **Bootstrap**: For styling and responsive design.

#### Component Structure
- **Authentication**: TON wallet login, Sleeper account association.
- **League Management**: Viewing league details, standings, and managing league settings.
- **Team Management**: Managing rosters, contracts, and transactions.
- **Contract Management**: Creating, viewing, and managing player contracts.
- **Profile Management**: User profile and settings.

### Backend
- **Flask**: Lightweight Python framework for creating API endpoints.
- **SQLite**: Using `keeper.db` for local data storage after the initial Sleeper API pull.
- **Sleeper API**: For initial data retrieval during login or league association.
- **TON Blockchain**: For secure and transparent transactions.

#### API Endpoints
- **Authentication**: `/auth/login`, `/auth/verify`, `/auth/associate_sleeper`
- **League**: `/league/connect`, `/league/local`, `/league/standings/local`
- **Team**: `/team/{id}/local`
- **Sleeper Data Pull**: `/sleeper/fetchAll`, `/sleeper/search`, `/sleeper/league/{id}/users`, `/sleeper/import`

## Database Schema (`keeper.db`)
- **Users**: Information about users, including wallet address and associated Sleeper user ID.
- **Leagues**: Details of connected Sleeper leagues.
- **Teams**: Team information within each league.
- **Players**: Player data including contracts and status.
- **Contracts**: Contract details for players.
- **Transactions**: Records of trades, waivers, etc.
- **Traded Picks**: Information on traded draft picks.
- **Drafts**: Draft details and status.
- **Sessions**: User session tokens for authentication.

## Development Phases
1. **Setup and Initial Design**
   - Set up the development environment with React.js, Flask, and necessary libraries.
   - Design the UI/UX for the platform.
2. **Core Functionality**
   - Implement TON wallet authentication.
   - Develop Sleeper API integration for one-time data pull.
   - Create local database schema and update backend to store and retrieve data from `keeper.db`.
3. **Feature Development**
   - Build components for league, team, and contract management using local data.
   - Implement transaction system with TON blockchain.
4. **Testing and Deployment**
   - Test the application for bugs and performance issues.
   - Deploy the application to a production environment.

## Challenges and Solutions
- **Data Synchronization**: Ensuring `keeper.db` stays updated with Sleeper data can be challenging. Solution: Implement a robust one-time pull mechanism with optional refresh capabilities.
- **Blockchain Integration**: Handling TON transactions securely. Solution: Use TonConnect library and follow best practices for blockchain integration.
- **User Experience**: Balancing functionality with simplicity. Solution: Use Bootstrap for a clean, responsive design and iterative user feedback.

## Future Enhancements
- Implement real-time updates for critical data if needed, with careful consideration of API usage.
- Add support for multiple league associations per user.
- Enhance contract management with more complex rules and automation.

## Timeline
- **Week 1-2**: Setup, initial design, and core architecture.
- **Week 3-4**: Authentication and one-time Sleeper data pull implementation.
- **Week 5-6**: League and team management features with local data.
- **Week 7-8**: Contract management and transaction system.
- **Week 9-10**: Testing, bug fixes, and deployment preparation.
- **Week 11-12**: Deployment and post-launch monitoring.

## Team Roles
- **Frontend Developer**: Focus on React.js components and UI/UX.
- **Backend Developer**: Manage Flask API, database, and Sleeper API integration.
- **Blockchain Specialist**: Handle TON integration and smart contracts if needed.
- **QA Engineer**: Ensure the application is bug-free and performs well. 