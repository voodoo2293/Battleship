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

    if len(args.ports) < 2:
        parser.error("At least two service ports are required")

    if len(set(args.ports)) != len(args.ports):
        parser.error("Service ports must be unique")

    if any(port < 1 or port > 65535 for port in args.ports):
        parser.error("Service ports must be between 1 and 65535")

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

    result = play_tournament(
        services,
        report_path="reports/tournament.json",
    )

    report_path = "reports/tournament.json"

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

    if result.completed:
        print("\nWinner:")

        for winner in result.winners:
            print(winner.name)
    else:
        print(
            "\nTournament incomplete: "
            "some matches failed due to arena error."
        )

        for failure in result.failed_matches:
            print(
                f"{failure.first_service.name} vs "
                f"{failure.second_service.name}: "
                f"{failure.reason}"
            )

    print(f"\nReport saved: {report_path}")

if __name__ == "__main__":
    main()