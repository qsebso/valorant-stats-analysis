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

def get_available_events() -> List[str]:
    """
    Get a list of all available events in the database.
    
    Returns:
        List of unique event names
    """
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT DISTINCT event_name 
    FROM map_stats 
    WHERE event_name IS NOT NULL AND event_name != ''
    ORDER BY event_name
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df['event_name'].tolist()

def print_available_events():
    """
    Print all available events in the database to help users choose.
    """
    events = get_available_events()
    print("=" * 60)
    print("AVAILABLE EVENTS IN DATABASE")
    print("=" * 60)
    print(f"Total events: {len(events)}")
    print("\nEvents:")
    for i, event in enumerate(events, 1):
        print(f"{i:3d}. {event}")
    print("=" * 60)

# Path to the SQLite database
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "map_stats.db")

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
    'total_assists'
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
    'Total Assists'
]

def get_player_games(player_names: List[str], event_names: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Get games for the specified players from the database.
    
    Args:
        player_names: List of player names to search for
        event_names: Optional list of specific event names to filter by. 
                    If None, includes all events.
        
    Returns:
        DataFrame with player game data
    """
    conn = sqlite3.connect(DB_PATH)
    
    # Use the centralized exclusion filters
    exclusion_filters = get_database_exclusion_filters()
    
    # Create the WHERE clause for multiple players
    player_conditions = " OR ".join([f"player_name LIKE '%{name}%'" for name in player_names])
    
    # Add event filtering if specified
    event_filter = ""
    if event_names:
        event_conditions = " OR ".join([f"event_name LIKE '%{event}%'" for event in event_names])
        event_filter = f"AND ({event_conditions})"
    
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
        total_assists
    FROM map_stats 
    WHERE ({player_conditions})
    {exclusion_filters}
    {event_filter}
    ORDER BY match_datetime DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Convert numeric columns to proper data types
    numeric_columns = ['rating_2_0', 'ACS', 'KDRatio', 'KAST_pct', 'ADR', 
                      'total_kills', 'total_deaths', 'total_assists',
                      'team1_score', 'team2_score']
    
    for col in numeric_columns:
        if col in df.columns:
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
                    avg_val = subset[col].mean()
                    game_stats[col] = avg_val if not np.isnan(avg_val) else 0
            
            stats[game_type.lower().replace(' ', '_')] = {
                'games_count': len(subset),
                'stats': game_stats
            }
        else:
            stats[game_type.lower().replace(' ', '_')] = {
                'games_count': 0,
                'stats': {col: 0 for col in STATS_COLUMNS}
            }
    
    return stats

def normalize_stats_for_radar(stats: Dict) -> Tuple[List[float], List[float]]:
    """
    Normalize stats for radar chart plotting (0-1 scale).
    
    Args:
        stats: Dictionary with player stats
        
    Returns:
        Tuple of (regular_season_values, playoff_values) normalized to 0-1
    """
    # Define reasonable max values for each stat for normalization
    max_values = {
        'rating_2_0': 3.0,      # Very high rating
        'ACS': 400,             # Very high ACS
        'KDRatio': 3.0,         # Very high K/D
        'KAST_pct': 100,        # Percentage (already 0-100)
        'ADR': 200,             # Very high ADR
        'total_kills': 30,      # Very high kill count
        'total_deaths': 20,     # Very high death count (inverted for radar)
        'total_assists': 15     # Very high assist count
    }
    
    regular_values = []
    playoff_values = []
    
    for col in STATS_COLUMNS:
        if col in stats['regular_season']['stats']:
            reg_val = stats['regular_season']['stats'][col]
            play_val = stats['playoffs']['stats'][col]
            
            max_val = max_values[col]
            
            # Normalize to 0-1 scale
            reg_norm = min(reg_val / max_val, 1.0) if max_val > 0 else 0
            play_norm = min(play_val / max_val, 1.0) if max_val > 0 else 0
            
            # For deaths, invert the scale (fewer deaths = better)
            if col == 'total_deaths':
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

def analyze_players(player_names: List[str], event_names: Optional[List[str]] = None) -> List[Dict]:
    """
    Main function to analyze multiple players.
    
    Args:
        player_names: List of player names to analyze
        event_names: Optional list of specific event names to filter by.
                    If None, includes all events.
        
    Returns:
        List of player statistics dictionaries
    """
    if event_names:
        print(f"Loading data for players: {', '.join(player_names)}")
        print(f"Filtering by events: {', '.join(event_names)}")
    else:
        print(f"Loading data for players: {', '.join(player_names)} (all events)")
    
    # Get player games
    df = get_player_games(player_names, event_names)
    
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

def main():
    """
    Main function - add player names and optionally specific events here for analysis.
    """
    # Add player names here for analysis
    player_names = [
        "Xeppaa",
        "OXY"
    ]
    
    # OPTIONAL: Add specific event names to filter by
    # If you want to analyze only specific events, uncomment and modify the line below:
    # event_names = ["VCT Champions", "VCT Masters"]
    # If you want all events (default), leave this as None:
    event_names = None
    
    # UNCOMMENT THE LINE BELOW TO SEE ALL AVAILABLE EVENTS:
    # print_available_events()
    
    # Analyze the players
    player_stats = analyze_players(player_names, event_names)
    
    if not player_stats:
        print("No data found for any players!")
        return
    
    # Print summary
    print_player_summary(player_stats)
    
    # Create radar chart
    print("\nCreating radar chart comparison...")
    
    # Generate appropriate filenames based on whether events are filtered
    if event_names:
        event_suffix = "_" + "_".join([event.replace(" ", "_").replace("-", "_") for event in event_names[:2]])
        if len(event_names) > 2:
            event_suffix += "_etc"
        chart_filename = f'player_radar_comparison{event_suffix}.png'
        csv_filename = f'player_comparison_data{event_suffix}.csv'
    else:
        chart_filename = 'player_radar_comparison.png'
        csv_filename = 'player_comparison_data.csv'
    
    create_radar_chart(player_stats, chart_filename)
    
    # Save detailed results to CSV
    output_file = os.path.join(OUTPUT_DIR, csv_filename)
    
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
        print(f"\nDetailed results saved to: {output_file}")

if __name__ == "__main__":
    main() 