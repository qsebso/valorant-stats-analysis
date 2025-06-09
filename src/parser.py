"""
Parser module for VALORANT match data collection.

This module handles the extraction of match data from VLR.gg HTML pages:
1. Event match lists - extracting all match IDs for an event
2. Match scoreboards - parsing player statistics and match metadata
"""

import logging
from typing import Dict, List
import requests
from bs4 import BeautifulSoup

# Set up module-level logger for consistent logging across functions
logger = logging.getLogger(__name__)

def get_match_ids(event_id: str) -> List[str]:
    """Extract all match IDs from an event's match list page.
    
    Args:
        event_id: The VLR.gg event identifier (e.g., "12345")
        
    Returns:
        A list of match ID strings found in the event's match list
        
    Raises:
        requests.RequestException: If the HTTP request fails
        ValueError: If the page structure is invalid or no matches found
    """
    # Construct the event matches URL
    url = f"https://www.vlr.gg/event/matches/{event_id}/"
    logger.info(f"Fetching match list from {url}")
    
    # Fetch the page and ensure the request succeeded
    response = requests.get(url)
    response.raise_for_status()
    
    # Parse the HTML and find all match links
    # Using the selector from scraping.rules: ".wf-table .match-row a"
    soup = BeautifulSoup(response.text, "html.parser")
    match_links = soup.select(".wf-table .match-row a")
    
    if not match_links:
        raise ValueError(f"No match links found for event {event_id}")
        
    # Extract match IDs from href attributes
    # Example href: "/12345/team1-vs-team2" -> extract "12345"
    match_ids = []
    for link in match_links:
        href = link.get("href", "")
        if href.startswith("/"):
            match_id = href.split("/")[1]
            # Only add if it's a valid numeric ID
            if match_id.isdigit():
                match_ids.append(match_id)
                
    logger.info(f"Found {len(match_ids)} matches for event {event_id}")
    return match_ids

def parse_scoreboard(soup: BeautifulSoup) -> List[Dict]:
    """Extract match data from a VLR.gg scoreboard page.
    
    Args:
        soup: BeautifulSoup object of the parsed scoreboard HTML
        
    Returns:
        A list of dictionaries, each containing one player's stats for a map.
        Each dict includes match metadata (bracket_stage, teams, etc.) and
        the player's performance metrics.
        
    Raises:
        ValueError: If required elements are missing or page structure is invalid
    """
    # First, extract the match header data which contains metadata
    # This includes bracket stage, datetime, patch, and team scores
    header = soup.select_one(".vm-header")
    if not header:
        raise ValueError("Match header not found in scoreboard")
        
    # Extract bracket stage from the header
    # Example: "Main Event: Upper Bracket Round 1"
    bracket_elem = header.select_one(".vm-header__stage")
    bracket_stage = bracket_elem.text.strip() if bracket_elem else "Unknown"
    if bracket_stage == "Unknown":
        logger.warning("Bracket stage not found in match header")
        
    # Get match datetime from the UTC timestamp attribute
    # This ensures consistent timezone handling
    time_elem = header.select_one(".vm-header__time")
    match_datetime = time_elem.get("data-utc-ts") if time_elem else None
    if not match_datetime:
        raise ValueError("Match datetime not found in header")
        
    # Get the game patch version
    # Example: "Patch 7.0"
    patch_elem = header.select_one(".vm-header__patch")
    patch = patch_elem.text.strip() if patch_elem else "Unknown"
    
    # Extract team names and scores
    # The header contains exactly two teams with their scores
    teams = header.select(".vm-header__team")
    if len(teams) != 2:
        raise ValueError("Expected exactly 2 teams in match header")
        
    # Parse team 1 data
    team1_name = teams[0].select_one(".vm-header__team-name").text.strip()
    team1_score = int(teams[0].select_one(".vm-header__score").text.strip())
    
    # Parse team 2 data
    team2_name = teams[1].select_one(".vm-header__team-name").text.strip()
    team2_score = int(teams[1].select_one(".vm-header__score").text.strip())
    
    # Process each map's statistics
    # A match can have multiple maps, each with its own stats table
    rows = []
    for map_section in soup.select(".vm-stats__layout"):
        # Get the map name (e.g., "Ascent", "Haven")
        map_name = map_section.select_one(".vm-stats__header").text.strip()
        
        # Find the stats table for this map
        # Each map has a table with player rows
        table = map_section.select_one("table")
        if not table:
            logger.warning(f"No stats table found for map {map_name}")
            continue
            
        # Process each player's row in the stats table
        for row in table.select("tbody tr"):
            cells = row.select("td")
            if len(cells) < 20:  # Sanity check for expected columns
                logger.warning(f"Invalid row structure in map {map_name}")
                continue
                
            # Extract player data in the exact order specified in schema
            # Each cell corresponds to a specific stat in our database schema
            player_data = {
                # Map and player identity
                "map_name": map_name,
                "player_name": cells[0].text.strip(),
                "player_team": cells[1].text.strip(),
                # Country is stored in an img tag's title attribute
                "player_country": cells[2].select_one("img")["title"] if cells[2].select_one("img") else "Unknown",
                "agent_played": cells[3].text.strip(),
                
                # Core stats
                "rounds_played": int(cells[4].text.strip()),
                "rating_2_0": float(cells[5].text.strip()),
                "game_score": float(cells[6].text.strip()),
                "ACS": float(cells[7].text.strip()),
                "KDRatio": float(cells[8].text.strip()),
                
                # Percentage stats (remove % symbol)
                "KAST_pct": float(cells[9].text.strip().rstrip("%")),
                "ADR": float(cells[10].text.strip()),
                "KPR": float(cells[11].text.strip()),
                "APR": float(cells[12].text.strip()),
                "FKPR": float(cells[13].text.strip()),
                "FDPR": float(cells[14].text.strip()),
                "HS_pct": float(cells[15].text.strip().rstrip("%")),
                "CL_pct": float(cells[16].text.strip().rstrip("%")),
                
                # Count stats
                "CL_count": int(cells[17].text.strip()),
                "max_kills_in_round": int(cells[18].text.strip()),
                "total_kills": int(cells[19].text.strip()),
                "total_deaths": int(cells[20].text.strip()),
                "total_assists": int(cells[21].text.strip()),
                "total_first_kills": int(cells[22].text.strip()),
                "total_first_deaths": int(cells[23].text.strip())
            }
            
            # Add the match metadata to each player's row
            # This ensures each row has complete context
            player_data.update({
                "bracket_stage": bracket_stage,
                "match_datetime": match_datetime,
                "patch": patch,
                "team1_name": team1_name,
                "team1_score": team1_score,
                "team2_name": team2_name,
                "team2_score": team2_score
            })
            
            rows.append(player_data)
            
    if not rows:
        raise ValueError("No player data found in scoreboard")
        
    logger.info(f"Parsed {len(rows)} player entries from scoreboard")
    return rows
