import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
from src.parser import parse_vlr_minimal_all_maps

# Set your test VLR.gg match URL here
MATCH_URL = "https://www.vlr.gg/490306/gen-g-vs-mibr-champions-tour-2025-masters-toronto-r1"  # <-- Replace with a real match link

def test_patch_extraction(url):
    resp = requests.get(url)
    resp.raise_for_status()
    html = resp.text
    result = parse_vlr_minimal_all_maps(html)
    print(f"=== {url} ===")
    print(f"  patch: {result['patch']}")
    print("-" * 40)

if __name__ == "__main__":
    test_patch_extraction(MATCH_URL) 