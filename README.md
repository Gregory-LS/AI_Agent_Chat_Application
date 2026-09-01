# Karbonite

A Python toolkit for data processing utilities.

## Installation

```bash
pip install karbonite
```

## Usage

### Progress bars with Rich

```python
from karbonite import RichProgress

with RichProgress("Processing items") as progress:
    task = progress.add_task("[cyan]Working...", total=100)
    for i in range(100):
        # do something
        progress.update(task, advance=1)
```

### Parallel execution

```python
from karbonite import run_parallel

def double(x):
    return x * 2

results = run_parallel(double, [1, 2, 3, 4, 5])
print(results)  # [2, 4, 6, 8, 10]
```

## API Reference

- `RichProgress(description: str = "Working...")` — Context manager yielding a Rich `Progress` instance.
- `run_parallel(func, items, *args, **kwargs)` — Run `func` on each item concurrently using a multiprocessing Pool.
- `process_data(...)` — (Core function, see core module for details).

## Testing

```bash
pytest tests/
```
