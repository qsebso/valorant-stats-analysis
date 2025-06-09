"""
Quick script to list all match URLs for each event,
using our parser.get_match_paths logic.
"""

from urllib.parse import urljoin
from src.loader import load_events
from src.parser import get_match_paths

def main():
    events = load_events()
    for event in events:
        print(f"\nEvent: {event['event_name']} ({event['event_id']})")
        paths = get_match_paths(event)
        for path in paths:
            print("https://www.vlr.gg" + path)

if __name__ == "__main__":
    main()
