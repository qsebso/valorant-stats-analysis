"""
Scraper module for VALORANT match data.
Handles fetching and parsing match data from VLR.gg.
"""

import logging
import requests
from typing import Dict, Any
from .parser import get_match_paths, parse_vlr_minimal_all_maps
from .loader import load_events
from .utils import rate_limit
from .saver import save_match

# Set up logging
logger = logging.getLogger(__name__)

def scrape_match(match_path: str, event: Dict[str, Any]) -> None:
    """
    Scrape a single match from VLR.gg, process all maps and all players.
    """
    match_url = f"https://www.vlr.gg{match_path}"
    logger.info(f"Scraping match: {match_url}")
    rate_limit()
    response = requests.get(match_url)
    response.raise_for_status()
    html = response.text
    # Use the new parser
    match_result = parse_vlr_minimal_all_maps(html)
    if not match_result or not match_result.get('maps'):
        logger.error(f"Failed to parse match data from {match_url}")
        return
    # For each map, for each player, save to DB
    for map_info in match_result['maps']:
        for player_data in map_info['players']:
            # Add event and match context
            player_data.update({
                "event_id": event["event_id"],
                "event_name": event["event_name"],
                "bracket_stage": event.get("bracket_stage", match_result.get("phase", "Unknown")),
                "match_id": match_path.split("/")[-2],
                "match_datetime": event.get("match_datetime", match_result.get("date", None)),
                "map_index": map_info["map_index"],
                "map_name": map_info["map_name"],
                "team1_name": map_info["team1_name"],
                "team2_name": map_info["team2_name"],
                "team1_score": map_info["team1_score"],
                "team2_score": map_info["team2_score"]
            })
            save_match(player_data)

def main() -> None:
    """Main entry point for the scraper."""
    # Load event configurations
    events = load_events()
    if not events:
        logger.error("No events found in config")
        return
        
    # Process each event
    for event in events:
        logger.info(f"Processing event: {event['event_name']} ({event['event_id']})")
        
        try:
            # Get all match paths for this event (auto-scrape or manual override)
            match_paths = get_match_paths(event)
            
            # Process each match path
            for path in match_paths:
                try:
                    scrape_match(path, event)
                except Exception as e:
                    logger.error(f"Failed to scrape match {path}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Failed to process event {event['event_id']}: {e}")
            continue

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
