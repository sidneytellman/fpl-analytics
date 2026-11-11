import requests
import pandas as pd
from datetime import date
from pathlib import Path

URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
FIXTURES_URL = "https://fantasy.premierleague.com/api/fixtures/?future=1"
DATA_DIR = Path(__file__).parent.parent / "data"

POSITIONS = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}


def download(url=URL):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def clean(data):
    players = pd.DataFrame(data["elements"])
    teams = {t["id"]: t["short_name"] for t in data["teams"]}
    players["team"] = players["team"].map(teams)
    players["position"] = players["element_type"].map(POSITIONS)

    cols = ["web_name", "team", "position", "now_cost", "total_points", "minutes",
            "goals_scored", "expected_goals", "expected_assists",
            "clean_sheets", "expected_goals_conceded",
            "selected_by_percent", "form"]
    players = players[cols]

    numeric = ["expected_goals", "expected_assists", "expected_goals_conceded",
               "selected_by_percent", "form"]
    players[numeric] = players[numeric].astype(float)
    players["now_cost"] = players["now_cost"] / 10
    return players


def clean_fixtures(fixtures, teams_data):
    """Turns the fixtures list into one row per team per match, with opponent and difficulty."""
    teams = {t["id"]: t["short_name"] for t in teams_data}
    rows = []
    for fixture in fixtures:
        if fixture["event"] is None:      # postponed/unscheduled matches have no gameweek yet
            continue
        home, away = teams[fixture["team_h"]], teams[fixture["team_a"]]
        rows.append({"gameweek": fixture["event"], "team": home, "opponent": away,
                     "home": True, "difficulty": fixture["team_h_difficulty"]})
        rows.append({"gameweek": fixture["event"], "team": away, "opponent": home,
                     "home": False, "difficulty": fixture["team_a_difficulty"]})
    return pd.DataFrame(rows)


def fetch_players():
    return clean(download())


def fetch_all():
    """Downloads players and upcoming fixtures. The team names come from the same player download."""
    data = download()
    fixtures = download(FIXTURES_URL)
    return clean(data), clean_fixtures(fixtures, data["teams"])


def save(players):
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / f"players_{date.today()}.csv"
    players.to_csv(path, index=False)
    print(f"Saved {len(players)} players to {path}")


def save_fixtures(fixtures):
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / f"fixtures_{date.today()}.csv"
    fixtures.to_csv(path, index=False)
    print(f"Saved {len(fixtures)} fixture rows to {path}")


if __name__ == "__main__":
    players, fixtures = fetch_all()
    save(players)
    save_fixtures(fixtures)