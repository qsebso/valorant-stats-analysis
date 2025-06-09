"""
Test script for the VALORANT match parser.

This script fetches a live match from VLR.gg and tests our parse_scoreboard()
implementation by printing the first few rows of parsed data.
"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, List
from src.parser import parse_scoreboard, parse_vlr_scoreboard_table, parse_vlr_minimal_all_maps
from src.utils import rate_limit

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_match(url: str) -> BeautifulSoup:
    """Fetch and parse a match page from VLR.gg.
    
    Args:
        url: Full URL of the match page to fetch
        
    Returns:
        BeautifulSoup object of the parsed HTML
        
    Raises:
        requests.RequestException: If the request fails
    """
    logger.info(f"Fetching match from {url}")
    rate_limit()  # Be nice to the server
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def print_row(row: Dict, indent: int = 2) -> None:
    """Pretty print a single row of match data.
    
    Args:
        row: Dictionary containing match/player data
        indent: Number of spaces to indent each line
    """
    indent_str = " " * indent
    print(f"\n{indent_str}Map: {row['map_name']} (index {row['map_index']})")
    print(f"{indent_str}Player: {row['player_name']} ({row['player_team']})")
    print(f"{indent_str}Agent: {row['agent_played']}")
    print(f"{indent_str}Stats:")
    print(f"{indent_str}  K/D/A: {row['total_kills']}/{row['total_deaths']}/{row['total_assists']}")
    print(f"{indent_str}  Rating: {row['rating_2_0']:.2f}")
    print(f"{indent_str}  ACS: {row['ACS']:.0f}")
    print(f"{indent_str}  ADR: {row['ADR']:.0f}")
    print(f"{indent_str}  KAST: {row['KAST_pct']:.1f}%")

def main() -> None:
    """Main test function."""
    # Use the Bilibili Gaming vs Sentinels match from VCT 2025 Masters Toronto
    test_url = "https://www.vlr.gg/490311/bilibili-gaming-vs-sentinels-champions-tour-2025-masters-toronto-r2-1-0"
    
    try:
        # Fetch and parse the match
        soup = fetch_match(test_url)
        
        # Parse the scoreboard
        rows = parse_scoreboard(soup)
        
        # Print match header info from first row
        if rows:
            first = rows[0]
            print("\nMatch Info (parsed fields):")
            for key, value in first.items():
                print(f"  {key}: {value}")
            
            # Print first 3 rows of player data
            print("\nPlayer Data (first 3 rows):")
            for row in rows[:3]:
                print_row(row)
            
            # Print summary
            print(f"\nTotal rows parsed: {len(rows)}")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

def test_minimal_html():
    with open('vlr_test_page.html', encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    rows = parse_scoreboard(soup)
    print(f"Parsed {len(rows)} player rows from minimal HTML.\n")
    for i, row in enumerate(rows):
        print(f"Player {i+1}:")
        for k, v in row.items():
            print(f"  {k}: {v}")
        print()

def test_minimal_all_maps():
    with open('vlr_test_page.html', encoding='utf-8') as f:
        html = f.read()
    result = parse_vlr_minimal_all_maps(html)
    
    # Print overall scoreboard info
    print("=== Overall Info ===")
    print(f"Event: {result['event']}")
    print(f"Phase: {result['phase']}")
    print(f"Date: {result['date']}")
    print(f"Time: {result['time']}")
    print(f"Patch: {result['patch']}")
    print()
    
    # Print match header
    print("=== Match Header ===")
    print(f"Teams: {result['match_header']['team1_name']} {result['match_header']['team1_score']} - {result['match_header']['team2_score']} {result['match_header']['team2_name']}")
    print()
    
    # Print each map section
    for m in result['maps']:
        print(f"=== {m['map_name']} (Index: {m['map_index']}) ===")
        if m['map_link']:
            print(f"Map link: {m['map_link']}")
        print(f"Scoreboard:")
        print(f"  {m['team1_name']} {m['team1_score']} - {m['team2_score']} {m['team2_name']}")
        print(f"Players ({len(m['players'])}):")
        for j, player in enumerate(m['players']):
            print(f"  Player {j+1}:")
            for k, v in player.items():
                print(f"    {k}: {v}")
            print()
        print()

def test_vlr_live_url():
    # Replace this with your actual VLR.gg match URL
    url = "https://www.vlr.gg/490311/bilibili-gaming-vs-sentinels-champions-tour-2025-masters-toronto-r2-1-0"
    print(f"Fetching: {url}")
    response = requests.get(url)
    response.raise_for_status()
    html = response.text
    result = parse_vlr_minimal_all_maps(html)
    
    # Print overall scoreboard info
    print("=== Overall Info ===")
    print(f"Event: {result['event']}")
    print(f"Phase: {result['phase']}")
    print(f"Date: {result['date']}")
    print(f"Time: {result['time']}")
    print(f"Patch: {result['patch']}")
    print()
    
    # Print match header
    print("=== Match Header ===")
    print(f"Teams: {result['match_header']['team1_name']} {result['match_header']['team1_score']} - {result['match_header']['team2_score']} {result['match_header']['team2_name']}")
    print()
    
    # Print each map section
    for m in result['maps']:
        print(f"=== {m['map_name']} (Index: {m['map_index']}) ===")
        if m['map_link']:
            print(f"Map link: {m['map_link']}")
        print(f"Scoreboard:")
        print(f"  {m['team1_name']} {m['team1_score']} - {m['team2_score']} {m['team2_name']}")
        print(f"Players ({len(m['players'])}):")
        for j, player in enumerate(m['players']):
            print(f"  Player {j+1}:")
            for k, v in player.items():
                print(f"    {k}: {v}")
            print()
        print()

if __name__ == "__main__":
    test_vlr_live_url() 