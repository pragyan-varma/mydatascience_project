from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, log_loss

from data_prep import load_clean_results
from elo import compute_elo_features

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
FEATURE_COLS = ["home_elo_pre", "away_elo_pre", "neutral_int"]


def train() -> None:
    played, _ = load_clean_results()
    played, ratings = compute_elo_features(played)
    played["neutral_int"] = played["neutral"].astype(int)

    features = played[FEATURE_COLS]
    target = played["result"]

    # Time-based holdout (last 10% of matches chronologically) just to sanity-check accuracy
    split_idx = int(len(played) * 0.9)
    model = RandomForestClassifier(n_estimators=300, max_depth=8, min_samples_leaf=20, random_state=42)
    model.fit(features.iloc[:split_idx], target.iloc[:split_idx])
    preds = model.predict(features.iloc[split_idx:])
    proba = model.predict_proba(features.iloc[split_idx:])
    print(f"Holdout accuracy: {accuracy_score(target.iloc[split_idx:], preds):.3f}")
    print(f"Holdout log loss: {log_loss(target.iloc[split_idx:], proba, labels=model.classes_):.3f}")

    # Refit on all available history for the model we actually deploy
    model.fit(features, target)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"model": model, "elo_ratings": ratings, "classes": list(model.classes_)},
        MODELS_DIR / "match_predictor.pkl",
    )
    print(f"Saved model + ratings for {len(ratings)} teams -> {MODELS_DIR / 'match_predictor.pkl'}")


if __name__ == "__main__":
    train()
