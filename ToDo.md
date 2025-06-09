Here’s your “where we left off → what’s next” roadmap:

---

## 🔍 1. Finish `parse_scoreboard()` in `src/parser.py`

* **Skip** the “All Maps” section so you only pull real map tabs.
* **Extract** match‐level header fields once per page:

  * `bracket_stage`
  * `match_datetime`
  * `patch`
  * `team1_name`, `team1_score`
  * `team2_name`, `team2_score`
* **Loop** every `<div class="vm-stats__layout">` except “All Maps”:

  * Grab `map_name` from the section header.
  * Within each table body, pull each `<tr>` row’s `<td>`s into your dict in **exact schema order**:

    1. `player_name`
    2. `player_team`
    3. `player_country`
    4. `agent_played`
    5. `rounds_played`
       … all the way through `total_first_deaths`
* **Return** a flat `List[Dict]` of all player‐map rows.

## 🧪 2. Smoke‐test your parser in isolation

* Create a quick script (or a simple REPL session) that:

  1. Fetches one live match URL with `requests`.
  2. Feeds its BeautifulSoup into `parse_scoreboard()`.
  3. Prints out the first few dicts to verify field names/types.

## 🔗 3. Wire parser → scraper → DB

* Confirm `scraper.py` is calling `parse_scoreboard` correctly and iterating its output.
* Ensure each returned row is being passed to `save_match(row)` without error.
* Make sure you call `init_db()` at startup so the table exists.

## ⚙️ 4. Full end-to-end run

* Populate `config/events.yaml` with all events you care about.
* From project root, run:

  ```bash
  python -m src.scraper
  ```
* Watch your logs for any parsing or DB errors.

## ✅ 5. Verify database contents

* Open the SQLite file (`data/map_stats.db`) in your favorite viewer or CLI:

  ```bash
  sqlite3 data/map_stats.db
  sqlite> SELECT map_name, COUNT(*) FROM map_stats GROUP BY map_name;
  ```
* Confirm you see one row per player per map, and that counts match expectations.

## 📊 6. Build your first analysis query

* Example: compare average `rating_2_0` in playoffs vs. “Main Event” stages:

  ```sql
  SELECT bracket_stage, AVG(rating_2_0)
    FROM map_stats
   GROUP BY bracket_stage;
  ```
* Iterate until you’re spotting “who rises and falls.”

---

Keep this checklist handy. As you knock each item off, you’ll have a fully scraped, persisted, and query-ready dataset for your Valorant “rise-or-fall” analysis.
