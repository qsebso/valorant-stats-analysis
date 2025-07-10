import sqlite3
import os
import sys
import pandas as pd
from typing import Dict, List, Tuple, Optional

# Add the queries directory to Python path for imports
sys.path.append(os.path.dirname(__file__))

# Path to the SQLite database
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "map_stats.db")

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "query_results")

def analyze_data_issues() -> Dict:
    """
    Analyze the main data issues found in the quality check.
    """
    conn = sqlite3.connect(DB_PATH)
    
    issues = {}
    
    # Check "All Maps" entries
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as count, 
               COUNT(DISTINCT match_id) as unique_matches,
               COUNT(DISTINCT player_name) as unique_players
        FROM map_stats 
        WHERE map_name = 'All Maps'
    """)
    all_maps_data = cursor.fetchone()
    
    issues['all_maps'] = {
        'total_rows': all_maps_data[0],
        'unique_matches': all_maps_data[1],
        'unique_players': all_maps_data[2],
        'description': f"{all_maps_data[0]} 'All Maps' entries across {all_maps_data[1]} matches"
    }
    
    # Check for extreme values in "All Maps" entries
    cursor.execute("""
        SELECT COUNT(*) 
        FROM map_stats 
        WHERE map_name = 'All Maps' 
        AND (total_kills > 50 OR total_deaths > 30 OR ACS > 500)
    """)
    extreme_all_maps = cursor.fetchone()[0]
    
    issues['extreme_all_maps'] = {
        'count': extreme_all_maps,
        'description': f"{extreme_all_maps} 'All Maps' entries with extreme values"
    }
    
    # Check for missing critical data
    cursor.execute("""
        SELECT COUNT(*) 
        FROM map_stats 
        WHERE (team1_score IS NULL OR team2_score IS NULL)
    """)
    missing_scores = cursor.fetchone()[0]
    
    issues['missing_scores'] = {
        'count': missing_scores,
        'description': f"{missing_scores} entries with missing team scores"
    }
    
    # Check for zero rounds played
    cursor.execute("""
        SELECT COUNT(*) 
        FROM map_stats 
        WHERE rounds_played = 0 OR rounds_played IS NULL
    """)
    zero_rounds = cursor.fetchone()[0]
    
    issues['zero_rounds'] = {
        'count': zero_rounds,
        'description': f"{zero_rounds} entries with zero or missing rounds played"
    }
    
    conn.close()
    return issues

def create_cleaning_recommendations(issues: Dict) -> List[str]:
    """
    Create recommendations for data cleaning based on the issues found.
    """
    recommendations = []
    
    # Recommendation for missing team scores
    if issues['missing_scores']['count'] > 0:
        recommendations.append({
            'priority': 'HIGH',
            'action': 'EXCLUDE',
            'target': 'Entries with missing team scores',
            'reason': f"Found {issues['missing_scores']['count']} entries with missing team scores",
            'sql_filter': "team1_score IS NOT NULL AND team2_score IS NOT NULL",
            'impact': 'Will ensure we have complete match context'
        })
    
    # Recommendation for zero rounds
    if issues['zero_rounds']['count'] > 0:
        recommendations.append({
            'priority': 'HIGH',
            'action': 'EXCLUDE',
            'target': 'Entries with zero rounds played',
            'reason': f"Found {issues['zero_rounds']['count']} entries with zero or missing rounds played",
            'sql_filter': "rounds_played > 0",
            'impact': 'Will ensure we only analyze actual gameplay data'
        })
    
    # Recommendation for missing player names
    recommendations.append({
        'priority': 'HIGH',
        'action': 'EXCLUDE',
        'target': 'Entries with missing player names',
        'reason': "Cannot analyze player performance without player names",
        'sql_filter': "player_name IS NOT NULL AND player_name != ''",
        'impact': 'Will ensure all entries have valid player data'
    })
    
    # Recommendation for missing event names
    recommendations.append({
        'priority': 'MEDIUM',
        'action': 'EXCLUDE',
        'target': 'Entries with missing event names',
        'reason': "Need event context for tournament classification",
        'sql_filter': "event_name IS NOT NULL AND event_name != ''",
        'impact': 'Will ensure proper event-based analysis'
    })
    
    return recommendations

def create_cleaned_query_filters() -> str:
    """
    Create SQL filters for cleaned data based on the recommendations.
    """
    filters = []
    
    # Exclude entries with missing team scores
    filters.append("team1_score IS NOT NULL AND team2_score IS NOT NULL")
    
    # Exclude entries with zero rounds
    filters.append("rounds_played > 0")
    
    # Exclude entries with missing player names
    filters.append("player_name IS NOT NULL AND player_name != ''")
    
    # Exclude entries with missing event names
    filters.append("event_name IS NOT NULL AND event_name != ''")
    
    return " AND ".join(filters)

def show_data_to_be_removed() -> Dict:
    """
    Show examples of data that will be removed by the cleaning filters.
    """
    conn = sqlite3.connect(DB_PATH)
    
    print("\n" + "=" * 80)
    print("EXAMPLES OF DATA TO BE REMOVED")
    print("=" * 80)
    
    # 1. Missing team scores (excluding All Maps)
    print("\n1. ENTRIES WITH MISSING TEAM SCORES (Individual Maps Only)")
    print("-" * 60)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT player_name, event_name, map_name, team1_score, team2_score, total_kills, total_deaths
        FROM map_stats 
        WHERE (team1_score IS NULL OR team2_score IS NULL)
        AND map_name != 'All Maps'
        LIMIT 5
    """)
    missing_scores = cursor.fetchall()
    
    if missing_scores:
        print("Player Name | Event | Map | Team1 | Team2 | Kills | Deaths")
        print("-" * 80)
        for row in missing_scores:
            print(f"{row[0][:15]:<15} | {row[1][:20]:<20} | {row[2]:<8} | {row[3] or 'NULL':>5} | {row[4] or 'NULL':>5} | {row[5]:>5} | {row[6]:>6}")
    else:
        print("No entries with missing team scores found.")
    
    # 2. Zero rounds played (excluding All Maps)
    print("\n2. ENTRIES WITH ZERO ROUNDS PLAYED (Individual Maps Only)")
    print("-" * 60)
    cursor.execute("""
        SELECT player_name, event_name, map_name, rounds_played, total_kills, total_deaths
        FROM map_stats 
        WHERE (rounds_played = 0 OR rounds_played IS NULL)
        AND map_name != 'All Maps'
        LIMIT 5
    """)
    zero_rounds = cursor.fetchall()
    
    if zero_rounds:
        print("Player Name | Event | Map | Rounds | Kills | Deaths")
        print("-" * 70)
        for row in zero_rounds:
            print(f"{row[0][:15]:<15} | {row[1][:20]:<20} | {row[2]:<8} | {row[3] or 'NULL':>6} | {row[4]:>5} | {row[5]:>6}")
    else:
        print("No entries with zero rounds found.")
    
    # 3. Missing player names (excluding All Maps)
    print("\n3. ENTRIES WITH MISSING PLAYER NAMES (Individual Maps Only)")
    print("-" * 60)
    cursor.execute("""
        SELECT player_name, event_name, map_name, total_kills, total_deaths
        FROM map_stats 
        WHERE (player_name IS NULL OR player_name = '')
        AND map_name != 'All Maps'
        LIMIT 5
    """)
    missing_names = cursor.fetchall()
    
    if missing_names:
        print("Player Name | Event | Map | Kills | Deaths")
        print("-" * 60)
        for row in missing_names:
            print(f"{row[0] or 'NULL':<15} | {row[1][:20]:<20} | {row[2]:<8} | {row[3]:>5} | {row[4]:>6}")
    else:
        print("No entries with missing player names found.")
    
    # 4. Missing event names (excluding All Maps)
    print("\n4. ENTRIES WITH MISSING EVENT NAMES (Individual Maps Only)")
    print("-" * 60)
    cursor.execute("""
        SELECT player_name, event_name, map_name, total_kills, total_deaths
        FROM map_stats 
        WHERE (event_name IS NULL OR event_name = '')
        AND map_name != 'All Maps'
        LIMIT 5
    """)
    missing_events = cursor.fetchall()
    
    if missing_events:
        print("Player Name | Event | Map | Kills | Deaths")
        print("-" * 60)
        for row in missing_events:
            print(f"{row[0][:15]:<15} | {row[1] or 'NULL':<20} | {row[2]:<8} | {row[3]:>5} | {row[4]:>6}")
    else:
        print("No entries with missing event names found.")
    
    # 5. "All Maps" entries (for reference - these will be KEPT)
    print("\n5. 'ALL MAPS' ENTRIES (THESE WILL BE KEPT)")
    print("-" * 50)
    cursor.execute("""
        SELECT player_name, event_name, map_name, total_kills, total_deaths, ACS, rating_2_0
        FROM map_stats 
        WHERE map_name = 'All Maps'
        LIMIT 5
    """)
    all_maps = cursor.fetchall()
    
    if all_maps:
        print("Player Name | Event | Map | Kills | Deaths | ACS | Rating")
        print("-" * 80)
        for row in all_maps:
            print(f"{row[0][:15]:<15} | {row[1][:20]:<20} | {row[2]:<8} | {row[3]:>5} | {row[4]:>6} | {row[5]:>3} | {row[6]:>5.2f}")
    else:
        print("No 'All Maps' entries found.")
    
    conn.close()
    
    return {
        'missing_scores_count': len(missing_scores),
        'zero_rounds_count': len(zero_rounds),
        'missing_names_count': len(missing_names),
        'missing_events_count': len(missing_events),
        'all_maps_count': len(all_maps)
    }

def test_cleaned_data() -> Dict:
    """
    Test the cleaned data to see the impact of the filters.
    """
    conn = sqlite3.connect(DB_PATH)
    
    # Get original counts
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM map_stats")
    original_count = cursor.fetchone()[0]
    
    # Get cleaned counts
    filters = create_cleaned_query_filters()
    cursor.execute(f"SELECT COUNT(*) FROM map_stats WHERE {filters}")
    cleaned_count = cursor.fetchone()[0]
    
    # Get sample of cleaned data
    cursor.execute(f"""
        SELECT player_name, event_name, map_name, total_kills, total_deaths, ACS, rating_2_0
        FROM map_stats 
        WHERE {filters}
        ORDER BY match_datetime DESC
        LIMIT 10
    """)
    sample_data = cursor.fetchall()
    
    conn.close()
    
    return {
        'original_count': original_count,
        'cleaned_count': cleaned_count,
        'removed_count': original_count - cleaned_count,
        'removal_percentage': ((original_count - cleaned_count) / original_count) * 100,
        'sample_data': sample_data
    }

def print_cleaning_analysis():
    """
    Print a comprehensive analysis of data cleaning recommendations.
    """
    print("=" * 80)
    print("DATA CLEANING ANALYSIS")
    print("=" * 80)
    
    # Show examples of data to be removed FIRST
    print("\n0. EXAMPLES OF DATA TO BE REMOVED")
    print("-" * 40)
    removed_examples = show_data_to_be_removed()
    
    # Analyze issues
    print("\n1. DATA ISSUES FOUND")
    print("-" * 40)
    issues = analyze_data_issues()
    
    for issue_name, issue_data in issues.items():
        print(f"  {issue_data['description']}")
    
    # Create recommendations
    print("\n2. CLEANING RECOMMENDATIONS")
    print("-" * 40)
    recommendations = create_cleaning_recommendations(issues)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['priority']} PRIORITY - {rec['action']}")
        print(f"   Target: {rec['target']}")
        print(f"   Reason: {rec['reason']}")
        print(f"   Impact: {rec['impact']}")
    
    # Test cleaned data
    print("\n3. CLEANED DATA IMPACT")
    print("-" * 40)
    cleaned_stats = test_cleaned_data()
    
    print(f"Original rows: {cleaned_stats['original_count']:,}")
    print(f"Cleaned rows: {cleaned_stats['cleaned_count']:,}")
    print(f"Removed rows: {cleaned_stats['removed_count']:,}")
    print(f"Removal percentage: {cleaned_stats['removal_percentage']:.1f}%")
    
    print("\n4. SAMPLE CLEANED DATA")
    print("-" * 40)
    print("Player Name | Event | Map | Kills | Deaths | ACS | Rating")
    print("-" * 80)
    for row in cleaned_stats['sample_data']:
        try:
            # Convert values to appropriate types for formatting
            player_name = str(row[0])[:15] if row[0] else "Unknown"
            event_name = str(row[1])[:20] if row[1] else "Unknown"
            map_name = str(row[2])[:8] if row[2] else "Unknown"
            
            # Handle numeric values safely
            kills = float(row[3]) if row[3] is not None and str(row[3]).replace('.', '').replace('-', '').isdigit() else 0
            deaths = float(row[4]) if row[4] is not None and str(row[4]).replace('.', '').replace('-', '').isdigit() else 0
            acs = float(row[5]) if row[5] is not None and str(row[5]).replace('.', '').replace('-', '').isdigit() else 0
            rating = float(row[6]) if row[6] is not None and str(row[6]).replace('.', '').replace('-', '').isdigit() else 0.0
            
            print(f"{player_name:<15} | {event_name:<20} | {map_name:<8} | {kills:>5.0f} | {deaths:>6.0f} | {acs:>3.0f} | {rating:>5.2f}")
        except (ValueError, TypeError, AttributeError) as e:
            # Fallback formatting for any problematic data
            print(f"{str(row[0])[:15]:<15} | {str(row[1])[:20]:<20} | {str(row[2])[:8]:<8} | {str(row[3]):>5} | {str(row[4]):>6} | {str(row[5]):>3} | {str(row[6]):>5}")
    
    # Create SQL filter
    print("\n5. RECOMMENDED SQL FILTER")
    print("-" * 40)
    filters = create_cleaned_query_filters()
    print("Use this WHERE clause for cleaned data:")
    print(f"WHERE {filters}")
    
    return {
        'issues': issues,
        'recommendations': recommendations,
        'cleaned_stats': cleaned_stats,
        'sql_filters': filters,
        'removed_examples': removed_examples
    }

def save_cleaning_report(analysis: Dict):
    """
    Save the cleaning analysis to a file.
    """
    output_path = os.path.join(OUTPUT_DIR, 'data_cleaning_report.txt')
    
    with open(output_path, 'w') as f:
        f.write("DATA CLEANING ANALYSIS REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        # Issues
        f.write("DATA ISSUES FOUND\n")
        f.write("-" * 20 + "\n")
        for issue_name, issue_data in analysis['issues'].items():
            f.write(f"{issue_data['description']}\n")
        f.write("\n")
        
        # Recommendations
        f.write("CLEANING RECOMMENDATIONS\n")
        f.write("-" * 25 + "\n")
        for i, rec in enumerate(analysis['recommendations'], 1):
            f.write(f"{i}. {rec['priority']} PRIORITY - {rec['action']}\n")
            f.write(f"   Target: {rec['target']}\n")
            f.write(f"   Reason: {rec['reason']}\n")
            f.write(f"   Impact: {rec['impact']}\n\n")
        
        # Impact
        cleaned_stats = analysis['cleaned_stats']
        f.write("CLEANED DATA IMPACT\n")
        f.write("-" * 20 + "\n")
        f.write(f"Original rows: {cleaned_stats['original_count']:,}\n")
        f.write(f"Cleaned rows: {cleaned_stats['cleaned_count']:,}\n")
        f.write(f"Removed rows: {cleaned_stats['removed_count']:,}\n")
        f.write(f"Removal percentage: {cleaned_stats['removal_percentage']:.1f}%\n\n")
        
        # SQL Filter
        f.write("RECOMMENDED SQL FILTER\n")
        f.write("-" * 25 + "\n")
        f.write(f"WHERE {analysis['sql_filters']}\n")
    
    print(f"\nCleaning report saved to: {output_path}")

def main():
    """
    Main function to run the data cleaning analysis.
    """
    print("Starting data cleaning analysis...")
    
    # Run analysis
    analysis = print_cleaning_analysis()
    
    # Save report
    save_cleaning_report(analysis)
    
    print("\nData cleaning analysis complete!")
    print("Use the recommended SQL filters in your analysis scripts for cleaner data.")

if __name__ == "__main__":
    main() 