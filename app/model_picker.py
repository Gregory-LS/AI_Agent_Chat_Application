import tkinter as tk
from tkinter import ttk

class ModelPicker:
    """A UI component for selecting a machine learning model."""

    def __init__(self, parent, models, on_select_callback):
        """
        Initialize the model picker.

        Args:
            parent: The parent tkinter widget.
            models: A list of model names (strings) to show in the dropdown.
            on_select_callback: A callable that receives the selected model name.
        """
        self.parent = parent
        self.models = models
        self.on_select_callback = on_select_callback
        self.selected_model = tk.StringVar()
        self._build_ui()

    def _build_ui(self):
        """Build the dropdown and label."""
        self.frame = ttk.Frame(self.parent)
        self.label = ttk.Label(self.frame, text="Select Model:")
        self.label.pack(side=tk.LEFT, padx=(0, 5))

        if self.models:
            self.dropdown = ttk.Combobox(
                self.frame,
                textvariable=self.selected_model,
                values=self.models,
                state="readonly"
            )
            self.dropdown.current(0)
            self.selected_model.set(self.models[0])
        else:
            self.dropdown = ttk.Combobox(
                self.frame,
                textvariable=self.selected_model,
                values=["No models available"],
                state="disabled"
            )
        self.dropdown.pack(side=tk.LEFT)

        self.select_button = ttk.Button(
            self.frame,
            text="Select",
            command=self._on_select
        )
        self.select_button.pack(side=tk.LEFT, padx=(5, 0))

        self.frame.pack(pady=5)

    def _on_select(self):
        """Trigger the callback with the currently selected model."""
        model = self.selected_model.get()
        if model and model != "No models available":
            self.on_select_callback(model)

    def get_selected_model(self):
        """Return the currently selected model name."""
        return self.selected_model.get()

    def update_models(self, new_models):
        """Update the list of available models.

        Args:
            new_models: List of model name strings.
        """
        self.models = new_models
        self.dropdown['values'] = new_models
        if new_models:
            self.dropdown['state'] = 'readonly'
            self.selected_model.set(new_models[0])
        else:
            self.dropdown['values'] = ["No models available"]
            self.dropdown['state'] = 'disabled'
