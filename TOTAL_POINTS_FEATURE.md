# Total Points Feature - League Standings

## Overview
The League Standings table now includes a "Total Points" column that displays each team's total points scored for the season. This data is sourced from the Sleeper API and provides users with additional insight into team performance beyond just wins and losses.

## Features

### Backend Changes
- **Database Schema**: Added `points_for` column to the `rosters` table
- **Sleeper Service**: Updated to fetch and store `points_for` data from Sleeper API roster settings
- **API Endpoint**: Modified `/league/standings/local` to return points data
- **Data Handling**: Gracefully handles null/missing points data by defaulting to 0.0

### Frontend Changes
- **New Column**: Added "Total Points" column to the League Standings table
- **Data Display**: Shows points with 2 decimal places (e.g., "1250.75")
- **Fallback**: Displays "0.00" for teams without points data

## Database Migration

### For New Installations
The `points_for` column will be automatically created when the database is initialized.

### For Existing Installations
Run the migration script to add the column to existing databases:

```bash
cd backend/scripts
python add_points_for_column.py
```

The script will:
1. Check if the column already exists
2. Add the column if it doesn't exist
3. Set a default value of 0.0 for existing rosters
4. Verify the migration was successful

## Data Source

The `points_for` data comes from the Sleeper API roster settings:
- **Field**: `roster.settings.points_for`
- **Type**: Real number (decimal)
- **Description**: Total fantasy points scored by the team for the season
- **Update Frequency**: Updated when Sleeper data is refreshed via `/sleeper/fetchAll`

## API Response Format

The standings endpoint now returns:

```json
{
  "success": true,
  "league_id": "league_123",
  "league_name": "My League",
  "standings": [
    {
      "roster_id": "roster_1",
      "team_name": "Team Alpha",
      "owner_display_name": "John Doe",
      "wins": 8,
      "losses": 5,
      "ties": 0,
      "points_for": 1250.75,
      "player_count": 15
    }
  ]
}
```

## Testing

Run the test suite to verify the functionality:

```bash
cd tests
pytest test_standings_with_points.py -v
```

Tests cover:
- ✅ Points data is correctly returned
- ✅ Null points data is handled gracefully
- ✅ Authorization checks work properly
- ✅ Error handling for missing parameters

## Usage Notes

1. **Data Availability**: Points data will only be available after the first Sleeper data refresh
2. **Season Context**: Points are cumulative for the current season
3. **Decimal Precision**: Points are displayed with 2 decimal places for accuracy
4. **Performance**: The additional column has minimal impact on query performance

## Future Enhancements

Potential improvements for future versions:
- **Points Against**: Add `points_against` column for defensive statistics
- **Weekly Breakdown**: Show points by week for detailed analysis
- **Points Rankings**: Sort standings by points scored
- **Historical Data**: Track points across multiple seasons

## Troubleshooting

### No Points Data Showing
1. Verify Sleeper data has been refreshed recently
2. Check that the `points_for` column exists in the database
3. Ensure the roster has played games in the current season

### Migration Issues
1. Run the migration script with proper database permissions
2. Check database logs for any constraint violations
3. Verify the database schema matches expected structure

### API Errors
1. Check that the user is authorized for the league
2. Verify the league_id parameter is provided
3. Ensure the database connection is working properly

## Support

For issues or questions about this feature:
1. Check the application logs for error messages
2. Verify the database schema is correct
3. Test with the provided test suite
4. Review the Sleeper API documentation for data format changes 