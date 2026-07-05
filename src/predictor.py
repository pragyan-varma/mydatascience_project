"""Clean prediction interface over the trained model.

Every tab and the Monte Carlo simulator call into here, so the predictive logic
lives in exactly one place. Wraps the artifact produced by train_model.py.
"""

from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from data_prep import load_clean_results
from elo import INITIAL_ELO
from train_model import FEATURE_COLS

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


@lru_cache(maxsize=1)
def load_predictor() -> dict:
    """Loads the trained model + Elo ratings once and caches it."""
    return joblib.load(MODELS_DIR / "match_predictor.pkl")


@lru_cache(maxsize=1)
def _played() -> pd.DataFrame:
    played, _ = load_clean_results()
    return played


def list_teams() -> list[str]:
    """Sorted team names the model knows about (has an Elo rating for)."""
    return sorted(load_predictor()["elo_ratings"].keys())


def get_team_rating(team: str) -> float:
    return load_predictor()["elo_ratings"].get(team, INITIAL_ELO)


def get_recent_form(team: str, n: int = 10) -> dict:
    """Points (3/1/0) and record over the team's last n played matches."""
    played = _played()
    mask = (played["home_team"] == team) | (played["away_team"] == team)
    games = played[mask].sort_values("date").tail(n)

    wins = draws = losses = points = 0
    for row in games.itertuples():
        is_home = row.home_team == team
        if row.result == "draw":
            draws += 1
            points += 1
        elif (row.result == "home") == is_home:
            wins += 1
            points += 3
        else:
            losses += 1
    return {"points": points, "played": len(games), "wins": wins, "draws": draws, "losses": losses}


@lru_cache(maxsize=8192)
def predict_match(team_a: str, team_b: str, neutral: bool = True) -> dict:
    """Win/draw/win probabilities for team_a vs team_b.

    team_a is treated as the home side (matters only when neutral is False).
    Returns {"a": p_a_win, "draw": p_draw, "b": p_b_win}, summing to 1.
    Cached: the Monte Carlo simulator hits the same matchups thousands of times,
    and the model is deterministic. Callers must not mutate the returned dict.
    """
    predictor = load_predictor()
    model = predictor["model"]
    ratings = predictor["elo_ratings"]

    row = pd.DataFrame(
        [[ratings.get(team_a, INITIAL_ELO), ratings.get(team_b, INITIAL_ELO), int(neutral)]],
        columns=FEATURE_COLS,
    )
    proba = model.predict_proba(row)[0]
    by_class = dict(zip(model.classes_, proba))
    return {
        "a": float(by_class.get("home", 0.0)),
        "draw": float(by_class.get("draw", 0.0)),
        "b": float(by_class.get("away", 0.0)),
    }


if __name__ == "__main__":
    for a, b in [("Brazil", "Norway"), ("France", "Paraguay"), ("Spain", "Austria")]:
        p = predict_match(a, b)
        print(f"{a} vs {b}: {p}  (sum={sum(p.values()):.3f})")
        print(f"   {a} rating={get_team_rating(a):.0f} form={get_recent_form(a)}")
