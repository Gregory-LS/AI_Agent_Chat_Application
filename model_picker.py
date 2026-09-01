import tkinter as tk
from tkinter import ttk

class ModelPicker:
    """A UI component for selecting an AI model from a list."""

    def __init__(self, parent, models, on_select=None):
        """
        Initialize the ModelPicker.

        Args:
            parent: The parent tkinter widget.
            models: List of model names (strings).
            on_select: Callback function(model_name) when a model is selected.
        """
        self.parent = parent
        self.models = models
        self.on_select = on_select
        self.filtered_models = models[:]

        # Create UI elements
        self.frame = ttk.Frame(parent)
        self.frame.pack(padx=10, pady=10)

        # Search label and entry
        ttk.Label(self.frame, text="Search models:").grid(row=0, column=0, sticky="w")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._filter_models)
        self.search_entry = ttk.Entry(self.frame, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Listbox for models
        self.listbox = tk.Listbox(self.frame, height=8, selectmode=tk.SINGLE)
        self.listbox.grid(row=1, column=0, columnspan=2, sticky="nsew")

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.listbox.yview)
        scrollbar.grid(row=1, column=2, sticky="ns")
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Bind selection event
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        # Populate list
        self._populate_list()

        # Configure grid weights
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(1, weight=1)

    def _populate_list(self):
        """Populate the listbox with the filtered models."""
        self.listbox.delete(0, tk.END)
        for model in self.filtered_models:
            self.listbox.insert(tk.END, model)

    def _filter_models(self, *args):
        """Filter the model list based on the search query."""
        query = self.search_var.get().lower()
        self.filtered_models = [
            model for model in self.models if query in model.lower()
        ]
        self._populate_list()

    def _on_select(self, event):
        """Handle selection event from listbox."""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            model_name = self.filtered_models[index]
            if self.on_select:
                self.on_select(model_name)

    def get_selected(self):
        """Return the currently selected model name, or None."""
        selection = self.listbox.curselection()
        if selection:
            return self.filtered_models[selection[0]]
        return None

    def destroy(self):
        """Clean up the UI component."""
        self.frame.destroy()
