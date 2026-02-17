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

5. **Run the Scraper**
   - Initial data collection can begin after configuration
   - Monitor the database for successful data insertion


IGL Performance Analysis — Findings
====================================

1. What we looked at
-------------------
We compared in-game performance (ACS: Average Combat Score) between players we know are IGLs (in-game leaders) and players we know are not, using only explicitly labeled players so the two groups are not contaminated. Data are map-level: one row per player per map per match, with duplicates removed so each game is counted once.

2. Main result: IGLs have slightly lower ACS
--------------------------------------------
- Mean ACS for IGLs: 192.7
- Mean ACS for non-IGLs: 206.6
- Difference: about 14 points lower for IGLs (small but consistent)

So on average, IGLs put up a bit less raw combat score than non-IGLs. That fits the common idea that IGLs spend more effort on shot-calling and strategy (“brain”) and less on pure fragging.

3. How we reached this
----------------------
- Step 1 — ACS was not normally distributed (Shapiro–Wilk p ≈ 2.2e-49), so we did not use a t-test. (Note: with N > 5000, Shapiro–Wilk p-values can be unreliable; the clear non-normality in our data still justifies a non-parametric test.)
- Step 2 — We used the Mann–Whitney U test. The difference in ACS between IGLs and non-IGLs was statistically significant (p ≈ 4.9e-49). With such a large sample, very small differences can be “significant,” so we focused on effect size.
- Step 3 — Cohen’s d ≈ -0.22 (negative = IGLs lower). By usual rules of thumb (0.2 small, 0.5 medium, 0.8 large), this is a small effect: IGLs are a bit below non-IGLs in ACS, but the overlap between the two groups is large.

4. Brain vs fragger (ACS delta and winning)
--------------------------------------------
We also looked at whether IGLs sit above or below their team’s average ACS (ACS delta) and how that relates to team win rate (see step5_acs_delta_vs_win_rate.png and acs_delta_winrate_table.csv).

- ACS delta = a player’s ACS minus their team’s average ACS on that map. Positive = above team average; negative = below.
- The scatter of “average ACS delta” vs “team win rate” shows that both IGLs and non-IGLs span a wide range: some are above team average, some below. There is no clear pattern that “IGLs who frag more than their team win more” in a simple linear way in this plot; win rate is driven by many factors (team, opponent, meta, etc.).

So: IGLs on average sit a bit below non-IGLs in ACS and slightly below team average in many cases, but the “brain vs fragger” story is about averages and roles, not a rule that every IGL must be below team average or that being above average guarantees wins.

5. Sample sizes and data quality
-------------------------------
- IGL map-rows: 5,107  |  Non-IGL map-rows: 39,383 (same players appear across many maps/matches).
- Only known IGL vs known non-IGL labels were used; unknowns were excluded.
- Rows are deduplicated on (match_id, map_name, player_name), so each player–map–match is counted once.

6. Takeaways
------------
- IGLs have slightly lower ACS than non-IGLs on average (small effect, Cohen’s d ≈ -0.22).
- The result is consistent with IGLs trading some fragging for leadership/strategy, but the effect is small and there is lots of overlap between the two groups.
- Win rate is not simply “more ACS delta = more wins”; the scatter and table are descriptive and do not imply that IGLs who frag more (or less) cause higher win rates by themselves.

7. Files to look at
-------------------
- analysis_summary.txt — numbers and test choices.
- step1_acs_histogram.png — ACS distribution.
- step5_acs_delta_vs_win_rate.png — ACS delta vs team win rate (min 5 maps).
- acs_delta_winrate_table.csv — per-player ACS delta and win rate.
