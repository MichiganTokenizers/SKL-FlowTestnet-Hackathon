# Backend Endpoints Review Task List

This document tracks the review and update status of all backend endpoints in the Supreme Keeper League application.

## Endpoints Status

| Endpoint | Method | Purpose | Status | Notes |
|----------|--------|---------|--------|-------|
| `/auth/login` | POST | User login with TonConnect | ✅ Implemented | |
| `/auth/verify` | GET | Verify user session | ✅ Implemented | |
| `/auth/associate_sleeper` | POST | Associate wallet with Sleeper account | ✅ Implemented | |
| `/auth/check_association` | GET | Check if wallet needs Sleeper association | ✅ Implemented | New endpoint for the login flow |
| `/auth/complete_association` | POST | Complete Sleeper account association | ✅ Implemented | New endpoint for the login flow |
| `/league/local` | GET | Get league data from local DB | ✅ Implemented | |
| `/league/standings/local` | GET | Get league standings from local DB | ✅ Implemented | Returns a list of rosters with owner info, team name, player count, and W-L-T record. Does not include full statistical ranking. |
| `/league/teams` | GET | Get team data | ✅ Implemented | Review data format |
| `/league/connect` | POST | Connect user to league | ✅ Implemented | |
| `/leagues` | GET | Get all leagues | ✅ Implemented | |
| `/league` | GET | Get league data | ✅ Implemented | Review relationship with `/league/local` |
| `/sleeper/import` | POST | Import Sleeper data | ✅ Implemented | |
| `/sleeper/fetchAll` | POST | Refresh all Sleeper data | ✅ Implemented | |
| `/sleeper/search` | GET | Search for Sleeper users | ✅ Implemented | Searches by username and returns user with leagues |
| `/sleeper/league/{id}/users` | GET | Get users in a league | ✅ Implemented | Added for user association flow |
| `/team/{id}/local` | GET | Get team data from local DB | ❌ Missing | Need to implement |
| `/waive_player` | POST | Waive a player | ⚠️ Review | Only partially implemented |
| `/season/settings` | GET | Get current season settings | ✅ Implemented | Returns year and offseason status |
| `/season/settings` | POST | Update season settings | ✅ Implemented | Update year and/or offseason status |

## Todo Items

1. Implement remaining endpoints:
   - `/team/{id}/local`

2. Review and update implemented endpoints:
   - Review `/league/teams` data format
   - Clarify relationship between `/league` and `/league/local`
   - Complete implementation of `/waive_player`

3. Ensure all endpoints handle:
   - Authentication consistently
   - Error handling
   - CORS headers
   - Proper transaction management for database operations

4. Add additional endpoints as needed:
   - Contract management
   - Draft pick trading
   - Transaction history

## New Association Flow Implementation

We've implemented a full user association flow that includes:

1. Backend endpoints:
   - `/auth/check_association`: Checks if a wallet address needs to be associated with a Sleeper account
   - `/sleeper/search`: Searches for Sleeper users by username
   - `/sleeper/league/{id}/users`: Gets all users in a specific league
   - `/auth/complete_association`: Completes the association process by updating the user record

2. Frontend component:
   - `SleeperAssociation.jsx`: React component that handles the entire flow
   - Allows users to search for their Sleeper account
   - Allows users to select their league and confirm their account
   - Completes the association process

## Testing Notes

- All endpoints should be tested with:
  - Valid authentication
  - Invalid/expired authentication
  - Missing required parameters
  - Malformed requests 