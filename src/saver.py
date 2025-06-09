"""
Handles persistence of match data into the database.

This module is responsible for saving scraped match data to the SQLite
database, using the schema defined in docs/schema.md. It provides a
clean interface for database operations, abstracting away the SQL
details from the rest of the application.
"""

import logging
from typing import Dict
from db import insert_map_stats

# Set up module-level logger
logger = logging.getLogger(__name__)

def save_match(row: Dict) -> None:
    """
    Insert a map_stats row into the database.

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
    try:
        # Attempt to insert the row into the database
        insert_map_stats(row)
        logger.info(f"Saved match {row.get('match_id')} for player {row.get('player_name')}")
    except Exception as e:
        # Log any database errors but don't re-raise
        # This allows the scraper to continue with other matches
        logger.error(f"Error saving match {row.get('match_id')}: {e}") 