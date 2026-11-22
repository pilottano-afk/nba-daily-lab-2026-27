"""Acquisizione stagionale: pubblica solo snapshot completi e validati."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import tempfile
import time
from datetime import datetime, timezone
from nba_api.stats.endpoints import leaguedashplayerstats, leaguedashteamstats, leaguedashlineups

ROOT = Path(__file__).resolve().parents[1] / 'data'
SPECS = [
    ('players_base', leaguedashplayerstats.LeagueDashPlayerStats, 'Base', ['PLAYER_ID', 'TEAM_ID'], ['PTS', 'MIN', 'GP']),
    ('players_advanced', leaguedashplayerstats.LeagueDashPlayerStats, 'Advanced', ['PLAYER_ID', 'TEAM_ID'], ['NET_RATING', 'TS_PCT']),
    ('teams_base', leaguedashteamstats.LeagueDashTeamStats, 'Base', ['TEAM_ID'], ['PTS', 'GP']),
    ('teams_advanced', leaguedashteamstats.LeagueDashTeamStats, 'Advanced', ['TEAM_ID'], ['OFF_RATING', 'DEF_RATING', 'NET_RATING']),
    ('lineups_base', leaguedashlineups.LeagueDashLineups, 'Base', ['TEAM_ID', 'GROUP_ID'], ['MIN', 'GP']),
    ('lineups_advanced', leaguedashlineups.LeagueDashLineups, 'Advanced', ['TEAM_ID', 'GROUP_ID'], ['NET_RATING']),
]

def validate(frame, keys, fields):
    missing = set(keys + fields) - set(frame.columns)
    if missing:
        raise ValueError(f'Colonne mancanti: {sorted(missing)}')
    if frame.empty:
        raise ValueError('Risposta vuota: snapshot non pubblicato')
    if frame[keys].isna().any().any() or frame.duplicated(keys).any():
        raise ValueError('Identificatori mancanti o duplicati')
    return frame

def fetch(factory, season, measure):
    for attempt in range(3):
        try:
            return factory(season=season, season_type_all_star='Regular Season',
                           measure_type_detailed_defense=measure,
                           per_mode_detailed='Totals', timeout=45).get_data_frames()[0]
        except Exception:
            if attempt == 2:
                raise
            time.sleep(5 * 2 ** attempt)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--season', default='2026-27')
    args = parser.parse_args()
    if args.season != '2026-27':
        parser.error('Questa versione acquisisce solo la stagione 2026-27')
    ROOT.mkdir(exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    try:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            staging = Path(directory)
            tables = {}
            for name, factory, measure, keys, fields in SPECS:
                frame = validate(fetch(factory, args.season, measure), keys, fields)
                path = staging / f'{name}.parquet'
                frame.to_parquet(path, index=False)
                tables[name] = {'rows': len(frame), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                time.sleep(2)
            for prefix, keys in [('players', ['PLAYER_ID', 'TEAM_ID']), ('teams', ['TEAM_ID']), ('lineups', ['TEAM_ID', 'GROUP_ID'])]:
                import pandas as pd
                base = pd.read_parquet(staging / f'{prefix}_base.parquet')
                advanced = pd.read_parquet(staging / f'{prefix}_advanced.parquet')
                if set(map(tuple, base[keys].values)) != set(map(tuple, advanced[keys].values)):
                    raise ValueError(f'Copertura base/avanzate incoerente: {prefix}')
            snapshot = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            destination = ROOT / 'snapshots' / snapshot
            destination.parent.mkdir(exist_ok=True)
            staging.rename(destination)
            manifest = {'season': args.season, 'season_type': 'Regular Season', 'per_mode': 'Totals',
                        'source': 'stats.nba.com tramite nba_api', 'nba_api_version': importlib.metadata.version('nba_api'),
                        'started_at': started, 'updated_at': datetime.now(timezone.utc).isoformat(),
                        'snapshot': f'snapshots/{snapshot}', 'tables': tables,
                        'coverage_note': 'Acquisizione completata; non certifica che tutte le partite concluse siano gia pubblicate dalla fonte.'}
            temporary = ROOT / 'current.tmp'
            temporary.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
            os.replace(temporary, ROOT / 'current.json')
        (ROOT / 'last_attempt.json').write_text(json.dumps({'status': 'ok', 'started_at': started}), encoding='utf-8')
    except Exception as exc:
        (ROOT / 'last_attempt.json').write_text(json.dumps({'status': 'failed', 'started_at': started, 'error': str(exc)}), encoding='utf-8')
        raise

if __name__ == '__main__':
    main()
