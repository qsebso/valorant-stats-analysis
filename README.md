# VALORANT Map Stats Scraper

A long-term data collection project for analyzing VALORANT player performance across tournament phases. This scraper collects per-map scoreboard data from VLR.gg, focusing on comparing player statistics between regular season and playoff matches.

## Project Structure

```
.
├── .cursor/rules/     # Project rules and guidelines
├── .ignore/          # Ignored files and directories
├── config/           # Configuration files
│   └── events.yaml   # Tournament and match configurations
├── src/              # Source code
│   ├── scraper.py    # Data collection
│   ├── parser.py     # Data processing
│   ├── db.py         # Database operations
│   └── scheduler.py  # Automated scheduling
├── docs/             # Documentation
│   └── schema.md     # Database schema
├── migrations/       # Database migrations
├── requirements.txt  # Python dependencies
└── README.md        # This file
```

## Getting Started

1. **Configure Events**
   - Populate `config/events.yaml` with tournament IDs and match URLs
   - Add event names and identifiers for tracking

2. **Database Setup**
   - Review `docs/schema.md` for the complete table structure
   - Create the SQLite database using the provided schema

3. **Environment Setup**
   - Install dependencies: `pip install -r requirements.txt`
   - Verify Python 3.8+ is installed

4. **First Steps for Quinn**
   - Scraper will use the `bracket_stage` field from each match header as the phase; no manual phase file needed.

5. **Run the Scraper**
   - Initial data collection can begin after configuration
   - Monitor the database for successful data insertion

## Development Status

This project is in initial setup phase. Core functionality for data collection and analysis will be implemented incrementally. 