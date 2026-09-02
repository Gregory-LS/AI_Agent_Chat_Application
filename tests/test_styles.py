import unittest
from pathlib import Path
import re


class TestStyles(unittest.TestCase):
    """Tests for CSS styles"""

    def setUp(self):
        self.styles_path = Path(__file__).parent.parent / 'static' / 'styles.css'
        self.css_content = self.styles_path.read_text()

    def test_css_file_exists(self):
        """Test that styles.css exists"""
        self.assertTrue(self.styles_path.exists())

    def test_light_theme_variables(self):
        """Test that light theme variables are defined"""
        self.assertIn('--bg-primary', self.css_content)
        self.assertIn('--text-primary', self.css_content)
        self.assertIn('--accent', self.css_content)

    def test_dark_theme_variables(self):
        """Test that dark theme variables are defined"""
        self.assertIn('[data-theme="dark"]', self.css_content)
        self.assertIn('--bg-primary', self.css_content)

    def test_modal_styles(self):
        """Test that modal styles exist"""
        self.assertIn('.modal', self.css_content)
        self.assertIn('.modal-content', self.css_content)
        self.assertIn('.modal-header', self.css_content)
        self.assertIn('.modal-body', self.css_content)
        self.assertIn('.modal-footer', self.css_content)

    def test_settings_input_styles(self):
        """Test that settings input styles exist"""
        self.assertIn('#settings-api-key', self.css_content)  # ID selector
        # Check for input styling in modal-body
        self.assertIn('.modal-body input', self.css_content)
        self.assertIn('.modal-body select', self.css_content)

    def test_css_syntax(self):
        """Test basic CSS syntax validity"""
        # Check that braces are balanced
        open_braces = self.css_content.count('{')
        close_braces = self.css_content.count('}')
        self.assertEqual(open_braces, close_braces, 'Unbalanced braces in CSS')


if __name__ == '__main__':
    unittest.main()
