# Supreme Keeper League - Project Planning Document

## Overview
The Supreme Keeper League is a fantasy football platform that extends the functionality of Sleeper fantasy football leagues by adding a contract system for players. While Sleeper handles the core fantasy football operations (drafting, lineups, scoring), our platform manages player contracts and keeper rules.

### Core Features
- Integration with Sleeper API for fantasy football operations
- Player contract management (up to 4 years)
- Contract waiver penalties
- TON wallet authentication
- Team roster management

## Project Scope

### In Scope
- User authentication via TON wallet
- League creation and management
- Player contract tracking
- Integration with Sleeper API
- Basic team management
- Contract waiver system
- Session management
- Payment processing (pay leauge fees with Ton wallet)

### Out of Scope
- Direct fantasy football operations (handled by Sleeper)
- Real-time scoring (handled by Sleeper)



## Technical Architecture

### Frontend
- React (Vite) setup
- Main entry point: `frontend/src/App.jsx`
- Key components:
  - Authentication (TON wallet integration)
  - League management
  - Team management
  - Contract management
  - Profile management

### Backend
- Flask server
- Main entry point: `app.py`
- SQLite database (`keeper.db`)
- Key endpoints:
  - Authentication
  - League management
  - Team management
  - Contract management
  - Sleeper API integration

### Data Flow
1. **Authentication Flow**
   - User connects TON wallet
   - Backend verifies wallet address
   - Session token generated and stored
   - Session recorded in keeper.db

2. **League Management Flow**
   - League creation/joining
   - Sleeper league integration
   - Contract management
   

3. **Contract Management Flow**
   - Contract creation after draft
   - Contract tracking
   - Waiver processing
   - Penalty calculation

### Database Schema (keeper.db)
```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    wallet_address TEXT UNIQUE,
    created_at TIMESTAMP
);

-- Sessions table
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    session_token TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Leagues table
CREATE TABLE leagues (
    id INTEGER PRIMARY KEY,
    name TEXT,
    sleeper_league_id TEXT,
    creator_id INTEGER,
    created_at TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES users(id)
);

-- Contracts table
CREATE TABLE contracts (
    id INTEGER PRIMARY KEY,
    league_id INTEGER,
    player_id TEXT,
    team_id INTEGER,
    years INTEGER,
    start_year INTEGER,
    created_at TIMESTAMP,
    FOREIGN KEY (league_id) REFERENCES leagues(id),
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

-- Teams table
CREATE TABLE teams (
    id INTEGER PRIMARY KEY,
    league_id INTEGER,
    owner_id INTEGER,
    name TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (league_id) REFERENCES leagues(id),
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
```

## Development Setup
1. Frontend (Vite + React)
   - Node.js environment
   - React dependencies
   - TONConnect integration

2. Backend (Flask)
   - Python environment
   - Flask dependencies
   - SQLite database
   - Sleeper API integration

3. Development Tools
   - ngrok for public URL generation
   - TON wallet for testing
   - Sleeper API credentials

## Security Considerations
- Secure session management
- TON wallet authentication
- API key protection
- Database security
- Input validation
- CORS configuration

## Future Enhancements
- Advanced statistics
- Trade management
- Contract negotiation system
- League history tracking
- Enhanced UI/UX
- Mobile responsiveness improvements 