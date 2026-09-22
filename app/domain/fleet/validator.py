from itertools import combinations
from collections import Counter
from app.domain.fleet.coordinates import is_inside_board, parse_coordinate

FLEET_COMPOSITION = {
    4: 1,
    3: 2,
    2: 3,
    1: 4,
}

def is_straight_and_continuous(ship: list[str]) -> bool:
    positions = [parse_coordinate(coordinate) for coordinate in ship]

    if not positions:
        return False

    if len(set(positions)) != len(positions):
        return False

    x_values = {x for x, _ in positions}
    y_values = {y for _, y in positions}

    if len(x_values) == 1:
        rows = sorted(y for _, y in positions)
        return rows == list(range(rows[0], rows[0] + len(rows)))

    if len(y_values) == 1:
        columns = sorted(x for x, _ in positions)
        return columns == list(range(columns[0], columns[0] + len(columns)))

    return False

def is_ship_inside_board(ship: list[str]) -> bool:
    try:
        positions = [parse_coordinate(coordinate) for coordinate in ship]
    except ValueError:
        return False

    return all(is_inside_board(position) for position in positions)

def has_valid_composition(fleet: list[list[str]]) -> bool:
    ship_sizes = Counter(len(ship) for ship in fleet)

    return ship_sizes == FLEET_COMPOSITION

def ships_touch(first_ship: list[str], second_ship: list[str]) -> bool:
    first_positions = [
        parse_coordinate(coordinate) for coordinate in first_ship
    ]
    second_positions = [
        parse_coordinate(coordinate) for coordinate in second_ship
    ]

    for x1, y1 in first_positions:
        for x2, y2 in second_positions:
            if abs(x1 - x2) <= 1 and abs(y1 - y2) <= 1:
                return True

    return False 

def has_no_touching_ships(fleet: list[list[str]]) -> bool: 
    for first_ship, second_ship in combinations(fleet, 2):
        if ships_touch(first_ship, second_ship):
            return False

    return True

def is_valid_fleet(fleet: list[list[str]]) -> bool:
    if not has_valid_composition(fleet):
        return False

    try:
        for ship in fleet:
            if not is_straight_and_continuous(ship):
                return False

            if not is_ship_inside_board(ship):
                return False

        if not has_no_touching_ships(fleet):
            return False

    except ValueError:
        return False

    return True