"""
Parser module for VALORANT match data collection.

This module handles the extraction of match data from VLR.gg HTML pages:
1. Event match lists - extracting all match IDs for an event
2. Match scoreboards - parsing player statistics and match metadata
"""

import logging
import re
import requests
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup

from .utils import rate_limit

# Set up module-level logger for consistent logging across functions
logger = logging.getLogger(__name__)

def get_match_paths(event: Dict[str, Any]) -> List[str]:
    """
    Get all match URL paths for an event.
    
    Args:
        event: Event configuration dict containing event_id and optional match_urls
        
    Returns:
        List of match URL paths (e.g. ['/19071/...', '/19072/...'])
        
    Raises:
        ValueError: If no matches found and no manual URLs provided
    """
    # Check for manual override only if non-empty
    if event.get("match_urls") and len(event["match_urls"]) > 0:
        logger.info(f"Using manual match URLs for event {event['event_id']}")
        return event["match_urls"]
        
    # Otherwise scrape from event page
    event_url = f"https://www.vlr.gg/event/{event['event_id']}"
    logger.info(f"Scraping match list from {event_url}")
    
    # Rate limit before request
    rate_limit()
    
    # Fetch event page
    resp = requests.get(event_url)
    resp.raise_for_status()
    
    # Parse HTML and find match links
    soup = BeautifulSoup(resp.text, "html.parser")
    # Find all anchors whose href begins with /<digits>/
    links = soup.find_all("a", href=re.compile(r"^/\d+/"))
    
    if not links:
        raise ValueError(f"No match links found for event {event['event_id']}")
        
    # Extract and dedupe the hrefs
    paths = []
    for a in links:
        href = a["href"].strip()
        if href not in paths:
            paths.append(href)
            
    logger.info(f"Found {len(paths)} unique matches for event {event['event_id']}")
    return paths

def parse_scoreboard(table: BeautifulSoup) -> list[dict[str, Any]]:
    """Parse a scoreboard table into a list of player stats dictionaries."""
    scoreboard = table.find('table', class_='wf-table-inset') if table.name != 'table' else table
    if not scoreboard:
        raise ValueError("No scoreboard table found.")
    player_rows = scoreboard.find_all('tr')[1:]
    if not player_rows:
        raise ValueError("No player rows found in scoreboard.")
    header_cells = scoreboard.find('tr').find_all('th')
    header_map = {}
    for i, cell in enumerate(header_cells):
        header_text = cell.get('title') or cell.get_text(strip=True)
        header_text = header_text.strip()
        if header_text.lower().startswith('kill, assist, trade, survive'):
            header_text = 'KAST'
        header_map[i] = header_text
    players = []
    for row in player_rows:
        cells = row.find_all('td')
        if not cells:
            continue
        player = {}
        player_cell = cells[0]
        name_div = player_cell.find('div', class_='text-of')
        if name_div:
            player['Player'] = name_div.get_text(strip=True)
        team_div = player_cell.find('div', class_='ge-text-light')
        if team_div:
            player['Team'] = team_div.get_text(strip=True)
        agent_cell = cells[1]
        agent_img = agent_cell.find('img')
        if agent_img:
            player['Agent'] = agent_img.get('alt', '').strip()
        kills_val = deaths_val = None
        for i, cell in enumerate(cells[2:], start=2):
            if i not in header_map:
                continue
            col_name = header_map[i]
            if col_name == 'Kills - Deaths':
                continue  # We'll calculate this ourselves
            stat_span = cell.find('span', class_='side mod-side mod-both')
            if not stat_span:
                stat_span = cell.find('span', class_='side mod-both')
            if stat_span:
                stat_value = stat_span.get_text(strip=True)
            else:
                stat_value = cell.get_text(strip=True)
                if stat_value.strip() in {'/', ''}:
                    stat_value = ''
            player[col_name] = stat_value
            if col_name == 'Kills':
                try:
                    kills_val = int(stat_value)
                except Exception:
                    kills_val = None
            if col_name == 'Deaths':
                try:
                    deaths_val = int(stat_value)
                except Exception:
                    deaths_val = None
        # Calculate Kills - Deaths
        if kills_val is not None and deaths_val is not None:
            diff = kills_val - deaths_val
            if diff > 0:
                kd_str = f'+{diff}'
            elif diff < 0:
                kd_str = f'{diff}'
            else:
                kd_str = '0'
            player['Kills - Deaths'] = kd_str
        else:
            player['Kills - Deaths'] = ''
        players.append(player)
    return players

def parse_vlr_scoreboard_table(html: str) -> List[Dict]:
    """
    Parse a VLR.gg scoreboard table (minimal or full HTML) and return player stats.
    - Finds the first .wf-table-inset.mod-overview table.
    - Maps <th> headers to <td> cells.
    - Extracts the 'both' value for stats with multiple values.
    - Handles player/agent/country/team info in the first two columns.
    Returns a list of dicts, one per player row.
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one(".wf-table-inset.mod-overview")
    if not table:
        raise ValueError("No scoreboard table found.")
    # 1. Parse headers
    headers = []
    for th in table.select("thead th"):
        # Use the title attribute if present, else text
        title = th.get("title") or th.get_text(strip=True)
        headers.append(title)
    # 2. Parse player rows
    rows = []
    for tr in table.select("tbody tr"):
        tds = tr.find_all("td")
        if not tds or len(tds) < 2:
            continue
        row = {}
        # Player info (first column)
        player_cell = tds[0]
        row["player_name"] = player_cell.select_one(".text-of").get_text(strip=True) if player_cell.select_one(".text-of") else "Unknown"
        row["player_team"] = player_cell.select_one(".ge-text-light").get_text(strip=True) if player_cell.select_one(".ge-text-light") else "Unknown"
        row["player_country"] = player_cell.select_one("i[title]")["title"] if player_cell.select_one("i[title]") else "Unknown"
        # Agent (second column)
        agent_cell = tds[1]
        row["agent_played"] = agent_cell.select_one("img")["title"] if agent_cell.select_one("img") else "Unknown"
        # Stat columns
        for i, td in enumerate(tds[2:], start=2):
            header = headers[i] if i < len(headers) else f"stat_{i}"
            # Try to get the 'both' value if present
            both = td.select_one(".side.mod-both, .side.mod-side.mod-both")
            if both:
                value = both.get_text(strip=True)
            else:
                # Fallback: get the first text value
                value = td.get_text(strip=True)
            row[header] = value
        rows.append(row)
    return rows

def parse_vlr_minimal_all_maps(html: str) -> dict[str, Any]:
    """Parse all maps from minimal VLR HTML, including match header and map sections."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Parse match header for overall match info
    match_header_div = soup.select_one('.match-header')
    if not match_header_div:
        raise ValueError("No match header found")
        
    # Team names
    team1_name = team2_name = None
    team1_elem = match_header_div.select_one('.match-header-link.mod-1 .wf-title-med')
    if team1_elem:
        team1_name = team1_elem.get_text(strip=True).split('\n')[0]
    team2_elem = match_header_div.select_one('.match-header-link.mod-2 .wf-title-med')
    if team2_elem:
        team2_name = team2_elem.get_text(strip=True).split('\n')[0]
    
    # Scores
    score_loser = match_header_div.select_one('.match-header-vs-score-loser')
    score_winner = match_header_div.select_one('.match-header-vs-score-winner')
    
    # Determine which team is which (left is mod-1, right is mod-2)
    # VLR puts winner/loser classes, so we need to check which team won
    team1_score = team2_score = None
    if score_loser and score_winner:
        # The order in the HTML is: loser, colon, winner
        # Team1 is left, Team2 is right
        # If left team won, winner is first, else second
        # Let's check which team name matches the winner
        # But for now, just assign as left/right
        team1_score = int(score_loser.get_text(strip=True))
        team2_score = int(score_winner.get_text(strip=True))
    
    match_header_data = {
        'team1_name': team1_name or 'Unknown',
        'team2_name': team2_name or 'Unknown',
        'team1_score': team1_score,
        'team2_score': team2_score
    }
    
    # Get map selection links
    map_links = []
    map_selection = soup.find('div', class_='vm-stats-gamesnav')
    if map_selection:
        for link in map_selection.find_all('a'):
            map_index = int(link.get('href', '').split('=')[-1]) if link.get('href') and '=' in link.get('href') else 0
            map_links.append({
                'map_index': map_index,
                'map_link': link.get('href', ''),
                'text': link.get_text(strip=True)
            })
    
    # Parse all map sections
    maps = []
    
    # First get the "All Maps" section
    all_maps_section = soup.find('div', class_='vm-stats-game mod-active')
    if all_maps_section:
        all_maps_table = all_maps_section.find('table', class_='wf-table-inset')
        if all_maps_table:
            players = parse_scoreboard(all_maps_table)
            maps.append({
                'map_name': 'All Maps',
                'map_index': 0,
                'map_link': None,
                'team1_name': match_header_data['team1_name'],
                'team2_name': match_header_data['team2_name'],
                'team1_score': match_header_data['team1_score'],
                'team2_score': match_header_data['team2_score'],
                'players': players
            })
    
    # Then get individual map sections
    map_sections = soup.find_all('div', class_='vm-stats-game')
    map_idx = 1
    for section in map_sections:
        if 'mod-active' in section.get('class', []):
            continue  # Skip the active section as we already processed it
            
        # Map name
        map_name = None
        map_name_elem = section.select_one('.map > div > span')
        if map_name_elem:
            map_name = map_name_elem.get_text(strip=True)
            # Remove 'PICK' or similar annotation
            map_name = map_name.replace('PICK', '').strip()
        
        # Map index
        map_link = section.find('a', class_='map-link')
        map_index = map_idx
        map_idx += 1
        
        # Team names and scores for this map
        left_team = section.select_one('.team')
        right_team = section.select_one('.team.mod-right')
        left_team_name = left_team.select_one('.team-name').get_text(strip=True) if left_team and left_team.select_one('.team-name') else None
        right_team_name = right_team.select_one('.team-name').get_text(strip=True) if right_team and right_team.select_one('.team-name') else None
        left_team_score = left_team.select_one('.score').get_text(strip=True) if left_team and left_team.select_one('.score') else None
        right_team_score = right_team.select_one('.score').get_text(strip=True) if right_team and right_team.select_one('.score') else None
        
        # Score conversion
        try:
            left_team_score = int(left_team_score)
        except (TypeError, ValueError):
            left_team_score = None
        try:
            right_team_score = int(right_team_score)
        except (TypeError, ValueError):
            right_team_score = None
        
        # Scoreboard table
        map_table = section.find('table', class_='wf-table-inset')
        if map_table:
            players = parse_scoreboard(map_table)
            maps.append({
                'map_name': map_name or 'Unknown',
                'map_index': map_index,
                'map_link': map_link.get('href') if map_link else None,
                'team1_name': left_team_name or 'Unknown',
                'team2_name': right_team_name or 'Unknown',
                'team1_score': left_team_score,
                'team2_score': right_team_score,
                'players': players
            })
    
    # Extract event, phase, date, time, and patch from match header
    event = phase = date = time = patch = None
    match_header_div = soup.select_one('.match-header')
    if match_header_div:
        event_elem = match_header_div.select_one('.match-header-event > div > div')
        if event_elem:
            event = event_elem.get_text(strip=True)
        phase_elem = match_header_div.select_one('.match-header-event-series')
        if phase_elem:
            # Normalize whitespace for phase
            phase = ' '.join(phase_elem.get_text(separator=' ', strip=True).split())
        date_elem = match_header_div.select_one('.match-header-date .moment-tz-convert')
        if date_elem:
            date = date_elem.get_text(strip=True)
        time_elem = match_header_div.select_one('.match-header-date .moment-tz-convert + .moment-tz-convert')
        if time_elem:
            time = time_elem.get_text(strip=True)
        patch_elem = match_header_div.find(string=lambda t: t and 'Patch' in t)
        if patch_elem:
            patch = patch_elem.strip()
    
    return {
        'event': event,
        'phase': phase,
        'date': date,
        'time': time,
        'patch': patch,
        'match_header': match_header_data,
        'map_links': map_links,
        'maps': maps
    }
