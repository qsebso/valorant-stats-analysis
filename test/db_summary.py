"""
Database Summary Script

This script connects to map_stats.db and prints:
- All table names
- Row count for each table
- A sample of 5 rows from each table
"""

import sqlite3
from tabulate import tabulate

DB_PATH = "data/map_stats.db"


def summarize_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables in {db_path}:")
    for t in tables:
        print(f"  - {t}")
    print()

    for table in tables:
        print(f"Table: {table}")
        # Row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  Row count: {count}")
        # Sample rows
        cursor.execute(f"SELECT * FROM {table} LIMIT 5")
        rows = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
        print(tabulate(rows, headers=col_names, tablefmt="grid"))
        print()

    conn.close()

if __name__ == "__main__":
    summarize_db() 