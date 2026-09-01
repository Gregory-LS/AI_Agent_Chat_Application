import time
import pytest
from karbonite.extras import RichProgress, run_parallel


def test_rich_progress_basic():
    """Test that RichProgress context manager works without error."""
    with RichProgress("Test progress") as progress:
        task = progress.add_task("[cyan]Testing...", total=10)
        for _ in range(10):
            progress.update(task, advance=1)
    # If no exception, test passes
    assert True


def test_rich_progress_nested():
    """Test that context manager can be nested (though not recommended)."""
    with RichProgress("Outer") as outer:
        with RichProgress("Inner") as inner:
            t1 = outer.add_task("outer task", total=5)
            t2 = inner.add_task("inner task", total=3)
            for _ in range(5):
                outer.update(t1, advance=1)
                time.sleep(0.01)
            for _ in range(3):
                inner.update(t2, advance=1)
                time.sleep(0.01)
    assert True


def square(x: int) -> int:
    return x * x


def test_run_parallel_basic():
    """Test run_parallel with a simple function."""
    items = [1, 2, 3, 4, 5]
    results = run_parallel(square, items)
    assert results == [1, 4, 9, 16, 25]


def test_run_parallel_empty():
    """Test run_parallel with empty list."""
    results = run_parallel(square, [])
    assert results == []


def test_run_parallel_with_args():
    """Test run_parallel with additional positional arguments."""
    def multiply(base, factor):
        return base * factor

    items = [1, 2, 3]
    results = run_parallel(multiply, items, 10)
    assert results == [10, 20, 30]


def test_run_parallel_with_kwargs():
    """Test run_parallel with additional keyword arguments."""
    def multiply(base, factor=1):
        return base * factor

    items = [1, 2, 3]
    results = run_parallel(multiply, items, factor=100)
    assert results == [100, 200, 300]
