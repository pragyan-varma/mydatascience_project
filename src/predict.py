from pathlib import Path

import joblib
import pandas as pd

from data_prep import load_clean_results
from elo import INITIAL_ELO
from train_model import FEATURE_COLS

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


def predict_upcoming() -> pd.DataFrame:
    predictor = joblib.load(MODELS_DIR / "match_predictor.pkl")
    model = predictor["model"]
    ratings = predictor["elo_ratings"]
    classes = predictor["classes"]

    _, upcoming = load_clean_results()
    upcoming = upcoming.copy()
    upcoming["home_elo_pre"] = upcoming["home_team"].map(lambda t: ratings.get(t, INITIAL_ELO))
    upcoming["away_elo_pre"] = upcoming["away_team"].map(lambda t: ratings.get(t, INITIAL_ELO))
    upcoming["neutral_int"] = upcoming["neutral"].astype(int)

    proba = model.predict_proba(upcoming[FEATURE_COLS])
    for i, cls in enumerate(classes):
        upcoming[f"prob_{cls}"] = proba[:, i]

    cols = ["date", "home_team", "away_team", "city", "country"] + [f"prob_{c}" for c in classes]
    return upcoming[cols].sort_values("date").reset_index(drop=True)


if __name__ == "__main__":
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    print(predict_upcoming())
