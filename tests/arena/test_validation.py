from arena.validation import (
    get_expected_shot_result,
    is_valid_fleet,
    is_valid_ship,
    parse_coordinate,
)

VALID_FLEET = [
    ["A1", "A2", "A3", "A4"],
    ["D1", "E1", "F1"],
    ["J1", "J2", "J3"],
    ["D4", "E4"],
    ["H5", "H6"],
    ["B7", "C7"],
    ["E7"],
    ["J8"],
    ["A10"],
    ["F10"],
]

def test_prse_coordinate_rejects_outside_board():
    try:
        parse_coordinate("K1")
        assert False, "ValueError was not raised"
    except ValueError:
        pass

def test_is_valid_ship_rejects_diagonal_ship():
    assert is_valid_ship(
        ["A1", "B2"]
    ) is False

def test_is_valid_fleet_accepts_correct_fleet():
    assert is_valid_fleet(
        VALID_FLEET
    ) is True

def test_is_valid_fleet_rejects_wrong_ship_count():
    assert is_valid_fleet(
        VALID_FLEET[:-1]
    ) is False

def test_is_valid_fleet_rejects_touching_ships():
    invalid_fleet = [
        ship.copy()
        for ship in VALID_FLEET
    ]

    invalid_fleet[-1] = ["D8"]

    assert is_valid_fleet(
        invalid_fleet
    ) is False

def test_expected_shot_result_returns_miss():
    fleet = [
        ["A1", "A2"],
    ]

    result = get_expected_shot_result(
        fleet,
        set(),
        "J10",
    )

    assert result == "miss"

def test_expected_shot_result_returns_hit():
    fleet = [
        ["A1", "A2"],
    ]

    result = get_expected_shot_result(
        fleet,
        set(),
        "A1",
    )

    assert result == "hit"

def test_expected_shot_result_returns_killed():
    fleet = [
        ["A1", "A2"],
    ]

    result = get_expected_shot_result(
        fleet,
        {"A1"},
        "A2",
    )

    assert result == "killed"

def test_expected_shot_result_repeated_hit_is_not_killed_again():
    fleet = [
        ["A1", "A2"],
    ]

    result = get_expected_shot_result(
        fleet,
        {"A1", "A2"},
        "A2",
    )

    assert result == "hit"