import unittest
import pandas as pd
from analytics import combine, per_game, percentiles

class AnalyticsTests(unittest.TestCase):
    def test_per_game_does_not_change_rates(self):
        frame = pd.DataFrame({'GP': [2, 0], 'PTS': [20, 0], 'TS_PCT': [.6, .5]})
        result = per_game(frame)
        self.assertEqual(result.loc[0, 'PTS'], 10)
        self.assertTrue(pd.isna(result.loc[1, 'PTS']))
        self.assertEqual(result.loc[0, 'TS_PCT'], .6)

    def test_percentiles(self):
        frame = pd.DataFrame({'x': [10, 20, 30]})
        self.assertEqual(percentiles(frame, 'x').tolist(), [0, 50, 100])
        self.assertEqual(percentiles(frame, 'x', True).tolist(), [100, 50, 0])

    def test_combine(self):
        base = pd.DataFrame({'TEAM_ID': [1], 'GP': [3]})
        advanced = pd.DataFrame({'TEAM_ID': [1], 'GP': [3], 'NET_RATING': [5]})
        self.assertEqual(combine(base, advanced, 'teams').loc[0, 'NET_RATING'], 5)

    def test_single_percentile_missing(self):
        self.assertTrue(percentiles(pd.DataFrame({'x': [2]}), 'x').isna().all())
