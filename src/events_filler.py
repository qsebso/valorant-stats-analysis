"""
Events Filler Script

This script scrapes completed events from VLR.gg and categorizes them by tier and type.
It helps populate the events.yaml file with all completed events for analysis.
"""

import requests
import yaml
import re
import time
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def rate_limit():
    """Simple rate limiting to avoid overwhelming VLR.gg"""
    time.sleep(1)

def clean_event_name(event_name: str) -> str:
    """
    Clean up event names by removing corrupted text and extra information.
    """
    if not event_name:
        return ""
    
    # Remove common corrupted suffixes
    patterns_to_remove = [
        r'ongoingStatus.*$',
        r'completedStatus.*$',
        r'upcomingStatus.*$',
        r'Prize Pool.*$',
        r'DatesRegion.*$',
        r'Status.*$',
        r'\$[\d,]+.*$',
        r'TBD.*$',
        r'[A-Za-z]{3}\s+\d{1,2}—[A-Za-z]{3}\s+\d{1,2}.*$',
        r'\d{4}—\d{4}.*$'
    ]
    
    cleaned_name = event_name
    for pattern in patterns_to_remove:
        cleaned_name = re.sub(pattern, '', cleaned_name, flags=re.IGNORECASE)
    
    # Clean up extra whitespace and punctuation
    cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()
    cleaned_name = re.sub(r'\s*[:\-]\s*$', '', cleaned_name)
    
    return cleaned_name

def categorize_event(event_name: str) -> Dict[str, str]:
    """
    Categorize an event based on its name.
    Returns a dict with 'tier' and 'type' classifications.
    """
    # Clean the event name first
    event_name = clean_event_name(event_name)
    event_lower = event_name.lower()
    
    # Initialize categories
    tier = "Unknown"
    event_type = "Unknown"
    
    # Tier 1 Events (Professional - Major international tournaments)
    tier1_keywords = [
        "masters", "champions", "world championship", "international", 
        "global", "world cup", "valorant champions", "esports world cup", 
        "first strike", "strike arabia championship", "kick off"
    ]
    
    # Tier 2 Events (Semi-pro - Regional major tournaments)
    tier2_keywords = [
        "challengers", "regional", "league", "pro league", "esports league",
        "national league", "saudi eleague", "strike arabia league", 
        "aorus league", "super league arena", "ae league", "a1 esports league", 
        "kombatklub league", "onfire league"
    ]
    
    # Tier 3 Events (Smaller tournaments)
    tier3_keywords = [
        "open", "qualifier", "qualification", "circuit", "series", "cup",
        "invitational", "showdown", "clash", "minor", "local", "academy",
        "grassroots", "community", "premier", "elite", "rising", "genesis",
        "challenge", "battle", "war", "fight", "trophy", "festival", "showdown",
        "arena", "gauntlet", "proving grounds", "scouting", "contenders"
    ]
    
    # Tier 4 Events (Community/Grassroots)
    tier4_keywords = [
        "nicecactus", "odyssey", "kingdom calling", "rush to glory",
        "valorant sunday showdown", "chroma cup", "beloud cup", "sakura cup",
        "fragleague", "epic", "nerd street gamers", "knights", "funhaver",
        "yfp", "raidiant", "glitched", "bleed", "lockdown", "underdogs",
        "versus legends", "valorant zone", "mandatory", "30bomb", "clutch battles"
    ]
    
    # Game Changers Events
    gc_keywords = [
        "game changers", "gc", "women", "female", "queens", "girls",
        "womens", "girlk1d", "equal esports queens", "project queens",
        "huntress trials", "women's community festival", "gaming culture girl power"
    ]
    
    # Collegiate Events
    collegiate_keywords = [
        "collegiate", "college", "university", "academic", "student",
        "campus", "school", "campus", "red bull campus clutch"
    ]
    
    # Determine tier
    # Check for Game Changers events first - they get their own tier
    if any(keyword in event_lower for keyword in gc_keywords):
        tier = "GC"
    # Check for Challengers events specifically (Tier 2)
    elif "challengers" in event_lower:
        tier = "Tier 2"
    # Check for Champions Tour events - need to distinguish between Tier 1 and Tier 2
    elif "champions tour" in event_lower:
        # If it contains "masters" or "champions", it's Tier 1
        if "masters" in event_lower or "champions" in event_lower:
            tier = "Tier 1"
        else:
            # Other Champions Tour events are Tier 2
            tier = "Tier 2"
    elif any(keyword in event_lower for keyword in tier1_keywords):
        tier = "Tier 1"
    elif any(keyword in event_lower for keyword in tier2_keywords):
        tier = "Tier 2"
    elif any(keyword in event_lower for keyword in tier3_keywords):
        tier = "Tier 3"
    elif any(keyword in event_lower for keyword in tier4_keywords):
        tier = "Tier 4"
    
    # Determine event type
    if any(keyword in event_lower for keyword in gc_keywords):
        event_type = "Game Changers"
    elif any(keyword in event_lower for keyword in collegiate_keywords):
        event_type = "Collegiate"
    elif "challengers" in event_lower:
        event_type = "Challengers"
    elif "masters" in event_lower:
        event_type = "Masters"
    elif "champions" in event_lower:
        event_type = "Champions"
    elif "playoff" in event_lower:
        event_type = "Playoffs"
    elif "qualifier" in event_lower or "qualification" in event_lower:
        event_type = "Qualifier"
    elif "open" in event_lower:
        event_type = "Open"
    elif "invitational" in event_lower:
        event_type = "Invitational"
    elif "cup" in event_lower:
        event_type = "Cup"
    elif "series" in event_lower:
        event_type = "Series"
    elif "league" in event_lower:
        event_type = "League"
    elif "tournament" in event_lower:
        event_type = "Tournament"
    elif "championship" in event_lower:
        event_type = "Championship"
    elif "battle" in event_lower or "war" in event_lower:
        event_type = "Battle"
    elif "showdown" in event_lower:
        event_type = "Showdown"
    elif "festival" in event_lower:
        event_type = "Festival"
    elif "gauntlet" in event_lower:
        event_type = "Gauntlet"
    elif "arena" in event_lower:
        event_type = "Arena"
    else:
        event_type = "Tournament"
    
    return {
        "tier": tier,
        "type": event_type
    }

def extract_event_id_from_url(url: str) -> Optional[str]:
    """Extract event ID from a VLR.gg event URL."""
    # Pattern: /event/123/event-name
    match = re.search(r'/event/(\d+)/', url)
    return match.group(1) if match else None

def is_truly_completed(event_name: str, parent_text: str) -> bool:
    """
    Check if an event is truly completed by looking for indicators.
    Returns True if the event appears to be actually completed.
    """
    parent_lower = parent_text.lower()
    # If 'ongoingStatus' or 'upcomingStatus' is present, skip
    if 'ongoingstatus' in parent_lower or 'upcomingstatus' in parent_lower:
        return False
    # If 'completedStatus' is present, accept
    if 'completedstatus' in parent_lower:
        return True
    # Default to True if we can't determine
    return True

def scrape_completed_events() -> List[Dict[str, Any]]:
    """
    Scrape all completed events from all VLR.gg events pages.
    Returns a list of event dictionaries.
    """
    base_url = "https://www.vlr.gg/events"
    all_events = []
    seen_event_ids = set()
    page = 1
    while True:
        url = f"{base_url}/?page={page}"
        print(f"Scraping completed events from {url}")
        rate_limit()
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # Save the first page HTML for debugging
        if page == 1:
            with open("debug_events_page.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("Saved HTML to debug_events_page.html for inspection")
        # Find all event links in the page
        event_links = soup.find_all('a', href=re.compile(r'/event/\d+/'))
        print(f"Found {len(event_links)} event links on page {page}")
        found_new = False
        for link in event_links:
            try:
                event_url = link.get('href')
                event_id = extract_event_id_from_url(event_url)
                if not event_id or event_id in seen_event_ids:
                    continue
                # Get event name from the link text or parent elements
                event_name = link.get_text(strip=True)
                if not event_name:
                    parent = link.parent
                    for _ in range(3):
                        if parent:
                            event_name = parent.get_text(strip=True)
                            if event_name and len(event_name) > 5:
                                break
                            parent = parent.parent
                if not event_name or len(event_name) < 5:
                    continue
                # Check if this event is completed by looking at surrounding context
                is_completed = False
                parent = link.parent
                parent_text = ""
                for _ in range(5):
                    if parent:
                        parent_text = parent.get_text().lower()
                        if 'completed' in parent_text:
                            is_completed = True
                            break
                        parent = parent.parent
                if not is_completed:
                    continue
                
                # Additional check to filter out ongoing events
                if not is_truly_completed(event_name, parent_text):
                    print(f"Skipping potentially ongoing event: {event_name}")
                    continue
                
                # Clean and categorize the event
                cleaned_name = clean_event_name(event_name)
                categories = categorize_event(cleaned_name)
                event_data = {
                    "event_id": event_id,
                    "event_name": cleaned_name,
                    "original_name": event_name,  # Keep original for debugging
                    "event_url": urljoin("https://www.vlr.gg", event_url),
                    "status": "completed",
                    "dates": "Unknown",
                    "prize_pool": "Unknown",
                    "tier": categories["tier"],
                    "type": categories["type"],
                    "match_urls": [],
                    "match_ids": []
                }
                all_events.append(event_data)
                seen_event_ids.add(event_id)
                found_new = True
                print(f"Found completed event: {cleaned_name} (ID: {event_id}, Tier: {categories['tier']}, Type: {categories['type']})")
            except Exception as e:
                print(f"Error processing event link: {e}")
                continue
        if not found_new:
            print(f"No new completed events found on page {page}. Stopping.")
            break
        page += 1
    return all_events

def save_events_to_yaml(events: List[Dict[str, Any]], filename: str = "config/events_completed.yaml"):
    """Save scraped events to a YAML file."""
    events_data = {"events": events}
    
    with open(filename, 'w', encoding='utf-8') as f:
        yaml.dump(events_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"Saved {len(events)} events to {filename}")

def update_main_events_yaml(events: List[Dict[str, Any]], filename: str = "config/events.yaml"):
    """Update the main events.yaml file with new events."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            existing_data = yaml.safe_load(f)
    except FileNotFoundError:
        existing_data = {"events": []}
    
    existing_event_ids = {event["event_id"] for event in existing_data.get("events", [])}
    
    new_events = []
    for event in events:
        if event["event_id"] not in existing_event_ids:
            # Only include essential fields for the main events.yaml
            new_event = {
                "event_id": event["event_id"],
                "event_name": event["event_name"],
                "match_urls": [],
                "match_ids": []
            }
            new_events.append(new_event)
            existing_event_ids.add(event["event_id"])
    
    if new_events:
        existing_data["events"].extend(new_events)
        
        with open(filename, 'w', encoding='utf-8') as f:
            yaml.dump(existing_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        print(f"Added {len(new_events)} new events to {filename}")
    else:
        print("No new events to add to main events.yaml")

def main():
    """Main function to scrape and save completed events."""
    print("Starting VLR.gg completed events scraper...")
    
    # Scrape completed events
    events = scrape_completed_events()
    
    if not events:
        print("No completed events found. The scraper might need adjustment.")
        print("Check debug_events_page.html to see the actual page structure.")
        return
    
    print(f"\nFound {len(events)} completed events")
    
    # Save to separate file with full details
    save_events_to_yaml(events, "config/events_completed_full.yaml")
    
    # Update main events.yaml with new events
    update_main_events_yaml(events)
    
    # Print summary by tier and type
    print("\nEvent Summary:")
    tier_counts = {}
    type_counts = {}
    
    for event in events:
        tier = event["tier"]
        event_type = event["type"]
        
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        type_counts[event_type] = type_counts.get(event_type, 0) + 1
    
    print("\nBy Tier:")
    for tier, count in sorted(tier_counts.items()):
        print(f"  {tier}: {count} events")
    
    print("\nBy Type:")
    for event_type, count in sorted(type_counts.items()):
        print(f"  {event_type}: {count} events")

if __name__ == "__main__":
    main() 