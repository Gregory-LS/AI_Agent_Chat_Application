import unittest
import os
import re

class TestStyles(unittest.TestCase):
    """Test CSS file validity and consistency."""

    @classmethod
    def setUpClass(cls):
        cls.css_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'styles.css')
        with open(cls.css_path, 'r') as f:
            cls.css_content = f.read()

    def test_file_exists(self):
        self.assertTrue(os.path.exists(self.css_path))

    def test_css_syntax_basic(self):
        """Check for balanced braces and basic syntax."""
        open_braces = self.css_content.count('{')
        close_braces = self.css_content.count('}')
        self.assertEqual(open_braces, close_braces,
                         f"Unbalanced braces: {open_braces} open vs {close_braces} close")

    def test_no_html_in_css(self):
        """Ensure CSS file doesn't contain HTML tags."""
        self.assertNotIn('<style', self.css_content)
        self.assertNotIn('</style', self.css_content)

    def test_light_theme_variables(self):
        """:root should have light theme variables."""
        self.assertIn(':root', self.css_content)
        self.assertIn('--bg-primary', self.css_content)

    def test_dark_theme_variables(self):
        """Dark theme should be defined via data-theme attribute."""
        self.assertIn('[data-theme="dark"]', self.css_content)
        self.assertIn('--bg-primary', self.css_content)

    def test_theme_contrast(self):
        """Light and dark theme should have different primary background values."""
        light_match = re.search(r':root\s*\{[^}]*--bg-primary:\s*([^;]+)', self.css_content)
        dark_match = re.search(r'\[data-theme="dark"\]\s*\{[^}]*--bg-primary:\s*([^;]+)', self.css_content)
        self.assertIsNotNone(light_match, "Could not find --bg-primary in :root")
        self.assertIsNotNone(dark_match, "Could not find --bg-primary in dark theme")
        self.assertNotEqual(light_match.group(1).strip(), dark_match.group(1).strip(),
                            "Light and dark themes should have different --bg-primary")

    def test_keyframes_present(self):
        """Should have animation keyframes."""
        self.assertIn('@keyframes', self.css_content)

    def test_media_query_responsive(self):
        """Should have responsive media query."""
        self.assertIn('@media', self.css_content)

    def test_no_important_overrides(self):
        """Avoid !important to maintain specificity."""
        important_count = self.css_content.count('!important')
        self.assertLess(important_count, 5,
                        f"Too many !important declarations ({important_count})")

    def test_selector_coverage(self):
        """Ensure key UI components have styles."""
        required_selectors = [
            '.sidebar',
            '.message',
            '.composer',
            '.drawer',
            '.modal',
            '.btn',
            '.toast',
            '.spinner',
            '.model-picker',
            '.skill-item',
            '.balance-display',
            '.typing-indicator',
        ]
        for selector in required_selectors:
            with self.subTest(selector=selector):
                self.assertIn(selector, self.css_content,
                              f"Missing styles for selector: {selector}")

    def test_css_custom_properties_defined(self):
        """All referenced custom properties should be defined in :root or dark theme."""
        # Find all var(--*) usages
        var_usages = set(re.findall(r'var\((--[a-z-]+)\)', self.css_content))
        # Find all definitions in :root and [data-theme="dark"]
        root_defs = set(re.findall(r'--[a-z-]+\s*:', self.css_content))
        root_defs = {d.replace(':', '').strip() for d in root_defs}
        # Check each usage has a definition
        for var_name in var_usages:
            if var_name not in root_defs:
                self.fail(f"CSS custom property {var_name} is used but not defined")

    def test_no_absolute_urls(self):
        """CSS should not contain absolute URLs (no external dependencies)."""
        self.assertNotIn('url(http', self.css_content)
        self.assertNotIn('url(https', self.css_content)

    def test_font_family_system(self):
        """Font families should use system fonts."""
        self.assertIn('-apple-system', self.css_content)
        self.assertIn('BlinkMacSystemFont', self.css_content)


if __name__ == '__main__':
    unittest.main()
