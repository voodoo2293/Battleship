import argparse

from arena.models import ServiceConfig
from arena.tournament import play_tournament

def main():
    parser = argparse.ArgumentParser(
        description="Battleship Arena"
    )

    parser.add_argument(
        "ports",
        nargs="+",
        type=int,
        help="Local ports of game services",
    )

    args = parser.parse_args()

    services = [
        ServiceConfig(
            name=f"service_{index}_{port}",
            base_url=f"http://127.0.0.1:{port}",
        )
        for index, port in enumerate(
            args.ports,
            start=1,
        )
    ]

    result = play_tournament(services)

    print("\nMatches:")

    for match in result.matches:
        print(
            f"{match.winner.name} defeated "
            f"{match.loser.name} "
            f"in {match.turns} turns"
        )

    print("\nScores:")

    for name, score in result.scores.items():
        print(f"{name}: {score}")

    print("\nWinner:")

    for winner in result.winners:
        print(winner.name)

if __name__ == "__main__":
    main()