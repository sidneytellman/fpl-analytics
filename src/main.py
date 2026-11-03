from fetch import fetch_players, save
from charts import make_all


def main():
    print("Fetching FPL data...")
    players = fetch_players()
    save(players)

    print("Making charts...")
    make_all()

    print("Done.")


if __name__ == "__main__":
    main()