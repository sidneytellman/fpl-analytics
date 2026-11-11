import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fetch import clean, clean_fixtures

FAKE_DATA = {
    "teams": [{"id": 1, "short_name": "ARS"}, {"id": 2, "short_name": "CHE"}],
    "elements": [{
        "web_name": "Saka", "team": 1, "element_type": 3, "now_cost": 105,
        "total_points": 80, "minutes": 900, "goals_scored": 5,
        "expected_goals": "4.2", "expected_assists": "3.1",
        "clean_sheets": 4, "expected_goals_conceded": "8.7",
        "selected_by_percent": "35.5", "form": "6.0",
    }],
}

FAKE_FIXTURES = [
    {"event": 12, "team_h": 1, "team_a": 2, "team_h_difficulty": 4, "team_a_difficulty": 3},
    {"event": None, "team_h": 2, "team_a": 1, "team_h_difficulty": 4, "team_a_difficulty": 3},
]


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


def test_fixture_gives_one_row_per_team():
    fixtures = clean_fixtures(FAKE_FIXTURES, FAKE_DATA["teams"])
    assert len(fixtures) == 2   # the unscheduled match is skipped


def test_fixture_difficulty_is_from_each_teams_side():
    fixtures = clean_fixtures(FAKE_FIXTURES, FAKE_DATA["teams"]).set_index("team")
    assert fixtures.loc["ARS", "opponent"] == "CHE"
    assert fixtures.loc["ARS", "difficulty"] == 4
    assert bool(fixtures.loc["CHE", "home"]) is False