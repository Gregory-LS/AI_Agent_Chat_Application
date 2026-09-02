import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class TestConversationManagementUI(unittest.TestCase):
    def test_static_files_exist(self):
        static_dir = BASE_DIR / '_app' / 'static'
        for name in (
            'conversations.html',
            'conversation_management.js',
            'conversation_management.css',
        ):
            self.assertTrue(
                (static_dir / name).exists(),
                f'{name} is missing in _app/static/'
            )

    def test_html_contains_required_elements(self):
        html = (BASE_DIR / '_app' / 'static' / 'conversations.html').read_text()
        self.assertIn('id="conversation-list"', html)
        self.assertIn('id="search-input"', html)
        self.assertIn('id="filter-status"', html)
        self.assertIn('id="export-all"', html)
        self.assertIn('id="import-file"', html)
        self.assertIn('id="bulk-archive"', html)
        self.assertIn('id="bulk-unarchive"', html)
        self.assertIn('id="bulk-export"', html)
        self.assertIn('id="bulk-delete"', html)

    def test_js_contains_core_functions(self):
        js = (BASE_DIR / '_app' / 'static' / 'conversation_management.js').read_text()
        self.assertIn('function toggleArchive', js)
        self.assertIn('function exportAll', js)
        self.assertIn('function exportSelected', js)
        self.assertIn('function importFile', js)

    def test_css_contains_style(self):
        css = (BASE_DIR / '_app' / 'static' / 'conversation_management.css').read_text()
        self.assertIn('.conversation-table', css)
        self.assertIn('.badge-archived', css)


if __name__ == '__main__':
    unittest.main()
