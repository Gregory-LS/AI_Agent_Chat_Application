# Double Application

A simple Python application that doubles an integer given as a command-line argument.

## Usage

```bash
python app.py <integer>
```

Example:

```bash
$ python app.py 5
10
```

## Error Handling

- If no argument is provided, the program prints usage information and exits with code 1.
- If the argument is not a valid integer, an error message is printed to stderr and the program exits with code 1.
- The `double` function itself raises `TypeError` if the input is not an integer.

## Testing

Run tests using pytest:

```bash
pytest tests/
```

Tests cover:
- Positive, zero, negative, and large integers
- Non-integer inputs (float, string, None) raise `TypeError`
