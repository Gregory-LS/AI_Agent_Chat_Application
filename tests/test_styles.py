import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS_PATH = ROOT / 'static' / 'styles.css'


class TestStyles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = CSS_PATH.read_text(encoding='utf-8')

    def test_file_exists_and_nonempty(self):
        self.assertTrue(CSS_PATH.exists())
        self.assertGreater(len(self.css), 0)

    def test_theme_variables(self):
        self.assertIn(':root', self.css)
        self.assertIn("[data-theme='dark']", self.css)

    def test_core_layout_selectors(self):
        for selector in ('.sidebar', '.chat', '.composer', '.drawer', '.modal', '.messages', '.message'):
            self.assertIn(selector, self.css)

    def test_braces_balanced(self):
        self.assertEqual(self.css.count('{'), self.css.count('}'))

    def test_no_url_missing(self):
        self.assertNotIn('url(', self.css)


if __name__ == '__main__':
    unittest.main()
