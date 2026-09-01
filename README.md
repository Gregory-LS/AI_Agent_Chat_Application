# Model Picker UI

This project provides a reusable `ModelPicker` UI component built with Tkinter.
It allows users to select a machine learning model from a dropdown list.

## Features

- Dropdown list populated with available model names.
- Read-only state when no models are available.
- Callback function triggered on model selection.
- Dynamic update of model list.

## Usage

```python
import tkinter as tk
from app.model_picker import ModelPicker

def on_model_selected(model):
    print(f"Selected model: {model}")

root = tk.Tk()
picker = ModelPicker(root, ["GPT-4", "BERT", "T5"], on_model_selected)
root.mainloop()
```

## Running Tests

```bash
python -m unittest tests.test_model_picker
```
