import pytest

from app.domain.fleet.coordinates import (
    format_coordinate,
    is_inside_board,
    parse_coordinate,
)

def test_parse_coordinate():
    assert parse_coordinate("A1") == (0, 0)
    assert parse_coordinate("D7") == (3, 6)
    assert parse_coordinate("J10") == (9, 9)

def test_parse_coordinate_rejects_invalid_format():
    with pytest.raises(ValueError):
        parse_coordinate("1A")

    with pytest.raises(ValueError):
        parse_coordinate("AA1")

    with pytest.raises(ValueError):
        parse_coordinate("A0")

    with pytest.raises(ValueError):
        parse_coordinate("A01")

    with pytest.raises(ValueError):
        parse_coordinate("K1")

    with pytest.raises(ValueError):
        parse_coordinate("A11") 

def test_is_inside_board():
    assert is_inside_board((0, 0)) is True
    assert is_inside_board((9, 9)) is True
    assert is_inside_board((10, 0)) is False
    assert is_inside_board((0, 10)) is False

def test_format_coordinate():
    assert format_coordinate((0, 0)) == "A1"
    assert format_coordinate((3, 6)) == "D7"
    assert format_coordinate((9, 9)) == "J10"

def test_format_coordinate_rejects_outside_board():
    with pytest.raises(ValueError):
        format_coordinate((10, 0))