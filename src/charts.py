import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"

BG = "#f4f4f2"
GREY = "#bdbdbd"
RED = "#e63946"


def load_latest():
    files = sorted(DATA_DIR.glob("players_*.csv"))
    if not files:
        raise FileNotFoundError("No data yet - run src/fetch.py first")
    print(f"Using {files[-1].name}")
    return pd.read_csv(files[-1])


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

    # Label the 6 biggest over- and underperformers
    df["abs_diff"] = df["diff"].abs()
    label_top(ax, df, "expected_goals", "goals_scored", n=12, by="abs_diff")

    ax.set_xlabel("Expected goals (xG)")
    ax.set_ylabel("Goals scored")
    style(ax, fig, "Who's beating their xG?",
          "Above the line = scoring more than expected | 450+ minutes")
    plt.subplots_adjust(top=0.88)
    fig.savefig(DOCS_DIR / "goals_vs_xg.png", dpi=150, facecolor=BG)
    plt.close(fig)

def make_all():
    DOCS_DIR.mkdir(exist_ok=True)
    df = load_latest()
    xg_vs_xa(df)
    value_chart(df)
    goals_vs_xg(df)
    print(f"Charts saved to {DOCS_DIR}")


if __name__ == "__main__":
    make_all()