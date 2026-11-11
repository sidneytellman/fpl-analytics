import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from history import clean_summary, project_points  # noqa: E402

TEAMS = {1: "ARS", 2: "CHE", 3: "LIV"}

FAKE_SUMMARY = {
    "history": [
        {"round": 1, "opponent_team": 2, "was_home": True, "total_points": 9, "minutes": 90,
         "goals_scored": 1, "assists": 1, "expected_goals": "0.65", "expected_assists": "0.30", "value": 100},
        {"round": 2, "opponent_team": 3, "was_home": False, "total_points": 0, "minutes": 0,
         "goals_scored": 0, "assists": 0, "expected_goals": "0.00", "expected_assists": "0.00", "value": 100},
        {"round": 3, "opponent_team": 2, "was_home": False, "total_points": 3, "minutes": 90,
         "goals_scored": 0, "assists": 0, "expected_goals": "0.20", "expected_assists": "0.10", "value": 101},
    ],
    "history_past": [
        {"season_name": "2025/26", "total_points": 180, "minutes": 2700, "goals_scored": 12, "assists": 8},
    ],
    "fixtures": [
        {"event": 4, "is_home": True, "team_h": 1, "team_a": 3, "difficulty": 4},
        {"event": None, "is_home": False, "team_h": 2, "team_a": 1, "difficulty": 3},
        {"event": 5, "is_home": False, "team_h": 2, "team_a": 1, "difficulty": 2},
    ],
}


def test_history_is_cleaned():
    history, _, _ = clean_summary(FAKE_SUMMARY, TEAMS)
    first = history[0]
    assert first["opp"] == "CHE"
    assert first["xg"] == 0.65            # string from the API becomes a number
    assert first["price"] == 10.0         # 100 becomes £10.0m


def test_upcoming_fixtures_have_the_right_opponent():
    _, _, upcoming = clean_summary(FAKE_SUMMARY, TEAMS)
    assert [f["opp"] for f in upcoming] == ["LIV", "CHE"]   # the unscheduled match is skipped
    assert upcoming[0]["home"] is True


def test_projection_blends_form_season_and_last_season():
    history, past, upcoming = clean_summary(FAKE_SUMMARY, TEAMS)
    projection = project_points(history, past, upcoming)
    # Played matches: 9 and 3 points (the 0-minute match is ignored)
    # recent = 6.0, season = 6.0, last season = 180 / 2700 * 90 minutes = 6.0
    # base = 6.0, so difficulty 4 gives 6.0 * 0.88 and difficulty 2 gives 6.0 * 1.12
    assert [f["pts"] for f in projection] == [pytest.approx(5.3), pytest.approx(6.7)]


def test_projection_is_empty_for_a_player_who_has_not_played():
    history = [{"gw": 1, "opp": "CHE", "home": True, "pts": 0, "min": 0}]
    assert project_points(history, [], [{"gw": 2, "difficulty": 3}]) == []