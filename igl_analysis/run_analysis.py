"""
IGL Performance Analysis — run all steps from todo.md.
Outputs: summary text, tables, and plots in igl_analysis folder.
"""
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Ensure we can import load_igl_data from this folder (run from project root or igl_analysis)
sys.path.insert(0, SCRIPT_DIR)
from load_igl_data import prepare_analysis_df

OUTPUT_DIR = SCRIPT_DIR


def ensure_numeric_acs(df: pd.DataFrame) -> pd.DataFrame:
    if "ACS" not in df.columns:
        return df
    df = df.copy()
    df["ACS"] = pd.to_numeric(df["ACS"], errors="coerce")
    return df


# ---------- Step 1: ACS distribution, normality ----------
def step1_acs_distribution(df: pd.DataFrame) -> dict:
    """Histogram, KDE, Shapiro-Wilk; return results and whether to use t-test or Mann-Whitney."""
    df = df.dropna(subset=["ACS"])
    if df.empty or len(df) < 3:
        return {"normal": None, "use_parametric": None, "shapiro_stat": None, "shapiro_p": None}
    acs = df["ACS"].astype(float)
    shapiro_stat, shapiro_p = stats.shapiro(acs)
    # Common rule: if p < 0.05 reject normality -> use Mann-Whitney
    use_parametric = shapiro_p >= 0.05
    return {
        "normal": shapiro_p >= 0.05,
        "use_parametric": use_parametric,
        "shapiro_stat": shapiro_stat,
        "shapiro_p": shapiro_p,
        "n": len(acs),
    }


def plot_step1(df: pd.DataFrame, out_dir: str):
    df = df.dropna(subset=["ACS"])
    if df.empty:
        return
    fig, ax = plt.subplots(1, 1, figsize=(8, 5))
    acs = df["ACS"].astype(float)
    ax.hist(acs, bins=min(50, max(15, len(acs) // 20)), density=True, alpha=0.7, color="steelblue", edgecolor="black")
    acs.plot.kde(ax=ax, color="red", linewidth=2, label="KDE")
    ax.set_xlabel("ACS")
    ax.set_ylabel("Density")
    ax.set_title("ACS distribution (all cohort)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "step1_acs_histogram.png"), dpi=150, bbox_inches="tight")
    plt.close()


# ---------- Step 2: IGL vs non-IGL comparison ----------
def step2_compare_igl_nonigl(df: pd.DataFrame, use_parametric: bool) -> dict:
    igl = df[df["is_igl"] == True]["ACS"].dropna().astype(float)
    non_igl = df[df["is_igl"] == False]["ACS"].dropna().astype(float)
    if igl.empty or non_igl.empty:
        return {"test": None, "statistic": None, "p_value": None, "n_igl": len(igl), "n_non_igl": len(non_igl)}
    if use_parametric:
        stat, p = stats.ttest_ind(igl, non_igl, equal_var=False)
        return {"test": "ttest", "statistic": stat, "p_value": p, "n_igl": len(igl), "n_non_igl": len(non_igl)}
    else:
        stat, p = stats.mannwhitneyu(igl, non_igl, alternative="two-sided")
        return {"test": "mannwhitney", "statistic": stat, "p_value": p, "n_igl": len(igl), "n_non_igl": len(non_igl)}


# ---------- Step 3: Cohen's d ----------
def step3_cohens_d(df: pd.DataFrame) -> dict:
    igl = df[df["is_igl"] == True]["ACS"].dropna().astype(float)
    non_igl = df[df["is_igl"] == False]["ACS"].dropna().astype(float)
    if igl.empty or non_igl.empty:
        return {"cohens_d": None, "interpretation": None}
    m1, m2 = igl.mean(), non_igl.mean()
    s1, s2 = igl.std(ddof=1), non_igl.std(ddof=1)
    n1, n2 = len(igl), len(non_igl)
    pooled_std = np.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2)) if (n1 + n2) > 2 else np.nan
    d = (m1 - m2) / pooled_std if pooled_std and pooled_std > 0 else np.nan
    if np.isnan(d):
        interp = "N/A"
    elif abs(d) < 0.2:
        interp = "negligible"
    elif abs(d) < 0.5:
        interp = "small"
    elif abs(d) < 0.8:
        interp = "medium"
    else:
        interp = "large"
    return {"cohens_d": d, "interpretation": interp, "mean_igl": m1, "mean_non_igl": m2}


# ---------- Step 4: IGL vs team ACS delta ----------
def step4_team_acs_delta(df: pd.DataFrame) -> pd.DataFrame:
    """Compute team average ACS per match, then each player's ACS - team_avg_ACS. Aggregate per player (and is_igl)."""
    # Per (match_id, map) get team's average ACS for that map
    df = df.copy()
    df["ACS"] = pd.to_numeric(df["ACS"], errors="coerce")
    match_team_acs = df.groupby(["match_id", "map_name", "player_team"], dropna=False)["ACS"].mean().reset_index()
    match_team_acs = match_team_acs.rename(columns={"ACS": "team_avg_acs"})
    df = df.merge(
        match_team_acs,
        on=["match_id", "map_name", "player_team"],
        how="left",
    )
    df["acs_delta"] = df["ACS"] - df["team_avg_acs"]
    return df


# ---------- Step 5: Brain vs Fragger (ACS delta vs team win rate) ----------
def step5_team_win_and_scatter(df: pd.DataFrame, out_dir: str) -> pd.DataFrame:
    """Add team_win (player's team won the map), then by-player acs_delta avg and team_win_rate."""
    # Determine winner: team with higher score won
    df = df.copy()
    df["team_score"] = np.where(
        df["player_team"] == df["team1_name"],
        pd.to_numeric(df["team1_score"], errors="coerce"),
        pd.to_numeric(df["team2_score"], errors="coerce"),
    )
    df["opp_score"] = np.where(
        df["player_team"] == df["team1_name"],
        pd.to_numeric(df["team2_score"], errors="coerce"),
        pd.to_numeric(df["team1_score"], errors="coerce"),
    )
    df["team_win"] = df["team_score"] > df["opp_score"]
    by_player = df.groupby("player_name").agg(
        acs_delta_avg=("acs_delta", "mean"),
        team_win_rate=("team_win", "mean"),
        maps=("team_win", "count"),
    ).reset_index()
    # Merge is_igl (take first per player)
    is_igl_map = df.drop_duplicates("player_name")[["player_name", "is_igl"]].set_index("player_name")["is_igl"]
    by_player["is_igl"] = by_player["player_name"].map(is_igl_map)
    # Scatter: only label IGLs or filter to min maps
    plot_df = by_player[by_player["maps"] >= 5].copy()
    if plot_df.empty:
        return by_player
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    for igl_val, label in [(True, "IGL"), (False, "Non-IGL")]:
        sub = plot_df[plot_df["is_igl"] == igl_val]
        if sub.empty:
            continue
        ax.scatter(sub["acs_delta_avg"], sub["team_win_rate"] * 100, label=label, alpha=0.7, s=sub["maps"].clip(5, 50))
    ax.axvline(0, color="gray", linestyle="--")
    ax.set_xlabel("Average ACS delta (vs team average)")
    ax.set_ylabel("Team win rate (%)")
    ax.set_title("Brain vs Fragger: ACS delta vs team win rate (min 5 maps)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "step5_acs_delta_vs_win_rate.png"), dpi=150, bbox_inches="tight")
    plt.close()
    return by_player


def main():
    print("Loading data...")
    df, cohort, non_igl_mains, crossref, _, n_duplicates_removed = prepare_analysis_df()
    df = ensure_numeric_acs(df)
    if n_duplicates_removed > 0:
        print(f"Removed {n_duplicates_removed} duplicate rows (same match_id, map_name, player_name).")
    # Restrict to rows with known is_igl for IGL vs non-IGL comparison
    df_known = df[df["is_igl"].notna()].copy()
    if df_known.empty:
        print("No rows with known is_igl. Check crossreference and cohort parsing.")
        return
    print(f"Rows with known is_igl: {len(df_known)} (IGL: {(df_known['is_igl']==True).sum()}, Non-IGL: {(df_known['is_igl']==False).sum()})")

    results = {}

    # Step 1
    print("Step 1: ACS distribution...")
    results["step1"] = step1_acs_distribution(df_known)
    plot_step1(df_known, OUTPUT_DIR)

    # Step 2
    print("Step 2: IGL vs non-IGL...")
    use_parametric = results["step1"].get("use_parametric", True)
    results["step2"] = step2_compare_igl_nonigl(df_known, use_parametric)

    # Step 3
    print("Step 3: Cohen's d...")
    results["step3"] = step3_cohens_d(df_known)

    # Step 4 & 5 need match-level team ACS and team_win
    print("Step 4 & 5: Team ACS delta and win rate...")
    df_with_delta = step4_team_acs_delta(df_known)
    by_player = step5_team_win_and_scatter(df_with_delta, OUTPUT_DIR)

    # Save summary and table
    summary_path = os.path.join(OUTPUT_DIR, "analysis_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("IGL Performance Analysis — Summary\n")
        f.write("=" * 50 + "\n\n")
        f.write("Data: cohort from igl_non_igl_player.txt; is_igl from crossrefference_list.txt.\n\n")
        f.write("Row deduplication: one row per (match_id, map_name, player_name); duplicates removed.\n")
        if n_duplicates_removed > 0:
            f.write(f"  Duplicate rows removed: {n_duplicates_removed}\n")
        f.write("\nComparison uses ONLY known IGL vs known non-IGL (no unknown labels):\n")
        f.write("  - IGL = explicitly labeled IGL in crossrefference_list.txt.\n")
        f.write("  - Non-IGL = labeled non-IGL in crossreference OR main name in igl_non_igl_player.txt.\n")
        f.write("  - Teammates not in either list are excluded (is_igl unknown).\n\n")
        n_igl = (df_known["is_igl"] == True).sum()
        n_non = (df_known["is_igl"] == False).sum()
        f.write("Sample sizes (map-level rows; same player appears many times, one row per map per match):\n")
        f.write(f"  IGL: {n_igl:,}  |  Non-IGL: {n_non:,}\n")
        f.write("  (Unequal n is fine for t-test/Mann-Whitney; with large n, prefer effect size over p-value.)\n\n")
        s1 = results["step1"]
        f.write("Step 1 — ACS distribution\n")
        f.write(f"  n = {s1.get('n', 'N/A')}\n")
        _p = s1.get("shapiro_p")
        f.write(f"  Shapiro-Wilk p = {_p:.2e}\n" if _p is not None and isinstance(_p, (int, float)) else f"  Shapiro-Wilk p = {_p}\n")
        f.write(f"  Normality (p>=0.05): {s1.get('normal')}\n")
        f.write(f"  Use parametric test: {s1.get('use_parametric')}\n\n")
        s2 = results["step2"]
        f.write("Step 2 — IGL vs non-IGL\n")
        f.write(f"  Test: {s2.get('test')}\n")
        _stat = s2.get("statistic")
        _pv = s2.get("p_value")
        f.write(f"  Statistic: {_stat:.4g}\n" if isinstance(_stat, (int, float)) else f"  Statistic: {_stat}\n")
        f.write(f"  p-value: {_pv:.2e}\n" if _pv is not None and isinstance(_pv, (int, float)) else f"  p-value: {_pv}\n")
        f.write(f"  n_IGL: {s2.get('n_igl')}, n_non_IGL: {s2.get('n_non_igl')}\n\n")
        s3 = results["step3"]
        f.write("Step 3 — Effect size\n")
        _d = s3.get("cohens_d")
        f.write(f"  Cohen's d: {_d:.4g}\n" if _d is not None and isinstance(_d, (int, float)) else f"  Cohen's d: {_d}\n")
        f.write(f"  Interpretation: {s3.get('interpretation')}\n")
        m_igl, m_non = s3.get("mean_igl"), s3.get("mean_non_igl")
        m_str = f"{m_igl:.2f}, Non-IGL: {m_non:.2f}" if m_igl is not None and m_non is not None else "N/A"
        f.write(f"  Mean ACS IGL: {m_str}\n\n")
        f.write("Deliverables: step1_acs_histogram.png, step5_acs_delta_vs_win_rate.png, acs_delta_winrate_table.csv\n")
    print(f"Summary written to {summary_path}")

    by_player.to_csv(os.path.join(OUTPUT_DIR, "acs_delta_winrate_table.csv"), index=False)
    print("Table saved: acs_delta_winrate_table.csv")

    # Print to console
    print("\n" + open(summary_path).read())
    return results, by_player


if __name__ == "__main__":
    main()
