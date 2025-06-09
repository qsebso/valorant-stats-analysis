"""
This module simply copies `bracket_stage` into the `phase` field for each row.

Scheduling module for automated data collection.
Manages periodic scraping tasks and event phase tracking.
"""

def assign_phase(row):
    """
    Assigns the phase field based on bracket_stage.
    
    Args:
        row (dict): A row of match data containing bracket_stage
        
    Returns:
        dict: The same row with phase = bracket_stage
    """
    row['phase'] = row['bracket_stage']
    return row 