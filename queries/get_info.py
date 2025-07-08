import sqlite3
import os
import pandas as pd

# Path to the SQLite database
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "map_stats.db")

OUTPUT_FILE = "unique_bracket_stages.txt"

def save_unique_event_bracket_pairs():
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT DISTINCT event_name, bracket_stage FROM map_stats ORDER BY event_name, bracket_stage"
    df = pd.read_sql_query(query, conn)
    conn.close()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("Unique (event_name, bracket_stage) pairs:\n")
        for _, row in df.dropna(subset=["bracket_stage"]).iterrows():
            f.write(f"Event: {row['event_name']} | Bracket Stage: {row['bracket_stage']}\n")
    print(f"Saved unique (event_name, bracket_stage) pairs to {OUTPUT_FILE}")

if __name__ == "__main__":
    save_unique_event_bracket_pairs()
