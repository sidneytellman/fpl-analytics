import re
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"

BG = "#f4f4f2"
GREY = "#bdbdbd"
RED = "#e63946"
BLUE = "#5b8fd1"


def latest_file():
    """Returns the path to the newest players_*.csv in data/."""
    files = sorted(DATA_DIR.glob("players_*.csv"))
    if not files:
        raise FileNotFoundError("No data yet - run src/fetch.py first")
    return files[-1]


def load_latest():
    path = latest_file()
    print(f"Using {path.name}")
    return pd.read_csv(path)


def load_latest_fixtures():
    """Returns the newest fixtures_*.csv, or None if there is none yet."""
    files = sorted(DATA_DIR.glob("fixtures_*.csv"))
    if not files:
        return None
    print(f"Using {files[-1].name}")
    return pd.read_csv(files[-1])


def update_last_updated():
    """Writes the date of the latest data file into the 'last updated' line in docs/index.html."""
    data_date = latest_file().stem.replace("players_", "")        # e.g. "2026-11-11"
    pretty_date = datetime.strptime(data_date, "%Y-%m-%d").strftime("%d %b %Y")
    index_path = DOCS_DIR / "index.html"
    html = index_path.read_text(encoding="utf-8")
    html = re.sub(r'(<span id="last-updated">).*?(</span>)',
                  rf"\g<1>{pretty_date}\g<2>", html)
    index_path.write_text(html, encoding="utf-8")


# ---------------------------------------------------------------------------
# Static PNG charts (matplotlib) - used in the README
# ---------------------------------------------------------------------------

def style(ax, fig, title, subtitle):
    fig.set_facecolor(BG)
    ax.set_facecolor(BG)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(True, ls=":", color="#999", alpha=0.6)
    ax.tick_params(length=0)
    fig.text(0.06, 0.95, title, fontsize=16, fontweight="bold")
    fig.text(0.06, 0.915, subtitle, fontsize=10, color="#888")


def label_top(ax, df, x, y, n=10, by=None):
    from adjustText import adjust_text
    import matplotlib.patheffects as pe

    top = df.nlargest(n, by or y)
    texts = [
        ax.text(getattr(r, x), getattr(r, y), r.web_name,
                fontsize=8, fontweight="bold", zorder=5,
                path_effects=[pe.withStroke(linewidth=3, foreground=BG)])
        for r in top.itertuples()
    ]
    adjust_text(
        texts, ax=ax,
        x=top[x].values, y=top[y].values,
        arrowprops=dict(arrowstyle="-", color="#555", lw=0.6),
        expand=(1.3, 1.6),
    )


def xg_vs_xa(df):
    df = df[df["minutes"] >= 450].copy()
    df["xgi"] = df["expected_goals"] + df["expected_assists"]

    fig, ax = plt.subplots(figsize=(9, 8))
    ax.scatter(df["expected_goals"], df["expected_assists"],
               s=90, c=GREY, edgecolors="#555", linewidths=0.5, alpha=0.8)

    top = df.nlargest(1, "xgi")
    ax.scatter(top["expected_goals"], top["expected_assists"],
               s=160, c=RED, zorder=3)

    ax.axvline(df["expected_goals"].quantile(0.9), ls="--", color="#333", lw=1)
    ax.axhline(df["expected_assists"].quantile(0.9), ls="--", color="#333", lw=1)

    label_top(ax, df, "expected_goals", "expected_assists", n=12, by="xgi")
    ax.set_xlabel("Expected goals (xG)")
    ax.set_ylabel("Expected assists (xA)")
    style(ax, fig, "Who's creating and finishing the most?",
          "FPL xG vs xA | players with 450+ minutes")
    plt.subplots_adjust(top=0.88)
    fig.savefig(DOCS_DIR / "xg_vs_xa.png", dpi=150, facecolor=BG)
    plt.close(fig)


def value_chart(df):
    df = df[df["minutes"] >= 450].copy()
    df["pts_per_m"] = df["total_points"] / df["now_cost"]

    fig, ax = plt.subplots(figsize=(9, 8))
    ax.scatter(df["now_cost"], df["total_points"],
               s=90, c=GREY, edgecolors="#555", linewidths=0.5, alpha=0.8)

    best = df.nlargest(1, "pts_per_m")
    ax.scatter(best["now_cost"], best["total_points"],
               s=160, c=RED, zorder=3)

    label_top(ax, df, "now_cost", "total_points", n=12, by="pts_per_m")
    ax.set_xlabel("Price (£m)")
    ax.set_ylabel("Total points")
    style(ax, fig, "Best value in FPL right now",
          "Total points vs price | labels = top 12 points per million")
    plt.subplots_adjust(top=0.88)
    fig.savefig(DOCS_DIR / "value.png", dpi=150, facecolor=BG)
    plt.close(fig)


def goals_vs_xg(df):
    df = df[df["minutes"] >= 450].copy()
    df["diff"] = df["goals_scored"] - df["expected_goals"]

    fig, ax = plt.subplots(figsize=(9, 8))
    ax.scatter(df["expected_goals"], df["goals_scored"],
               s=90, c=GREY, edgecolors="#555", linewidths=0.5, alpha=0.8)

    # Diagonal line: goals = xG
    top = max(df["expected_goals"].max(), df["goals_scored"].max()) + 1
    ax.plot([0, top], [0, top], ls="--", color="#333", lw=1)

    # Highlight biggest overperformer in red
    best = df.nlargest(1, "diff")
    ax.scatter(best["expected_goals"], best["goals_scored"], s=160, c=RED, zorder=3)

    # Label the 12 biggest over- and underperformers
    df["abs_diff"] = df["diff"].abs()
    label_top(ax, df, "expected_goals", "goals_scored", n=12, by="abs_diff")

    ax.set_xlabel("Expected goals (xG)")
    ax.set_ylabel("Goals scored")
    style(ax, fig, "Who's beating their xG?",
          "Above the line = scoring more than expected | 450+ minutes")
    plt.subplots_adjust(top=0.88)
    fig.savefig(DOCS_DIR / "goals_vs_xg.png", dpi=150, facecolor=BG)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Interactive HTML charts (Plotly) - used on the GitHub Pages site
# ---------------------------------------------------------------------------

def prepare(df):
    """Filters to 450+ minutes and adds the calculated columns used by the charts."""
    df = df[df["minutes"] >= 450].copy()
    df["xgi"] = df["expected_goals"] + df["expected_assists"]
    df["pts_per_m"] = df["total_points"] / df["now_cost"]
    df["diff"] = df["goals_scored"] - df["expected_goals"]
    df["abs_diff"] = df["diff"].abs()
    # Form among players owned by fewer than 10% of managers (others get -1 so they never rank)
    df["differential_score"] = df["form"].where(df["selected_by_percent"] < 10, -1)
    df["xgc_per_90"] = df["expected_goals_conceded"] / df["minutes"] * 90
    df["cs_per_m"] = df["clean_sheets"] / df["now_cost"]
    return df


def label_annotations(df, top, x, y, plot_width=700, plot_height=520):
    """Returns label annotations with leader lines, nudging each one until it no longer overlaps another."""
    x_min, x_max = df[x].min(), df[x].max()
    y_min, y_max = df[y].min(), df[y].max()
    px_per_x = plot_width / ((x_max - x_min) or 1)
    px_per_y = plot_height / ((y_max - y_min) or 1)

    # Pixel offsets to try, in order: above, below, diagonals, then further out
    offsets = [(0, -24), (0, 24), (45, -20), (-45, -20), (45, 20), (-45, 20),
               (0, -48), (0, 48), (70, 0), (-70, 0)]
    placed = []
    annotations = []

    for row in top.sort_values(y, ascending=False).itertuples():
        name = row.web_name
        dot_x = (getattr(row, x) - x_min) * px_per_x
        dot_y = (y_max - getattr(row, y)) * px_per_y   # screen y grows downwards
        width, height = len(name) * 7 + 8, 16

        for offset_x, offset_y in offsets:
            box = (dot_x + offset_x - width / 2, dot_y + offset_y - height / 2,
                   dot_x + offset_x + width / 2, dot_y + offset_y + height / 2)
            if not any(box[0] < b[2] and box[2] > b[0] and box[1] < b[3] and box[3] > b[1]
                       for b in placed):
                break
        placed.append(box)

        annotations.append(dict(
            x=getattr(row, x), y=getattr(row, y), text=name,
            ax=offset_x, ay=offset_y,
            showarrow=True, arrowhead=0, arrowwidth=0.7, arrowcolor="#555",
            font=dict(size=11, color="#222"),
            bgcolor="rgba(244, 244, 242, 0.6)", borderpad=2,
        ))
    return annotations


HOVER_COLS = ["web_name", "minutes", "team", "now_cost"]


def split_groups(df, x, y, rank_by, n):
    """Splits players into the rest (blue), top n (red) and the single best, plus their labels."""
    top = df.nlargest(n, rank_by)
    best = df.nlargest(1, rank_by)
    rest = df.drop(top.index)
    groups = [rest, top, best]
    data = {
        "x": [g[x].tolist() for g in groups],
        "y": [g[y].tolist() for g in groups],
        "customdata": [g[HOVER_COLS].values.tolist() for g in groups],
    }
    return data, label_annotations(df, top, x, y)


def interactive_scatter(df, x, y, rank_by, x_label, y_label, title, subtitle,
                        n=12, x_format=".2f", y_format=".2f",
                        positions=("GK", "DEF", "MID", "FWD")):
    """Builds a Plotly scatter where every dot shows the player name on hover,
    with buttons to filter by position. Top players are re-ranked within each position."""
    hover = (
        "<b>%{customdata[0]}</b><br>"
        f"{x_label}: %{{x:{x_format}}}<br>"
        f"{y_label}: %{{y:{y_format}}}<br>"
        "Team: %{customdata[2]} | Price: £%{customdata[3]:.1f}m<br>"
        "Minutes: %{customdata[1]}<extra></extra>"
    )
    marker_line = dict(color="#333", width=0.5)
    data, annotations = split_groups(df, x, y, rank_by, n)

    fig = go.Figure()
    # Everyone outside the top group (blue)
    fig.add_trace(go.Scatter(
        x=data["x"][0], y=data["y"][0], customdata=data["customdata"][0],
        mode="markers", name="Other players", hovertemplate=hover,
        marker=dict(size=10, color=BLUE, opacity=0.55, line=marker_line),
    ))
    # The top group (red)
    fig.add_trace(go.Scatter(
        x=data["x"][1], y=data["y"][1], customdata=data["customdata"][1],
        mode="markers", name=f"Top {n}", hovertemplate=hover,
        marker=dict(size=13, color=RED, opacity=0.9, line=marker_line),
    ))
    # The single best player (bigger red dot with a dark ring)
    fig.add_trace(go.Scatter(
        x=data["x"][2], y=data["y"][2], customdata=data["customdata"][2],
        mode="markers", name="Best", showlegend=False, hovertemplate=hover,
        marker=dict(size=18, color=RED, line=dict(color="#222", width=2)),
    ))

    # One button per position: swaps the dots and labels for that position's players
    buttons = [dict(label="All", method="update", args=[data, {"annotations": annotations}])]
    for position in positions:
        subset = df[df["position"] == position]
        if subset.empty:
            continue
        pos_data, pos_annotations = split_groups(subset, x, y, rank_by, n)
        buttons.append(dict(label=position, method="update",
                            args=[pos_data, {"annotations": pos_annotations}]))

    fig.update_layout(
        title=dict(text=f"<b>{title}</b><br><sup>{subtitle}</sup>", x=0.05),
        xaxis_title=x_label, yaxis_title=y_label,
        plot_bgcolor=BG, paper_bgcolor=BG, height=720,
        margin=dict(t=130),
        annotations=annotations,
        legend=dict(orientation="h", x=1, xanchor="right", y=1.02, yanchor="bottom"),
        hoverlabel=dict(bgcolor="white", font_size=13, bordercolor="#555"),
        updatemenus=[dict(type="buttons", direction="right", buttons=buttons,
                          x=0, xanchor="left", y=1.02, yanchor="bottom",
                          bgcolor="white", bordercolor="#bbb", font=dict(size=12))],
    )
    fig.update_xaxes(gridcolor="#ccc", griddash="dot", zeroline=False)
    fig.update_yaxes(gridcolor="#ccc", griddash="dot", zeroline=False)
    return fig


def save_html(fig, filename):
    fig.write_html(str(DOCS_DIR / filename), include_plotlyjs="cdn")


def xg_vs_xa_interactive(df):
    fig = interactive_scatter(df, "expected_goals", "expected_assists", "xgi",
        "Expected goals (xG)", "Expected assists (xA)",
        "Who's creating and finishing the most?", "FPL xG vs xA | players with 450+ minutes")
    fig.add_vline(x=df["expected_goals"].quantile(0.9), line_dash="dash", line_color="#333", line_width=1)
    fig.add_hline(y=df["expected_assists"].quantile(0.9), line_dash="dash", line_color="#333", line_width=1)
    save_html(fig, "xg_vs_xa.html")


def value_interactive(df):
    fig = interactive_scatter(df, "now_cost", "total_points", "pts_per_m",
        "Price (£m)", "Total points",
        "Best value in FPL right now", "Total points vs price | labels = top 12 points per million",
        x_format=".1f", y_format=".0f")
    save_html(fig, "value.html")


def goals_vs_xg_interactive(df):
    fig = interactive_scatter(df, "expected_goals", "goals_scored", "abs_diff",
        "Expected goals (xG)", "Goals scored",
        "Who's beating their xG?", "Above the line = scoring more than expected | 450+ minutes",
        y_format=".0f")
    top = max(df["expected_goals"].max(), df["goals_scored"].max()) + 1
    fig.add_shape(type="line", x0=0, y0=0, x1=top, y1=top,
                  line=dict(dash="dash", color="#333", width=1))
    save_html(fig, "goals_vs_xg.html")


def form_vs_ownership_interactive(df):
    fig = interactive_scatter(df, "selected_by_percent", "form", "differential_score",
        "Ownership (%)", "Form",
        "Differentials: in form, but not widely owned",
        "Form vs ownership | red = top 12 by form among players under 10% owned",
        x_format=".1f", y_format=".1f")
    fig.add_vline(x=10, line_dash="dash", line_color="#333", line_width=1)
    save_html(fig, "form_vs_ownership.html")


def value_by_position_interactive(df, n=10):
    positions = ["GK", "DEF", "MID", "FWD"]
    fig = make_subplots(rows=2, cols=2, subplot_titles=positions,
                        horizontal_spacing=0.18, vertical_spacing=0.12)

    for i, position in enumerate(positions):
        top = df[df["position"] == position].nlargest(n, "pts_per_m")
        top = top.sort_values("pts_per_m")   # best ends up at the top of the bar chart
        colors = [RED if j == len(top) - 1 else BLUE for j in range(len(top))]
        fig.add_trace(go.Bar(
            x=top["pts_per_m"], y=top["web_name"], orientation="h",
            marker=dict(color=colors),
            customdata=top[["team", "now_cost", "total_points"]].values,
            hovertemplate=("<b>%{y}</b><br>Points per £m: %{x:.1f}<br>"
                           "Team: %{customdata[0]} | Price: £%{customdata[1]:.1f}m<br>"
                           "Total points: %{customdata[2]}<extra></extra>"),
        ), row=i // 2 + 1, col=i % 2 + 1)

    fig.update_layout(
        title=dict(text="<b>Best value by position</b><br>"
                        f"<sup>Top {n} points per million in each position | 450+ minutes</sup>", x=0.05),
        plot_bgcolor=BG, paper_bgcolor=BG, height=900, showlegend=False,
        hoverlabel=dict(bgcolor="white", font_size=13, bordercolor="#555"),
    )
    fig.update_xaxes(gridcolor="#ccc", griddash="dot", zeroline=False)
    save_html(fig, "value_by_position.html")


def defensive_interactive(df):
    defenders = df[df["position"].isin(["GK", "DEF"])]
    fig = interactive_scatter(defenders, "xgc_per_90", "clean_sheets", "cs_per_m",
        "Expected goals conceded per 90", "Clean sheets",
        "Defensive returns: GK and DEF",
        "Left = conceding fewer chances | red = top 12 clean sheets per million",
        y_format=".0f", positions=("GK", "DEF"))
    save_html(fig, "defensive.html")


# Colours for fixture difficulty 1 (easiest) to 5 (hardest)
FDR_COLORS = [[0.0, "#2a9d55"], [0.25, "#9fd8b0"], [0.5, "#e4e4e0"], [0.75, "#f4a3a8"], [1.0, "#c1121f"]]


def fixture_difficulty_interactive(fixtures, n_gameweeks=5):
    """Heatmap of every team's next fixtures, easiest run at the top."""
    gameweeks = sorted(fixtures["gameweek"].unique())[:n_gameweeks]
    upcoming = fixtures[fixtures["gameweek"].isin(gameweeks)].copy()
    upcoming["label"] = upcoming["opponent"] + upcoming["home"].map({True: " (H)", False: " (A)"})

    # A team can have two matches in a gameweek (double) or none (blank)
    per_cell = upcoming.groupby(["team", "gameweek"]).agg(
        difficulty=("difficulty", "mean"), label=("label", "<br>".join)).reset_index()
    difficulty = per_cell.pivot(index="team", columns="gameweek", values="difficulty").reindex(columns=gameweeks)
    labels = per_cell.pivot(index="team", columns="gameweek", values="label").reindex(columns=gameweeks)

    # Sort by average difficulty; a blank gameweek counts as the hardest (5)
    order = difficulty.fillna(5).mean(axis=1).sort_values().index
    difficulty, labels = difficulty.loc[order], labels.loc[order].fillna("Blank")

    fig = go.Figure(go.Heatmap(
        z=difficulty.values, x=[f"GW{gw}" for gw in gameweeks], y=list(order),
        text=labels.values, texttemplate="%{text}", textfont=dict(size=11),
        colorscale=FDR_COLORS, zmin=1, zmax=5, xgap=2, ygap=2,
        colorbar=dict(title="Difficulty", tickvals=[1, 2, 3, 4, 5], len=0.6),
        hovertemplate="<b>%{y}</b> %{x}<br>%{text}<br>Difficulty: %{z:.0f}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="<b>Fixture difficulty</b><br>"
                        f"<sup>Next {len(gameweeks)} gameweeks | easiest run at the top | FPL difficulty rating 1-5</sup>", x=0.05),
        plot_bgcolor=BG, paper_bgcolor=BG, height=820,
        yaxis=dict(autorange="reversed"), xaxis=dict(side="top"),
        hoverlabel=dict(bgcolor="white", font_size=13, bordercolor="#555"),
    )
    save_html(fig, "fixture_difficulty.html")


def make_all():
    DOCS_DIR.mkdir(exist_ok=True)
    df = load_latest()

    # Static PNGs
    xg_vs_xa(df)
    value_chart(df)
    goals_vs_xg(df)

    # Interactive HTML
    prepared = prepare(df)
    xg_vs_xa_interactive(prepared)
    value_interactive(prepared)
    goals_vs_xg_interactive(prepared)
    form_vs_ownership_interactive(prepared)
    value_by_position_interactive(prepared)
    defensive_interactive(prepared)

    fixtures = load_latest_fixtures()
    if fixtures is not None:
        fixture_difficulty_interactive(fixtures)
    else:
        print("No fixtures data yet - skipping fixture difficulty chart")

    update_last_updated()
    print(f"Charts saved to {DOCS_DIR}")


if __name__ == "__main__":
    make_all()