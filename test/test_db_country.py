"""
Test script to verify player country data is being saved to the database.
"""

import logging
import sys
import os
import sqlite3
from typing import Dict, Any

# Add src directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper import scrape_match
from src.db import get_connection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_db_country_save(match_path: str, event: Dict[str, Any]) -> None:
    """
    Test that country data is being saved to the database.
    
    Args:
        match_path: The VLR.gg match path
        event: Event configuration dictionary
    """
    # First scrape the match
    logger.info(f"Scraping match: {match_path}")
    scrape_match(match_path, event)
    
    # Then verify the data in the database
    conn = get_connection()
    cursor = conn.cursor()
    
    # Query the database for player country data
    cursor.execute("""
        SELECT player_name, player_country, map_name, team1_name, team2_name
        FROM map_stats
        WHERE match_id = ?
        ORDER BY map_name, player_name
    """, (match_path.split('/')[-2],))
    
    rows = cursor.fetchall()
    if not rows:
        logger.error("No data found in database!")
        return
        
    logger.info("\nVerifying country data in database:")
    logger.info("-" * 80)
    for row in rows:
        logger.info(f"Player: {row[0]}")
        logger.info(f"Country: {row[1]}")
        logger.info(f"Map: {row[2]}")
        logger.info(f"Match: {row[3]} vs {row[4]}")
        logger.info("-" * 40)
    
    conn.close()

if __name__ == "__main__":
    # Test with a recent match
    test_match = "/19071/100-thieves-vs-sentinels-valorant-champions-2023-champions-tour-2023-americas-lcq"
    test_event = {
        "event_id": "19071",
        "event_name": "VALORANT Champions 2023",
        "bracket_stage": "Champions Tour 2023: Americas LCQ"
    }
    test_db_country_save(test_match, test_event) 