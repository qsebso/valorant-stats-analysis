# IGL Performance Analysis — To-Do Checklist

A step-by-step checklist for analyzing IGL performance using the Valorant player database.

---

## Data Source
- **Player list:** `igl_non_igl_player.txt` — lists non-IGL players and their team rosters (teammates). Use this file to define the analysis cohort: each line is one non-IGL player plus their teammates; IGLs are either teammates or from a separate reference and will be flagged with `is_igl`.

---

## Data Preparation
- [ ] Connect to SQLite database
- [ ] Load match and player data into a Pandas DataFrame
- [ ] Use `igl_non_igl_player.txt` to build player set; manually flag known IGLs with a new `is_igl` column (listed players in the file are non-IGL; flag IGLs from roster/teammate context or external list)
- [ ] Filter to valid player rounds only (e.g., `rounds_played > 0`)

---

## Step 1 — Analyze ACS Distribution
- [ ] Plot histogram and KDE of all `ACS` values
- [ ] Run Shapiro-Wilk test for normality
- [ ] Optional: Q-Q plot to visually inspect normality
- [ ] Decide whether to use t-test or Mann-Whitney for next step

---

## Step 2 — Compare IGLs vs Non-IGLs
- [ ] Create two groups: IGL ACS and non-IGL ACS (non-IGL roster from `igl_non_igl_player.txt`)
- [ ] Run t-test if normal, else Mann-Whitney U test
- [ ] Record p-value and determine if performance difference is significant

---

## Step 3 — Calculate Effect Size
- [ ] Use Cohen’s d to measure size of performance gap
- [ ] Interpret result: small (0.2), medium (0.5), or large (0.8+)

---

## Step 4 — Analyze IGL vs Team ACS
- [ ] Compute team average ACS per match
- [ ] Calculate each player’s ACS delta from team average
- [ ] Aggregate ACS delta per IGL

---

## Step 5 — Brain vs Fragger Visualization
- [ ] Define `team_win` as a Boolean column for each row
- [ ] Group IGLs by player name
- [ ] Calculate average `acs_delta` and `team_win_rate`
- [ ] Create scatterplot: ACS delta vs team win rate
- [ ] Add vertical line at x=0 to show over/under team average

---

## Step 6 (Optional) — Build Predictive Model
- [ ] Create features: `acs_delta`, `KAST_pct`, `KPR`, `APR`, etc.
- [ ] Run logistic regression predicting `team_win`
- [ ] Analyze coefficients to interpret what drives IGL success

---

## Final Deliverables
- [ ] Summary of normality results
- [ ] T-test/Mann-Whitney p-value
- [ ] Cohen’s d effect size
- [ ] Table with ACS delta and win rate per IGL
- [ ] Scatterplot of ACS delta vs win rate
- [ ] Model results (if included)
