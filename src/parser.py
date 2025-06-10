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
    # Collect all player rows from all <tbody> elements (both teams)
    player_rows = []
    for tbody in scoreboard.find_all('tbody'):
        player_rows.extend(tbody.find_all('tr'))
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
        else:
            player['Player'] = 'Unknown'
            print('[DEBUG] Missing player name in row:', row)
        team_div = player_cell.find('div', class_='ge-text-light')
        if team_div:
            player['Team'] = team_div.get_text(strip=True)
        else:
            player['Team'] = 'Unknown'
            print('[DEBUG] Missing team in row:', row)
        # Extract country from the flag icon's title attribute
        country_icon = player_cell.find('i', attrs={'title': True})
        if country_icon:
            player['Country'] = country_icon['title']
        else:
            player['Country'] = 'Unknown'
            print('[DEBUG] Missing country in row:', row)
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

def parse_vlr_match(html: str) -> dict[str, Any]:
    """Parse a full VLR match (header and all map sections) from minimal HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Parse match header for overall match info
    match_header_div = soup.select_one('.match-header')
    if not match_header_div:
        raise ValueError("No match header found")
        
    # Team names
    team1_elem = match_header_div.select_one('.match-header-link.mod-1 .wf-title-med')
    team2_elem = match_header_div.select_one('.match-header-link.mod-2 .wf-title-med')
    team1_name = team1_elem.get_text(strip=True).split('\n')[0] if team1_elem else None
    team2_name = team2_elem.get_text(strip=True).split('\n')[0] if team2_elem else None

    # Scores: robustly extract left/right from spans inside .match-header-vs
    vs_div = match_header_div.select_one('.match-header-vs')
    score_spans = vs_div.select('span.match-header-vs-score-winner, span.match-header-vs-score-loser') if vs_div else []
    if len(score_spans) == 2:
        try:
            team1_score = int(score_spans[0].get_text(strip=True))
        except Exception:
            team1_score = None
        try:
            team2_score = int(score_spans[1].get_text(strip=True))
        except Exception:
            team2_score = None
    else:
        team1_score = team2_score = None

    # Determine winner for All Maps
    winner = None
    if team1_score is not None and team2_score is not None:
        if team1_score > team2_score:
            winner = team1_name
        elif team2_score > team1_score:
            winner = team2_name
        else:
            winner = None

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
        all_tables = all_maps_section.find_all('table', class_='wf-table-inset')
        all_players = []
        for table in all_tables:
            all_players.extend(parse_scoreboard(table))
        maps.append({
            'map_name': 'All Maps',
            'map_index': 0,
            'map_link': None,
            'team1_name': match_header_data['team1_name'],
            'team2_name': match_header_data['team2_name'],
            'team1_score': match_header_data['team1_score'],
            'team2_score': match_header_data['team2_score'],
            'winner': winner,
            'players': all_players
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
        
        # Determine winner for this map
        map_winner = None
        if left_team_score is not None and right_team_score is not None:
            if left_team_score > right_team_score:
                map_winner = left_team_name
            elif right_team_score > left_team_score:
                map_winner = right_team_name
            else:
                map_winner = None
        
        # Find all tables for both teams in this map section
        all_tables = section.find_all('table', class_='wf-table-inset')
        all_players = []
        for table in all_tables:
            all_players.extend(parse_scoreboard(table))
        maps.append({
            'map_name': map_name or 'Unknown',
            'map_index': map_index,
            'map_link': map_link.get('href') if map_link else None,
            'team1_name': left_team_name or 'Unknown',
            'team2_name': right_team_name or 'Unknown',
            'team1_score': left_team_score,
            'team2_score': right_team_score,
            'winner': map_winner,
            'players': all_players
        })
    
    # Extract event, phase, date, time, and patch from match header
    event = phase = date = time = patch = None
    match_header_div = soup.select_one('.match-header')
    if match_header_div:
        event_elem = match_header_div.select_one('.match-header-event a')
        if event_elem:
            event = event_elem.get_text(strip=True)
        phase_elem = match_header_div.select_one('.match-header-event .mod-live, .match-header-event .mod-completed')
        if phase_elem:
            phase = phase_elem.get_text(strip=True)
        date_elem = match_header_div.select_one('.match-header-date')
        if date_elem:
            date = date_elem.get_text(strip=True)
        time_elem = match_header_div.select_one('.match-header-time')
        if time_elem:
            time = time_elem.get_text(strip=True)
        patch_elem = match_header_div.select_one('.match-header-patch')
        if patch_elem:
            patch = patch_elem.get_text(strip=True)
    
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
