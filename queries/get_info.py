import sqlite3
import os
import pandas as pd

# Path to the SQLite database
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "map_stats.db")

OUTPUT_FILE = "unique_bracket_stages.txt"
FILTERED_OUTPUT_FILE = "filtered_bracket_stages.txt"
CLASSIFICATION_OUTPUT_FILE = "classification_results.txt"

def save_unique_event_bracket_pairs():
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT DISTINCT event_name, bracket_stage FROM map_stats ORDER BY event_name, bracket_stage"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Filter out rows where bracket_stage is null and exclude those with 'Playoffs'
    df = df.dropna(subset=["bracket_stage"])
    df = df[~df['bracket_stage'].str.contains('Playoffs', case=False, na=False)]
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("Unique (event_name, bracket_stage) pairs (excluding 'Playoffs'):\n")
        for _, row in df.iterrows():
            f.write(f"Event: {row['event_name']} | Bracket Stage: {row['bracket_stage']}\n")
    print(f"Saved {len(df)} unique (event_name, bracket_stage) pairs (excluding 'Playoffs') to {OUTPUT_FILE}")

def analyze_bracket_stages():
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT DISTINCT event_name, bracket_stage FROM map_stats ORDER BY event_name, bracket_stage"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Filter out rows where bracket_stage is null
    df = df.dropna(subset=["bracket_stage"])
    
    # Count how many contain "Playoffs"
    playoffs_count = df[df['bracket_stage'].str.contains('Playoffs', case=False, na=False)].shape[0]
    total_count = df.shape[0]
    
    print(f"Total unique (event, bracket) pairs: {total_count}")
    print(f"Pairs containing 'Playoffs': {playoffs_count}")
    print(f"Remaining pairs to analyze: {total_count - playoffs_count}")
    
    # Get remaining bracket stages (without event names)
    non_playoffs = df[~df['bracket_stage'].str.contains('Playoffs', case=False, na=False)]
    unique_remaining_stages = non_playoffs['bracket_stage'].unique()
    
    with open(FILTERED_OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("Remaining unique bracket stages (excluding those with 'Playoffs'):\n")
        f.write("=" * 60 + "\n")
        for stage in sorted(unique_remaining_stages):
            f.write(f"- {stage}\n")
    
    print(f"Saved {len(unique_remaining_stages)} remaining unique bracket stages to {FILTERED_OUTPUT_FILE}")

def test_new_classification():
    """
    Test the new classification system on all unique bracket stages.
    """
    def is_playoff(stage: str) -> bool:
        if pd.isna(stage) or stage is None:
            return False
        
        stage_lower = str(stage).lower()
        
        # Tier 1: DEFINITELY PLAYOFFS - Direct keywords
        playoff_keywords = [
            'grand final', 'grand finals', 'final', 'finals',
            'semifinal', 'semifinals', 'quarterfinal', 'quarterfinals',
            'upper bracket', 'lower bracket', 'upper final', 'lower final',
            'upper semifinal', 'lower semifinal', 'upper quarterfinal', 'lower quarterfinal',
            'upper round', 'lower round', 'upper bracket final', 'lower bracket final',
            'upper bracket semifinal', 'lower bracket semifinal',
            'upper bracket quarterfinal', 'lower bracket quarterfinal',
            'consolation final', 'bronze final', '3rd place match', 'bronze match',
            'round of 16', 'round of 32', 'round of 8', 'round of 4',
            'elimination', 'knockout', 'championship'
        ]
        
        # Check for direct playoff keywords
        for keyword in playoff_keywords:
            if keyword in stage_lower:
                return True
        
        # Tier 2: DEFINITELY REGULAR SEASON - Direct keywords
        regular_season_keywords = [
            'group stage', 'group a', 'group b', 'group c', 'group d',
            'swiss stage', 'opening matches', 'winners\' match', 'losers\' match',
            'group a -', 'group b -', 'group c -', 'group d -'
        ]
        
        # Check for direct regular season keywords
        for keyword in regular_season_keywords:
            if keyword in stage_lower:
                return False
        
        # Tier 3: Context-dependent analysis
        # Look for patterns like "Main Event: Grand Final" vs "Main Event: Group A"
        if 'main event:' in stage_lower or 'tournament:' in stage_lower:
            # Extract the part after the colon
            parts = stage.split(':')
            if len(parts) > 1:
                after_colon = parts[1].strip().lower()
                
                # Check if what comes after colon is playoff-related
                playoff_after_colon = [
                    'grand final', 'semifinal', 'quarterfinal', 'upper', 'lower',
                    'final', 'finals', 'round of', 'elimination', 'knockout'
                ]
                
                for keyword in playoff_after_colon:
                    if keyword in after_colon:
                        return True
                
                # Check if what comes after colon is regular season-related
                regular_after_colon = [
                    'group', 'round 1', 'round 2', 'round 3', 'round 4',
                    'opening', 'winners', 'losers'
                ]
                
                for keyword in regular_after_colon:
                    if keyword in after_colon:
                        return False
        
        # Default to regular season for ambiguous cases
        return False
    
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT DISTINCT event_name, bracket_stage FROM map_stats ORDER BY event_name, bracket_stage"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Filter out rows where bracket_stage is null
    df = df.dropna(subset=["bracket_stage"])
    
    # Apply classification
    df['classification'] = df['bracket_stage'].apply(
        lambda x: 'Playoffs' if is_playoff(x) else 'Regular Season'
    )
    
    # Count classifications
    playoff_count = len(df[df['classification'] == 'Playoffs'])
    regular_count = len(df[df['classification'] == 'Regular Season'])
    total_count = len(df)
    
    print(f"\n" + "="*60)
    print("NEW CLASSIFICATION SYSTEM RESULTS")
    print("="*60)
    print(f"Total unique (event, bracket) pairs: {total_count}")
    print(f"Classified as Playoffs: {playoff_count} ({playoff_count/total_count*100:.1f}%)")
    print(f"Classified as Regular Season: {regular_count} ({regular_count/total_count*100:.1f}%)")
    
    # Show some examples of each classification
    playoff_examples = df[df['classification'] == 'Playoffs'].head(10)
    regular_examples = df[df['classification'] == 'Regular Season'].head(10)
    
    with open(CLASSIFICATION_OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("NEW CLASSIFICATION SYSTEM RESULTS\n")
        f.write("="*60 + "\n")
        f.write(f"Total unique (event, bracket) pairs: {total_count}\n")
        f.write(f"Classified as Playoffs: {playoff_count} ({playoff_count/total_count*100:.1f}%)\n")
        f.write(f"Classified as Regular Season: {regular_count} ({regular_count/total_count*100:.1f}%)\n\n")
        
        f.write("EXAMPLES OF PLAYOFF CLASSIFICATIONS:\n")
        f.write("-"*40 + "\n")
        for _, row in playoff_examples.iterrows():
            f.write(f"Event: {row['event_name']} | Stage: {row['bracket_stage']}\n")
        
        f.write("\nEXAMPLES OF REGULAR SEASON CLASSIFICATIONS:\n")
        f.write("-"*40 + "\n")
        for _, row in regular_examples.iterrows():
            f.write(f"Event: {row['event_name']} | Stage: {row['bracket_stage']}\n")
    
    print(f"\nDetailed results saved to {CLASSIFICATION_OUTPUT_FILE}")

if __name__ == "__main__":
    save_unique_event_bracket_pairs()
    print("\n" + "="*50)
    analyze_bracket_stages()
    print("\n" + "="*50)
    test_new_classification()
