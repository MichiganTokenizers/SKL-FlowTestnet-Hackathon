# Supreme Keeper League - Project Plan

## Overview
Supreme Keeper League is a fantasy football platform integrated with the TON blockchain for secure transactions and the Sleeper API for league management. The goal is to create a decentralized, transparent, and user-friendly environment for managing keeper leagues.

## Data Pull Strategy
- **One-Time Data Pull**: All Sleeper API data will be pulled once during user login or after a new league association. This pull will update the local database (`keeper.db`) with the latest information on users, leagues, teams, rosters, standings, and other relevant data.
  - **League Filtering**: Only leagues whose names begin with "SKL" will be imported and processed into `keeper.db`.
- **Local Data Usage**: After the initial data pull, the application will use data stored in `keeper.db` for all subsequent requests, minimizing repeated calls to Sleeper APIs.
- **Refresh Mechanism**: A manual refresh option or scheduled task may be implemented to update `keeper.db` when necessary, but this will be an exception rather than the norm.
- **Backend Endpoints**: New endpoints will be created or existing ones updated to fetch data from `keeper.db` (e.g., `/league/local`, `/league/standings/local`). A specific endpoint `/sleeper/fetchAll` will handle the full data pull from Sleeper APIs.

## Architecture
### Frontend
- **React.js**: For building a dynamic and responsive user interface.
- **React Router**: For navigation and routing within the single-page application.
- **FlowConnect**: For account management and payments.
- **Bootstrap**: For styling and responsive design.

#### Component Structure
- **Authentication**: TON wallet login, Sleeper account association (linking wallet to Sleeper user ID).
  - `AssociateSleeper.jsx`: Component to handle user input of Sleeper username and trigger backend association.
- **League Management**: Viewing league details, standings.
- **Team Management**: Rosters for the most part will be managed on Sleeper app. 
   - **Waived Player Detection and Penalty Process**:
     - Players are waived directly on the Sleeper platform.
     - During the `fetch_all_data` process (triggered on login/association or manually), the system compares the latest Sleeper roster for a team against the roster previously stored in `keeper.db`.
     - If a player with an active contract in `keeper.db` is no longer on the team's Sleeper roster, they are considered "dropped" or "waived".
     - For each dropped player with an active contract:
       - The `calculate_penalty` function is called. Penalties are 25% of the contract's value for that specific year, rounded normally, for each remaining year of the contract. This applies regardless of off-season status.
       - For example, a 4-year $1 contract dropped before Year 1 would incur four separate penalties: $1 for Year 1, $1 for Year 2, $1 for Year 3, and $1 for Year 4. If the same contract was dropped before Year 3, it would incur two penalties: $1 for Year 3 and $1 for Year 4.
       - The corresponding contract record in the `contracts` table is updated:
         - `IsActive` is set to `0`.
       - A new table, `penalties`, will store individual penalty entries, linking back to the original contract. Each entry will include `contract_id`, `penalty_year`, and `penalty_amount`.
         - `updated_at` is refreshed on the original contract.
     - This ensures penalties are assessed based on the contract state *before* the local roster is updated with the latest API data. The local roster is then updated (upserted) with the current player list from Sleeper.
   - Trading player on Supreme Keeper League site with options for trading next year's auction money. The trade will have to also take place on Sleeper app with players only.
  - **Team Page Analytics & Display**:
    - **Current Year Positional Spending Ranks**: Displays the team's total contract spending for each player position (QB, RB, WR, TE, etc.) for the current season. This is ranked against all other teams in the league to show comparative spending by position.
    - **Future Contract Yearly Ranks**: Shows the team's projected total contract commitments for each of the next three future seasons. These projected totals are also ranked against all other teams in the league for each respective future year, providing insight into long-term financial obligations.
- **Contract Management**: Creating, viewing, and managing player contracts. 
  - **Contract Setting Phase:** After the annual league draft and before the start of the season, users will access a contract setting page for newly drafted players. These settings can be accessed and modified up until the official start of the season.
  - **Contract Duration:** Players can be signed to contracts of up to 4 years.
  - **Contract Cost Structure:**
    - The initial `draft_amount` is the cost for Year 1 of the contract.
    - For each subsequent year of the contract (Year 2, Year 3, Year 4), the cost increases by 10% of the *previous year's cost*, with the result rounded up to the nearest dollar.
    - Example:
      - Year 1 Cost = `draft_amount`
      - Year 2 Cost = `ceil(Year 1 Cost * 1.1)`
      - Year 3 Cost = `ceil(Year 2 Cost * 1.1)`
      - Year 4 Cost = `ceil(Year 3 Cost * 1.1)`
  - **Calculated Annual Costs:** The `contracts` table will store the initial `draft_amount`, `contract_year`, and `duration`. To provide the escalated annual costs for each year of a contract, a database view (e.g., `vw_contractByYear`) will be created. This view will perform the necessary calculations based on the stored contract terms.
  - Franchise Tag System: Each team can designate one player as their franchise player before the start of the season.
    - Tag value is calculated as the greater of:
      - Average of the top 5 contracts at that position from the previous year (using their final year, escalated costs).
      - The player's final year, escalated contract cost from their expiring contract + 10%.
    - Franchise tag can only be used on players with expiring contracts.
- **Profile Management**: User profile and settings.

### Backend
- **Flask**: Lightweight Python framework for creating API endpoints.
- **SQLite**: Using `keeper.db` for local data storage after the initial Sleeper API pull.
- **Sleeper API**: For initial data retrieval during login or league association.
- **TON Blockchain**: For secure and transparent transactions.

#### API Endpoints
- See `EndPoints_review.md` for a detailed review and current status of all backend API endpoints.
- **Authentication**: `/auth/login`, `/auth/verify`, `/auth/associate_sleeper`, `/auth/complete_association` (new endpoint for saving association).
- **League**: `/league/connect`, `/league/local`, `/league/standings/local`
- **Team**: `/team/{id}/local`
- **Sleeper Data Pull**: `/sleeper/fetchAll`, `/sleeper/search`, `/sleeper/league/{id}/users`, `/sleeper/import`

## Database Schema (`keeper.db`)
- **Users**: Information about users, including wallet address and associated Sleeper user ID.
- **Leagues**: Details of connected Sleeper leagues. (This refers to `LeagueMetadata`)
- **Teams**: Team information within each league. (This is represented by the `rosters` table)
  - **Rosters (`rosters` table)**: Stores team composition linking to a `LeagueMetadata`.
    - `sleeper_roster_id` (PK): Sleeper's unique ID for the roster.
    - `sleeper_league_id` (FK to `LeagueMetadata`): The league this roster belongs to.
    - `owner_id`: Sleeper user ID of the team owner.
    - `players`: JSON string list of Sleeper player IDs on the main roster.
    - `metadata`: JSON string for roster-specific metadata from Sleeper (e.g., custom team name).
    - `reserve`: JSON string list of Sleeper player IDs on the reserve squad.
    - `taxi`: JSON string list of Sleeper player IDs on the taxi squad.
    - `wins`, `losses`, `ties`: Integer values for the team's record, sourced from roster settings in Sleeper.
- **Players**: Player data including contracts and status.
- **Contracts**: Contract details for players.
  - `player_id`: Foreign key to `players` table.
  - `team_id`: Foreign key to `rosters` table (identifies the `sleeper_roster_id`).
  - `draft_amount`: The initial auction cost for Year 1 of the contract.
  - `contract_year`: The season (e.g., 2024) in which the contract starts.
  - `duration`: The length of the contract in years (1 to 4).
  - `is_active`: Boolean indicating if the contract is currently active.
  - `penalty_incurred`, `penalty_year`: For recording waiver penalties.
  - **Calculated Yearly Costs (View):** The actual cost for subsequent years (Year 2, 3, 4) escalates as described in the Contract Management section. This calculation will be encapsulated in a database view (e.g., `vw_contractByYear`) to be created, which will derive annual costs from the base contract terms.
- **Transactions**: Records of trades, waivers, etc.
- **Traded Picks**: Information on traded draft picks.
- **Drafts**: Draft details and status.
- **Sessions**: User session tokens for authentication.
- **season_curr**: One row with current_season and IsOffSeason. Manually controlled.

## Development Phases
1. **Setup and Initial Design**
   - Set up the development environment with React.js, Flask, and necessary libraries.
   - Design the UI/UX for the platform.
2. **Core Functionality**
   - **Initial User Onboarding and Data Synchronization Flow (Implemented & Verified):**
     - **TON Wallet Authentication:** Users authenticate via their TON wallet. 
       - **Frontend Process:** Upon successful TON wallet connection, the frontend React application initiates a login sequence:
         1. Calls the backend `/auth/login` endpoint, receiving a `sessionToken` and an `isNewUser` status.
         2. Stores the `sessionToken` in `localStorage` and updates its internal state.
         3. Fetches essential user data (leagues via `/league/local`, association status via `/auth/check_association`) and updates relevant states (`leagues`, `selectedLeagueId`, `isNewUser`).
         4. A global `isAppReady` state flag is set to `true` only after all initial authentication calls and essential data fetches are complete.
         5. Declarative routing then navigates the user: to `/associate-sleeper` if `isNewUser` is true, or to the main `/league` page if the user is already associated. A loading indicator is shown if `sessionToken` exists but `isAppReady` is false, preventing premature navigation.
       - **Backend Process:** The `/auth/login` route verifies the wallet, creates/retrieves the user record, and generates a session.
     - **Sleeper Account Association:** Users link their authenticated wallet to their Sleeper username. The `/auth/complete_association` endpoint manages this. Upon successful association:
       - An internal `sleeper_service.fetch_all_data` function is triggered.
       - This function executes a comprehensive one-time data pull from the Sleeper API, retrieving all associated user, league, roster, player, and standings information.
       - All fetched data is then stored in the local `keeper.db`. The database schema, particularly the `rosters` table (with `sleeper_roster_id` as `PRIMARY KEY`) and its `ON CONFLICT` resolution strategy, has been confirmed to operate correctly, ensuring data integrity.
     - **Local Data Utilization:** Following the initial data synchronization, the frontend application primarily accesses league and team data (e.g., through `/league/local`, `/league/standings/local`) from the local `keeper.db`, thereby minimizing direct calls to the Sleeper API.

3. **Feature Development**
   - Build components for trade interface using local data.
   - Implement transaction system with TON blockchain, including:
     - Enabling users to pay league fees using their TON wallet.
     - Displaying the payment status of league fees for users.
     - Logging league fee transactions from the TON blockchain into the local database.
     - Notifying users of unpaid league fees, with eventual removal from the league if fees remain unpaid by a deadline.


## Challenges and Solutions
- **Data Synchronization**: Ensuring `keeper.db` stays updated with Sleeper data can be challenging. Solution: Implement a robust one-time pull mechanism with optional refresh capabilities.
- **Blockchain Integration**: Handling TON transactions securely. Solution: Use TonConnect library and follow best practices for blockchain integration.
- **User Experience**: Balancing functionality with simplicity. Solution: Use Bootstrap for a clean, responsive design and iterative user feedback.

## Future Enhancements

- Add support for multiple league associations per user. Need to review leauge selection process when a user has multiple leagues.
- Enhance contract setting form with enhanced real time data viz type look at the future of your franchise, based on selected contract durations. Including remaining budget calculated for 4 years. Large contracts could dark shade a bar to indicate large contracts, light green for small contracts.
- **League Commissioner Tools:**
  - Member management tools (invites, removals, ownership transfers) potentially integrated with Telegram user IDs.
  - Commissioner announcements and communications primarily via Telegram Messenger.
- **Enhanced User Interaction & Engagement (Telegram-Centric):**
  - All notifications (key league events, trade updates, fee reminders, etc.) to be delivered via Telegram Messenger.
  - Trade block and initial trade negotiation facilitation, possibly using Telegram bots or groups.
  - League chat/forum features primarily leveraging Telegram groups or channels.
- **Draft Management & Support:**
  - Draft contract setting page for viewing results, traded auction dollars.
  - Support for auction draft budget tracking.
- **Historical Data and League History:**
  - Archive and display past season champions, standings, trades, and contract histories.
- **User Support and Onboarding:**
  - Comprehensive FAQ/Help section.
  - Guidance and resources for using TON wallets.
- **Deeper Financial/Transaction Transparency:**
  - League treasury view (fees collected, pot total, payouts).
  - Detailed, user-accessible audit log for significant league actions.
  - Develop smart contract(s) to automate the payout of league winnings to winners on the TON blockchain.
- Create NFTs for league trophies and accomplishments
- **Enhanced Contract Setting Form:**
  - Add franchise tag selection option with clear visual indicators
  - Display calculated franchise tag values by position showing both calculation methods:
    - Average of previous year's top 5 position contracts
    - Current contract + 10%
  - Show eligible players for franchise tag (expiring contracts only)
  - Include franchise tag usage history and restrictions
  - Show impact of franchise tag on team's salary cap and future contract options
  - Real-time data visualization of future franchise outlook based on contract durations
  - Remaining budget calculation for 4 years
  - Visual contract size indicators (dark shade for large contracts, light green for small contracts)

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