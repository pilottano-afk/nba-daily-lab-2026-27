from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest

class AppTests(unittest.TestCase):
    def test_app_starts_without_unhandled_errors(self):
        path = Path(__file__).resolve().parents[1] / 'app.py'
        app = AppTest.from_file(str(path)).run(timeout=30)
        self.assertEqual(len(app.exception), 0)
