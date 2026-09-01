# TaskBuddy

A small, dependency-free web app that shows how to add polish to any web UI:

- **Loading states** — a `role=status` region with a spinner and disabled button while data is fetched.
- **Error toasts** — an `role=alert` toast that announces server errors and disappears automatically.
- **Accessibility** — skip link, semantic landmarks, focus-visible styles, `aria-live`, `aria-busy`, and reduced-motion support.

## Run the app

```bash
python app.py
```

Then open <http://127.0.0.1:8000>.

## API

`GET /api/data` returns a JSON object with an `items` list.

Query parameters:

| Parameter | Default | Description                             |
|-----------|---------|-----------------------------------------|
| `delay`   | `0.6`   | Simulated server latency in seconds     |
| `fail`    | `0`     | Set to `1` to force a 500 error         |

Example:

```bash
curl http://127.0.0.1:8000/api/data?delay=0&fail=1
```

## Run the tests

```bash
python -m unittest discover -s tests -v
```

## Accessibility notes

- The skip link lets keyboard users jump to the main content.
- The loading region uses `role=status` and `aria-live=polite`.
- The error toast uses `role=alert` and `aria-live=assertive`.
- Focus indicators are visible and high contrast.
- `prefers-reduced-motion` is respected.
- The button is disabled during loading to avoid duplicate requests.
