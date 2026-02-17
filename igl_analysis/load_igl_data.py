"""
Load and prepare IGL analysis data.
- Parses igl_non_igl_player.txt for cohort (non-IGL players + teammates).
- Parses crossrefference_list.txt for is_igl labels.
- Loads map_stats from SQLite and merges.
"""
import os
import re
import sqlite3
import pandas as pd

# Paths: run from project root or igl_analysis
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
# Path to the SQLite database (same cleaned DB as other queries; has map_stats table)
DB_PATH = os.path.join(PROJECT_ROOT, "data", "valorant_stats_matchcentric_clean.db")
IGL_NON_IGL_FILE = os.path.join(SCRIPT_DIR, "igl_non_igl_player.txt")
CROSSREF_FILE = os.path.join(SCRIPT_DIR, "crossrefference_list.txt")


def parse_igl_non_igl_player_file(path: str):
    """
    Parse igl_non_igl_player.txt. Returns (cohort_names, non_igl_main_names).
    - cohort_names: set of all player names mentioned (main + teammates) for DB filter.
    - non_igl_main_names: set of the main player on each line (explicitly non-IGL).
    """
    cohort = set()
    non_igl_mains = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or re.match(r"^##\s+[A-Z]$", line):
                continue
            # Format: "- Name (Team) – Teammates: A, B, C, D" or "- Name (Team)"
            if not line.startswith("- "):
                continue
            line = line[2:].strip()
            # Split on " – " to get "Name (Team)" and "Teammates: A, B, C, D"
            parts = re.split(r"\s+–\s+", line, maxsplit=1)
            main_part = parts[0].strip()
            # Extract name (before " (")
            name_match = re.match(r"^([^(]+)", main_part)
            if name_match:
                main_name = name_match.group(1).strip()
                cohort.add(main_name)
                non_igl_mains.add(main_name)
            if len(parts) > 1 and "Teammates:" in parts[1]:
                teammates_str = parts[1].replace("Teammates:", "").strip()
                for raw in re.split(r",\s*", teammates_str):
                    # "Allen (JP)" -> "Allen"
                    t = re.match(r"^([^(]+)", raw.strip()).group(1).strip() if raw.strip() else ""
                    if t:
                        cohort.add(t)
    return cohort, non_igl_mains


def parse_crossreference_igl(path: str):
    """
    Parse crossrefference_list.txt. Returns dict: normalized_name -> is_igl (bool).
    Uses first token of line before " – " as name; "igl" vs "non-igl" after that.
    """
    result = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "– igl" in line or "– non-igl" in line:
                # "FNS – igl" or "steel – igl (Joshua Nissan) – new addition"
                parts = line.split("–", 1)
                if len(parts) < 2:
                    continue
                name = parts[0].strip()
                rest = parts[1].strip().lower()
                if not name or name.startswith("("):
                    continue
                is_igl = "non-igl" not in rest or rest.startswith("igl")  # "igl" -> True, "non-igl" -> False
                if "non-igl" in rest:
                    is_igl = False
                elif "igl" in rest:
                    is_igl = True
                else:
                    continue
                result[name] = is_igl
    return result


def normalize_name_for_match(name: str) -> str:
    """Normalize for matching DB player_name to our lists (case-insensitive, strip)."""
    if not name or not isinstance(name, str):
        return ""
    return name.strip().lower()


def load_map_stats_for_cohort(cohort_names: set, exclusion_sql: str) -> pd.DataFrame:
    """Load map_stats rows for players in cohort; apply exclusions and rounds_played > 0."""
    if not cohort_names:
        return pd.DataFrame()
    names_list = [n.strip() for n in cohort_names if n and isinstance(n, str)]
    if not names_list:
        return pd.DataFrame()
    # Case-insensitive: match DB TRIM(player_name) against our list
    placeholders = ",".join("?" * len(names_list))
    query = f"""
    SELECT
        event_name, bracket_stage, match_id, match_datetime, map_name,
        team1_name, team1_score, team2_name, team2_score,
        player_name, player_team, agent_played,
        rating_2_0, ACS, KDRatio, KAST_pct, ADR,
        total_kills, total_deaths, total_assists,
        total_first_kills, total_first_deaths,
        rounds_played
    FROM map_stats
    WHERE LOWER(TRIM(player_name)) IN ({placeholders})
    AND rounds_played > 0
    AND map_name IS NOT NULL AND map_name != 'All Maps'
    {exclusion_sql}
    ORDER BY match_datetime, match_id, player_name
    """
    if not os.path.isfile(DB_PATH):
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}\n"
            "Ensure the project has data/valorant_stats_matchcentric_clean.db (or point DB_PATH in this file to your DB)."
        )
    conn = sqlite3.connect(DB_PATH)
    params = [n.lower() for n in names_list]
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    # One row per (match_id, map_name, player_name) — same as check_tenz_duplicates / player_radar
    if not df.empty and all(c in df.columns for c in ["match_id", "map_name", "player_name"]):
        n_before = len(df)
        df = df.drop_duplicates(subset=["match_id", "map_name", "player_name"], keep="first")
        n_dupes = n_before - len(df)
        if n_dupes > 0:
            df.attrs["_n_duplicates_removed"] = n_dupes
    return df


def add_is_igl(df: pd.DataFrame, crossref_igl: dict, non_igl_mains: set) -> pd.DataFrame:
    """
    Add is_igl column. Prefer crossreference; else if player in non_igl_mains -> False.
    Unknown -> None (drop or keep for cohort-only stats).
    """
    def resolve(row):
        name = (row.get("player_name") or "").strip()
        norm = normalize_name_for_match(name)
        # Exact match in crossreference (by original name keys)
        for k, v in crossref_igl.items():
            if normalize_name_for_match(k) == norm:
                return v
        # Name in non_igl_mains (explicitly non-IGL from igl_non_igl_player.txt)
        for n in non_igl_mains:
            if normalize_name_for_match(n) == norm:
                return False
        # Teammate: not in non_igl_mains; could be IGL. Prefer crossreference only.
        return None  # unknown

    df = df.copy()
    df["is_igl"] = df.apply(resolve, axis=1)
    return df


def prepare_analysis_df():
    """
    Full pipeline: load cohort, crossreference, DB; return DataFrame with is_igl,
    and exclusion_sql for use elsewhere. Also returns cohort, non_igl_mains, crossref.
    """
    exclusion_sql = """
    AND bracket_stage NOT LIKE '%Showmatch%' AND bracket_stage NOT LIKE '%showmatch%'
    AND bracket_stage NOT LIKE '%Exhibition%' AND bracket_stage NOT LIKE '%exhibition%'
    AND bracket_stage NOT LIKE '%All-Star%' AND bracket_stage NOT LIKE '%all-star%'
    AND bracket_stage NOT LIKE '%Charity%' AND bracket_stage NOT LIKE '%charity%'
    AND bracket_stage NOT LIKE '%Fun Match%' AND bracket_stage NOT LIKE '%fun match%'
    AND bracket_stage NOT LIKE '%Showcase%' AND bracket_stage NOT LIKE '%showcase%'
    """
    cohort, non_igl_mains = parse_igl_non_igl_player_file(IGL_NON_IGL_FILE)
    crossref_igl = parse_crossreference_igl(CROSSREF_FILE)
    df = load_map_stats_for_cohort(cohort, exclusion_sql)
    if df.empty:
        return df, cohort, non_igl_mains, crossref_igl, exclusion_sql, 0
    n_duplicates_removed = df.attrs.get("_n_duplicates_removed", 0)
    for col in ["rating_2_0", "ACS", "KDRatio", "KAST_pct", "ADR", "team1_score", "team2_score",
                "total_kills", "total_deaths", "total_assists", "rounds_played",
                "total_first_kills", "total_first_deaths"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = add_is_igl(df, crossref_igl, non_igl_mains)
    return df, cohort, non_igl_mains, crossref_igl, exclusion_sql, n_duplicates_removed


if __name__ == "__main__":
    df, cohort, non_igl_mains, crossref, _, n_dupes = prepare_analysis_df()
    print("Cohort size:", len(cohort))
    print("Non-IGL main names:", len(non_igl_mains))
    print("Crossreference IGL labels:", len(crossref))
    print("Rows loaded (after dedup on match_id, map_name, player_name):", len(df))
    if n_dupes > 0:
        print("Duplicate rows removed:", n_dupes)
    if not df.empty:
        known = df["is_igl"].notna()
        print("Rows with known is_igl:", known.sum(), "IGL:", (df["is_igl"] == True).sum(), "Non-IGL:", (df["is_igl"] == False).sum())
