"""
Loads event configurations from YAML.

This module handles reading and parsing the events.yaml configuration file,
which contains the list of VALORANT events to scrape.
"""

import yaml
import logging
from typing import List, Dict

# Set up module-level logger
logger = logging.getLogger(__name__)

def load_events() -> List[Dict]:
    """
    Read config/events.yaml and return its 'events' list.

    The YAML file should have this structure:
    ```yaml
    events:
      - event_id: "12345"
        event_name: "VCT 2024: Masters Tokyo"
      - event_id: "67890"
        event_name: "VCT 2024: Champions"
    ```

    Returns:
        List of event dictionaries, or empty list on failure.
        Each dict contains at least 'event_id' and 'event_name'.
    """
    try:
        # Open and parse the YAML file
        # Using safe_load to prevent code execution from YAML
        with open("config/events.yaml") as f:
            data = yaml.safe_load(f)
            
        # Extract the events list, defaulting to empty list if missing
        events = data.get("events", [])
        logger.info(f"Loaded {len(events)} events")
        return events
        
    except Exception as e:
        # Log any errors (file not found, invalid YAML, etc.)
        # but return empty list to allow graceful degradation
        logger.error(f"Failed to load events: {e}")
        return [] 