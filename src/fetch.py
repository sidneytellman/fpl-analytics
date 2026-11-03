import requests
import pandas as pd
from datetime import date
from pathlib import Path

URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
DATA_DIR = Path(__file__).parent.parent / "data"


def download():
    response = requests.get(URL, timeout=10)
    response.raise_for_status()
    return response.json()


def clean(data):
    players = pd.DataFrame(data["elements"])
    teams = {t["id"]: t["short_name"] for t in data["teams"]}
    players["team"] = players["team"].map(teams)

    cols = ["web_name", "team", "now_cost", "total_points", "minutes",
            "goals_scored", "expected_goals", "expected_assists",
            "selected_by_percent", "form"]
    players = players[cols]

    numeric = ["expected_goals", "expected_assists", "selected_by_percent", "form"]
    players[numeric] = players[numeric].astype(float)
    players["now_cost"] = players["now_cost"] / 10
    return players


def fetch_players():
    return clean(download())


def save(players):
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / f"players_{date.today()}.csv"
    players.to_csv(path, index=False)
    print(f"Saved {len(players)} players to {path}")


if __name__ == "__main__":
    save(fetch_players())