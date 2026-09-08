import random
from app.domain.fleet.coordinates import BOARD_SIZE, format_coordinate
from app.domain.fleet.validator import (
    FLEET_COMPOSITION,
    is_valid_fleet,
    ships_touch,
)

def build_ship(
        start: tuple[int, int],
        length: int,
        horizontal: bool,
) -> list[str]:
    x, y = start
    ship = []

    for offset in range(length):
        if horizontal:
            position = (x + offset, y)
        else: 
            position = (x, y + offset)

        ship.append(format_coordinate(position))

    return ship

def can_place_ship(ship: list[str], fleet: list[list[str]]) -> bool:
    for placed_ship in fleet:
        if ships_touch(ship, placed_ship):
            return False

    return True

def generate_ship(length: int) -> list[str]:
    horizontal = random.choice([True, False])

    if horizontal:
        x = random.randint(0, BOARD_SIZE - length)
        y = random.randint(0, BOARD_SIZE - 1)
    else:
        x = random.randint(0, BOARD_SIZE - 1)
        y = random.randint(0, BOARD_SIZE - length)

    return build_ship((x, y), length, horizontal)

def generate_placeable_ship(
        length: int,
        fleet: list[list[str]],
        max_attempts: int = 1000,
) -> list[str]:
    for _ in range(max_attempts):
        ship = generate_ship(length)

        if can_place_ship(ship, fleet):
            return ship

    raise RuntimeError("Could not place ship")

def generate_fleet() -> list[list[str]]:
    fleet = []

    for length, count in FLEET_COMPOSITION.items():
        for _ in range(count):
            ship = generate_placeable_ship(length, fleet)
            fleet.append(ship)

    if not is_valid_fleet(fleet):
        raise RuntimeError("Generated fleet is invalid")

    return fleet