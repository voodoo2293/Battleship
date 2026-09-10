import pytest

from app.domain.fleet.generator import (
    build_ship,
    can_place_ship,
    generate_fleet,
    generate_placeable_ship,
    generate_ship,
)

from app.domain.fleet.validator import (
    is_ship_inside_board,
    is_straight_and_continuous,
    is_valid_fleet,
)

def test_build_horizontal_ship():
    assert build_ship((0, 0), 4, True) == [
        "A1",
        "B1",
        "C1",
        "D1",
    ]

def test_build_vertical_ship():
    assert build_ship((0, 0), 4, False) == [
        "A1",
        "A2",
        "A3",
        "A4",
    ]

def test_build_ship_outside_board_raises_error():
    with pytest.raises(ValueError):
        build_ship((8, 0), 4, True)

def test_can_place_ship_without_touching():
    fleet = [
        ["A1", "A2"],
    ]

    assert can_place_ship(["C1", "C2"], fleet) is True

def test_cannot_place_touching_ship():
    fleet = [
        ["A1", "A2"],
    ]

    assert can_place_ship(["B3"], fleet) is False

def test_generate_ship():
    for length in (1, 2, 3, 4):
        for _ in range(100):
            ship = generate_ship(length)

            assert len(ship) == length
            assert is_straight_and_continuous(ship) is True
            assert is_ship_inside_board(ship) is True

def test_generate_placeable_ship():
    fleet = [
        ["A1", "A2", "A3", "A4"],
    ]

    ship = generate_placeable_ship(3, fleet)

    assert len(ship) == 3
    assert can_place_ship(ship, fleet) is True

def test_generate_fleet():
    fleet = generate_fleet()

    assert len(fleet) == 10
    assert sum(len(ship) for ship in fleet) == 20
    assert is_valid_fleet(fleet) is True

def test_generate_fleet_multiple_times():
    for _ in range(100):
        fleet = generate_fleet()

        assert len(fleet) == 10
        assert sum(len(ship) for ship in fleet) == 20
        assert is_valid_fleet(fleet) is True