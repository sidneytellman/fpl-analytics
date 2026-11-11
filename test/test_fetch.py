import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fetch import clean

FAKE_DATA = {
    "teams": [{"id": 1, "short_name": "ARS"}],
    "elements": [{
        "web_name": "Saka", "team": 1, "element_type": 3, "now_cost": 105,
        "total_points": 80, "minutes": 900, "goals_scored": 5,
        "expected_goals": "4.2", "expected_assists": "3.1",
        "clean_sheets": 4, "expected_goals_conceded": "8.7",
        "selected_by_percent": "35.5", "form": "6.0",
    }],
}


def test_price_is_converted_to_millions():
    players = clean(FAKE_DATA)
    assert players["now_cost"].iloc[0] == 10.5


def test_team_id_becomes_name():
    players = clean(FAKE_DATA)
    assert players["team"].iloc[0] == "ARS"


def test_xg_is_a_number():
    players = clean(FAKE_DATA)
    assert players["expected_goals"].iloc[0] == 4.2


def test_position_id_becomes_name():
    players = clean(FAKE_DATA)
    assert players["position"].iloc[0] == "MID"


def test_xgc_is_a_number():
    players = clean(FAKE_DATA)
    assert players["expected_goals_conceded"].iloc[0] == 8.7