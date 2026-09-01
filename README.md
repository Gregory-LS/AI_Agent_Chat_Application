# Model Picker UI Component

A simple Tkinter-based UI component for selecting AI models from a list.

## Features

- Display a list of available models.
- Filter models by typing in a search box (case-insensitive).
- Select a model by clicking on it; triggers a callback.
- Get the currently selected model programmatically.

## Usage

```python
import tkinter as tk
from model_picker import ModelPicker

root = tk.Tk()
root.title("Model Selection")

models = ["gpt-3.5", "gpt-4", "claude-2", "llama-2", "bert-base"]

def on_model_selected(model_name):
    print(f"Selected model: {model_name}")

picker = ModelPicker(root, models, on_select=on_model_selected)

root.mainloop()
```

## API

### `ModelPicker(parent, models, on_select=None)`

- `parent`: The parent Tkinter widget.
- `models`: A list of model name strings.
- `on_select`: Optional callback function that receives the selected model name.

### Methods

- `get_selected()`: Returns the currently selected model name, or `None`.
- `destroy()`: Removes the UI component.

## Tests

Run tests with pytest:

```bash
pytest tests/test_model_picker.py -v
```

## Files

- `model_picker.py` – Main component.
- `tests/test_model_picker.py` – Unit tests.
- `README.md` – This file.
