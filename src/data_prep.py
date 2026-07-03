from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def load_clean_results() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (played, upcoming) match dataframes.

    `played` has a `result` column (home/draw/away), resolved through penalty
    shootouts for knockout matches that finished level.
    `upcoming` is every fixture with no score recorded yet.
    """
    results = pd.read_csv(RAW_DIR / "results.csv", parse_dates=["date"])
    shootouts = pd.read_csv(RAW_DIR / "shootouts.csv", parse_dates=["date"])

    results = results.merge(
        shootouts[["date", "home_team", "away_team", "winner"]],
        on=["date", "home_team", "away_team"],
        how="left",
    ).rename(columns={"winner": "shootout_winner"})

    has_score = results["home_score"].notna() & results["away_score"].notna()
    played = results[has_score].copy()
    upcoming = results[~has_score].copy()

    def outcome(row):
        if row.home_score > row.away_score:
            return "home"
        if row.home_score < row.away_score:
            return "away"
        if pd.notna(row.shootout_winner):
            return "home" if row.shootout_winner == row.home_team else "away"
        return "draw"

    played["result"] = played.apply(outcome, axis=1)
    return played, upcoming


if __name__ == "__main__":
    played, upcoming = load_clean_results()
    print(f"Played matches: {len(played)}")
    print(f"Upcoming/unplayed fixtures: {len(upcoming)}")
    print(played["result"].value_counts())
