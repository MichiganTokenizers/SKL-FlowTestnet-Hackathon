-- Create the season_curr table
CREATE TABLE IF NOT EXISTS season_curr (
    current_year INTEGER NOT NULL,
    IsOffSeason INTEGER NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Delete any existing data to ensure we only have one row
DELETE FROM season_curr;

-- Insert the initial values (2025 and 1 for off-season)
INSERT INTO season_curr (current_year, IsOffSeason) VALUES (2025, 1); 