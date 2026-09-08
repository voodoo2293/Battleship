import pytest

from app.domain.fleet.coordinates import is_inside_board, parse_coordinate

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
def test_is_inside_board():
    assert is_inside_board(parse_coordinate("A1")) is True
    assert is_inside_board(parse_coordinate("J10")) is True
    assert is_inside_board(parse_coordinate("K1")) is False
    assert is_inside_board(parse_coordinate("A11")) is False