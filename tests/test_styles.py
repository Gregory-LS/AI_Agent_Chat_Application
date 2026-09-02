import unittest
import html
import re
class TestStyles(unittest.TestCase):
    def test_html_structure(self):
        with open('static/index.html', 'r') as f:
            content = f.read()
        self.assertIn('<html', content)
        self.assertIn('</html>', content)
        self.assertIn('<head>', content)
        self.assertIn('</head>', content)
        self.assertIn('<body>', content)
        self.assertIn('</body>', content)
        self.assertIn('id="app"', content)
        self.assertIn('id="sidebar"', content)
        self.assertIn('id="chat-area"', content)
        self.assertIn('id="composer"', content)
        self.assertIn('id="model-picker-modal"', content)
        self.assertIn('id="skills-drawer"', content)
        self.assertIn('id="settings-modal"', content)

    def test_essential_elements(self):
        with open('static/index.html', 'r') as f:
            content = f.read()
        self.assertIn('id="message-input"', content)
        self.assertIn('id="send-btn"', content)
        self.assertIn('id="new-chat-btn"', content)
        self.assertIn('id="conversation-list"', content)
        self.assertIn('id="models-btn"', content)
        self.assertIn('id="skills-btn"', content)
        self.assertIn('id="settings-btn"', content)
        self.assertIn('id="stop-btn"', content)
        self.assertIn('id="model-search"', content)
        self.assertIn('id="model-list"', content)
        self.assertIn('id="skills-list"', content)
        self.assertIn('id="api-key-input"', content)
        self.assertIn('id="theme-select"', content)

    def test_markup_validity(self):
        with open('static/index.html', 'r') as f:
            content = f.read()
        # Simple check: no unclosed tags or obvious issues
        open_tags = re.findall(r'<([a-zA-Z]+)[^>]*>', content)
        close_tags = re.findall(r'</([a-zA-Z]+)>', content)
        for tag in ['html', 'head', 'body', 'aside', 'main', 'header', 'div']:
            self.assertIn(tag, open_tags)
            self.assertIn(tag, close_tags)

if __name__ == '__main__':
    unittest.main()
