import sqlite3
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import numpy as np
from scipy.stats import ttest_ind
import matplotlib.dates as mdates

# Path to the SQLite database
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "map_stats.db")

def get_tenz_games() -> pd.DataFrame:
    """
    Get all TenZ games from the database, excluding "All Maps" entries.
    Returns a DataFrame with TenZ's individual map performances.
    """
    conn = sqlite3.connect(DB_PATH)
    
    query = """
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
    WHERE player_name LIKE '%TenZ%' 
    AND map_name != 'All Maps'
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
            # Convert to numeric, coercing errors to NaN
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def classify_playoff_games(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify games as playoffs or regular season based on bracket_stage.
    Returns DataFrame with a new 'game_type' column.
    """
    # Keywords that indicate playoff games
    playoff_keywords = [
        'playoff', 'playoffs', 'final', 'finals', 'semifinal', 'semifinals',
        'quarterfinal', 'quarterfinals', 'elimination', 'knockout', 'bracket',
        'championship', 'grand final', 'upper bracket', 'lower bracket',
        'decider', 'consolation'
    ]
    
    def is_playoff(stage: str) -> bool:
        if pd.isna(stage) or stage is None:
            return False
        stage_lower = str(stage).lower()
        return any(keyword in stage_lower for keyword in playoff_keywords)
    
    df['game_type'] = df['bracket_stage'].apply(
        lambda x: 'Playoffs' if is_playoff(x) else 'Regular Season'
    )
    
    return df

def analyze_tenz_performance(df: pd.DataFrame) -> Dict:
    """
    Analyze TenZ's performance statistics for both playoffs and regular season.
    """
    analysis = {}
    
    # Overall stats
    analysis['total_games'] = len(df)
    analysis['playoff_games'] = len(df[df['game_type'] == 'Playoffs'])
    analysis['regular_games'] = len(df[df['game_type'] == 'Regular Season'])
    
    # Performance by game type
    for game_type in ['Playoffs', 'Regular Season']:
        subset = df[df['game_type'] == game_type]
        if len(subset) > 0:
            kast_mean = subset['KAST_pct'].mean()
            if np.isnan(kast_mean):
                kast_mean = 'N/A'
            analysis[f'{game_type.lower().replace(" ", "_")}_stats'] = {
                'avg_rating': subset['rating_2_0'].mean(),
                'avg_acs': subset['ACS'].mean(),
                'avg_kd': subset['KDRatio'].mean(),
                'avg_kast': kast_mean,
                'avg_adr': subset['ADR'].mean(),
                'total_kills': subset['total_kills'].sum(),
                'total_deaths': subset['total_deaths'].sum(),
                'total_assists': subset['total_assists'].sum(),
                'games_count': len(subset)
            }
    
    # Statistical significance (t-test) for Rating 2.0
    playoffs_ratings = df[df['game_type'] == 'Playoffs']['rating_2_0'].dropna()
    regular_ratings = df[df['game_type'] == 'Regular Season']['rating_2_0'].dropna()
    if len(playoffs_ratings) > 1 and len(regular_ratings) > 1:
        t_stat, p_val = ttest_ind(playoffs_ratings, regular_ratings, equal_var=False)
        analysis['rating2_ttest'] = {'t_stat': t_stat, 'p_val': p_val}
    else:
        analysis['rating2_ttest'] = None
    
    return analysis

def print_analysis(analysis: Dict, df: pd.DataFrame):
    """
    Print a formatted analysis of TenZ's performance.
    """
    print("=" * 60)
    print("TENZ PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    print(f"\nTotal Games Analyzed: {analysis['total_games']}")
    print(f"Playoff Games: {analysis['playoff_games']}")
    print(f"Regular Season Games: {analysis['regular_games']}")
    
    print("\n" + "=" * 40)
    print("REGULAR SEASON PERFORMANCE")
    print("=" * 40)
    if 'regular_season_stats' in analysis:
        stats = analysis['regular_season_stats']
        kast_str = stats['avg_kast'] if stats['avg_kast'] == 'N/A' else f"{stats['avg_kast']:.1f}%"
        print(f"Games: {stats['games_count']}")
        print(f"Average Rating 2.0: {stats['avg_rating']:.2f}")
        print(f"Average ACS: {stats['avg_acs']:.1f}")
        print(f"Average K/D: {stats['avg_kd']:.2f}")
        print(f"Average KAST%: {kast_str}")
        print(f"Average ADR: {stats['avg_adr']:.1f}")
        print(f"Total Kills: {stats['total_kills']}")
        print(f"Total Deaths: {stats['total_deaths']}")
        print(f"Total Assists: {stats['total_assists']}")
    
    print("\n" + "=" * 40)
    print("PLAYOFF PERFORMANCE")
    print("=" * 40)
    if 'playoffs_stats' in analysis:
        stats = analysis['playoffs_stats']
        kast_str = stats['avg_kast'] if stats['avg_kast'] == 'N/A' else f"{stats['avg_kast']:.1f}%"
        print(f"Games: {stats['games_count']}")
        print(f"Average Rating 2.0: {stats['avg_rating']:.2f}")
        print(f"Average ACS: {stats['avg_acs']:.1f}")
        print(f"Average K/D: {stats['avg_kd']:.2f}")
        print(f"Average KAST%: {kast_str}")
        print(f"Average ADR: {stats['avg_adr']:.1f}")
        print(f"Total Kills: {stats['total_kills']}")
        print(f"Total Deaths: {stats['total_deaths']}")
        print(f"Total Assists: {stats['total_assists']}")
    
    # Print t-test result
    if analysis.get('rating2_ttest'):
        ttest = analysis['rating2_ttest']
        print("\nT-test for Rating 2.0 (Playoffs vs Regular Season):")
        print(f"t-statistic: {ttest['t_stat']:.3f}, p-value: {ttest['p_val']:.4f}")
        if ttest['p_val'] < 0.05:
            print("Result: Statistically significant difference (p < 0.05)")
        else:
            print("Result: No statistically significant difference (p >= 0.05)")
    
    # Show sample of recent games
    print("\n" + "=" * 60)
    print("RECENT GAMES SAMPLE")
    print("=" * 60)
    recent_games = df.head(10)[['event_name', 'bracket_stage', 'map_name', 'rating_2_0', 'game_type']]
    print(recent_games.to_string(index=False))

def create_visualizations(df: pd.DataFrame):
    """
    Create visualizations comparing TenZ's playoff vs regular season performance.
    """
    # Set up the plotting style
    plt.style.use('seaborn-v0_8')
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('TenZ Performance: Playoffs vs Regular Season', fontsize=16, fontweight='bold')
    
    # Filter out any NaN values for plotting
    plot_df = df.dropna(subset=['rating_2_0', 'ACS', 'KDRatio', 'ADR'])
    
    # 1. Rating 2.0 comparison
    playoff_ratings = plot_df[plot_df['game_type'] == 'Playoffs']['rating_2_0']
    regular_ratings = plot_df[plot_df['game_type'] == 'Regular Season']['rating_2_0']
    
    axes[0, 0].hist([regular_ratings, playoff_ratings], 
                    label=['Regular Season', 'Playoffs'], 
                    alpha=0.7, bins=15)
    axes[0, 0].set_title('Rating 2.0 Distribution')
    axes[0, 0].set_xlabel('Rating 2.0')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].legend()
    
    # 2. ACS comparison
    playoff_acs = plot_df[plot_df['game_type'] == 'Playoffs']['ACS']
    regular_acs = plot_df[plot_df['game_type'] == 'Regular Season']['ACS']
    
    axes[0, 1].hist([regular_acs, playoff_acs], 
                    label=['Regular Season', 'Playoffs'], 
                    alpha=0.7, bins=15)
    axes[0, 1].set_title('ACS Distribution')
    axes[0, 1].set_xlabel('ACS')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].legend()
    
    # 3. Box plot comparison
    metrics = ['rating_2_0', 'ACS', 'KDRatio', 'ADR']
    avg_data = []
    labels = []
    
    for metric in metrics:
        for game_type in ['Regular Season', 'Playoffs']:
            subset = plot_df[plot_df['game_type'] == game_type]
            if len(subset) > 0:
                avg_data.append(subset[metric].values)
                labels.append(f'{game_type}\n{metric}')
    
    axes[1, 0].boxplot(avg_data, labels=labels)
    axes[1, 0].set_title('Performance Metrics Comparison')
    axes[1, 0].set_ylabel('Value')
    axes[1, 0].tick_params(axis='x', rotation=45)
    
    # 4. Rating 2.0 over time (improved x-axis and annotate outliers)
    plot_df_sorted = plot_df.sort_values('match_datetime')
    # Convert match_datetime to datetime if not already
    if not pd.api.types.is_datetime64_any_dtype(plot_df_sorted['match_datetime']):
        plot_df_sorted['match_datetime'] = pd.to_datetime(plot_df_sorted['match_datetime'], errors='coerce')
    ax = axes[1, 1]
    reg = plot_df_sorted[plot_df_sorted['game_type'] == 'Regular Season']
    play = plot_df_sorted[plot_df_sorted['game_type'] == 'Playoffs']
    ax.scatter(reg['match_datetime'], reg['rating_2_0'], alpha=0.6, label='Regular Season', s=30)
    ax.scatter(play['match_datetime'], play['rating_2_0'], alpha=0.8, label='Playoffs', s=50, marker='s')
    ax.set_title('Rating 2.0 Over Time')
    ax.set_xlabel('Match Date')
    ax.set_ylabel('Rating 2.0')
    ax.legend()
    # Format x-axis for better readability
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
    # Annotate top 3 and bottom 3 games by rating
    for group, color in [(reg, 'blue'), (play, 'green')]:
        if not group.empty:
            top3 = group.nlargest(3, 'rating_2_0')
            bot3 = group.nsmallest(3, 'rating_2_0')
            for _, row in pd.concat([top3, bot3]).iterrows():
                ax.annotate(f"{row['rating_2_0']:.2f}", (row['match_datetime'], row['rating_2_0']),
                            textcoords="offset points", xytext=(0,5), ha='center', fontsize=8, color=color)
    plt.tight_layout()
    plt.savefig('tenz_performance_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """
    Main function to run the TenZ analysis.
    """
    print("Loading TenZ's game data...")
    df = get_tenz_games()
    
    if df.empty:
        print("No TenZ games found in the database!")
        return
    
    print(f"Found {len(df)} TenZ games")
    
    # Classify games as playoffs or regular season
    df = classify_playoff_games(df)
    
    # Analyze performance
    analysis = analyze_tenz_performance(df)
    
    # Print results
    print_analysis(analysis, df)
    
    # Create visualizations
    print("\nCreating visualizations...")
    create_visualizations(df)
    
    # Save detailed results to CSV
    output_file = 'tenz_games_analysis.csv'
    df.to_csv(output_file, index=False)
    print(f"\nDetailed results saved to: {output_file}")

if __name__ == "__main__":
    main() 