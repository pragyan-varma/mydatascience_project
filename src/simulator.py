"""Monte Carlo World Cup 2026 tournament simulator.

Live-aware and replayable: an `as_of` cutoff date locks every match that has
really been played on or before it, and simulates everything after. The Round-of-32
slot skeleton is reconstructed from the real fixtures, so the played portion of the
bracket reproduces reality exactly while the unplayed frontier is simulated. Pure
logic — no Streamlit imports.
"""

from collections import defaultdict
from datetime import date
from functools import lru_cache
from pathlib import Path

import pandas as pd

from predictor import get_team_rating, predict_match
import random

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
GROUP_MATCH_COUNT = 72  # 12 groups x 6 round-robin matches
SHOOTOUT_QUALITY_EXPONENT = 1.15

STAGES = ["Group", "R32", "R16", "QF", "SF", "Final", "Champion"]
STAGE_RANK = {s: i for i, s in enumerate(STAGES)}


@lru_cache(maxsize=1)
def _wc_matches() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "results.csv", parse_dates=["date"])
    wc = df[(df["tournament"] == "FIFA World Cup") & (df["date"] >= "2026-06-01")]
    return wc.sort_values("date").reset_index(drop=True)


@lru_cache(maxsize=1)
def build_groups() -> dict[str, list[str]]:
    """Reconstruct the 12 groups from the group-stage matches via connected components."""
    group_matches = _wc_matches().head(GROUP_MATCH_COUNT)
    adj = defaultdict(set)
    for r in group_matches.itertuples():
        adj[r.home_team].add(r.away_team)
        adj[r.away_team].add(r.home_team)

    seen, components = set(), []
    for team in adj:
        if team in seen:
            continue
        stack, comp = [team], set()
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            comp.add(x)
            stack.extend(adj[x] - seen)
        components.append(sorted(comp))

    components.sort()  # deterministic labelling A, B, C, ...
    return {chr(65 + i): teams for i, teams in enumerate(components)}


def _standings_from_points(points, gd, gf, teams, tiebreak_rating=True):
    """Rank teams by points, then goal diff / goals for (real data) or Elo (simulated)."""
    def key(t):
        if tiebreak_rating:
            return (points[t], get_team_rating(t))
        return (points[t], gd[t], gf[t])

    return sorted(teams, key=key, reverse=True)


@lru_cache(maxsize=1)
def _real_group_qualifiers() -> dict:
    """Real final group standings (all group matches are played), used only to label
    each real Round-of-32 participant with a slot code so we can reconstruct the
    bracket skeleton. Returns {team: slot_code} where slot_code is 'A1'/'A2'/... or
    ('3', rank) for the eight best third-placed teams.
    """
    groups = build_groups()
    gm = _wc_matches().head(GROUP_MATCH_COUNT)

    points = defaultdict(int)
    gd = defaultdict(int)
    gf = defaultdict(int)
    for r in gm.itertuples():
        if pd.isna(r.home_score):
            continue
        hs, as_ = int(r.home_score), int(r.away_score)
        gf[r.home_team] += hs
        gf[r.away_team] += as_
        gd[r.home_team] += hs - as_
        gd[r.away_team] += as_ - hs
        if hs > as_:
            points[r.home_team] += 3
        elif hs < as_:
            points[r.away_team] += 3
        else:
            points[r.home_team] += 1
            points[r.away_team] += 1

    slot = {}
    thirds = []
    for label, teams in groups.items():
        ranked = _standings_from_points(points, gd, gf, teams, tiebreak_rating=False)
        slot[ranked[0]] = f"{label}1"
        slot[ranked[1]] = f"{label}2"
        thirds.append(ranked[2])

    thirds_ranked = _standings_from_points(points, gd, gf, thirds, tiebreak_rating=False)
    for rank, team in enumerate(thirds_ranked[:8], start=1):
        slot[team] = ("3", rank)
    return slot


@lru_cache(maxsize=1)
def _knockout_rounds() -> list[pd.DataFrame]:
    """Split knockout matches into rounds by count: R32(16), R16(8), QF(4), SF(2), Final(1)."""
    ko = _wc_matches().iloc[GROUP_MATCH_COUNT:].reset_index(drop=True)
    sizes = [16, 8, 4, 2, 1]
    rounds, start = [], 0
    for size in sizes:
        rounds.append(ko.iloc[start:start + size])
        start += size
    return rounds


@lru_cache(maxsize=1)
def _r32_skeleton() -> list[tuple]:
    """The 16 Round-of-32 pairings expressed as (slot_code, slot_code), in fixture order."""
    real_slot = _real_group_qualifiers()
    r32 = _knockout_rounds()[0]
    skeleton = []
    for r in r32.itertuples():
        skeleton.append((real_slot[r.home_team], real_slot[r.away_team]))
    return skeleton


@lru_cache(maxsize=1)
def _real_results() -> dict:
    """{frozenset({team_a, team_b}): (winner, date)} for every knockout match with a score."""
    ko = _wc_matches().iloc[GROUP_MATCH_COUNT:]
    out = {}
    for r in ko.itertuples():
        if pd.isna(r.home_score):
            continue
        hs, as_ = int(r.home_score), int(r.away_score)
        winner = r.home_team if hs >= as_ else r.away_team  # scores already reflect real result
        out[frozenset({r.home_team, r.away_team})] = (winner, r.date.date())
    return out


def resolve_shootout(a: str, b: str) -> str:
    """Penalty-shootout winner, weighted slightly toward the stronger team."""
    ra = get_team_rating(a) ** SHOOTOUT_QUALITY_EXPONENT
    rb = get_team_rating(b) ** SHOOTOUT_QUALITY_EXPONENT
    return a if random.random() < ra / (ra + rb) else b


def simulate_match(a: str, b: str, knockout: bool = False) -> str | None:
    """Sample an outcome. Group games can draw (returns None); knockouts resolve to a winner."""
    p = predict_match(a, b, neutral=True)
    roll = random.random()
    if roll < p["a"]:
        return a
    if roll < p["a"] + p["b"]:
        return b
    return None if not knockout else resolve_shootout(a, b)


def _play_knockout(a: str, b: str, as_of: date) -> str:
    """Real winner if this exact pairing was played on/before as_of, else simulate."""
    real = _real_results().get(frozenset({a, b}))
    if real and real[1] <= as_of:
        return real[0]
    return simulate_match(a, b, knockout=True)


def _simulate_groups(as_of: date, rng_points):
    """Return {slot_code: team}: 12 winners, 12 runners-up, 8 best third-placed teams."""
    groups = build_groups()
    gm = _wc_matches().head(GROUP_MATCH_COUNT)

    points = defaultdict(int)
    gd = defaultdict(int)
    gf = defaultdict(int)
    for r in gm.itertuples():
        played = pd.notna(r.home_score) and r.date.date() <= as_of
        if played:
            hs, as_ = int(r.home_score), int(r.away_score)
            gf[r.home_team] += hs
            gf[r.away_team] += as_
            gd[r.home_team] += hs - as_
            gd[r.away_team] += as_ - hs
            outcome = "home" if hs > as_ else "away" if hs < as_ else "draw"
        else:
            w = simulate_match(r.home_team, r.away_team, knockout=False)
            outcome = "draw" if w is None else ("home" if w == r.home_team else "away")
        if outcome == "home":
            points[r.home_team] += 3
        elif outcome == "away":
            points[r.away_team] += 3
        else:
            points[r.home_team] += 1
            points[r.away_team] += 1

    slot, thirds = {}, []
    for label, teams in groups.items():
        ranked = _standings_from_points(points, gd, gf, teams, tiebreak_rating=True)
        slot[f"{label}1"] = ranked[0]
        slot[f"{label}2"] = ranked[1]
        thirds.append(ranked[2])
    thirds_ranked = _standings_from_points(points, gd, gf, thirds, tiebreak_rating=True)
    for rank, team in enumerate(thirds_ranked[:8], start=1):
        slot[("3", rank)] = team
    return slot


def simulate_tournament_once(as_of: date) -> dict[str, str]:
    """Play one full tournament from as_of. Returns {team: furthest stage reached}."""
    slot_to_team = _simulate_groups(as_of, None)
    reached = {team: "R32" for team in slot_to_team.values()}

    # Round of 32 from the real slot skeleton, then pair winners forward.
    current = [(slot_to_team[sa], slot_to_team[sb]) for sa, sb in _r32_skeleton()]
    for stage in ["R16", "QF", "SF", "Final"]:
        winners = []
        for a, b in current:
            w = _play_knockout(a, b, as_of)
            reached[w] = stage
            winners.append(w)
        current = [(winners[i], winners[i + 1]) for i in range(0, len(winners), 2)]

    champion = current[0][0]
    reached[champion] = "Champion"
    return reached


def run_monte_carlo(n_iterations: int, as_of: date | None = None, progress_cb=None) -> pd.DataFrame:
    """Aggregate n simulations into per-team advancement probabilities."""
    if as_of is None:
        as_of = date.today()

    advanced = defaultdict(int)   # reached R32 (qualified from group)
    semifinal = defaultdict(int)  # reached SF or beyond
    champion = defaultdict(int)
    all_teams = set(t for g in build_groups().values() for t in g)

    for i in range(n_iterations):
        reached = simulate_tournament_once(as_of)
        for team, stage in reached.items():
            if STAGE_RANK[stage] >= STAGE_RANK["R32"]:
                advanced[team] += 1
            if STAGE_RANK[stage] >= STAGE_RANK["SF"]:
                semifinal[team] += 1
            if stage == "Champion":
                champion[team] += 1
        if progress_cb and (i + 1) % max(1, n_iterations // 100) == 0:
            progress_cb((i + 1) / n_iterations)

    rows = []
    for team in all_teams:
        rows.append({
            "Team": team,
            "Advance %": 100 * advanced[team] / n_iterations,
            "Semifinal %": 100 * semifinal[team] / n_iterations,
            "Title %": 100 * champion[team] / n_iterations,
        })
    df = pd.DataFrame(rows).sort_values("Title %", ascending=False).reset_index(drop=True)
    return df


if __name__ == "__main__":
    groups = build_groups()
    print(f"Groups: {len(groups)} | teams: {sum(len(v) for v in groups.values())}")
    print(f"R32 skeleton pairs: {len(_r32_skeleton())}")
    print("Running 200 simulations from today...")
    result = run_monte_carlo(200)
    print(result.head(12).to_string(index=False))
