import sqlite3
import pandas as pd
import os

# Path to the cleaned database
DB_PATH = os.path.join(os.path.dirname(__file__), os.pardir, 'data', 'valorant_stats_clean.db')
# Output CSV path
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), 'chronicle_unique_matches.csv')

# Query to get unique matches for Chronicle
query = '''
SELECT DISTINCT match_id, match_datetime, event_name, team1_name, team2_name, bracket_stage
FROM map_stats
WHERE player_name LIKE '%chronicle%'
ORDER BY match_datetime DESC
'''

def export_chronicle_matches():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    print(f"Found {len(df)} unique matches for Chronicle.")
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Exported to {OUTPUT_CSV}")

if __name__ == "__main__":
    export_chronicle_matches() 