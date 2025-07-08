import sqlite3
import os
import pandas as pd

# Path to the SQLite database
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "map_stats.db")

def validate_tenz_classification():
    """
    Validate our classification system against TenZ's recent matches.
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
    
    # Get TenZ's recent matches
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT 
        event_name,
        bracket_stage,
        match_datetime,
        team1_name,
        team2_name,
        player_name
    FROM map_stats 
    WHERE player_name LIKE '%TenZ%' 
    AND map_name != 'All Maps'
    ORDER BY match_datetime DESC
    LIMIT 50
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Apply classification
    df['our_classification'] = df['bracket_stage'].apply(
        lambda x: 'Playoffs' if is_playoff(x) else 'Regular Season'
    )
    
    print("VALIDATION OF TENZ CLASSIFICATION SYSTEM")
    print("=" * 60)
    print(f"Analyzing {len(df)} recent TenZ matches...\n")
    
    # Show examples by event
    recent_events = df['event_name'].unique()[:10]  # Show first 10 unique events
    
    for event in recent_events:
        event_matches = df[df['event_name'] == event]
        print(f"Event: {event}")
        print("-" * 40)
        
        for _, match in event_matches.iterrows():
            classification = match['our_classification']
            stage = match['bracket_stage']
            teams = f"{match['team1_name']} vs {match['team2_name']}"
            date = match['match_datetime']
            
            print(f"  {classification:12} | {stage:30} | {teams}")
        
        print()
    
    # Summary statistics
    playoff_count = len(df[df['our_classification'] == 'Playoffs'])
    regular_count = len(df[df['our_classification'] == 'Regular Season'])
    
    print("SUMMARY:")
    print(f"Playoffs: {playoff_count} ({playoff_count/len(df)*100:.1f}%)")
    print(f"Regular Season: {regular_count} ({regular_count/len(df)*100:.1f}%)")
    
    # Check for potential misclassifications
    print("\nPOTENTIAL ISSUES TO REVIEW:")
    print("-" * 30)
    
    # Look for "Play-Ins" which might be misclassified
    play_ins_matches = df[df['bracket_stage'].str.contains('Play-Ins', case=False, na=False)]
    if not play_ins_matches.empty:
        print("Play-Ins matches found (should probably be Regular Season):")
        for _, match in play_ins_matches.iterrows():
            print(f"  {match['bracket_stage']} - {match['event_name']}")
    
    # Look for "Showmatch" which should be excluded
    showmatch_matches = df[df['bracket_stage'].str.contains('Showmatch', case=False, na=False)]
    if not showmatch_matches.empty:
        print("\nShowmatch matches found (should be excluded from analysis):")
        for _, match in showmatch_matches.iterrows():
            print(f"  {match['bracket_stage']} - {match['event_name']}")

if __name__ == "__main__":
    validate_tenz_classification() 