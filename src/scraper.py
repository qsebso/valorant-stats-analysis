"""
Scraper module for VALORANT match data.
Handles fetching and parsing match data from VLR.gg.
"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any

from .parser import get_match_paths, parse_scoreboard
from .loader import load_events
from .utils import rate_limit
from .saver import save_match

# Set up logging
logger = logging.getLogger(__name__)

def scrape_match(match_path: str, event: Dict[str, Any]) -> None:
    """
    Scrape a single match from VLR.gg.
    
    Args:
        match_path: URL path to the match (e.g. '/match/12345/team1-vs-team2')
        event: Event configuration dict containing metadata
    """
    # Construct full match URL
    match_url = f"https://www.vlr.gg{match_path}"
    logger.info(f"Scraping match: {match_url}")
    
    # Rate limit before request
    rate_limit()
    
    # Fetch match page
    response = requests.get(match_url)
    response.raise_for_status()
    
    # Parse HTML
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extract match data
    match_data = parse_scoreboard(soup)
    if not match_data:
        logger.error(f"Failed to parse match data from {match_url}")
        return
        
    # Add event context to each player's data
    for player_data in match_data:
        player_data.update({
            "event_id": event["event_id"],
            "event_name": event["event_name"],
            "bracket_stage": event.get("bracket_stage", "Unknown"),
            "match_id": match_path.split("/")[-2],  # Extract ID from path
            "match_datetime": event.get("match_datetime", None)
        })
        
        # Save to database
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
