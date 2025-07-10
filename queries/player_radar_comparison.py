import sqlite3
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple, Optional
import seaborn as sns

# Add the queries directory to Python path for imports
sys.path.append(os.path.dirname(__file__))

# Import the centralized classification system
from classification import (
    classify_tournament_stage, 
    get_database_exclusion_filters
)

# Database paths
ORIGINAL_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "map_stats.db")
CLEAN_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "valorant_stats_clean.db")

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "query_results")

# Define the stats we want to compare
STATS_COLUMNS = [
    'rating_2_0',
    'ACS', 
    'KDRatio',
    'KAST_pct',
    'ADR',
    'total_kills',
    'total_deaths',
    'total_assists',
    'total_first_kills',
    'total_first_deaths'
]

# Stats labels for the radar chart
STATS_LABELS = [
    'Rating 2.0',
    'ACS',
    'K/D Ratio', 
    'KAST%',
    'ADR',
    'Total Kills',
    'Total Deaths',
    'Total Assists',
    'First Kills',
    'First Deaths'
]

def get_player_games(player_names: List[str], event_names: Optional[List[str]] = None, db_path: str = ORIGINAL_DB_PATH) -> pd.DataFrame:
    """
    Get games for the specified players from the database.
    
    Args:
        player_names: List of player names to search for
        event_names: Optional list of specific event names to filter by. 
                    If None, includes all events.
        db_path: Path to the database to query
        
    Returns:
        DataFrame with player game data
    """
    conn = sqlite3.connect(db_path)
    
    # For clean database, we don't need exclusion filters since data is already cleaned
    if db_path == CLEAN_DB_PATH:
        exclusion_filters = ""
    else:
        # Use the centralized exclusion filters for original database
        exclusion_filters = get_database_exclusion_filters()
    
    # Create the WHERE clause for multiple players
    player_conditions = " OR ".join([f"player_name LIKE '%{name}%'" for name in player_names])
    
    # Add event filtering if specified
    event_filter = ""
    if event_names:
        event_conditions = " OR ".join([f"event_name LIKE '%{event}%'" for event in event_names])
        event_filter = f"AND ({event_conditions})"
    
    # Exclude 'All Maps' entries
    all_maps_filter = "AND map_name != 'All Maps'"
    
    query = f"""
    SELECT 
        event_name,
        bracket_stage,
        match_id,
        match_datetime,
        map_name,
        team1_name,
        team1_score,
        team2_name,
        team2_score,
        player_name,
        player_team,
        agent_played,
        rating_2_0,
        ACS,
        KDRatio,
        KAST_pct,
        ADR,
        total_kills,
        total_deaths,
        total_assists,
        total_first_kills,
        total_first_deaths
    FROM map_stats 
    WHERE ({player_conditions})
    {exclusion_filters}
    {event_filter}
    {all_maps_filter}
    ORDER BY match_datetime DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Convert numeric columns to proper data types
    numeric_columns = ['rating_2_0', 'ACS', 'KDRatio', 'KAST_pct', 'ADR', 
                      'total_kills', 'total_deaths', 'total_assists',
                      'total_first_kills', 'total_first_deaths',
                      'team1_score', 'team2_score']
    
    # Fix KAST_pct: strip % and convert to float if present
    if 'KAST_pct' in df.columns:
        df['KAST_pct'] = df['KAST_pct'].astype(str).str.strip()
        df['KAST_pct'] = df['KAST_pct'].str.replace('%', '', regex=False)
        df['KAST_pct'] = pd.to_numeric(df['KAST_pct'], errors='coerce')
        # If all values are <= 1, treat as fraction and convert to percent
        if (df['KAST_pct'].dropna() <= 1).all():
            df['KAST_pct'] = df['KAST_pct'] * 100
    
    for col in numeric_columns:
        if col in df.columns and col != 'KAST_pct':
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def classify_playoff_games(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify games as playoffs or regular season using the enhanced classification system.
    """
    df['game_type'] = df.apply(
        lambda row: classify_tournament_stage(row['bracket_stage'], row['event_name']), 
        axis=1
    )
    return df

def calculate_player_stats(df: pd.DataFrame, player_name: str) -> Dict:
    """
    Calculate average stats for a player in both regular season and playoffs.
    
    Args:
        df: DataFrame with all player games
        player_name: Name of the player to analyze
        
    Returns:
        Dictionary with regular season and playoff stats
    """
    # Filter for the specific player
    player_df = df[df['player_name'].str.contains(player_name, case=False, na=False)]
    
    if player_df.empty:
        return None
    
    stats = {
        'player_name': player_name,
        'total_games': len(player_df),
        'regular_season': {},
        'playoffs': {}
    }
    
    # Calculate stats for each game type
    for game_type in ['Regular Season', 'Playoffs']:
        subset = player_df[player_df['game_type'] == game_type]
        
        if len(subset) > 0:
            game_stats = {}
            for col in STATS_COLUMNS:
                if col in subset.columns:
                    # Use mean for all stats
                    val = subset[col].mean()
                    game_stats[col] = val
            stats[game_type.lower().replace(' ', '_')] = {
                'games_count': len(subset),
                'stats': game_stats
            }
            # Debug print for KAST_pct
            if 'KAST_pct' in game_stats:
                print(f"[DEBUG] {player_name} {game_type} KAST_pct mean: {game_stats['KAST_pct']}")
        else:
            stats[game_type.lower().replace(' ', '_')] = {
                'games_count': 0,
                'stats': {col: 0 for col in STATS_COLUMNS}
            }
    return stats

def normalize_stats_for_radar(stats: Dict) -> Tuple[List[float], List[float]]:
    """
    Normalize stats for radar chart (0-1 scale for each stat, using fixed max values).
    Args:
        stats: Player stats dictionary
    Returns:
        Tuple of (regular_season_values, playoffs_values)
    """
    # Fixed max values for normalization (tune as needed for Valorant)
    max_values = {
        'rating_2_0': 2.0,      # Typical upper bound for rating
        'ACS': 300,             # Typical upper bound for ACS
        'KDRatio': 2.0,         # Typical upper bound for K/D
        'KAST_pct': 100,        # Percentage
        'ADR': 200,             # Typical upper bound for ADR
        'total_kills': 30,      # High kill count in a map
        'total_deaths': 30,     # High death count in a map (inverted)
        'total_assists': 15,    # High assist count
        'total_first_kills': 8, # High first kill count
        'total_first_deaths': 8 # High first death count (inverted)
    }
    regular = stats['regular_season']['stats']
    playoffs = stats['playoffs']['stats']
    regular_values = []
    playoff_values = []
    for col in STATS_COLUMNS:
        reg_val = regular.get(col, 0)
        play_val = playoffs.get(col, 0)
        max_val = max_values.get(col, 1)
        # Normalize to 0-1 scale
        reg_norm = min(reg_val / max_val, 1.0) if max_val > 0 else 0
        play_norm = min(play_val / max_val, 1.0) if max_val > 0 else 0
        # Invert deaths and first deaths (lower is better)
        if col in ['total_deaths', 'total_first_deaths']:
            reg_norm = 1.0 - reg_norm
            play_norm = 1.0 - play_norm
        regular_values.append(reg_norm)
        playoff_values.append(play_norm)
    return regular_values, playoff_values

def create_radar_chart(player_stats: List[Dict], output_filename: str = None):
    """
    Create radar charts comparing regular season vs playoff performance for all players.
    
    Args:
        player_stats: List of player statistics dictionaries
        output_filename: Optional filename to save the chart
    """
    # Set up the plotting style
    plt.style.use('seaborn-v0_8')
    
    # Calculate number of subplots needed
    n_players = len(player_stats)
    cols = min(3, n_players)  # Max 3 columns
    rows = (n_players + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(6*cols, 5*rows), subplot_kw=dict(projection='polar'))
    
    # Ensure axes is always a 2D array
    if n_players == 1:
        axes = np.array([axes])
    elif rows == 1:
        axes = axes.reshape(1, -1)
    
    # Flatten axes for easier iteration
    axes_flat = axes.flatten()
    
    # Number of stats
    num_stats = len(STATS_COLUMNS)
    
    # Calculate angles for each stat
    angles = np.linspace(0, 2 * np.pi, num_stats, endpoint=False).tolist()
    angles += angles[:1]  # Complete the circle
    
    for idx, player_stat in enumerate(player_stats):
        if player_stat is None:
            continue
            
        ax = axes_flat[idx]
        
        # Get normalized values
        regular_values, playoff_values = normalize_stats_for_radar(player_stat)
        
        # Complete the circle by adding the first value at the end
        regular_values += regular_values[:1]
        playoff_values += playoff_values[:1]
        
        # Plot the radar chart
        ax.plot(angles, regular_values, 'o-', linewidth=2, label='Regular Season', color='blue', alpha=0.7)
        ax.fill(angles, regular_values, alpha=0.25, color='blue')
        
        ax.plot(angles, playoff_values, 'o-', linewidth=2, label='Playoffs', color='red', alpha=0.7)
        ax.fill(angles, playoff_values, alpha=0.25, color='red')
        
        # Set the labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(STATS_LABELS)
        
        # Set the y-axis limits
        ax.set_ylim(0, 1)
        
        # Add title
        player_name = player_stat['player_name']
        reg_games = player_stat['regular_season']['games_count']
        play_games = player_stat['playoffs']['games_count']
        ax.set_title(f'{player_name}\nRegular: {reg_games} games | Playoffs: {play_games} games', 
                    pad=20, fontsize=12, fontweight='bold')
        
        # Add legend
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        
        # Add grid
        ax.grid(True)
    
    # Hide unused subplots
    for idx in range(n_players, len(axes_flat)):
        axes_flat[idx].set_visible(False)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the chart
    if output_filename is None:
        output_filename = 'player_radar_comparison.png'
    
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"Radar chart saved to: {output_path}")

def print_player_summary(player_stats: List[Dict]):
    """
    Print a summary of all players' performance.
    
    Args:
        player_stats: List of player statistics dictionaries
    """
    print("=" * 80)
    print("PLAYER PERFORMANCE SUMMARY")
    print("=" * 80)
    
    for player_stat in player_stats:
        if player_stat is None:
            continue
            
        player_name = player_stat['player_name']
        print(f"\n{player_name.upper()}")
        print("-" * 40)
        print(f"Total Games: {player_stat['total_games']}")
        
        for game_type in ['regular_season', 'playoffs']:
            games_count = player_stat[game_type]['games_count']
            print(f"\n{game_type.replace('_', ' ').title()}: {games_count} games")
            
            if games_count > 0:
                stats = player_stat[game_type]['stats']
                print(f"  Rating 2.0: {stats['rating_2_0']:.2f}")
                print(f"  ACS: {stats['ACS']:.1f}")
                print(f"  K/D: {stats['KDRatio']:.2f}")
                print(f"  KAST%: {stats['KAST_pct']:.1f}%")
                print(f"  ADR: {stats['ADR']:.1f}")
                print(f"  Kills: {stats['total_kills']:.1f}")
                print(f"  Deaths: {stats['total_deaths']:.1f}")
                print(f"  Assists: {stats['total_assists']:.1f}")
                print(f"  First Kills: {stats['total_first_kills']:.1f}")
                print(f"  First Deaths: {stats['total_first_deaths']:.1f}")

def analyze_players(player_names: List[str], event_names: Optional[List[str]] = None, db_path: str = ORIGINAL_DB_PATH) -> List[Dict]:
    """
    Main function to analyze multiple players.
    
    Args:
        player_names: List of player names to analyze
        event_names: Optional list of specific event names to filter by.
                    If None, includes all events.
        db_path: Path to the database to query
        
    Returns:
        List of player statistics dictionaries
    """
    db_name = "Original" if db_path == ORIGINAL_DB_PATH else "Clean"
    
    if event_names:
        print(f"Loading data for players: {', '.join(player_names)}")
        print(f"Filtering by events: {', '.join(event_names)}")
        print(f"Using {db_name} database")
    else:
        print(f"Loading data for players: {', '.join(player_names)} (all events)")
        print(f"Using {db_name} database")
    
    # Get player games
    df = get_player_games(player_names, event_names, db_path)
    
    if df.empty:
        print("No games found for the specified players!")
        return []
    
    print(f"Found {len(df)} total games")
    
    # Classify games as playoffs or regular season
    df = classify_playoff_games(df)
    
    # Calculate stats for each player
    player_stats = []
    for player_name in player_names:
        stats = calculate_player_stats(df, player_name)
        player_stats.append(stats)
        
        if stats:
            print(f"  {player_name}: {stats['total_games']} games "
                  f"({stats['regular_season']['games_count']} regular, "
                  f"{stats['playoffs']['games_count']} playoffs)")
        else:
            print(f"  {player_name}: No games found")
    
    return player_stats

def compare_databases(player_names: List[str], event_names: Optional[List[str]] = None) -> Tuple[List[Dict], List[Dict]]:
    """
    Compare player performance between original and cleaned databases.
    
    Args:
        player_names: List of player names to analyze
        event_names: Optional list of specific event names to filter by.
                    If None, includes all events.
        
    Returns:
        Tuple of (original_stats, clean_stats)
    """
    print("=" * 80)
    print("DATABASE COMPARISON ANALYSIS")
    print("=" * 80)
    
    # Check if clean database exists
    if not os.path.exists(CLEAN_DB_PATH):
        print(f"Warning: Clean database not found at {CLEAN_DB_PATH}")
        print("Please run the data cleaning script first.")
        return [], []
    
    # Analyze with original database
    print("\n1. ANALYZING WITH ORIGINAL DATABASE")
    print("-" * 50)
    original_stats = analyze_players(player_names, event_names, ORIGINAL_DB_PATH)
    
    # Analyze with clean database
    print("\n2. ANALYZING WITH CLEAN DATABASE")
    print("-" * 50)
    clean_stats = analyze_players(player_names, event_names, CLEAN_DB_PATH)
    
    return original_stats, clean_stats

def print_database_comparison(original_stats: List[Dict], clean_stats: List[Dict]):
    """
    Print a comparison between original and clean database results.
    
    Args:
        original_stats: Player statistics from original database
        clean_stats: Player statistics from clean database
    """
    print("\n" + "=" * 80)
    print("DATABASE COMPARISON SUMMARY")
    print("=" * 80)
    
    for i, player_name in enumerate([stat['player_name'] for stat in original_stats if stat]):
        print(f"\n{player_name.upper()}")
        print("-" * 40)
        
        orig_stat = original_stats[i] if i < len(original_stats) else None
        clean_stat = clean_stats[i] if i < len(clean_stats) else None
        
        if orig_stat and clean_stat:
            print("ORIGINAL DATABASE:")
            print(f"  Total Games: {orig_stat['total_games']}")
            print(f"  Regular Season: {orig_stat['regular_season']['games_count']} games")
            print(f"  Playoffs: {orig_stat['playoffs']['games_count']} games")
            
            print("\nCLEAN DATABASE:")
            print(f"  Total Games: {clean_stat['total_games']}")
            print(f"  Regular Season: {clean_stat['regular_season']['games_count']} games")
            print(f"  Playoffs: {clean_stat['playoffs']['games_count']} games")
            
            # Calculate differences
            total_diff = clean_stat['total_games'] - orig_stat['total_games']
            reg_diff = clean_stat['regular_season']['games_count'] - orig_stat['regular_season']['games_count']
            play_diff = clean_stat['playoffs']['games_count'] - orig_stat['playoffs']['games_count']
            
            print(f"\nDIFFERENCES (Clean - Original):")
            print(f"  Total Games: {total_diff:+d}")
            print(f"  Regular Season: {reg_diff:+d}")
            print(f"  Playoffs: {play_diff:+d}")
            
            # Show stat differences for regular season
            if orig_stat['regular_season']['games_count'] > 0 and clean_stat['regular_season']['games_count'] > 0:
                print(f"\nREGULAR SEASON STAT DIFFERENCES:")
                orig_reg = orig_stat['regular_season']['stats']
                clean_reg = clean_stat['regular_season']['stats']
                for stat in STATS_COLUMNS:
                    if stat in orig_reg and stat in clean_reg:
                        diff = clean_reg[stat] - orig_reg[stat]
                        print(f"  {stat}: {diff:+.3f}")
            
            # Show stat differences for playoffs
            if orig_stat['playoffs']['games_count'] > 0 and clean_stat['playoffs']['games_count'] > 0:
                print(f"\nPLAYOFFS STAT DIFFERENCES:")
                orig_play = orig_stat['playoffs']['stats']
                clean_play = clean_stat['playoffs']['stats']
                for stat in STATS_COLUMNS:
                    if stat in orig_play and stat in clean_play:
                        diff = clean_play[stat] - orig_play[stat]
                        print(f"  {stat}: {diff:+.3f}")
        else:
            print("Data not available for comparison")

def main():
    """
    Main function - create 4 comparisons: 2 with original database, 2 with cleaned database.
    """
    # Add player names here for analysis
    player_names = [
        "TenZ",
        "Boaster"
    ]
    
    # OPTIONAL: Add specific event names to filter by
    # If you want to analyze only specific events, uncomment and modify the line below:
    # event_names = ["VCT Champions", "VCT Masters"]
    # If you want all events (default), leave this as None:
    event_names = None
    
    # UNCOMMENT THE LINE BELOW TO SEE ALL AVAILABLE EVENTS:
    # print_available_events()
    
    print("=" * 80)
    print("PLAYER RADAR COMPARISON - ORIGINAL vs CLEAN DATABASE")
    print("=" * 80)
    
    # First, compare databases and show differences
    original_stats, clean_stats = compare_databases(player_names, event_names)
    
    if not original_stats and not clean_stats:
        print("No data found for any players!")
        return
    
    # Print database comparison summary
    print_database_comparison(original_stats, clean_stats)
    
    # Create 4 radar charts: 2 with original, 2 with cleaned
    print("\n" + "=" * 80)
    print("CREATING RADAR CHARTS")
    print("=" * 80)
    
    # Generate appropriate filenames based on whether events are filtered
    if event_names:
        event_suffix = "_" + "_".join([event.replace(" ", "_").replace("-", "_") for event in event_names[:2]])
        if len(event_names) > 2:
            event_suffix += "_etc"
    else:
        event_suffix = ""
    
    # 1. Original database radar chart
    if original_stats:
        print("\n1. Creating radar chart with ORIGINAL database...")
        orig_chart_filename = f'player_radar_comparison_original{event_suffix}.png'
        create_radar_chart(original_stats, orig_chart_filename)
        
        # Save original database results to CSV
        orig_csv_filename = f'player_comparison_data_original{event_suffix}.csv'
        save_results_to_csv(original_stats, orig_csv_filename)
    
    # 2. Clean database radar chart
    if clean_stats:
        print("\n2. Creating radar chart with CLEAN database...")
        clean_chart_filename = f'player_radar_comparison_clean{event_suffix}.png'
        create_radar_chart(clean_stats, clean_chart_filename)
        
        # Save clean database results to CSV
        clean_csv_filename = f'player_comparison_data_clean{event_suffix}.csv'
        save_results_to_csv(clean_stats, clean_csv_filename)
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE!")
    print("=" * 80)
    print("Created 4 files:")
    if original_stats:
        print(f"  - Original database radar chart: {orig_chart_filename}")
        print(f"  - Original database CSV data: {orig_csv_filename}")
    if clean_stats:
        print(f"  - Clean database radar chart: {clean_chart_filename}")
        print(f"  - Clean database CSV data: {clean_csv_filename}")
    print("\nCompare the results to see the impact of data cleaning!")

def save_results_to_csv(player_stats: List[Dict], filename: str):
    """
    Save player statistics to CSV file.
    
    Args:
        player_stats: List of player statistics dictionaries
        filename: Output filename
    """
    output_file = os.path.join(OUTPUT_DIR, filename)
    
    # Create a summary DataFrame for CSV export
    summary_data = []
    for player_stat in player_stats:
        if player_stat is None:
            continue
            
        for game_type in ['regular_season', 'playoffs']:
            games_count = player_stat[game_type]['games_count']
            if games_count > 0:
                stats = player_stat[game_type]['stats']
                row = {
                    'player_name': player_stat['player_name'],
                    'game_type': game_type.replace('_', ' ').title(),
                    'games_count': games_count
                }
                row.update(stats)
                summary_data.append(row)
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(output_file, index=False)
        print(f"  Detailed results saved to: {output_file}")
    else:
        print(f"  No data to save for {filename}")

if __name__ == "__main__":
    main() 