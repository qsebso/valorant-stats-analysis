import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging
import requests
from src.parser import parse_vlr_match
from src.utils import rate_limit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rounds_and_duration_from_live_url():
    # TODO: Fill in a real VLR.gg match URL below
    url = "https://www.vlr.gg/490309/team-heretics-vs-paper-rex-champions-tour-2025-masters-toronto-r1"
    assert url, "Please provide a VLR.gg match URL."
    logger.info(f"Fetching match from {url}")
    rate_limit()
    response = requests.get(url)
    response.raise_for_status()
    html = response.text
    result = parse_vlr_match(html)
    assert 'maps' in result and result['maps'], "No maps found in parsed result."
    for i, m in enumerate(result['maps']):
        print(f"\n=== Map {i+1}: {m.get('map_name', 'Unknown')} (Index: {m.get('map_index')}) ===")
        print(f"  Team 1: {m.get('team1_name')} | Attacker Rounds: {m.get('team1_attacker_rounds')} | Defender Rounds: {m.get('team1_defender_rounds')}")
        print(f"  Team 2: {m.get('team2_name')} | Attacker Rounds: {m.get('team2_attacker_rounds')} | Defender Rounds: {m.get('team2_defender_rounds')}")
        print(f"  Map Duration: {m.get('map_duration')}")
        # Only check for these fields on individual maps, not 'All Maps'
        if m.get('map_name', '').lower() != 'all maps':
            assert 'team1_attacker_rounds' in m
            assert 'team1_defender_rounds' in m
            assert 'team2_attacker_rounds' in m
            assert 'team2_defender_rounds' in m
            assert 'map_duration' in m

if __name__ == "__main__":
    test_rounds_and_duration_from_live_url() 