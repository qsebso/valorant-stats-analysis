"""
Event Categorizer

This module provides functions to categorize events and matches by tier and type.
It helps distinguish between different levels of competition and tournament types.
"""

import re
from typing import Dict, List, Any, Optional

def categorize_event(event_name: str) -> Dict[str, str]:
    """
    Categorize an event based on its name.
    Returns a dict with 'tier' and 'type' classifications.
    """
    event_lower = event_name.lower()
    
    # Initialize categories
    tier = "Unknown"
    event_type = "Unknown"
    
    # Tier 1 Events (Major international tournaments)
    tier1_keywords = [
        "champions tour", "masters", "champions", "world championship",
        "international", "global", "world cup", "valorant champions"
    ]
    
    # Tier 2 Events (Regional major tournaments)
    tier2_keywords = [
        "challengers", "regional", "league", "pro league", "esports league",
        "vct", "valorant champions tour"
    ]
    
    # Tier 3 Events (Smaller tournaments)
    tier3_keywords = [
        "open", "qualifier", "qualification", "circuit", "series", "cup",
        "invitational", "showdown", "clash", "minor", "local"
    ]
    
    # Game Changers Events
    gc_keywords = [
        "game changers", "gc", "women", "female", "queens", "girls"
    ]
    
    # Collegiate Events
    collegiate_keywords = [
        "collegiate", "college", "university", "academic", "student",
        "campus", "school"
    ]
    
    # Determine tier
    if any(keyword in event_lower for keyword in tier1_keywords):
        tier = "Tier 1"
    elif any(keyword in event_lower for keyword in tier2_keywords):
        tier = "Tier 2"
    elif any(keyword in event_lower for keyword in tier3_keywords):
        tier = "Tier 3"
    
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
    else:
        event_type = "Tournament"
    
    return {
        "tier": tier,
        "type": event_type
    }

def categorize_match_stage(bracket_stage: str) -> Dict[str, str]:
    """
    Categorize a match based on its bracket stage.
    Returns a dict with 'phase' and 'importance' classifications.
    """
    if not bracket_stage:
        return {"phase": "Unknown", "importance": "Unknown"}
    
    stage_lower = bracket_stage.lower()
    
    # Phase categorization
    phase = "Unknown"
    if "group" in stage_lower or "swiss" in stage_lower:
        phase = "Group Stage"
    elif "playoff" in stage_lower or "bracket" in stage_lower:
        phase = "Playoffs"
    elif "final" in stage_lower:
        phase = "Finals"
    elif "semi" in stage_lower:
        phase = "Semifinals"
    elif "quarter" in stage_lower:
        phase = "Quarterfinals"
    elif "round" in stage_lower:
        phase = "Round Robin"
    elif "qualifier" in stage_lower:
        phase = "Qualifier"
    elif "upper" in stage_lower:
        phase = "Upper Bracket"
    elif "lower" in stage_lower:
        phase = "Lower Bracket"
    
    # Importance categorization
    importance = "Regular"
    if any(keyword in stage_lower for keyword in ["final", "championship", "grand final"]):
        importance = "Championship"
    elif any(keyword in stage_lower for keyword in ["semi", "quarter"]):
        importance = "Elimination"
    elif any(keyword in stage_lower for keyword in ["playoff", "bracket"]):
        importance = "Playoff"
    elif any(keyword in stage_lower for keyword in ["group", "swiss", "round"]):
        importance = "Group"
    elif any(keyword in stage_lower for keyword in ["qualifier"]):
        importance = "Qualifier"
    
    return {
        "phase": phase,
        "importance": importance
    }

def is_playoff_match(bracket_stage: str) -> bool:
    """Check if a match is a playoff match based on bracket stage."""
    if not bracket_stage:
        return False
    
    playoff_keywords = [
        "playoff", "bracket", "final", "semi", "quarter", "elimination",
        "upper", "lower", "championship"
    ]
    
    stage_lower = bracket_stage.lower()
    return any(keyword in stage_lower for keyword in playoff_keywords)

def is_high_stakes_match(bracket_stage: str, event_name: str) -> bool:
    """Check if a match is high stakes (finals, championships, etc.)."""
    if not bracket_stage:
        return False
    
    high_stakes_keywords = [
        "final", "championship", "grand final", "title", "trophy"
    ]
    
    stage_lower = bracket_stage.lower()
    event_lower = event_name.lower() if event_name else ""
    
    return any(keyword in stage_lower for keyword in high_stakes_keywords)

def get_event_priority(event_name: str) -> int:
    """
    Get a numeric priority for an event (higher = more important).
    Used for sorting and filtering.
    """
    categories = categorize_event(event_name)
    
    # Priority based on tier
    tier_priority = {
        "Tier 1": 100,
        "Tier 2": 50,
        "Tier 3": 10,
        "Unknown": 0
    }
    
    # Priority based on type
    type_priority = {
        "Champions": 50,
        "Masters": 40,
        "Challengers": 30,
        "Game Changers": 25,
        "Playoffs": 20,
        "Qualifier": 15,
        "Open": 10,
        "Tournament": 5,
        "Unknown": 0
    }
    
    base_priority = tier_priority.get(categories["tier"], 0)
    type_bonus = type_priority.get(categories["type"], 0)
    
    return base_priority + type_bonus

def filter_events_by_tier(events: List[Dict[str, Any]], tier: str) -> List[Dict[str, Any]]:
    """Filter events by tier."""
    return [event for event in events if event.get("tier") == tier]

def filter_events_by_type(events: List[Dict[str, Any]], event_type: str) -> List[Dict[str, Any]]:
    """Filter events by type."""
    return [event for event in events if event.get("type") == event_type]

def get_event_summary(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get a summary of events by tier and type."""
    summary = {
        "total_events": len(events),
        "by_tier": {},
        "by_type": {},
        "by_region": {}
    }
    
    for event in events:
        # Count by tier
        tier = event.get("tier", "Unknown")
        summary["by_tier"][tier] = summary["by_tier"].get(tier, 0) + 1
        
        # Count by type
        event_type = event.get("type", "Unknown")
        summary["by_type"][event_type] = summary["by_type"].get(event_type, 0) + 1
        
        # Count by region (if available)
        region = event.get("region", "Unknown")
        summary["by_region"][region] = summary["by_region"].get(region, 0) + 1
    
    return summary

# Example usage and testing
if __name__ == "__main__":
    # Test event categorization
    test_events = [
        "Valorant Champions Tour 2025: Masters Toronto",
        "VCT 2025: Americas Challengers Stage 2",
        "Game Changers 2025: North America Stage 2",
        "College VALORANT 2024-2025: East",
        "FunhaverGG: ZERO//IN - Qualifier 7",
        "Valorant Champions 2025"
    ]
    
    print("Event Categorization Test:")
    for event in test_events:
        categories = categorize_event(event)
        priority = get_event_priority(event)
        print(f"{event}: {categories} (Priority: {priority})")
    
    # Test match stage categorization
    test_stages = [
        "Swiss Stage: Round 2 (1-0)",
        "Playoffs: Upper Bracket Semifinals",
        "Group Stage: Day 3",
        "Finals: Grand Championship",
        "Qualifier: Round 1"
    ]
    
    print("\nMatch Stage Categorization Test:")
    for stage in test_stages:
        categories = categorize_match_stage(stage)
        is_playoff = is_playoff_match(stage)
        is_high_stakes = is_high_stakes_match(stage, "Test Event")
        print(f"{stage}: {categories} (Playoff: {is_playoff}, High Stakes: {is_high_stakes})") 