import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from app import create_server


class TaskBuddyAppTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server("127.0.0.1", 0)
        cls.port = cls.server.server_port
        cls.base_url = "http://127.0.0.1:{}".format(cls.port)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def fetch(self, path, expected_status=200):
        try:
            with urlopen(self.base_url + path, timeout=5) as response:
                status = response.status
                body = response.read()
        except HTTPError as error:
            status = error.code
            body = error.read()
        self.assertEqual(status, expected_status)
        return body

    def test_home_page_serves_polished_accessible_html(self):
        html = self.fetch("/").decode("utf-8")
        self.assertIn('<title>TaskBuddy', html)
        self.assertIn('id="loading-status"', html)
        self.assertIn('role="status"', html)
        self.assertIn('role="alert"', html)
        self.assertIn('aria-live="polite"', html)
        self.assertIn('class="skip-link"', html)
        self.assertIn('<main', html)

    def test_static_javascript_is_served(self):
        js = self.fetch("/static/app.js").decode("utf-8")
        self.assertIn("loadTasks", js)
        self.assertIn("showToast", js)
        self.assertIn("setLoading", js)

    def test_static_css_is_served(self):
        css = self.fetch("/static/styles.css").decode("utf-8")
        self.assertIn("spinner", css)
        self.assertIn(".toast", css)
        self.assertIn("prefers-reduced-motion", css)

    def test_api_returns_tasks(self):
        data = json.loads(self.fetch("/api/data?delay=0").decode("utf-8"))
        self.assertIn("items", data)
        self.assertGreater(len(data["items"]), 0)
        self.assertIn("title", data["items"][0])

    def test_api_failure_returns_500(self):
        self.fetch("/api/data?fail=1&delay=0", expected_status=500)

    def test_unknown_path_returns_404(self):
        self.fetch("/nope", expected_status=404)


if __name__ == "__main__":
    unittest.main()
