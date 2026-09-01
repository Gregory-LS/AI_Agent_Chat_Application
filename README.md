# My Flask App

A simple Flask application demonstrating endpoints with error handling and extras.

## Features

- **GET /** - Returns a greeting message.
- **POST /data** - Accepts JSON with a "name" field (string, non-empty). Returns a personalized greeting.
- **GET /extras** - Returns random generated data. Accepts optional query parameter `type`:
  - `all` (default): returns random string, integer, and float.
  - `random_string`: returns a random string.
  - `random_int`: returns a random integer between 1 and 1000.
  - `random_float`: returns a random float between 0 and 100 (2 decimal places).

## Error Handling

- 400 for bad requests (missing JSON, missing/invalid fields, invalid query parameters)
- 404 for unknown routes
- 405 for unsupported HTTP methods
- 500 for unexpected server errors (with logging)

## Running

```bash
python app.py
```

The app runs on http://localhost:5000 by default.

## Tests

```bash
pytest tests/
```
