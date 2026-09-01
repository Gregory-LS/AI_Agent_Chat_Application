import pytest
from app import double

def test_double_positive():
    assert double(3) == 6

def test_double_zero():
    assert double(0) == 0

def test_double_negative():
    assert double(-4) == -8

def test_double_large():
    assert double(10**6) == 2 * 10**6

def test_double_not_integer_float():
    with pytest.raises(TypeError) as exc_info:
        double(3.14)
    assert "float" in str(exc_info.value)

def test_double_not_integer_string():
    with pytest.raises(TypeError) as exc_info:
        double("hello")
    assert "str" in str(exc_info.value)

def test_double_not_integer_none():
    with pytest.raises(TypeError) as exc_info:
        double(None)
    assert "NoneType" in str(exc_info.value)
