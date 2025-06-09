````markdown
# ToDo

A checklist of next steps to finish and validate our VALORANT scraper pipeline.

---

## 1. Finish `parse_scoreboard()` in `src/parser.py`
- [X] Ensure the “All Maps” section is **included** with `map_index = 0` and `map_name = "All Maps"`.
- [X] Extract match-level header fields **once per page**:
  - `bracket_stage`
  - `match_datetime`
  - `patch`
  - `team1_name`, `team1_score`
  - `team2_name`, `team2_score`
- [X] Loop every `<div class="vm-stats__layout">` (including All Maps):
  - Parse the header text into:
    - `map_index` (0 for All Maps, 1, 2, …)
    - `map_name` (strip numeric prefix)
  - Within each section’s `<table><tbody>`, for each `<tr>` extract **in this exact order**:
    1. `player_name`
    2. `player_team`
    3. `player_country`
    4. `agent_played`
    5. `rounds_played`
    6. `rating_2_0`
    7. `game_score`
    8. `ACS`
    9. `KDRatio`
    10. `KAST_pct`
    11. `ADR`
    12. `KPR`
    13. `APR`
    14. `FKPR`
    15. `FDPR`
    16. `HS_pct`
    17. `CL_pct`
    18. `CL_count`
    19. `max_kills_in_round`
    20. `total_kills`
    21. `total_deaths`
    22. `total_assists`
    23. `total_first_kills`
    24. `total_first_deaths`
- [X] Return a flat `List[Dict]` of all player-map records.

---

## 2. Smoke-test your parser in isolation
- [ ] Create a small script or REPL snippet that:
  1. Fetches one live match URL with `requests`.  
  2. Calls `parse_scoreboard(soup)` on it.  
  3. Prints the first few dicts to verify field names, types, and values.

---

## 3. Wire parser → scraper → DB
- [ ] Confirm `scraper.py` calls `parse_scoreboard` and iterates its output.
- [ ] Ensure each dict is passed to `save_match(row)` without errors.
- [ ] Verify `init_db()` is called at startup so the `map_stats` table exists.

---

## 4. Full end-to-end run
- [ ] Populate `config/events.yaml` with all desired event IDs and names.
- [ ] From the project root, run:
  ```bash
  python -m src.scraper
````

* [ ] Watch the logs for any parsing or database errors.

---

## 5. Verify database contents

* [ ] Open the SQLite database:

  ```bash
  sqlite3 data/map_stats.db
  .tables
  PRAGMA table_info(map_stats);
  SELECT map_index, map_name, COUNT(*) FROM map_stats GROUP BY map_index, map_name;
  ```
* [ ] Confirm you see one entry per player per map (including All Maps) with correct indices.

---

## 6. Build your first analysis queries

* [ ] Example: compare average `rating_2_0` across different `bracket_stage` values:

  ```sql
  SELECT bracket_stage, AVG(rating_2_0)
    FROM map_stats
   GROUP BY bracket_stage;
  ```
* [ ] Iterate to identify players who “rise” or “fall” under pressure.

```
```
