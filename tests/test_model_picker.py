import tkinter as tk
import pytest
from model_picker import ModelPicker

@pytest.fixture
def root():
    root = tk.Tk()
    yield root
    root.destroy()

@pytest.fixture
def sample_models():
    return ["gpt-3.5", "gpt-4", "claude-2", "llama-2", "bert-base"]

def test_initial_population(root, sample_models):
    picker = ModelPicker(root, sample_models)
    # Listbox should contain all models
    assert picker.listbox.size() == len(sample_models)
    for i, model in enumerate(sample_models):
        assert picker.listbox.get(i) == model
    picker.destroy()

def test_filter_models(root, sample_models):
    picker = ModelPicker(root, sample_models)
    # Simulate typing in search
    picker.search_var.set("gpt")
    # Should show only gpt-3.5 and gpt-4
    assert picker.listbox.size() == 2
    assert picker.listbox.get(0) == "gpt-3.5"
    assert picker.listbox.get(1) == "gpt-4"
    picker.destroy()

def test_filter_case_insensitive(root, sample_models):
    picker = ModelPicker(root, sample_models)
    picker.search_var.set("BERT")
    assert picker.listbox.size() == 1
    assert picker.listbox.get(0) == "bert-base"
    picker.destroy()

def test_filter_no_match(root, sample_models):
    picker = ModelPicker(root, sample_models)
    picker.search_var.set("nonexistent")
    assert picker.listbox.size() == 0
    picker.destroy()

def test_clear_filter_shows_all(root, sample_models):
    picker = ModelPicker(root, sample_models)
    picker.search_var.set("gpt")
    picker.search_var.set("")
    assert picker.listbox.size() == len(sample_models)
    picker.destroy()

def test_selection_triggers_callback(root, sample_models):
    selected_models = []
    def callback(model):
        selected_models.append(model)
    picker = ModelPicker(root, sample_models, on_select=callback)
    # Simulate selecting the first item
    picker.listbox.selection_set(0)
    picker.listbox.event_generate("<<ListboxSelect>>")
    assert selected_models == ["gpt-3.5"]
    picker.destroy()

def test_get_selected_returns_none_when_nothing_selected(root, sample_models):
    picker = ModelPicker(root, sample_models)
    assert picker.get_selected() is None
    picker.destroy()

def test_get_selected_after_filter(root, sample_models):
    picker = ModelPicker(root, sample_models)
    picker.search_var.set("claude")
    picker.listbox.selection_set(0)
    picker.listbox.event_generate("<<ListboxSelect>>")
    assert picker.get_selected() == "claude-2"
    picker.destroy()

def test_destroy_removes_frame(root, sample_models):
    picker = ModelPicker(root, sample_models)
    frame = picker.frame
    assert frame.winfo_exists()
    picker.destroy()
    # After destroy, frame should not exist
    try:
        exists = frame.winfo_exists()
        assert not exists
    except tk.TclError:
        pass
