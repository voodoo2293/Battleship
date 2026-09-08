BOARD_SIZE = 10
BOARD_COLUMNS = "ABCDEFGHIJ"

def parse_coordinate(coordinate: str) -> tuple[int, int]:
    if len(coordinate) < 2:
        raise ValueError("Invalid coordinate")

    column = coordinate[0]
    row = coordinate[1:]

    if not ("A" <= column <= "Z"):
        raise ValueError("Invalid coordinate")

    if not row.isdigit():
        raise ValueError("Invalid coordinate")

    if row.startswith("0"):
        raise ValueError("Invalid coordinate")

    row_number = int(row)

    return ord(column) - ord("A"), row_number - 1

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