import requests
import pandas as pd
from datetime import date
from pathlib import Path

URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
DATA_DIR = Path(__file__).parent.parent / "data"

def fetch_players():
    response = requests.get(URL, timeout=10)
    response.raise_for_status()          # crash clearly if the API fails
    data = response.json()

    players = pd.DataFrame(data["elements"])
    teams = {t["id"]: t["short_name"] for t in data["teams"]}
    players["team"] = players["team"].map(teams)

    cols = ["web_name", "team", "now_cost", "total_points", "minutes",
            "expected_goals", "expected_assists", "selected_by_percent", "form"]
    players = players[cols]

    numeric = ["expected_goals", "expected_assists", "selected_by_percent", "form"]
    players[numeric] = players[numeric].astype(float)
    players["now_cost"] = players["now_cost"] / 10   # 55 -> 5.5m
    return players

def save(players):
    path = DATA_DIR / f"players_{date.today()}.csv"
    DATA_DIR.mkdir(exist_ok=True)
    players.to_csv(path, index=False)
    print(f"Saved {len(players)} players to {path}")

if __name__ == "__main__":
    save(fetch_players())