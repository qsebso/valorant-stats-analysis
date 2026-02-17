# IGL Performance Analysis

Analysis pipeline for the **IGL Performance Analysis** todo (see `todo.md`).

## Data sources (in this folder)

- **`igl_non_igl_player.txt`** — Defines the cohort: non-IGL players and their teammates (one per line).
- **`crossrefference_list.txt`** — IGL vs non-IGL labels (e.g. `Name – igl` / `Name – non-igl`).

## Database

The script uses the same cleaned DB as other project queries:

- **`../data/valorant_stats_matchcentric_clean.db`** (table `map_stats`).

To use a different DB, set `DB_PATH` in `load_igl_data.py`. The DB must have the `map_stats` table with columns such as `player_name`, `ACS`, `match_id`, `map_name`, `team1_name`, `team2_name`, `team1_score`, `team2_score`, `rounds_played`, etc.

## How to run

From the **project root**:

```bash
python igl_analysis/run_analysis.py
```

Or from this folder:

```bash
python run_analysis.py
```

## Outputs (written in this folder)

| File | Description |
|------|-------------|
| `analysis_summary.txt` | Normality (Step 1), test and p-value (Step 2), Cohen’s d (Step 3), and deliverable list. |
| `step1_acs_histogram.png` | Histogram + KDE of ACS (cohort with known IGL status). |
| `step5_acs_delta_vs_win_rate.png` | Scatter: average ACS delta vs team win rate (min 5 maps). |
| `acs_delta_winrate_table.csv` | Per-player: `acs_delta_avg`, `team_win_rate`, `maps`, `is_igl`. |

## Pipeline steps (in code)

1. **Data prep** — `load_igl_data.py`: parse cohort and crossreference, load `map_stats`, add `is_igl`, filter `rounds_played > 0` and exclusions.
2. **Step 1** — ACS distribution: histogram, KDE, Shapiro–Wilk; choose t-test vs Mann–Whitney.
3. **Step 2** — IGL vs non-IGL: t-test or Mann–Whitney on ACS.
4. **Step 3** — Cohen’s d and interpretation.
5. **Step 4** — Team average ACS per map; player `acs_delta` = ACS − team_avg_ACS.
6. **Step 5** — `team_win` per row; per-player `acs_delta_avg` and `team_win_rate`; scatter plot.

Optional Step 6 (predictive model) is not implemented; you can add it later if needed.
