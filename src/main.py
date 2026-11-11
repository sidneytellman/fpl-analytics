from charts import make_all
from fetch import fetch_all, save, save_fixtures


def main():
    print("Fetching FPL data...")
    players, fixtures = fetch_all()
    save(players)
    save_fixtures(fixtures)

    print("Making charts...")
    make_all()

    print("Done.")


if __name__ == "__main__":
    main()