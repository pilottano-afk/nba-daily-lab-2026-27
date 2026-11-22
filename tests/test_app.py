import unittest
from streamlit.testing.v1 import AppTest

class AppTests(unittest.TestCase):
    def test_app_starts_without_unhandled_errors(self):
        app = AppTest.from_file('app.py').run(timeout=30)
        self.assertEqual(len(app.exception), 0)
