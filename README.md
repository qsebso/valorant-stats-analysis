# Raise and Fall — VALORANT Analysis

Data collection and analysis for **VALORANT** esports: per-map scoreboard data from VLR.gg, tournament phase classification (regular season vs playoffs), and analysis of **in-game leader (IGL) performance** vs non-IGLs.

## What’s in this repo

- **Scraping & DB** — Collect per-map player stats (ACS, rating, K/D, etc.) into SQLite; clean and deduplicate for analysis.
- **Classification** — Label bracket stages as Playoffs vs Regular Season (see `queries/classification.py`).
- **IGL analysis** — Compare IGL vs non-IGL ACS, effect size (Cohen’s d), and “brain vs fragger” (ACS delta vs team win rate). See **`igl_analysis/`** and [IGL findings](igl_analysis/findings.txt).

## Project structure

```
.
├── config/           # Tournament and match config (e.g. events.yaml)
├── data/             # SQLite DBs (map_stats, cleaned)
├── docs/             # Schema and docs
├── igl_analysis/      # IGL vs non-IGL analysis (data prep, stats, plots, findings)
├── queries/          # Classification, player/event queries, Boaster/TenZ-style analyses
├── src/              # Scraper, parser, DB, scheduler
├── requirements.txt
└── README.md
```

## Getting started

1. **Environment** — Python 3.8+. Install deps: `pip install -r requirements.txt`
2. **Database** — See `docs/schema.md`. Analysis uses cleaned DBs in `data/` (e.g. `valorant_stats_matchcentric_clean.db` with table `map_stats`).
3. **Config** — Populate `config/events.yaml` with tournament IDs and match URLs for scraping.
4. **Run IGL analysis** (no scraping required if you have the clean DB):
   ```bash
   python igl_analysis/run_analysis.py
   ```
   Outputs and findings: `igl_analysis/analysis_summary.txt`, `igl_analysis/findings.txt`, and plots in that folder.

## IGL analysis summary

Using only **known** IGL vs non-IGL labels (no contamination):

- **Result:** IGLs have slightly lower ACS on average than non-IGLs (Cohen’s d ≈ −0.22, small effect).
- **Methods:** Mann–Whitney (ACS not normal); one row per (match_id, map_name, player_name).
- **Details:** [igl_analysis/findings.txt](igl_analysis/findings.txt) and [igl_analysis/README.md](igl_analysis/README.md). 