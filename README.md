# SupremeKeeperLeague-TON

## Commissioner Logic Update

### Overview
The system now uses Sleeper's actual commissioner designation (`is_owner` field) instead of automatically making the first user to associate with a league the commissioner.

### Changes Made

1. **New Method in SleeperService**: Added `update_commissioner_status_for_league()` method that:
   - Fetches all users from Sleeper API for a league
   - Checks the `is_owner` field for each user
   - **Only updates users who have wallet addresses in the database**
   - **Only updates if the status actually needs to change** (no unnecessary resets)

2. **Updated fetch_all_data()**: Modified to call the new commissioner update method for each league after processing league data.

3. **Removed Old Logic**: Eliminated the first-user-gets-commissioner logic from `app.py`.

4. **New API Endpoints**: 
   - `/sleeper/league/<league_id>/update-commissioners` for single league updates
   - `/sleeper/update-all-commissioners` for updating all leagues

### How It Works

1. **When a user associates their Sleeper account:**
   - The system fetches all their leagues from Sleeper
   - Processes league data (rosters, users, etc.)
   - **NEW**: Updates commissioner status based on Sleeper's `is_owner` field for each league

2. **Commissioner Status Updates:**
   - **Only affects users who have connected their wallets** (have entries in UserLeagueLinks)
   - **Only updates if the status actually changed** (no unnecessary database writes)
   - **Preserves existing commissioner status** for users who haven't connected wallets yet
   - **Supports multiple commissioners** per league (as Sleeper allows)

3. **Safety Features:**
   - No mass reset of all users to 0
   - Only processes users with wallet addresses
   - Logs all changes for audit purposes
   - Graceful handling of users who haven't connected wallets yet

### Testing

Run the test script to verify the new logic:
```bash
cd backend
python test_commissioner_logic.py
```

### API Usage

To manually update commissioner status:

**Single league:**
```bash
POST /sleeper/league/{league_id}/update-commissioners
Authorization: {session_token}
```

**All leagues:**
```bash
POST /sleeper/update-all-commissioners
Authorization: {session_token}
```

### Database Schema

The `UserLeagueLinks` table structure remains the same:
```sql
CREATE TABLE UserLeagueLinks (
    wallet_address TEXT,
    sleeper_league_id TEXT,
    is_commissioner INTEGER DEFAULT 0,  -- Now based on Sleeper's is_owner field
    fee_paid_amount REAL DEFAULT 0.0,
    fee_payment_status TEXT DEFAULT 'unpaid',
    updated_at DATETIME,
    PRIMARY KEY (wallet_address, sleeper_league_id)
)
```

### Important Notes

- **No mass resets**: The system no longer resets all commissioner status to 0
- **Selective updates**: Only users with wallet addresses are processed
- **Change detection**: Only updates when the status actually needs to change
- **Preserves existing data**: Users without wallet connections retain their status
- **Audit trail**: All changes are logged for debugging and audit purposes 
