import unittest
import html.parser
import os

class HTMLUploadUIParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.found_attachment_button = False
        self.found_file_input = False
        self.found_preview = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'button' and attrs_dict.get('id') == 'attachment-button':
            self.found_attachment_button = True
        if tag == 'input' and attrs_dict.get('type') == 'file' and attrs_dict.get('id') == 'file-input':
            self.found_file_input = True
        if tag == 'div' and attrs_dict.get('id') == 'attachment-preview':
            self.found_preview = True

class TestUploadUI(unittest.TestCase):
    def setUp(self):
        # Path relative to project root
        html_path = os.path.join(os.path.dirname(__file__), '..', '_app', 'static', 'index.html')
        with open(html_path, 'r', encoding='utf-8') as f:
            self.html_content = f.read()

    def test_attachment_button_exists(self):
        parser = HTMLUploadUIParser()
        parser.feed(self.html_content)
        self.assertTrue(parser.found_attachment_button, "Attachment button (#attachment-button) not found in index.html")

    def test_file_input_exists(self):
        parser = HTMLUploadUIParser()
        parser.feed(self.html_content)
        self.assertTrue(parser.found_file_input, "File input (#file-input) not found in index.html")

    def test_attachment_preview_exists(self):
        parser = HTMLUploadUIParser()
        parser.feed(self.html_content)
        self.assertTrue(parser.found_preview, "Attachment preview (#attachment-preview) not found in index.html")

if __name__ == '__main__':
    unittest.main()