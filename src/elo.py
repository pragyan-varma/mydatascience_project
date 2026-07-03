import pandas as pd

INITIAL_ELO = 1500.0
HOME_ADVANTAGE = 100.0

# Bigger tournaments move ratings more, per the standard world-football-elo method
TOURNAMENT_K = {
    "FIFA World Cup": 60,
    "FIFA World Cup qualification": 40,
    "UEFA Euro": 60,
    "Copa América": 60,
}
DEFAULT_K = 30


def _k_factor(tournament: str) -> int:
    return TOURNAMENT_K.get(tournament, DEFAULT_K)


def _goal_diff_multiplier(goal_diff: int) -> float:
    if goal_diff <= 1:
        return 1.0
    if goal_diff == 2:
        return 1.5
    return (11 + goal_diff) / 8


def compute_elo_features(played: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    """Walks matches in date order, recording each team's PRE-match rating
    (so training features never see the outcome they're predicting), then
    updates ratings using the actual result. Returns the enriched dataframe
    plus the final rating for every team as of the most recent match.
    """
    played = played.sort_values("date").reset_index(drop=True)
    ratings: dict[str, float] = {}
    home_elo_pre = []
    away_elo_pre = []

    for row in played.itertuples():
        r_home = ratings.get(row.home_team, INITIAL_ELO)
        r_away = ratings.get(row.away_team, INITIAL_ELO)
        home_elo_pre.append(r_home)
        away_elo_pre.append(r_away)

        advantage = 0.0 if row.neutral else HOME_ADVANTAGE
        expected_home = 1 / (10 ** (-(r_home + advantage - r_away) / 400) + 1)

        if row.result == "home":
            score_home = 1.0
        elif row.result == "away":
            score_home = 0.0
        else:
            score_home = 0.5

        goal_diff = abs(int(row.home_score) - int(row.away_score))
        k = _k_factor(row.tournament) * _goal_diff_multiplier(goal_diff)
        change = k * (score_home - expected_home)

        ratings[row.home_team] = r_home + change
        ratings[row.away_team] = r_away - change

    played = played.copy()
    played["home_elo_pre"] = home_elo_pre
    played["away_elo_pre"] = away_elo_pre
    return played, ratings
