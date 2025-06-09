"""
Scraper module for VALORANT match data collection.

This module orchestrates the scraping process:
1. Loads event configurations from config/events.yaml
2. Fetches match lists for each event
3. Scrapes individual match scoreboards
4. Saves the parsed data to the database
"""

import logging
from typing import Dict, List
import requests
from bs4 import BeautifulSoup

# Import our custom modules
from parser import get_match_ids, parse_scoreboard
from loader import load_events
from utils import rate_limit
from saver import save_match

# Set up module-level logger
logger = logging.getLogger(__name__)

def scrape_match(match_id: str, event: Dict) -> None:
    """Scrape and save data from a single match scoreboard.
    
    Args:
        match_id: The VLR.gg match identifier
        event: Dictionary containing event metadata (id, name)
        
    Raises:
        requests.RequestException: If the HTTP request fails
        ValueError: If the page structure is invalid
    """
    # Rate limit requests to avoid overwhelming the server
    # This ensures we're respectful of VLR.gg's resources
    rate_limit()
    
    # Construct the match URL and log the attempt
    url = f"https://www.vlr.gg/match/{match_id}/"
    logger.info(f"Scraping match {match_id} from {url}")
    
    try:
        # Fetch the match page
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse the HTML and extract match data
        soup = BeautifulSoup(response.text, "html.parser")
        rows = parse_scoreboard(soup)
        
        # Enrich each player's row with event context
        # This ensures we have complete metadata for each entry
        for row in rows:
            row.update({
                "event_id": event["event_id"],
                "event_name": event["event_name"],
                "phase": row["bracket_stage"]  # Use bracket_stage as phase
            })
            # Save to database
            save_match(row)
            
        logger.info(f"Successfully saved {len(rows)} rows for match {match_id}")
        
    except Exception as e:
        # Log any errors but re-raise to let caller handle them
        logger.error(f"Failed to scrape match {match_id}: {str(e)}")
        raise

def main() -> None:
    """Main entry point for the scraper.
    
    Loads event configurations and scrapes all matches for each event.
    Handles errors gracefully and logs progress.
    """
    logger.info("Starting scraper")
    
    try:
        # Load event configurations from YAML
        events = load_events()
        logger.info(f"Loaded {len(events)} events from config")
        
        # Process each event
        for event in events:
            logger.info(f"Processing event: {event['event_name']} ({event['event_id']})")
            
            try:
                # Get all match IDs for this event
                match_ids = get_match_ids(event["event_id"])
                
                # Process each match
                for match_id in match_ids:
                    try:
                        scrape_match(match_id, event)
                    except Exception as e:
                        # Log match errors but continue with next match
                        logger.error(f"Failed to process match {match_id}: {str(e)}")
                        continue
                        
            except Exception as e:
                # Log event errors but continue with next event
                logger.error(f"Failed to process event {event['event_id']}: {str(e)}")
                continue
                
        logger.info("Scraper completed successfully")
        
    except Exception as e:
        # Log fatal errors that prevent scraping from continuing
        logger.error(f"Scraper failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
