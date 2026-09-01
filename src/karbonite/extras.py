import logging
from contextlib import contextmanager
from typing import Callable, Iterator, List, TypeVar

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

T = TypeVar("T")

logger = logging.getLogger(__name__)


@contextmanager
def RichProgress(description: str = "Working...") -> Iterator[Progress]:
    """
    Context manager that yields a Rich Progress instance with a standard set of columns.
    Usage:
        with RichProgress("Processing items") as progress:
            task = progress.add_task("[cyan]Processing...", total=100)
            for i in range(100):
                # do work
                progress.update(task, advance=1)
    """
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
    )
    try:
        progress.start()
        yield progress
    finally:
        progress.stop()


def run_parallel(func: Callable[..., T], items: List[T], *args, **kwargs) -> List[T]:
    """
    Apply `func` to each item in `items` concurrently using a multiprocessing Pool.
    Returns a list of results in the same order as `items`.

    Example:
        results = run_parallel(process_item, [1, 2, 3, 4], extra_arg='hello')
    """
    from multiprocessing import Pool

    if not items:
        return []

    with Pool() as pool:
        # Use starmap if additional args/kwargs need to be passed
        if args or kwargs:
            # Build a partial function
            from functools import partial

            partial_func = partial(func, *args, **kwargs)
            result = pool.map(partial_func, items)
        else:
            result = pool.map(func, items)
    return result
