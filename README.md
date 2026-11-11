# FPL Analytics

![Tests](https://github.com/sidneytellman/fpl-analytics/actions/workflows/tests.yml/badge.svg)
![Weekly update](https://github.com/sidneytellman/fpl-analytics/actions/workflows/weekly.yml/badge.svg)

Automated Fantasy Premier League analytics. Every week, a GitHub Actions
workflow fetches fresh player and fixture data from the FPL API, generates
charts with Python, and publishes them to a live site.

**Live site:** https://sidneytellman.github.io/fpl-analytics/

The charts on the live site are interactive: hover over any player to see
their name, team, price and stats, filter by position, and drag to zoom in.
You can also search for any player to see their season so far and a projection
for their next five fixtures.

![xG vs xA chart](docs/xg_vs_xa.png)

## How it works

```
FPL API → fetch.py / history.py → data/*.csv + docs/data/players.json
        → charts.py → docs/*.html + docs/*.png → GitHub Pages
                 ↑
     GitHub Actions (every Tuesday 06:00 UTC)
```

1. `src/fetch.py` pulls all player data and upcoming fixtures from the FPL API
   and saves them as dated CSV files in `data/`.
2. `src/history.py` downloads each player's gameweek history and previous
   seasons, calculates a points projection, and saves everything to
   `docs/data/players.json` for the player search page.
3. `src/charts.py` builds the charts: interactive HTML with Plotly for the live
   site, and static PNG images with matplotlib for this README.
4. `src/main.py` runs all of the above in order.
5. `.github/workflows/weekly.yml` runs the pipeline on a schedule and commits
   the new data and charts back to the repo.
6. GitHub Pages serves the `docs/` folder as the public site.

## Charts

All scatter charts include players with 450+ minutes. In each chart the top
players are highlighted in red and labelled, everyone else is shown in blue,
and buttons let you filter by position.

- **Who's creating and finishing the most?** Expected goals (xG) vs expected
  assists (xA). Dashed lines mark the top 10% for each.
- **Best value in FPL right now.** Total points vs price, highlighting points
  per million.
- **Best value by position.** The top 10 points per million for goalkeepers,
  defenders, midfielders and forwards.
- **Who's beating their xG?** Goals scored vs expected goals. Players above
  the diagonal are scoring more than their chances suggest.
- **Differentials.** Form vs ownership, highlighting in-form players owned by
  fewer than 10% of managers.
- **Defensive returns.** Clean sheets vs expected goals conceded per 90 for
  goalkeepers and defenders.
- **Fixture difficulty.** Every team's next five fixtures, coloured by FPL's
  difficulty rating, with the easiest run at the top.
- **Trends over time.** Total points, form, price and ownership for the current
  top 10, built from the weekly data files.

## Player search

`docs/player.html` lets you search for any player who has played this season
and shows:

- points per gameweek, cumulative points, and xG/xA per gameweek
- previous Premier League seasons, with points per 90
- a projection for the next five fixtures, next to FPL's own expected points

The projection is a simple, transparent model: 50% recent form (last five
matches played), 30% this season's average and 20% last season's points per
90, scaled to the minutes the player gets now. Each fixture then adjusts that
up or down by its difficulty rating. It does not know about injuries,
rotation or penalties.

## Run it locally

```
pip install -r requirements.txt
python src/main.py
```

Fetching player histories makes one request per player, so a full run takes a
few minutes. The charts and data are saved to `docs/`. The player search page
reads a JSON file, so view the site through a local web server rather than
opening the file directly:

```
python -m http.server 8000 -d docs
```

Then open http://localhost:8000.

## Engineering

- **Continuous integration.** Every push and pull request runs
  `.github/workflows/tests.yml`: linting with ruff, then the test suite.
- **Tests.** `pytest` covers the data cleaning (`test_fetch.py`), the chart