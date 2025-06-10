"""
Test script to verify player country extraction from VLR.gg matches.
"""

import logging
import sys
import os
from typing import Dict, Any

# Add src directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parser import parse_vlr_minimal_all_maps
from src.utils import rate_limit
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_match_country_extraction(match_path: str) -> None:
    """
    Test country extraction from a specific match.
    
    Args:
        match_path: The VLR.gg match path (e.g. '/12345/match-1')
    """
    match_url = f"https://www.vlr.gg{match_path}"
    logger.info(f"Testing country extraction from: {match_url}")
    
    # Fetch match page
    rate_limit()
    response = requests.get(match_url)
    response.raise_for_status()
    
    # Parse match data
    match_data = parse_vlr_minimal_all_maps(response.text)
    
    # Check each map's player data
    for map_info in match_data['maps']:
        logger.info(f"\nChecking map: {map_info['map_name']}")
        for player in map_info['players']:
            logger.info(f"Player: {player['Player']}")
            logger.info(f"Country: {player.get('Country', 'MISSING')}")
            logger.info(f"Team: {player['Team']}")
            logger.info(f"Agent: {player['Agent']}")
            logger.info("-" * 40)

if __name__ == "__main__":
    # Test with a recent match - you can change this to any match path
    test_match = "/19071/100-thieves-vs-sentinels-valorant-champions-2023-champions-tour-2023-americas-lcq"
    test_match_country_extraction(test_match) 