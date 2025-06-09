# Database Schema

## Match Statistics Table

This document defines the complete SQLite table schema for storing VALORANT match statistics.

```sql
CREATE TABLE IF NOT EXISTS map_stats (
  event_id            TEXT,
  event_name          TEXT,
  bracket_stage       TEXT,
  match_id            TEXT,
  match_datetime      DATETIME,
  patch               TEXT,
  map_name            TEXT,
  team1_name          TEXT,
  team1_score         INTEGER,
  team2_name          TEXT,
  team2_score         INTEGER,
  player_name         TEXT,
  player_team         TEXT,
  player_country      TEXT,
  agent_played        TEXT,
  rounds_played       INTEGER,
  rating_2_0          REAL,
  game_score          REAL,
  ACS                 REAL,
  KDRatio             REAL,
  KAST_pct            REAL,
  ADR                 REAL,
  KPR                 REAL,
  APR                 REAL,
  FKPR                REAL,
  FDPR                REAL,
  HS_pct              REAL,
  CL_pct              REAL,
  CL_count            INTEGER,
  max_kills_in_round  INTEGER,
  total_kills         INTEGER,
  total_deaths        INTEGER,
  total_assists       INTEGER,
  total_first_kills   INTEGER,
  total_first_deaths  INTEGER
);
```

### Column Descriptions

- `event_id`: Unique identifier for the tournament/event
- `event_name`: Name of the tournament or event
- `bracket_stage`: Tournament stage (e.g., "Group Stage", "Playoffs", "Finals")
- `match_id`: Unique identifier for the match
- `match_datetime`: Date and time when the match was played
- `patch`: Game version/patch number
- `map_name`: Name of the map played
- `team1_name`: Name of the first team
- `team1_score`: Final score of the first team
- `team2_name`: Name of the second team
- `team2_score`: Final score of the second team
- `player_name`: Player's in-game name
- `player_team`: Team the player belongs to
- `player_country`: Player's country of origin
- `agent_played`: Agent selected by the player
- `rounds_played`: Number of rounds the player participated in
- `rating_2_0`: Player's VLR rating (2.0 formula)
- `game_score`: Player's game score
- `ACS`: Average Combat Score
- `KDRatio`: Kill/Death ratio
- `KAST_pct`: Percentage of rounds with a kill, assist, survival, or trade
- `ADR`: Average Damage per Round
- `KPR`: Kills per Round
- `APR`: Assists per Round
- `FKPR`: First Kills per Round
- `FDPR`: First Deaths per Round
- `HS_pct`: Headshot percentage
- `CL_pct`: Clutch percentage
- `CL_count`: Number of clutches won
- `max_kills_in_round`: Most kills in a single round
- `total_kills`: Total kills in the match
- `total_deaths`: Total deaths in the match
- `total_assists`: Total assists in the match
- `total_first_kills`: Total first kills in the match
- `total_first_deaths`: Total first deaths in the match 