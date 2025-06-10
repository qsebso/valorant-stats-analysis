import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
from src.parser import parse_vlr_minimal_all_maps

# Set your test VLR.gg match URL here
MATCH_URL = "https://www.vlr.gg/19071/fnatic-vs-kr-esports-valorant-champions-tour-stage-2-masters-reykjavik-main-event-ur1"  # <-- Replace with a real match link

def test_winner_extraction(url):
    resp = requests.get(url)
    resp.raise_for_status()
    html = resp.text
    result = parse_vlr_minimal_all_maps(html)
    print(f"=== {url} ===")
    for m in result['maps']:
        if m['map_index'] == 0:
            print(f"  team1_name: {m['team1_name']}")
            print(f"  team1_score: {m['team1_score']}")
            print(f"  team2_name: {m['team2_name']}")
            print(f"  team2_score: {m['team2_score']}")
            print(f"  winner: {m['winner']}")
    print(f"  patch: {result['patch']}")
    print("-" * 40)

if __name__ == "__main__":
    test_winner_extraction(MATCH_URL) 