"""Historical World Cup aggregations for the Insights Vault tab.

Derived from the raw results feed (no explicit stage column exists), so metrics
are the robustly-derivable ones: appearances, matches, wins, goals, win rate.
"""

from functools import lru_cache
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


@lru_cache(maxsize=1)
def _world_cup_matches() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "results.csv", parse_dates=["date"])
    wc = df[(df["tournament"] == "FIFA World Cup") & df["home_score"].notna()].copy()
    wc["year"] = wc["date"].dt.year
    return wc


def wc_history(team: str) -> dict:
    """Aggregate World Cup finals record for one nation."""
    wc = _world_cup_matches()
    games = wc[(wc["home_team"] == team) | (wc["away_team"] == team)]
    if games.empty:
        return {"appearances": 0, "matches": 0, "wins": 0, "draws": 0,
                "losses": 0, "goals_for": 0, "win_rate": 0.0}

    wins = draws = losses = gf = ga = 0
    for r in games.itertuples():
        is_home = r.home_team == team
        team_goals = r.home_score if is_home else r.away_score
        opp_goals = r.away_score if is_home else r.home_score
        gf += int(team_goals)
        ga += int(opp_goals)
        if team_goals > opp_goals:
            wins += 1
        elif team_goals < opp_goals:
            losses += 1
        else:
            draws += 1

    matches = len(games)
    return {
        "appearances": games["year"].nunique(),
        "matches": matches,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_for": gf,
        "goals_against": ga,
        "win_rate": 100 * wins / matches if matches else 0.0,
    }


def wc_goals_by_year(team: str) -> pd.DataFrame:
    """Goals scored by the team in each World Cup edition (for a trend chart)."""
    wc = _world_cup_matches()
    games = wc[(wc["home_team"] == team) | (wc["away_team"] == team)]
    rows = []
    for year, chunk in games.groupby("year"):
        goals = 0
        for r in chunk.itertuples():
            goals += int(r.home_score if r.home_team == team else r.away_score)
        rows.append({"year": year, "goals": goals})
    return pd.DataFrame(rows)
