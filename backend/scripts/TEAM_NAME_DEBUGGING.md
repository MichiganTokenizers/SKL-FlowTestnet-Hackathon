# Team Name Resolution System

## Overview
The team name resolution system in `sleeper_service.py` has been enhanced with comprehensive debugging and improved priority logic to help identify and resolve team name import issues.

## Priority Order (Updated)

### 1. **Custom Roster Team Name** (Highest Priority)
- **Source**: `roster.metadata.team_name`
- **Description**: Team name explicitly set by the user for this specific roster
- **When Used**: When user has set a custom team name for their roster
- **Validation**: Must be non-empty and not just whitespace

### 2. **League-Specific Team Name** (Second Priority)
- **Source**: `participant.metadata.team_name`
- **Description**: Team name set by the user specifically for this league
- **When Used**: When user has set a team name for this particular league
- **Validation**: Must be non-empty and not just whitespace

### 3. **User Display Name** (Third Priority)
- **Source**: `participant.display_name`
- **Description**: User's general display name across all Sleeper
- **When Used**: When no league-specific or roster-specific team name is available
- **Validation**: Must be non-empty and not just whitespace

### 4. **User Username** (Fourth Priority)
- **Source**: `participant.username`
- **Description**: User's Sleeper username
- **When Used**: When no other team name sources are available
- **Validation**: Must be non-empty and not just whitespace

### 5. **Default Fallback** (Lowest Priority)
- **Source**: Generated fallback
- **Description**: `"Unknown Team (Owner: {owner_id})"`
- **When Used**: When no valid team name sources are found
- **Validation**: Always available as last resort

## Debugging Features

### 1. **Participant Data Logging**
- Logs all participant information including metadata
- Shows available team name sources for each user
- Helps identify missing or incorrect participant data

### 2. **Roster Data Logging**
- Logs roster metadata and team name information
- Shows what team name data is available in roster objects
- Helps identify missing roster metadata

### 3. **Team Name Resolution Debugging**
- Comprehensive logging of all available team name sources
- Shows which source was selected and why
- Includes validation checks for suspicious team names

### 4. **Validation Checks**
- Checks for empty strings, whitespace-only strings
- Identifies suspicious team names (unknown, n/a, null, etc.)
- Provides detailed error information when validation fails

## Debug Output Examples

### Participant Data Log
```json
{
  "user_id": "123456",
  "username": "user123",
  "display_name": "John Doe",
  "metadata": {
    "team_name": "Dynasty Warriors"
  },
  "team_name_from_metadata": "Dynasty Warriors"
}
```

### Roster Data Log
```json
{
  "roster_id": "789",
  "owner_id": "123456",
  "metadata": {
    "team_name": "Custom Team Name"
  },
  "team_name_from_metadata": "Custom Team Name"
}
```

### Team Name Resolution Log
```json
{
  "roster_id": "789",
  "league_id": "456",
  "owner_id": "123456",
  "available_sources": {
    "roster_metadata": {
      "value": "Custom Team Name",
      "source": "roster.metadata.team_name"
    },
    "participant_metadata": {
      "value": "Dynasty Warriors",
      "source": "participant.metadata.team_name",
      "participant_details": {
        "display_name": "John Doe",
        "username": "user123"
      }
    },
    "display_name": {
      "value": "John Doe",
      "source": "participant.display_name"
    },
    "username": {
      "value": "user123",
      "source": "participant.username"
    }
  },
  "final_selection": {
    "team_name": "Custom Team Name",
    "selected_source": "roster_metadata"
  }
}
```

## Troubleshooting Common Issues

### 1. **"Unknown Team" Appearing**
- Check if participant data is being fetched correctly
- Verify that owner_id matches between roster and participant data
- Look for missing or empty metadata in participant objects

### 2. **Wrong Team Name Selected**
- Review the priority order to ensure it matches expectations
- Check if custom roster team names are being set correctly
- Verify that league-specific team names are available in participant metadata

### 3. **Missing Participant Data**
- Ensure `get_league_users()` API call is successful
- Check if participant_map is being populated correctly
- Verify that owner_id values match between roster and participant data

### 4. **Empty or Invalid Team Names**
- Look for validation warnings in logs
- Check if team names contain only whitespace
- Verify that API responses contain expected data structure

## Configuration Options

The system can be easily modified by adjusting the priority order in the team name resolution logic. The current order prioritizes user-customized names over system-generated ones, which is typically the desired behavior.

## Future Enhancements

1. **User Preferences**: Allow users to set their preferred team name source
2. **Team Name Templates**: Support for dynamic team name generation
3. **Historical Tracking**: Track team name changes over time
4. **Bulk Operations**: Support for bulk team name updates 