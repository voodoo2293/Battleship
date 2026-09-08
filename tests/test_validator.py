from app.domain.fleet.validator import (
    has_no_touching_ships,
    has_valid_composition,
    is_ship_inside_board,
    is_straight_and_continuous,
    is_valid_fleet,
    ships_touch,
)

def test_vertical_ship_is_valid():
    assert is_straight_and_continuous(["A1", "A2", "A3"]) is True

def test_horizontal_ship_is_valid():
    assert is_straight_and_continuous(["A1", "B1", "C1"]) is True

def test_single_deck_ship_is_valid():
    assert is_straight_and_continuous(["D7"]) is True

def test_diagonal_ship_is_invalid():
    assert is_straight_and_continuous(["A1", "B2"]) is False

def test_ship_with_gap_is_invalid():
    assert is_straight_and_continuous(["A1", "A3", "A4"]) is False

def test_ship_with_duplicate_cell_is_invalid():
    assert is_straight_and_continuous(["A1", "A1", "A2"]) is False 

def test_ship_inside_board_is_valid():
    assert is_ship_inside_board(["J8", "J9", "J10"]) is True

def test_ship_outside_board_is_invalid():
    assert is_ship_inside_board(["J9", "J10", "J11"]) is False

def test_fleet_composition_is_valid():
    fleet = [
        ["A1", "A2", "A3", "A4"],
        ["C1", "C2", "C3"],
        ["E1", "E2", "E3"],
        ["G1", "G2"],
        ["I1", "I2"],
        ["A5", "B5"],
        ["D5"],
        ["F5"],
        ["H5"],
        ["J5"],
    ]

    assert has_valid_composition(fleet) is True

def test_fleet_composition_is_invalid():
    fleet = [
        ["A1", "A2", "A3", "A4"],
        ["C1", "C2", "C3"],
        ["E1", "E2", "E3"],
        ["G1", "G2"],
        ["I1", "I2"],
        ["A5", "B5"],
        ["D5"],
        ["F5"],
        ["H5"],
    ]

    assert has_valid_composition(fleet) is False

def test_ships_touch_by_side():
    assert ships_touch(["A1", "A2"], ["B1"]) is True

def test_ships_touch_by_corner():
    assert ships_touch(["A1"], ["B2"]) is True

def test_ships_overlap():
    assert ships_touch(["A1", "A2"], ["A2", "A3"]) is True

def test_ships_do_not_touch():
    assert ships_touch(["A1", "A2"], ["C1"]) is False

def test_fleet_with_no_touching_ships_is_valid():
    fleet = [
        ["A1", "A2"],
        ["C1", "C2"],
        ["E5"],
    ]

    assert has_no_touching_ships(fleet) is True

def test_fleet_with_touching_ships_is_invalid():
    fleet = [
        ["A1", "A2"],
        ["B3"],
    ]

    assert has_no_touching_ships(fleet) is False

def test_valid_fleet():
    fleet = [
        ["A1", "A2", "A3", "A4"],
        ["C1", "C2", "C3"],
        ["E1", "E2", "E3"],
        ["G1", "G2"],
        ["I1", "I2"],
        ["A6", "B6"],
        ["D6"],
        ["F6"],
        ["H6"],
        ["J6"],
    ]

    assert is_valid_fleet(fleet) is True

def test_invalid_fleet_composition():
    fleet = [
        ["A1", "A2", "A3", "A4"],
        ["C1", "C2", "C3"],
        ["E1", "E2", "E3"],
        ["G1", "G2"],
        ["I1", "I2"],
        ["A6", "B6"],
        ["D6"],
        ["F6"],
        ["H6"],
    ]

    assert is_valid_fleet(fleet) is False

def test_invalid_fleet_ship_geometry():
    fleet = [
        ["A1", "A2", "A3", "A4"],
        ["C1", "C2", "C3"],
        ["E1", "E2", "E3"],
        ["G1", "G3"],
        ["I1", "I2"],
        ["A6", "B6"],
        ["D6"],
        ["F6"],
        ["H6"],
        ["J6"],
    ]

    assert is_valid_fleet(fleet) is False

def test_invalid_fleet_ship_outside_board():
    fleet = [
        ["A1", "A2", "A3", "A4"],
        ["C1", "C2", "C3"],
        ["E1", "E2", "E3"],
        ["G1", "G2"],
        ["I1", "I2"],
        ["J9", "J10"],
        ["D6"],
        ["F6"],
        ["H6"],
        ["K6"],
    ]

    assert is_valid_fleet(fleet) is False

def test_invalid_fleet_touching_ships():
    fleet = [
        ["A1", "A2", "A3", "A4"],
        ["C1", "C2", "C3"],
        ["E1", "E2", "E3"],
        ["G1", "G2"],
        ["I1", "I2"],
        ["A6", "B6"],
        ["C5"],
        ["F6"],
        ["H6"],
        ["J6"],
    ]

    assert is_valid_fleet(fleet) is False