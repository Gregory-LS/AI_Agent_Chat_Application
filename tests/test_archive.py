import json
import unittest
from http.server import HTTPServer
from threading import Thread
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from _app.server import ChatHandler, conversations

class TestArchiveEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Clear any leftover state
        conversations.clear()
        # Start server on a random port
        cls.server = HTTPServer(('localhost', 0), ChatHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = Thread(target=cls.server.serve_forever)
        cls.thread.daemon = True
        cls.thread.start()
        cls.base_url = f'http://localhost:{cls.port}/api/conversations'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()

    def setUp(self):
        # Create a fresh conversation for each test
        req = Request(self.base_url, data=b'{"title":"Test"}', method='POST')
        resp = urlopen(req)
        self.conv = json.loads(resp.read())
        self.conv_id = self.conv['id']

    def test_archive_conversation(self):
        url = f'{self.base_url}/{self.conv_id}/archive'
        req = Request(url, method='POST')
        resp = urlopen(req)
        data = json.loads(resp.read())
        self.assertEqual(resp.status, 200)
        self.assertTrue(data['archived'])

    def test_unarchive_conversation(self):
        # First archive
        url = f'{self.base_url}/{self.conv_id}/archive'
        urlopen(Request(url, method='POST'))
        # Then unarchive
        url = f'{self.base_url}/{self.conv_id}/unarchive'
        req = Request(url, method='POST')
        resp = urlopen(req)
        data = json.loads(resp.read())
        self.assertEqual(resp.status, 200)
        self.assertFalse(data['archived'])

    def test_archive_nonexistent(self):
        url = f'{self.base_url}/nonexistent/archive'
        with self.assertRaises(HTTPError) as ctx:
            urlopen(Request(url, method='POST'))
        self.assertEqual(ctx.exception.code, 404)

    def test_unarchive_nonexistent(self):
        url = f'{self.base_url}/nonexistent/unarchive'
        with self.assertRaises(HTTPError) as ctx:
            urlopen(Request(url, method='POST'))
        self.assertEqual(ctx.exception.code, 404)

    def test_archive_already_archived(self):
        # Archive twice
        url = f'{self.base_url}/{self.conv_id}/archive'
        urlopen(Request(url, method='POST'))
        resp = urlopen(Request(url, method='POST'))
        data = json.loads(resp.read())
        self.assertTrue(data['archived'])

if __name__ == '__main__':
    unittest.main()
