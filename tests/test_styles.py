import os
import unittest

class TestStyles(unittest.TestCase):
    def setUp(self):
        self.styles_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'styles.css')
        self.assertTrue(os.path.exists(self.styles_path), 'styles.css not found')

    def test_light_theme_variables(self):
        with open(self.styles_path, 'r') as f:
            content = f.read()
        # Check that :root has light theme variables
        self.assertIn('--bg-primary: #ffffff', content)
        self.assertIn('--text-primary: #1a1a1a', content)
        self.assertIn('--accent: #3b82f6', content)

    def test_dark_theme_variables(self):
        with open(self.styles_path, 'r') as f:
            content = f.read()
        # Check that [data-theme="dark"] has dark theme variables
        self.assertIn('[data-theme="dark"]', content)
        self.assertIn('--bg-primary: #1a1a2e', content)
        self.assertIn('--text-primary: #e0e0e0', content)
        self.assertIn('--accent: #60a5fa', content)

    def test_theme_toggle_selector(self):
        with open(self.styles_path, 'r') as f:
            content = f.read()
        self.assertIn('#theme-toggle', content)

if __name__ == '__main__':
    unittest.main()
