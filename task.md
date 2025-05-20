# Project Tasks

## Active Tasks

- [ ] Review and update `EndPoints_review.md` (Started: 2025-05-17)
- [x] Restructure database based on dbRestructure.md (Started: 2025-05-21)
- [x] Update `SleeperService.py` to align with new DB schema (Started: 2025-05-21)
- [ ] Test `SleeperService.py` `fetch_all_data` with new DB schema (Started: 2025-05-21)
- [x] Update frontend component `League.jsx` (and others) for new API responses (Started: 2025-05-21)
- [x] Fix AttributeError in `get_league_standings_local` due to null metadata (Started: 2025-05-25)
- [x] Simplify `rosters` table and dependent code to remove detailed player/team stats (Started: 2025-05-25)
- [x] Update documentation (PLANNING.md, ENDPOINTS_REVIEW.md) with recent roster/API changes (Started: 2025-05-25)
- [x] UI Refinements (Navbar, League Page, Welcome Message) (Completed: 2025-05-28)
  - [x] League Page: Remove hardcoded "Supreme Keeper League" title, use dynamic `league_name`.
  - [x] Welcome Message: Remove wallet address display.
  - [x] Tables: Remove avatar display from tables.

- [ ] Add "Recent Transactions" table to League page (Started: 2025-05-28)
- [ ] Build out Team Page functionality (Started: 2025-05-29)
  - [x] 'My Team' link in navbar goes to logged-in user's team page
  - [x] Team names in standings table link to respective team pages
  - [x] Team page displays players by position (QB, RB, WR, TE, DEF)
  - [x] Team page displays player draft amount

## Discovered During Work

## Completed Tasks

# Supreme Keeper League - Development Tasks

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

### Database Setup
- [ ] Create SQLite database schema
- [ ] Set up database migrations
- [ ] Implement database connection handling
- [ ] Add database backup system
- [ ] Create database indexes for performance

### League Management
- [ ] Create league creation endpoint
- [ ] Implement league joining functionality
- [ ] Add league settings management
- [ ] Create league standings view
- [ ] Implement league member management

### Contract System
- [ ] Design contract creation flow
- [ ] Implement contract tracking
- [ ] Add contract waiver system
- [ ] Create penalty calculation system
- [ ] Implement contract expiration handling
- [ ] Rewrite waive player route
  - [ ] Add proper authentication checks
  - [ ] Implement contract validation
  - [ ] Calculate waiver penalties
  - [ ] Update player status
  - [ ] Handle waiver wire priority
  - [ ] Add transaction logging
  - [ ] Implement error handling

### Sleeper Integration
- [ ] Set up Sleeper API connection
- [ ] Implement league data sync
- [ ] Create player data import
- [ ] Add roster sync functionality
- [ ] Implement standings sync

## Medium Priority Tasks

### Frontend Development
- [ ] Set up React project structure
- [ ] Create responsive navigation
- [ ] Implement league dashboard
- [ ] Add team management interface
- [ ] Create contract management UI
- [ ] Design and implement profile page
- [ ] Add loading states and error handling

### Backend Development
- [ ] Set up Flask project structure
- [ ] Implement API endpoints
- [ ] Add request validation
- [ ] Create error handling middleware
- [ ] Implement logging system
- [ ] Add API documentation

### Payment Integration
- [ ] Set up TON payment processing
- [ ] Implement league fee collection
- [ ] Add payment verification
- [ ] Create payment history tracking
- [ ] Implement refund handling

## Low Priority Tasks

### Testing
- [ ] Write unit tests for backend
- [ ] Add integration tests
- [ ] Create frontend component tests
- [ ] Implement end-to-end tests
- [ ] Add performance testing

### Documentation
- [ ] Create API documentation
- [ ] Write user documentation
- [ ] Add developer setup guide
- [ ] Create deployment documentation
- [ ] Document database schema

### UI/UX Improvements
- [ ] Add dark mode support
- [ ] Implement responsive design
- [ ] Create loading animations
- [ ] Add success/error notifications
- [ ] Improve form validation feedback

## Future Enhancements
- [ ] Add advanced statistics
- [ ] Implement trade management system
- [ ] Create contract negotiation features
- [ ] Add league history tracking
- [ ] Implement mobile app
- [ ] Add social features

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