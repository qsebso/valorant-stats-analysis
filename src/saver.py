"""
Handles persistence of match data into the database.

This module is responsible for saving scraped match data to the SQLite
database, using the schema defined in docs/schema.md. It provides a
clean interface for database operations, abstracting away the SQL
details from the rest of the application.
"""

import logging
from typing import Dict, Any, Optional
from .db import insert_map_stats

# Set up module-level logger
logger = logging.getLogger(__name__)

# Mapping from VLR stat names to DB schema keys (expanded for all DB columns)
STAT_KEY_MAP = {
    # Player info
    "Player": "player_name",
    "Team": "player_team",
    "Agent": "agent_played",
    "Country": "player_country",
    # Core stats
    "Rating 2.0": "rating_2_0",
    "Game Score": "game_score",
    "Average Combat Score": "ACS",
    "K/D Ratio": "KDRatio",
    "KAST": "KAST_pct",
    # Advanced stats
    "Average Damage per Round": "ADR",
    "Headshot %": "HS_pct",
    # Raw stats
    "Kills": "total_kills",
    "Deaths": "total_deaths",
    "Assists": "total_assists",
    "First Kills": "total_first_kills",
    "First Deaths": "total_first_deaths",
}

# List of all columns in the map_stats table
MAP_STATS_COLUMNS = [
    'event_id', 'event_name', 'bracket_stage', 'match_id', 'match_datetime', 'patch',
    'map_name', 'map_index', 'team1_name', 'team1_score', 'team2_name', 'team2_score',
    'winner',
    'rounds_played',  # Calculated from team scores
    'player_name', 'player_team', 'player_country', 'agent_played',
    'rating_2_0', 'ACS', 'KDRatio', 'KDARatio', 'KAST_pct',
    'ADR', 'KPR', 'APR', 'FKPR', 'FDPR', 'HS_pct',  # KPR, APR, FKPR, FDPR are calculated
    'total_kills', 'total_deaths', 'total_assists',
    'total_first_kills', 'total_first_deaths',
    # New columns for round sides and duration
    'team1_attacker_rounds', 'team1_defender_rounds',
    'team2_attacker_rounds', 'team2_defender_rounds',
    'map_duration'
]

def calculate_per_round_stats(row: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """
    Calculate per-round statistics from raw totals and rounds played.
    Also calculate KDRatio and KDARatio.
    """
    rounds = row.get('rounds_played')
    if not rounds or rounds <= 0:
        return {
            'KPR': None,
            'APR': None,
            'FKPR': None,
            'FDPR': None,
            'KDRatio': None,
            'KDARatio': None
        }
    try:
        kills = int(row.get('total_kills', 0) or 0)
        assists = int(row.get('total_assists', 0) or 0)
        deaths = int(row.get('total_deaths', 0) or 0)
        first_kills = int(row.get('total_first_kills', 0) or 0)
        first_deaths = int(row.get('total_first_deaths', 0) or 0)
    except (ValueError, TypeError):
        return {
            'KPR': None,
            'APR': None,
            'FKPR': None,
            'FDPR': None,
            'KDRatio': None,
            'KDARatio': None
        }
    # Per-round stats
    kpr = round(kills / rounds, 3)
    apr = round(assists / rounds, 3)
    fkpr = round(first_kills / rounds, 3)
    fdpr = round(first_deaths / rounds, 3)
    # KDRatio and KDARatio
    if deaths > 0:
        kdr = round(kills / deaths, 3)
        kdar = round((kills + assists) / deaths, 3)
    else:
        kdr = None
        kdar = None
    return {
        'KPR': kpr,
        'APR': apr,
        'FKPR': fkpr,
        'FDPR': fdpr,
        'KDRatio': kdr,
        'KDARatio': kdar
    }

def save_match(row: Dict) -> None:
    """
    Insert a map_stats row into the database.
    Remap stat keys to DB schema before saving.

    This function takes a dictionary matching our schema and saves it
    to the map_stats table. It handles any database errors and logs
    the result of the operation.

    Args:
        row: Dictionary matching the map_stats schema.
            Must contain at least match_id, map_name, and player_name
            for logging purposes.

    Note:
        The actual database insertion is handled by db.insert_map_stats.
        This function just provides error handling and logging.
    """
    # Remap keys using STAT_KEY_MAP, keep other keys as-is, skip 'Kills - Deaths'
    db_row = {}
    for k, v in row.items():
        if k == "Kills - Deaths":
            continue  # Not in DB schema
        db_key = STAT_KEY_MAP.get(k, k)
        db_row[db_key] = v

    # Calculate rounds_played from team scores
    try:
        team1_score = int(row.get('team1_score', 0) or 0)
        team2_score = int(row.get('team2_score', 0) or 0)
        db_row['rounds_played'] = team1_score + team2_score
    except (ValueError, TypeError):
        db_row['rounds_played'] = None
        logger.warning(f"Could not calculate rounds_played for match {row.get('match_id')}")

    # Calculate per-round stats and ratios
    per_round_stats = calculate_per_round_stats(db_row)
    db_row.update(per_round_stats)

    # Ensure all required columns are present, fill missing with None
    for col in MAP_STATS_COLUMNS:
        if col not in db_row:
            db_row[col] = None

    # Remove any extra keys not in schema
    db_row = {k: db_row[k] for k in MAP_STATS_COLUMNS}

    # Ensure phase/bracket_stage is set
    if not db_row.get('bracket_stage'):
        db_row['bracket_stage'] = row.get('phase') or row.get('bracket_stage') or 'Unknown'
    # Ensure patch is set if available
    if not db_row.get('patch'):
        db_row['patch'] = row.get('patch') or None

    # Add winner if present
    if 'winner' in row:
        db_row['winner'] = row['winner']

    try:
        insert_map_stats(db_row)
        logger.info(f"Saved match {db_row.get('match_id')} for player {db_row.get('player_name')}")
    except Exception as e:
        # Log any database errors but don't re-raise
        # This allows the scraper to continue with other matches
        logger.error(f"Error saving match {db_row.get('match_id')}: {e}") 