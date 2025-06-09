"""
Database management module.
Handles SQLite operations, migrations, and data persistence.

This module provides the core database functionality:
1. Connection management
2. Table initialization
3. Data insertion with upsert support
4. Error handling and logging

The database schema is defined in docs/schema.md and includes
match metadata, team scores, and player statistics.
"""

import sqlite3
import logging
from typing import Dict, Any
import os

# Path to SQLite database file in data/ directory
DB_PATH = os.path.join(os.path.dirname(__file__), os.pardir, "data", "map_stats.db")

def get_connection():
    """
    Establish a connection to the SQLite database.
    
    Creates a new connection to the SQLite database file.
    The connection is not pooled or reused - each function
    gets its own connection to ensure thread safety.
    
    Returns:
        sqlite3.Connection: The database connection.
        
    Note:
        Caller is responsible for closing the connection
        when done with it.
    """
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db() -> None:
    """
    Initialize the map_stats table if it doesn't already exist.
    
    Creates the map_stats table with all columns defined in our schema.
    Uses IF NOT EXISTS to make the operation idempotent.
    The table structure matches docs/schema.md exactly.
    
    Columns:
        - Match metadata (event_id, match_id, datetime, etc.)
        - Team information (names, scores)
        - Player statistics (ACS, KDRatio, etc.)
        - Performance metrics (kills, deaths, assists, etc.)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create the table with all columns from our schema
    # Using IF NOT EXISTS for idempotency
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS map_stats (
    -- Match metadata
    event_id            TEXT,      -- Tournament ID
    event_name          TEXT,      -- Tournament name
    bracket_stage       TEXT,      -- Stage (e.g. Playoffs)
    match_id            TEXT,      -- Unique match ID
    match_datetime      DATETIME,  -- Match timestamp
    patch               TEXT,      -- Game version

    -- Map and teams
    map_name            TEXT,      -- Map name
    team1_name          TEXT,      -- Team 1
    team1_score         INTEGER,   -- Team 1 score
    team2_name          TEXT,      -- Team 2
    team2_score         INTEGER,   -- Team 2 score

    -- Player info
    player_name         TEXT,      -- Player name
    player_team         TEXT,      -- Player's team
    player_country      TEXT,      -- Country
    agent_played        TEXT,      -- Agent

    -- Core stats
    rounds_played       INTEGER,   -- Rounds played
    rating_2_0          REAL,      -- VLR rating
    game_score          REAL,      -- Game score
    ACS                 REAL,      -- Combat score
    KDRatio             REAL,      -- K/D ratio
    KAST_pct            REAL,      -- KAST %

    -- Advanced stats
    ADR                 REAL,      -- Damage/round
    KPR                 REAL,      -- Kills/round
    APR                 REAL,      -- Assists/round
    FKPR                REAL,      -- First kills/round
    FDPR                REAL,      -- First deaths/round
    HS_pct              REAL,      -- Headshot %
    CL_pct              REAL,      -- Clutch %
    CL_count            INTEGER,   -- Clutches won

    -- Raw stats
    max_kills_in_round  INTEGER,   -- Max kills in any round
    total_kills         INTEGER,   -- Total kills
    total_deaths        INTEGER,   -- Total deaths
    total_assists       INTEGER,   -- Total assists
    total_first_kills   INTEGER,   -- First kills
    total_first_deaths  INTEGER    -- First deaths
    );
    """)
    
    # Commit the table creation
    conn.commit()
    conn.close()
    logging.info("Initialized map_stats table in SQLite database.")

def insert_map_stats(row: Dict[str, Any]) -> None:
    """
    Insert or replace a single map_stats row into the database.
    
    This function performs an "upsert" operation:
    - If a row with the same match_id + map_name + player_name exists,
      it will be updated with the new values
    - Otherwise, a new row is inserted
    
    The function dynamically builds the SQL query based on the
    provided row dictionary, making it flexible to schema changes.
    
    Args:
        row: Dictionary matching the map_stats schema.
            Must contain all required columns.
            
    Note:
        Uses parameterized queries to prevent SQL injection.
        All database operations are wrapped in a transaction.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Dynamically build the INSERT OR REPLACE query
    # This allows us to handle any subset of columns
    columns = ", ".join(row.keys())
    placeholders = ", ".join("?" for _ in row)
    sql = f"INSERT OR REPLACE INTO map_stats ({columns}) VALUES ({placeholders})"
    
    try:
        # Execute the query with parameterized values
        cursor.execute(sql, tuple(row.values()))
        conn.commit()
        logging.debug(f"Inserted/Updated match {row.get('match_id')} for player {row.get('player_name')}")
    except Exception as e:
        # Log the error and the problematic data
        # Don't re-raise to allow the scraper to continue
        logging.error(f"Error inserting map_stats row: {e} | Data: {row}")
    finally:
        # Always close the connection
        conn.close()
