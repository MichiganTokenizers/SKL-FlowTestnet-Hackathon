# Project Tasks

## Active Tasks

- [x] Change navbar from "My Team" to "Teams" with teams listing page (Completed: 2025-01-27)
  - [x] Add backend endpoint `/api/league/<league_id>/teams` for fetching all teams
  - [x] Create new Teams.jsx component for displaying all teams
  - [x] Update navbar to show "Teams" instead of "My Team" button
  - [x] Add routing for `/league/:leagueId/teams` path
  - [x] Highlight current user's team in the teams list
  - [x] Ensure each team links to their respective team page

- [x ] Review and update `EndPoints_review.md` (Started: 2025-05-17)
- [x] Restructure database based on dbRestructure.md (Started: 2025-05-21)
- [x] Update `SleeperService.py` to align with new DB schema (Started: 2025-05-21)
- [x ] Test `SleeperService.py` `fetch_all_data` with new DB schema (Started: 2025-05-21)
- [x] Update frontend component `League.jsx` (and others) for new API responses (Started: 2025-05-21)
- [x] Fix AttributeError in `get_league_standings_local` due to null metadata (Started: 2025-05-25)
- [x] Simplify `rosters` table and dependent code to remove detailed player/team stats (Started: 2025-05-25)
- [x] Update documentation (PLANNING.md, ENDPOINTS_REVIEW.md) with recent roster/API changes (Started: 2025-05-25)
- [x] UI Refinements (Navbar, League Page, Welcome Message) (Completed: 2025-05-28)
  - [x] League Page: Remove hardcoded "Supreme Keeper League" title, use dynamic `league_name`.
  - [x] Welcome Message: Remove wallet address display.
  - [x] Tables: Remove avatar display from tables.

- [x] Add "Recent Transactions" table to League page (Started: 2025-05-28) (Completed: 2025-07-30)
  - [ ] Refine `RecentTransactionsTable.jsx` - `renderTransactionDetails` function to correctly parse and display various transaction types based on `SleeperService.py` data structure (Discovered: 2025-07-30)
- [x] Get nfl state for offseason inseason toggle from SLeeper API
- [ ] Disable draft data pull in `SleeperService.fetch_all_data` if league status is "InSeason" (or NFL state indicates active season). (Started: 2025-05-22)
- [x] Build out Team Page functionality (Started: 2025-05-29) (Completed: 2025-07-28)
  - [x] 'My Team' link in navbar goes to logged-in user's team page (Completed: 2023-10-27)
  - [x] Team names in standings table link to respective team pages (Completed: 2023-10-27)
  - [x] Team page displays players by position (QB, RB, WR, TE, DEF) (Completed: 2023-10-27)
  - [x] Team page displays player draft amount (Completed: 2023-10-27)
  - [x] Team page displays "Years Remaining" (Completed: 2023-10-27)
  - [x] Team page displays 4-year projected contract costs (Completed: 2025-07-28)
  - [x] Team page displays "Projected Future Yearly Contract Totals" (Completed: 2025-07-28)
  - [x] Team page implements UI for setting new player contract durations during the contract setting window (Completed: 2025-07-28)
  - [x] Backend supports fetching 4-year costs and saving contract durations (Completed: 2025-07-28)
  - [x] Fix free agent display logic - show $0 for waived auction players (Completed: 2025-01-27)
- [ ] Clean up routes upon login with Flow, seeing an error page before correct league page loads
- [x] Detect players who have been waived from Sleeper team but still have an active contract during season
- [ ] Build Trade Desk (big)
  - [x] Database schema for trades, trade_items, trade_approvals tables
  - [x] Backend API endpoints for trade management
  - [x] Frontend trade approval interface in League page
  - [x] Trade creation modal in Team page
  - [x] Budget calculation integration with trades
  - [x] Automatic commissioner detection from Sleeper API
  - [x] **TEMPORARY**: Database reset endpoint for production testing
- [ ] Build league fee structure in keeper.db
- [ ] Add pay league fee button in league page
- [x] Correct commissioner status for user LordTokenizer (wallet 0xf8d6e0586b0a20c7) in league 1230890383865552896 in keeper.db (Discovered: 2025-06-03) - **RESOLVED**: Commissioner status now automatically determined from Sleeper API
- [ ] Prevent association more than once per Sleeper user name upon production

- [x] Clean up navbar hamburger menu issue (Started: 2025-07-29)

## Discovered During Work
- Refine `RecentTransactionsTable.jsx` - `renderTransactionDetails` function to correctly parse and display various transaction types based on `SleeperService.py` data structure (From: Add "Recent Transactions" table to League page, Date: 2025-07-30)
- **2025-08-25**: SleeperService user import issue - When a team ownership changes (user removed and replaced), the API may return roster data with `null` owner_id values, causing user import failures. RareWareNate's team was originally owned by another user who was removed, causing API data inconsistencies. **RESOLUTION**: Manual database insert required. **TODO**: Investigate why automated import fails for ownership changes and add error handling for null owner_id scenarios.

- **2025-08-26**: User association endpoint bug - When users are imported by SleeperService before they have wallet addresses, the association endpoint fails to link their existing records. C0Y0T3z was imported with NULL wallet_address but could authenticate via sessions table. **RESOLUTION**: Fixed `/auth/complete_association` endpoint to handle existing user records with NULL wallet_address by updating them instead of requiring new record creation. **STATUS**: Fixed in backend/app.py

- **2025-08-26**: User association endpoint UNIQUE constraint error - When both a wallet record and sleeper record exist separately, attempting to update one causes UNIQUE constraint violations. **RESOLUTION**: Enhanced association endpoint to detect and merge duplicate records, updating the wallet record with sleeper info and deleting the redundant sleeper record. **STATUS**: Fixed in backend/app.py

## Completed Tasks

- **2025-01-XX**: Fixed penalty calculation logic in `utils.py` to properly handle in-season vs offseason player waivers
  - In-season drops: First penalty (next year) now correctly based on current year's salary
  - Offseason drops: First penalty (current year) correctly based on current year's salary
  - Eliminates misalignment where in-season penalties were incorrectly calculated from future contract years# Supreme Keeper League - Development Tasks

## High Priority Tasks

### Authentication & User Management
- [x] Set up TON wallet connection
- [x] Implement session management
- [x] Create user registration flow
- [x] Add user profile management
- [x] Implement logout functionality
- [x] Create league connection page for new users
  - [x] Design league connection UI
  - [x] Add Sleeper league ID input
  - [x] Implement league validation
  - [x] Add league association logic
  - [x] Create success/error handling
  - [x] Add loading states
- [x] Implement Sleeper Account Association Flow (New Task - 2025-05-15)
  - [x] Frontend: Create/Update `AssociateSleeper.jsx` component (UI, state, form handling)
  - [x] Frontend: Pass `onAssociationSuccess` callback from `AppContent` to `AssociateSleeper`
  - [x] Frontend: `AppContent`'s `handleAssociationSuccess` to re-fetch data and navigate to `/league`
  - [x] Backend: Create `/auth/complete_association` route in `app.py`
  - [x] Backend: `/auth/complete_association` - validate session, get `sleeperUsername`
  - [x] Backend: `/auth/complete_association` - call `sleeper_service.get_user()`
  - [x] Backend: `/auth/complete_association` - update `users` table with `sleeper_user_id` and `display_name`
  - [x] Backend: `/auth/complete_association` - call `sleeper_service.fetch_all_data()`
  - [x] Backend: `/auth/complete_association` - return success/error JSON response


## Notes
- Tasks are organized by priority and category
- Check off tasks as they are completed
- Add new tasks as they are identified
- Update task status during development
- Add subtasks as needed for complex features

## Task Status Legend
- [ ] Not Started
- [~] In Progress
- [x] Completed
- [!] Blocked
- [?] Needs Review 