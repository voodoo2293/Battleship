BOARD_COLUMNS = "ABCDEFGHIJ"
BOARD_SIZE = 10

def parse_coordinate(coordinate: str) -> tuple[int, int]:
    if not isinstance(coordinate, str):
        raise ValueError("Invalid coordinate")

    if not 2 <= len(coordinate) <= 3:
        raise ValueError("Invalid coordinate")

    column = coordinate[0]
    row = coordinate[1:]

    if column not in BOARD_COLUMNS:
        raise ValueError("Invalid coordinate")

    if row not in (
        "1", "2", "3", "4", "5",
        "6", "7", "8", "9", "10",
    ):
        raise ValueError("Invalid coordinate")

    x = BOARD_COLUMNS.index(column)
    y = int(row) - 1

    return x, y

def is_valid_ship(ship: list[str]) -> bool:
    if not 1 <= len(ship) <= 4:
        return False

    try:
        positions = [
            parse_coordinate(coordinate)
            for coordinate in ship
        ]
    except ValueError:
        return False

    if len(set(positions)) != len(positions):
        return False

    if len(positions) == 1:
        return True

    xs = [x for x, _ in positions]
    ys = [y for _, y in positions]

    if len(set(xs)) == 1:
        sorted_ys = sorted(ys)

        return sorted_ys == list(
            range(sorted_ys[0], sorted_ys[0] + len(sorted_ys))
        )

    if len(set(ys)) == 1:
        sorted_xs = sorted(xs)

        return sorted_xs == list(
            range(sorted_xs[0], sorted_xs[0] + len(sorted_xs))
        )

    return False

def ships_touch(
        first_ship: list[str],
        second_ship: list[str],
) -> bool:
    first_positions = [
        parse_coordinate(coordinate)
        for coordinate in first_ship
    ]

    second_positions = [
        parse_coordinate(coordinate)
        for coordinate in second_ship
    ]

    for first_x, first_y in first_positions:
        for second_x, second_y in second_positions:
            if (
                abs(first_x - second_x) <= 1
                and abs(first_y - second_y) <= 1
            ):
                return True

    return False

def is_valid_fleet(
        fleet: list[list[str]],
) -> bool:
    if len(fleet) != 10:
        return False

    if not all(
        is_valid_ship(ship)
        for ship in fleet
    ):
        return False

    ship_lengths = sorted(
        len(ship)
        for ship in fleet
    )

    if ship_lengths != [
        1, 1, 1, 1,
        2, 2, 2,
        3, 3,
        4,
    ]:
        return False

    for first_index in range(len(fleet)):
        for second_index in range(
            first_index + 1,
            len(fleet),
        ):
            if ships_touch(
                fleet[first_index],
                fleet[second_index],
            ):
                return False

    return True

def get_expected_shot_result(
        fleet: list[list[str]],
        hit_coordinates: set[str],
        coordinate: str,
) -> str:
    parse_coordinate(coordinate)

    target_ship = next(
        (
            ship
            for ship in fleet
            if coordinate in ship
        ),
        None,
    )

    if target_ship is None:
        return "miss"

    if coordinate in hit_coordinates:
        return "hit"

    updated_hits = {
        *hit_coordinates,
        coordinate,
    }

    if all(
        ship_coordinate in updated_hits
        for ship_coordinate in target_ship
    ):
        return "killed"

    return "hit"
