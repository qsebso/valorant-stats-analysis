"""
Sample Events Script

This script randomly samples events from each tier to verify the classifications.
"""

import yaml
import random
from typing import Dict, List

def sample_events_by_tier(filename: str = "config/events_completed_full.yaml", samples_per_tier: int = 10):
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
    print("=" * 60)
    
    for tier in sorted(tier_groups.keys()):
        events_in_tier = tier_groups[tier]
        print(f"\n{tier} ({len(events_in_tier)} events):")
        print("-" * 40)
        
        # Sample events
        if len(events_in_tier) <= samples_per_tier:
            samples = events_in_tier
        else:
            samples = random.sample(events_in_tier, samples_per_tier)
        
        for i, event in enumerate(samples, 1):
            event_name = event.get("event_name", "")
            event_type = event.get("type", "Unknown")
            event_id = event.get("event_id", "")
            print(f"  {i:2d}. {event_name} (Type: {event_type}, ID: {event_id})")

def analyze_unknown_events(filename: str = "config/events_completed_full.yaml", max_samples: int = 20):
    """Analyze unknown tier events to understand why they weren't classified."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"File {filename} not found!")
        return
    
    events = data.get("events", [])
    
    # Find unknown tier events
    unknown_events = [event for event in events if event.get("tier") == "Unknown"]
    
    print(f"\nAnalyzing {len(unknown_events)} Unknown tier events:")
    print("=" * 60)
    
    # Sample some unknown events
    if len(unknown_events) <= max_samples:
        samples = unknown_events
    else:
        samples = random.sample(unknown_events, max_samples)
    
    for i, event in enumerate(samples, 1):
        event_name = event.get("event_name", "")
        event_type = event.get("type", "Unknown")
        event_id = event.get("event_id", "")
        print(f"  {i:2d}. {event_name} (Type: {event_type}, ID: {event_id})")

def print_tier_summary(filename: str = "config/events_completed_full.yaml"):
    """Print a summary of events by tier and type."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"File {filename} not found!")
        return
    
    events = data.get("events", [])
    
    # Count by tier and type
    tier_counts = {}
    type_counts = {}
    
    for event in events:
        tier = event.get("tier", "Unknown")
        event_type = event.get("type", "Unknown")
        
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        type_counts[event_type] = type_counts.get(event_type, 0) + 1
    
    print("Event Summary:")
    print("=" * 40)
    
    print("\nBy Tier:")
    for tier, count in sorted(tier_counts.items()):
        print(f"  {tier}: {count} events")
    
    print("\nBy Type:")
    for event_type, count in sorted(type_counts.items()):
        print(f"  {event_type}: {count} events")

if __name__ == "__main__":
    # Print summary
    print_tier_summary()
    
    # Sample events from each tier
    print("\n" + "="*60)
    sample_events_by_tier()
    
    # Analyze unknown events
    print("\n" + "="*60)
    analyze_unknown_events() 