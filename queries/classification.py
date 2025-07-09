"""
Enhanced Valorant Tournament Classification System
==================================================

This module provides a centralized classification system for Valorant tournament matches.
Implements the enhanced system based on audit findings to address false positives and false negatives.

Usage:
    from queries.classification import classify_tournament_stage
    
    df['game_type'] = df['bracket_stage'].apply(
        lambda x: classify_tournament_stage(x, df['event_name'])
    )
"""

from typing import Optional
import pandas as pd

# DEFINITE PLAYOFF KEYWORDS (unless vetoed by group context)
PLAYOFF_KEYWORDS = [
    # Finals and Championship matches
    'grand final', 'grand finals', 'final', 'finals', 'championship',
    
    # Bracket stages (more specific to avoid false positives)
    'upper bracket final', 'lower bracket final',
    'upper bracket semifinal', 'lower bracket semifinal',
    'upper bracket quarterfinal', 'lower bracket quarterfinal',
    'upper bracket round', 'lower bracket round',
    
    # Elimination stages
    'semifinal', 'semifinals', 'quarterfinal', 'quarterfinals',
    'round of 16', 'round of 32', 'round of 8', 'round of 4',
    'elimination', 'knockout',
    
    # Placement matches (NEW - fixes false negatives)
    'consolation final', 'bronze final', '3rd place match', 'bronze match',
    'third place match', 'gold medal match', 'silver medal match', 'bronze medal match',
    'bronze', 'third place', '3rd place', 'medal match', 'place match',
    'consolation', 'placement final', '5th place match', 'fourth place match'
]

# DEFINITE REGULAR SEASON KEYWORDS
REGULAR_SEASON_KEYWORDS = [
    # Group stages
    'group stage', 'group a', 'group b', 'group c', 'group d',
    'group a -', 'group b -', 'group c -', 'group d -',
    
    # Swiss stages
    'swiss stage', 'swiss round', 'swiss phase',
    
    # Qualifying matches
    'opening matches', 'winners\' match', 'losers\' match',
    'qualification', 'qualifying',
    
    # Round robin and league
    'round robin', 'league stage', 'regular season',
    
    # Generic rounds (not elimination)
    'round 1', 'round 2', 'round 3', 'round 4', 'round 5', 'round 6'
]

# GROUP STAGE INDICATORS (VETO PLAYOFF KEYWORDS)
GROUP_STAGE_INDICATORS = [
    # Group identifiers
    'group a', 'group b', 'group c', 'group d', 'group e', 'group f',
    'group stage', 'group phase',
    
    # Swiss format
    'swiss', 'swiss stage', 'swiss phase',
    
    # League indicators
    'league', 'regular season', 'season',
    
    # Qualifying phases
    'qualification', 'qualifying', 'play-in', 'play ins',
    
    # Week/Day indicators
    'week', 'day', 'matchday'
]

# PLAY-INS KEYWORDS (classify as Regular Season)
PLAY_INS_KEYWORDS = [
    'play-ins', 'play ins', 'playin', 'play-in'
]

# EXCLUDED KEYWORDS (should be filtered out)
EXCLUDED_KEYWORDS = [
    'showmatch', 'show match', 'exhibition', 'all-star', 'all star',
    'charity match', 'fun match', 'demonstration', 'showcase'
]

# INTERNATIONAL EVENT KEYWORDS
INTERNATIONAL_EVENT_KEYWORDS = [
    'olympics', 'olympic', 'asian games', 'sea games', 'commonwealth games',
    'world cup', 'continental championship'
]

# INTERNATIONAL PLAYOFF KEYWORDS
INTERNATIONAL_PLAYOFF_KEYWORDS = [
    'gold medal', 'silver medal', 'bronze medal', 'final', 'semifinal'
]

# CONTEXT-DEPENDENT ANALYSIS KEYWORDS
PLAYOFF_AFTER_COLON_KEYWORDS = [
    'grand final', 'semifinal', 'quarterfinal', 'upper bracket', 'lower bracket',
    'final', 'finals', 'round of', 'elimination', 'knockout',
    'bronze', 'third place', 'medal'
]

REGULAR_AFTER_COLON_KEYWORDS = [
    'group', 'round 1', 'round 2', 'round 3', 'round 4',
    'opening', 'winners', 'losers', 'swiss'
]

# HIERARCHICAL STAGE ANALYSIS
PLAYOFF_PREFIXES = [
    'playoffs:', 'playoff:', 'knockout:', 'elimination:'
]

REGULAR_PREFIXES = [
    'group stage:', 'group:', 'swiss:', 'qualification:', 'play-in:'
]

CONTEXT_PREFIXES = [
    'main event:', 'tournament:', 'championship:'
]


def classify_tournament_stage(bracket_stage: str, event_name: Optional[str] = None) -> str:
    """
    Enhanced classification function that addresses false positives and false negatives.
    
    Args:
        bracket_stage: The bracket stage string from the database
        event_name: Optional event name for context-dependent classification
    
    Returns:
        'Playoffs', 'Regular Season', or 'Excluded'
    """
    if bracket_stage is None or str(bracket_stage).strip() == '':
        return 'Regular Season'
    
    stage_lower = str(bracket_stage).lower()
    event_lower = str(event_name).lower() if event_name else ''
    
    # TIER 1: Check for excluded keywords first
    for keyword in EXCLUDED_KEYWORDS:
        if keyword in stage_lower:
            return 'Excluded'
    
    # TIER 2: Check for group stage indicators (veto playoff keywords)
    # This is the key fix for false positives from the audit
    for indicator in GROUP_STAGE_INDICATORS:
        if indicator in stage_lower:
            return 'Regular Season'
    
    # TIER 3: Check for Play-Ins (classify as Regular Season)
    for keyword in PLAY_INS_KEYWORDS:
        if keyword in stage_lower:
            return 'Regular Season'
    
    # TIER 4: Apply hierarchical stage analysis
    # Trust tournament stage labeling hierarchy
    for prefix in PLAYOFF_PREFIXES:
        if stage_lower.startswith(prefix):
            return 'Playoffs'
    
    for prefix in REGULAR_PREFIXES:
        if stage_lower.startswith(prefix):
            return 'Regular Season'
    
    # TIER 5: Check for direct playoff keywords
    for keyword in PLAYOFF_KEYWORDS:
        if keyword in stage_lower:
            return 'Playoffs'
    
    # TIER 6: Check for direct regular season keywords
    for keyword in REGULAR_SEASON_KEYWORDS:
        if keyword in stage_lower:
            return 'Regular Season'
    
    # TIER 7: Context-dependent analysis for "Main Event:" and "Tournament:" prefixes
    if any(prefix in stage_lower for prefix in CONTEXT_PREFIXES):
        parts = bracket_stage.split(':')
        if len(parts) > 1:
            after_colon = parts[1].strip().lower()
            
            # Check if what comes after colon is playoff-related
            for keyword in PLAYOFF_AFTER_COLON_KEYWORDS:
                if keyword in after_colon:
                    return 'Playoffs'
            
            # Check if what comes after colon is regular season-related
            for keyword in REGULAR_AFTER_COLON_KEYWORDS:
                if keyword in after_colon:
                    return 'Regular Season'
    
    # TIER 8: International competition handling
    if any(keyword in event_lower for keyword in INTERNATIONAL_EVENT_KEYWORDS):
        for keyword in INTERNATIONAL_PLAYOFF_KEYWORDS:
            if keyword in stage_lower:
                return 'Playoffs'
        # For international events, if it's not a medal match, it's likely regular season
        if any(keyword in stage_lower for keyword in ['group', 'round', 'pool']):
            return 'Regular Season'
    
    # TIER 9: Default to Regular Season for ambiguous cases
    return 'Regular Season'


def validate_classification_distribution(df, game_type_column='game_type'):
    """
    Validate that the classification distribution is reasonable.
    
    Args:
        df: DataFrame with classification results
        game_type_column: Name of the column containing classifications
    
    Returns:
        dict: Validation results and warnings
    """
    total_games = len(df)
    playoff_games = len(df[df[game_type_column] == 'Playoffs'])
    regular_games = len(df[df[game_type_column] == 'Regular Season'])
    excluded_games = len(df[df[game_type_column] == 'Excluded'])
    
    playoff_pct = (playoff_games / total_games * 100) if total_games > 0 else 0
    regular_pct = (regular_games / total_games * 100) if total_games > 0 else 0
    excluded_pct = (excluded_games / total_games * 100) if total_games > 0 else 0
    
    warnings = []
    
    # Check for unusual distributions (based on audit findings)
    if playoff_pct > 50:
        warnings.append(f"WARNING: High playoff percentage ({playoff_pct:.1f}%) - review classification")
    
    if playoff_pct < 5:
        warnings.append(f"WARNING: Low playoff percentage ({playoff_pct:.1f}%) - review classification")
    
    if regular_pct < 50:
        warnings.append(f"WARNING: Low regular season percentage ({regular_pct:.1f}%) - review classification")
    
    if excluded_pct > 10:
        warnings.append(f"WARNING: High excluded percentage ({excluded_pct:.1f}%) - review filters")
    
    return {
        'total_games': total_games,
        'playoff_games': playoff_games,
        'regular_games': regular_games,
        'excluded_games': excluded_games,
        'playoff_percentage': playoff_pct,
        'regular_percentage': regular_pct,
        'excluded_percentage': excluded_pct,
        'warnings': warnings,
        'is_reasonable': len(warnings) == 0
    }


def get_database_exclusion_filters():
    """
    Get the standard database exclusion filters for analysis queries.
    
    Returns:
        str: SQL AND clause for excluding unwanted matches
    """
    return """
    AND map_name != 'All Maps'
    AND bracket_stage NOT LIKE '%Showmatch%'
    AND bracket_stage NOT LIKE '%showmatch%'
    AND bracket_stage NOT LIKE '%Exhibition%'
    AND bracket_stage NOT LIKE '%exhibition%'
    AND bracket_stage NOT LIKE '%All-Star%'
    AND bracket_stage NOT LIKE '%all-star%'
    AND bracket_stage NOT LIKE '%Charity%'
    AND bracket_stage NOT LIKE '%charity%'
    AND bracket_stage NOT LIKE '%Fun Match%'
    AND bracket_stage NOT LIKE '%fun match%'
    AND bracket_stage NOT LIKE '%Showcase%'
    AND bracket_stage NOT LIKE '%showcase%'
    """


def classify_dataframe(df: pd.DataFrame, bracket_stage_column: str = 'bracket_stage', 
                      event_name_column: str = 'event_name', 
                      game_type_column: str = 'game_type') -> pd.DataFrame:
    """
    Apply classification to an entire DataFrame.
    
    Args:
        df: DataFrame containing tournament data
        bracket_stage_column: Name of the bracket stage column
        event_name_column: Name of the event name column
        game_type_column: Name of the column to store classifications
    
    Returns:
        DataFrame with added game_type column
    """
    df_copy = df.copy()
    
    # Apply classification
    df_copy[game_type_column] = df_copy.apply(
        lambda row: classify_tournament_stage(
            row[bracket_stage_column], 
            row.get(event_name_column)
        ), 
        axis=1
    )
    
    return df_copy


# TEST CASES for validation (based on audit findings)
TEST_CASES = {
    # Playoff cases
    'Main Event: Grand Final': 'Playoffs',
    'Upper Bracket Final': 'Playoffs',
    'Lower Bracket Semifinal': 'Playoffs',
    'Round of 16': 'Playoffs',
    'Consolation Final': 'Playoffs',
    'Bronze Match': 'Playoffs',
    '3rd Place Match': 'Playoffs',
    'Gold Medal Match': 'Playoffs',
    'Playoffs: Bronze Medal Match': 'Playoffs',
    'Grand Final': 'Playoffs',
    'Semifinal': 'Playoffs',
    'Quarterfinal': 'Playoffs',
    'Championship': 'Playoffs',
    
    # Regular season cases (including false positive fixes)
    'Group Stage: Group A': 'Regular Season',
    'Swiss Stage: Round 1': 'Regular Season',
    'Main Event: Group A': 'Regular Season',
    'Play-Ins: Round 1': 'Regular Season',
    'Group A: Lower Bracket Final': 'Regular Season',  # Group context vetoes playoff
    'Swiss Phase: Lower Round 2': 'Regular Season',    # Swiss context vetoes playoff
    'Group A': 'Regular Season',
    'Swiss Round': 'Regular Season',
    'Opening Matches': 'Regular Season',
    'Winners\' Match': 'Regular Season',
    'Group Stage: Round 1': 'Regular Season',
    
    # Excluded cases
    'Showmatch': 'Excluded',
    'Exhibition Match': 'Excluded',
    'All-Star Game': 'Excluded',
    'Charity Match': 'Excluded',
    'Fun Match': 'Excluded'
}


def run_classification_tests():
    """
    Run tests to validate the classification function.
    
    Returns:
        dict: Test results
    """
    results = {
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    for test_input, expected_output in TEST_CASES.items():
        try:
            actual_output = classify_tournament_stage(test_input)
            if actual_output == expected_output:
                results['passed'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'input': test_input,
                    'expected': expected_output,
                    'actual': actual_output
                })
        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'input': test_input,
                'expected': expected_output,
                'actual': f'ERROR: {str(e)}'
            })
    
    return results


def analyze_classification_accuracy(df: pd.DataFrame, bracket_stage_column: str = 'bracket_stage'):
    """
    Analyze the classification accuracy by examining edge cases and distributions.
    
    Args:
        df: DataFrame with tournament data
        bracket_stage_column: Name of the bracket stage column
    
    Returns:
        dict: Analysis results
    """
    # Apply classification
    df_classified = classify_dataframe(df, bracket_stage_column)
    
    # Get validation results
    validation = validate_classification_distribution(df_classified)
    
    # Analyze edge cases
    edge_cases = {
        'group_with_playoff_terms': [],
        'playoff_with_unusual_names': [],
        'ambiguous_cases': []
    }
    
    for _, row in df.iterrows():
        stage = str(row[bracket_stage_column]).lower()
        
        # Check for group stages with playoff-like terms
        if any(indicator in stage for indicator in GROUP_STAGE_INDICATORS):
            if any(playoff_term in stage for playoff_term in ['final', 'semifinal', 'lower', 'upper']):
                edge_cases['group_with_playoff_terms'].append(row[bracket_stage_column])
        
        # Check for playoff matches with unusual names
        if any(playoff_term in stage for playoff_term in ['bronze', 'medal', '3rd place', 'consolation']):
            if 'group' not in stage and 'swiss' not in stage:
                edge_cases['playoff_with_unusual_names'].append(row[bracket_stage_column])
    
    return {
        'validation': validation,
        'edge_cases': edge_cases,
        'total_stages_analyzed': len(df)
    }


if __name__ == "__main__":
    # Run tests when module is executed directly
    test_results = run_classification_tests()
    print(f"Enhanced Classification Tests: {test_results['passed']} passed, {test_results['failed']} failed")
    
    if test_results['failed'] > 0:
        print("\nFailed tests:")
        for error in test_results['errors']:
            print(f"  Input: '{error['input']}'")
            print(f"  Expected: {error['expected']}, Got: {error['actual']}")
            print()
    
    # Test specific audit cases
    print("\nTesting audit-specific cases:")
    audit_cases = [
        ('Group A: Lower Bracket Final', 'Regular Season'),  # False positive fix
        ('Playoffs: Bronze Medal Match', 'Playoffs'),        # False negative fix
        ('Lower Swiss Phase: Round 3', 'Regular Season'),    # False positive fix
        ('3rd Place Match', 'Playoffs'),                     # False negative fix
    ]
    
    for test_input, expected in audit_cases:
        actual = classify_tournament_stage(test_input)
        status = "✓" if actual == expected else "✗"
        print(f"  {status} '{test_input}' → {actual} (expected: {expected})") 