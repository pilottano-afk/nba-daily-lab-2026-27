"""Trasformazioni riproducibili sulle tabelle stagionali."""
import pandas as pd

KEYS = {'players': ['PLAYER_ID', 'TEAM_ID'], 'teams': ['TEAM_ID'], 'lineups': ['TEAM_ID', 'GROUP_ID']}

def combine(base, advanced, kind):
    keys = KEYS[kind]
    extra = [c for c in advanced.columns if c not in base.columns and c not in keys]
    return base.merge(advanced[keys + extra], on=keys, how='left', validate='one_to_one')

def per_game(frame):
    result = frame.copy()
    games = pd.to_numeric(result['GP'], errors='coerce').replace(0, float('nan'))
    for column in ['MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 'OREB', 'DREB', 'PLUS_MINUS']:
        if column in result:
            result[column] = pd.to_numeric(result[column], errors='coerce') / games
    return result

def percentiles(frame, metric, lower_is_better=False):
    values = pd.to_numeric(frame[metric], errors='coerce')
    valid = values.notna().sum()
    if valid < 2:
        return pd.Series(float('nan'), index=frame.index)
    ranks = values.rank(method='average', ascending=not lower_is_better)
    return 100 * (ranks - 1) / (valid - 1)
