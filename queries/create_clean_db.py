#!/usr/bin/env python3
"""
Create a clean version of the database by applying data cleaning filters.
This script creates a new database with only clean, reliable data.
"""

import sqlite3
import os
import shutil
from datetime import datetime
from pathlib import Path

def create_clean_database():
    """Create a clean version of the database with only reliable data."""
    
    # Database paths
    original_db = "data/map_stats.db"
    clean_db = "data/valorant_stats_clean.db"
    
    # Check if original database exists
    if not os.path.exists(original_db):
        print(f"Error: Original database not found at {original_db}")
        return False
    
    print("Creating clean database...")
    print(f"Original: {original_db}")
    print(f"Clean: {clean_db}")
    print("-" * 50)
    
    try:
        # Connect to original database
        conn_original = sqlite3.connect(original_db)
        cursor_original = conn_original.cursor()
        
        # Create clean database
        conn_clean = sqlite3.connect(clean_db)
        cursor_clean = conn_clean.cursor()
        
        # Get table schema from original database
        cursor_original.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='map_stats'")
        table_schema = cursor_original.fetchone()[0]
        
        # Create table in clean database
        cursor_clean.execute(table_schema)
        
        # Apply cleaning filters and copy clean data
        cleaning_query = """
        SELECT DISTINCT * FROM map_stats 
        WHERE team1_score IS NOT NULL 
        AND team2_score IS NOT NULL 
        AND rounds_played > 0 
        AND player_name IS NOT NULL 
        AND player_name != '' 
        AND event_name IS NOT NULL 
        AND event_name != ''
        """

        # Get column names for proper insertion
        cursor_original.execute("PRAGMA table_info(map_stats)")
        columns = [col[1] for col in cursor_original.fetchall()]
        placeholders = ', '.join(['?' for _ in columns])

        # Select clean data
        cursor_original.execute(cleaning_query)
        clean_data = cursor_original.fetchall()

        # Insert clean data into new database
        insert_query = f"INSERT INTO map_stats ({', '.join(columns)}) VALUES ({placeholders})"
        cursor_clean.executemany(insert_query, clean_data)
        
        # Commit changes
        conn_clean.commit()
        
        # Get statistics
        cursor_original.execute("SELECT COUNT(*) FROM map_stats")
        original_count = cursor_original.fetchone()[0]
        
        cursor_clean.execute("SELECT COUNT(*) FROM map_stats")
        clean_count = cursor_clean.fetchone()[0]
        
        removed_count = original_count - clean_count
        removal_percentage = (removed_count / original_count) * 100
        
        # Get some sample data from clean database
        cursor_clean.execute(f"SELECT * FROM map_stats LIMIT 10")
        sample_data = cursor_clean.fetchall()

        # Print results
        print("CLEAN DATABASE CREATED SUCCESSFULLY!")
        print("=" * 50)
        print(f"Original rows: {original_count:,}")
        print(f"Clean rows: {clean_count:,}")
        print(f"Removed rows: {removed_count:,}")
        print(f"Removal percentage: {removal_percentage:.1f}%")
        
        print("\nSAMPLE CLEAN DATA:")
        print("-" * 30)
        # Print all column headers
        print(' | '.join(columns))
        print("-" * 120)
        for row in sample_data:
            print(' | '.join(str(x) if x is not None else '' for x in row))
        
        print(f"\nClean database saved to: {clean_db}")
        print(f"File size: {os.path.getsize(clean_db) / (1024*1024):.1f} MB")
        
        # Save summary report
        report_path = "query_results/clean_database_summary.txt"
        os.makedirs("query_results", exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write("CLEAN DATABASE CREATION SUMMARY\n")
            f.write("=" * 40 + "\n")
            f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Original database: {original_db}\n")
            f.write(f"Clean database: {clean_db}\n")
            f.write(f"Original rows: {original_count:,}\n")
            f.write(f"Clean rows: {clean_count:,}\n")
            f.write(f"Removed rows: {removed_count:,}\n")
            f.write(f"Removal percentage: {removal_percentage:.1f}%\n")
            f.write(f"File size: {os.path.getsize(clean_db) / (1024*1024):.1f} MB\n")
            f.write("\nCleaning filters applied:\n")
            f.write("- team1_score IS NOT NULL\n")
            f.write("- team2_score IS NOT NULL\n")
            f.write("- rounds_played > 0\n")
            f.write("- player_name IS NOT NULL AND player_name != ''\n")
            f.write("- event_name IS NOT NULL AND event_name != ''\n")
        
        print(f"Summary report saved to: {report_path}")
        
        return True
        
    except Exception as e:
        print(f"Error creating clean database: {e}")
        return False

def main():
    """Main function to create clean database."""
    print("VALORANT STATS - CLEAN DATABASE CREATOR")
    print("=" * 50)
    
    success = create_clean_database()
    
    if success:
        print("\n✅ Clean database created successfully!")
        print("You can now use valorant_stats_clean.db for your analysis.")
    else:
        print("\n❌ Failed to create clean database.")
        print("Please check the error messages above.")

if __name__ == "__main__":
    main() 