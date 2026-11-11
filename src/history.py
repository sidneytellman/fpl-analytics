"""Per-player season history, previous seasons and a simple points projection."""

import json
import time
from datetime import date
from pathlib import Path
from statistics import mean

import requests

from fetch import POSITIONS

SUMMARY_URL = "https://fantasy.premierleague.com/api/element-summary/{}/"
DOCS_DIR = Path(__file__).parent.parent / "docs"

# How much easier/harder each FPL difficulty rating (1-5) makes a fixture
DIFFICULTY_FACTOR = {1: 1.25, 2: 1.12, 3: 1.0, 4: 0.88, 5: 0.76}


def to_float(value):
    """The API sends some numbers as strings, and sometimes as None."""
    return float(value) if value not in (None, "") else 0.0


def clean_summary(summary, teams):
    """Turns one element-summary response into history, past seasons and upcoming fixtures."""
    history = [{
        "gw": h["round"], "opp": teams[h["opponent_team"]], "home": h["was_home"],
        "pts": h["total_points"], "min": h["minutes"],
        "goals": h["goals_scored"], "assists": h["assists"],
        "xg": to_float(h["expected_goals"]), "xa": to_float(h["expected_assists"]),
        "price": h["value"] / 10,
    } for h in summary["history"]]

    past = [{
        "season": p["season_name"], "pts": p["total_points"], "min": p["minutes"],
        "goals": p["goals_scored"], "assists": p["assists"],
    } for p in summary["history_past"]]

    upcoming = []
    for fixture in summary["fixtures"]:
        if fixture["event"] is None:          # postponed, no gameweek yet
            continue
        opponent_id = fixture["team_a"] if fixture["is_home"] else fixture["team_h"]
        upcoming.append({"gw": fixture["event"], "opp": teams[opponent_id],
                         "home": fixture["is_home"], "difficulty": fixture["difficulty"]})
    return history, past, upcoming


def project_points(history, past, upcoming, n=5):
    """Simple projection for the next n fixtures.

    Base = 50% recent form (last 5 matches played) + 30% season average
         + 20% last season's points per 90, scaled to the minutes they play now.
    Each fixture then multiplies the base by its difficulty factor.
    """
    played = [h for h in history if h["min"] > 0]
    if not played:
        return []

    recent = played[-5:]
    recent_ppg = mean(h["pts"] for h in recent)
    season_ppg = mean(h["pts"] for h in played)
    recent_minutes = mean(h["min"] for h in recent)

    last_season = past[-1] if past else None
    if last_season and last_season["min"] >= 900:
        prior = last_season["pts"] / last_season["min"] * recent_minutes
    else:
        prior = season_ppg                    # no reliable last season: lean on this season

    base = 0.5 * recent_ppg + 0.3 * season_ppg + 0.2 * prior
    return [{**fixture, "pts": round(base * DIFFICULTY_FACTOR[fixture["difficulty"]], 1)}
            for fixture in upcoming[:n]]


def build_profile(player, summary, teams):
    """Combines a bootstrap player entry and their element-summary into one profile."""
    history, past, upcoming = clean_summary(summary, teams)
    return {
        "id": player["id"], "name": player["web_name"], "team": teams[player["team"]],
        "position": POSITIONS[player["element_type"]], "price": player["now_cost"] / 10,
        "total_points": player["total_points"], "form": to_float(player["form"]),
        "ownership": to_float(player["selected_by_percent"]),
        "fpl_expected_next": to_float(player.get("ep_next")),
        "history": history, "past": past,
        "projection": project_points(history, past, upcoming),
    }


def build_player_profiles(data, min_minutes=1, pause=0.2):
    """Downloads the history for every player who has played this season."""
    teams = {t["id"]: t["short_name"] for t in data["teams"]}
    players = [p for p in data["elements"] if p["minutes"] >= min_minutes]
    session = requests.Session()
    profiles = []

    for count, player in enumerate(players, start=1):
        try:
            response = session.get(SUMMARY_URL.format(player["id"]), timeout=10)
            response.raise_for_status()
        except requests.RequestException as error:
            print(f"  Skipping {player['web_name']}: {error}")
            continue
        profiles.append(build_profile(player, response.json(), teams))
        if count % 50 == 0:
            print(f"  {count}/{len(players)} players")
        time.sleep(pause)                     # be polite to the FPL API
    return profiles


def save_profiles(profiles):
    path = DOCS_DIR / "data" / "players.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"updated": str(date.today()), "players": profiles}
    path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"Saved {len(profiles)} player profiles to {path}")