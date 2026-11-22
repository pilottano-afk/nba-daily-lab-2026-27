import importlib.util
from pathlib import Path
import unittest
import pandas as pd

spec = importlib.util.spec_from_file_location('refresh', Path(__file__).resolve().parents[1] / 'scripts/refresh.py')
refresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)

class ValidationTests(unittest.TestCase):
    def test_valid(self):
        frame = pd.DataFrame({'PLAYER_ID': [1], 'PTS': [0]})
        self.assertIs(refresh.validate(frame, ['PLAYER_ID'], ['PTS']), frame)

    def test_empty(self):
        with self.assertRaises(ValueError):
            refresh.validate(pd.DataFrame(columns=['PLAYER_ID', 'PTS']), ['PLAYER_ID'], ['PTS'])

    def test_duplicates(self):
        with self.assertRaises(ValueError):
            refresh.validate(pd.DataFrame({'PLAYER_ID': [1, 1], 'PTS': [2, 3]}), ['PLAYER_ID'], ['PTS'])

    def test_missing(self):
        with self.assertRaises(ValueError):
            refresh.validate(pd.DataFrame({'PLAYER_ID': [1]}), ['PLAYER_ID'], ['PTS'])

if __name__ == '__main__':
    unittest.main()
