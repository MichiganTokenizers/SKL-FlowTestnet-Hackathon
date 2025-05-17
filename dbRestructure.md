Here's how I'll proceed with modifying backend/app.py:
Modify get_global_db_connection(): I'll add cursor.execute("PRAGMA foreign_keys = ON;") to ensure foreign key constraints are enforced for the global connection.
Update init_db():
Adjust the table drop order in force_create to respect foreign key dependencies.
Modify the Users table to explicitly define wallet_address TEXT PRIMARY KEY.
Create the new LeagueMetadata table with sleeper_league_id as its primary key.
Replace the existing leagues table definition with UserLeagueLinks, establishing foreign keys to Users(wallet_address) and LeagueMetadata(sleeper_league_id).
Update the rosters table:
Rename its league_id column to sleeper_league_id.
Add a foreign key from rosters(sleeper_league_id) to LeagueMetadata(sleeper_league_id).
The owner_id in rosters (which is a sleeper_user_id) will remain as TEXT without a direct foreign key to Users.sleeper_user_id, as roster owners might not always be registered users of your application. The existing LEFT JOIN logic to fetch user details if they are an app user is appropriate.
Ensure the table creation order respects dependencies.
Refactor get_league_data_local(): This endpoint will now query UserLeagueLinks and join with LeagueMetadata to fetch league details for the authenticated user.
Refactor get_league_standings_local():
It will first determine the relevant sleeper_league_id(s) for the user via UserLeagueLinks.
Then, it will fetch rosters for that sleeper_league_id from the rosters table (which now uses sleeper_league_id to link to LeagueMetadata).
Refactor get_leagues(): This generic endpoint will be updated to fetch data from the new LeagueMetadata table (e.g., sleeper_league_id and name).
Add comments: I'll add comments indicating that SleeperService and any direct DB manipulation in functions like connect_league (which uses an undefined KeeperDB class) will also need updates to work with the new schema.
I will apply these changes to backend/app.py. Since I don't have the content of app.jsx or SleeperService.py, I can't modify them, but you should review them afterwards, as changes to endpoint responses (like /league/local) might require frontend adjustments, and SleeperService.py will be crucial for correctly populating the new table structures.