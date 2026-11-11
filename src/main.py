from charts import make_all
from fetch import fetch_all, save, save_fixtures
from history import build_player_profiles, save_profiles


def main():
    print("Fetching FPL data...")
    data, players, fixtures = fetch_all()
    save(players)
    save_fixtures(fixtures)

    print("Fetching player histories (takes a few minutes)...")
    save_profiles(build_player_profiles(data))

    print("Making charts...")
    make_all()

    print("Done.")


if __name__ == "__main__":
    main()