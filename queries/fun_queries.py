import sqlite3
import os

# Path to the SQLite database (assumed to be in data/map_stats.db)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "map_stats.db")

# SQL query to sum total_kills per player (grouped by player_name and player_team) and order by total kills descending
QUERY = """
SELECT player_name, player_team, SUM(total_kills) AS total_kills
FROM map_stats
GROUP BY player_name, player_team
ORDER BY total_kills DESC
LIMIT 1
"""

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(QUERY)
    row = cursor.fetchone()
    if row:
         (player, team, kills) = row
         print("Player with the most kills (across all maps):")
         print("Player: {}\nTeam: {}\nTotal Kills: {}".format(player, team, kills))
    else:
         print("No player data found.")
    conn.close() 