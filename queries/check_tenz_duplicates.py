"""
Check for data duplication in TenZ's match data.
This script investigates why TenZ shows 355 total games when VLR only shows 203.
"""

import pandas as pd
import sqlite3
import os
from typing import Dict, Any

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), os.pardir, "data", "valorant_stats_matchcentric_clean.db")

def get_tenz_data() -> pd.DataFrame:
    """Get all TenZ data from the database."""
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT * FROM map_stats 
    WHERE player_name LIKE '%TenZ%' OR player_name LIKE '%tenz%'
    ORDER BY match_datetime DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def analyze_tenz_duplicates():
    """Analyze potential duplication in TenZ's data."""
    print("=== TENZ DATA DUPLICATION ANALYSIS ===\n")
    
    # Get all TenZ data
    df = get_tenz_data()
    
    if df.empty:
        print("No TenZ data found in database!")
        return
    
    print(f"Total rows for TenZ: {len(df)}")
    print(f"Unique matches: {df['match_id'].nunique()}")
    print(f"Unique match-datetime combinations: {df[['match_id', 'match_datetime']].drop_duplicates().shape[0]}")
    print()
    
    # Check map_name distribution
    print("=== MAP NAME DISTRIBUTION ===")
    map_counts = df['map_name'].value_counts()
    print(map_counts)
    print()
    
    # Check for "All Maps" entries
    all_maps = df[df['map_name'] == 'All Maps']
    individual_maps = df[df['map_name'] != 'All Maps']
    
    print(f"All Maps entries: {len(all_maps)}")
    print(f"Individual map entries: {len(individual_maps)}")
    print()
    
    # Check if "All Maps" entries duplicate individual map data
    if len(all_maps) > 0:
        print("=== ALL MAPS ANALYSIS ===")
        all_maps_matches = set(all_maps['match_id'].unique())
        individual_maps_matches = set(individual_maps['match_id'].unique())
        
        print(f"Matches with 'All Maps' entries: {len(all_maps_matches)}")
        print(f"Matches with individual map entries: {len(individual_maps_matches)}")
        print(f"Matches with BOTH 'All Maps' AND individual maps: {len(all_maps_matches & individual_maps_matches)}")
        print()
        
        # Show some examples of matches with both
        both_matches = all_maps_matches & individual_maps_matches
        if both_matches:
            print("Examples of matches with both 'All Maps' and individual maps:")
            for match_id in list(both_matches)[:5]:  # Show first 5
                match_data = df[df['match_id'] == match_id]
                print(f"\nMatch ID: {match_id}")
                print(f"Event: {match_data['event_name'].iloc[0]}")
                print(f"Teams: {match_data['team1_name'].iloc[0]} vs {match_data['team2_name'].iloc[0]}")
                print(f"Maps: {match_data['map_name'].tolist()}")
    
    # Check for exact duplicates (same match_id, map_name, player_name)
    print("\n=== EXACT DUPLICATE CHECK ===")
    duplicates = df.duplicated(subset=['match_id', 'map_name', 'player_name'], keep=False)
    if duplicates.any():
        print(f"Found {duplicates.sum()} exact duplicate rows!")
        duplicate_data = df[duplicates]
        print("\nDuplicate examples:")
        print(duplicate_data[['match_id', 'map_name', 'player_name', 'match_datetime']].head(10))
    else:
        print("No exact duplicates found.")
    
    # Check for matches with unusually high map counts
    print("\n=== MATCHES WITH HIGH MAP COUNTS ===")
    match_map_counts = df.groupby('match_id')['map_name'].nunique().sort_values(ascending=False)
    print("Top 10 matches by number of different map entries:")
    print(match_map_counts.head(10))
    
    # Show some recent matches to verify against VLR
    print("\n=== RECENT MATCHES (last 10) ===")
    recent_matches = df.groupby(['match_id', 'match_datetime', 'event_name', 'team1_name', 'team2_name']).size().reset_index(name='map_count')
    recent_matches = recent_matches.sort_values('match_datetime', ascending=False).head(10)
    print(recent_matches[['match_datetime', 'event_name', 'team1_name', 'team2_name', 'map_count']])

def check_classification_distribution():
    """Check how the playoff/regular season classification looks."""
    print("\n=== CLASSIFICATION DISTRIBUTION ===")
    
    from queries.classification import classify_tournament_stage
    
    df = get_tenz_data()
    
    # Apply classification
    df['game_type'] = df.apply(
        lambda row: classify_tournament_stage(row['bracket_stage'], row['event_name']), 
        axis=1
    )
    
    # Count by game type
    game_type_counts = df['game_type'].value_counts()
    print("Games by type:")
    print(game_type_counts)
    
    # Count unique matches by game type
    unique_matches_by_type = df.groupby('game_type')['match_id'].nunique()
    print("\nUnique matches by type:")
    print(unique_matches_by_type)
    
    # Check if "All Maps" entries are affecting the classification
    all_maps_classified = df[df['map_name'] == 'All Maps']['game_type'].value_counts()
    print("\n'All Maps' entries by classification:")
    print(all_maps_classified)

if __name__ == "__main__":
    analyze_tenz_duplicates()
    check_classification_distribution() 