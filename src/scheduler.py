"""
This module simply copies `bracket_stage` into the `phase` field for each row.

Scheduling module for automated data collection.
Manages periodic scraping tasks and event phase tracking.

Phase assignment: uses scraped bracket_stage as the map_stats phase field.
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)

def assign_phase(stats: Dict) -> str:
    """
    Return the bracket_stage as phase, or 'Unknown' if missing.

    Args:
        stats: A dict containing at least 'bracket_stage' and 'match_id'.

    Returns:
        A string phase value.
    """
    stage = stats.get("bracket_stage")
    if isinstance(stage, str) and stage.strip():
        return stage
    logger.warning(f"Missing bracket_stage for match {stats.get('match_id')}")
    return "Unknown" 