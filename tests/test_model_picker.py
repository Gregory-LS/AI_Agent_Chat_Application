import unittest
from unittest.mock import Mock
import tkinter as tk
from app.model_picker import ModelPicker

class TestModelPicker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.callback = Mock()

    def test_initialization_with_models(self):
        models = ["GPT-4", "BERT", "T5"]
        picker = ModelPicker(self.root, models, self.callback)
        self.assertEqual(picker.get_selected_model(), "GPT-4")
        self.assertIn("Select Model:", picker.label.cget("text"))
        self.assertEqual(picker.dropdown.cget('state'), 'readonly')

    def test_initialization_without_models(self):
        picker = ModelPicker(self.root, [], self.callback)
        self.assertEqual(picker.get_selected_model(), "No models available")
        self.assertEqual(picker.dropdown.cget('state'), 'disabled')

    def test_select_model_triggers_callback(self):
        models = ["ModelA", "ModelB"]
        picker = ModelPicker(self.root, models, self.callback)
        picker.dropdown.current(1)
        picker.selected_model.set("ModelB")
        picker._on_select()
        self.callback.assert_called_once_with("ModelB")

    def test_select_placeholder_does_not_trigger_callback(self):
        picker = ModelPicker(self.root, [], self.callback)
        picker._on_select()
        self.callback.assert_not_called()

    def test_update_models_with_new_list(self):
        models = ["OldModel"]
        picker = ModelPicker(self.root, models, self.callback)
        new_models = ["NewModel1", "NewModel2"]
        picker.update_models(new_models)
        self.assertEqual(picker.get_selected_model(), "NewModel1")
        self.assertEqual(picker.dropdown.cget('state'), 'readonly')

    def test_update_models_to_empty(self):
        models = ["OldModel"]
        picker = ModelPicker(self.root, models, self.callback)
        picker.update_models([])
        self.assertEqual(picker.get_selected_model(), "No models available")
        self.assertEqual(picker.dropdown.cget('state'), 'disabled')

if __name__ == '__main__':
    unittest.main()
