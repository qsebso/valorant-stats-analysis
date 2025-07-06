"""
Clean Existing Events Script

This script cleans up the existing events.yaml file by removing corrupted text
and re-categorizing events properly.
"""

import yaml
import re
from typing import Dict, List, Any

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

def clean_existing_events(filename: str = "config/events.yaml"):
    """Clean up existing events in the events.yaml file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"File {filename} not found!")
        return
    
    events = data.get("events", [])
    cleaned_events = []
    
    print(f"Processing {len(events)} events...")
    
    for event in events:
        original_name = event.get("event_name", "")
        cleaned_name = clean_event_name(original_name)
        
        if cleaned_name != original_name:
            print(f"Cleaned: '{original_name}' -> '{cleaned_name}'")
        
        # Re-categorize the event
        categories = categorize_event(cleaned_name)
        
        # Update the event
        cleaned_event = {
            "event_id": event.get("event_id", ""),
            "event_name": cleaned_name,
            "match_urls": event.get("match_urls", []),
            "match_ids": event.get("match_ids", []),
            "tier": categories["tier"],
            "type": categories["type"]
        }
        
        cleaned_events.append(cleaned_event)
    
    # Save the cleaned events
    data["events"] = cleaned_events
    
    with open(filename, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"Cleaned and saved {len(cleaned_events)} events to {filename}")
    
    # Print summary
    tier_counts = {}
    type_counts = {}
    
    for event in cleaned_events:
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

def sample_events_by_tier(filename: str = "config/events.yaml", samples_per_tier: int = 10):
    """Sample events from each tier to verify classifications."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"File {filename} not found!")
        return
    
    events = data.get("events", [])
    
    # Group events by tier
    tier_groups = {}
    for event in events:
        tier = event.get("tier", "Unknown")
        if tier not in tier_groups:
            tier_groups[tier] = []
        tier_groups[tier].append(event)
    
    print("Sampling events from each tier:")
    print("=" * 50)
    
    import random
    for tier in sorted(tier_groups.keys()):
        events_in_tier = tier_groups[tier]
        print(f"\n{tier} ({len(events_in_tier)} events):")
        print("-" * 30)
        
        # Sample events
        if len(events_in_tier) <= samples_per_tier:
            samples = events_in_tier
        else:
            samples = random.sample(events_in_tier, samples_per_tier)
        
        for i, event in enumerate(samples, 1):
            event_name = event.get("event_name", "")
            event_type = event.get("type", "Unknown")
            print(f"  {i}. {event_name} (Type: {event_type})")

if __name__ == "__main__":
    # Clean existing events
    clean_existing_events()
    
    # Sample events to verify classifications
    print("\n" + "="*60)
    sample_events_by_tier() 