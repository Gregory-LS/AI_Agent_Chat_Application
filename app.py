import sys

def double(x: int) -> int:
    """Return twice the input integer.

    Args:
        x: An integer.

    Returns:
        Twice the integer.

    Raises:
        TypeError: If x is not an integer.
    """
    if not isinstance(x, int):
        raise TypeError(f"Expected an integer, got {type(x).__name__}")
    return x * 2

def main() -> None:
    """Read an integer from command-line and print its double."""
    if len(sys.argv) != 2:
        print("Usage: python app.py <integer>", file=sys.stderr)
        sys.exit(1)
    try:
        value = int(sys.argv[1])
        result = double(value)
        print(result)
    except ValueError:
        print("Error: Argument must be an integer.", file=sys.stderr)
        sys.exit(1)
    except TypeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
