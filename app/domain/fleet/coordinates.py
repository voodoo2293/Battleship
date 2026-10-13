BOARD_SIZE = 10
BOARD_COLUMNS = "ABCDEFGHIJ"

def parse_coordinate(
        coordinate: str,
) -> tuple[int, int]:
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
        "6", "7", "8", "9", "10"
    ):
        raise ValueError("Invalid coordinate")

    x = BOARD_COLUMNS.index(column)
    y = int(row) - 1

    return x, y

def is_inside_board(position: tuple[int, int]) -> bool:
    x, y = position

    return (
        0 <= x < len(BOARD_COLUMNS)
        and 0 <= y < BOARD_SIZE
    )

def format_coordinate(position: tuple[int, int]) -> str:
    x, y = position

    if not is_inside_board(position):
        raise ValueError("Position outside board")

    return f"{BOARD_COLUMNS[x]}{y + 1}"