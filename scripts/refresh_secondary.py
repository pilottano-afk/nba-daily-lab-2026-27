"""Importa sei tabelle SportsDataverse solo dopo controlli espliciti."""
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
from datetime import datetime, timezone
import pandas as pd
import requests
from refresh import validate

ROOT = Path(__file__).resolve().parents[1]
KEYS = {'players': ['PLAYER_ID', 'TEAM_ID'], 'teams': ['TEAM_ID'], 'lineups': ['TEAM_ID', 'GROUP_ID']}
REQUIRED = {'players_base': ['PTS', 'MIN', 'GP', 'PLAYER_NAME'], 'players_advanced': ['NET_RATING', 'TS_PCT'], 'teams_base': ['PTS', 'GP', 'MIN', 'TEAM_NAME'], 'teams_advanced': ['OFF_RATING', 'DEF_RATING', 'NET_RATING'], 'lineups_base': ['MIN', 'GP', 'GROUP_NAME'], 'lineups_advanced': ['NET_RATING']}

def normalize(frame, kind):
    frame = frame.rename(columns=lambda c: str(c).upper())
    if frame.columns.duplicated().any():
        raise ValueError('Colonne duplicate dopo normalizzazione')
    for column, accepted in [('SEASON', {'2027', '2026-27'}), ('SEASON_TYPE', {'Regular Season'}), ('PER_MODE', {'Totals'})]:
        if column not in frame or frame[column].isna().any() or not set(frame[column].astype(str)).issubset(accepted):
            raise ValueError(f'Metadati non compatibili: {column}')
    if kind == 'lineups':
        if 'GROUP_QUANTITY' not in frame or not pd.to_numeric(frame['GROUP_QUANTITY'], errors='coerce').eq(5).all():
            raise ValueError('Sono richiesti esclusivamente quintetti di cinque giocatori')
    return frame.rename(columns={'FG3_M': 'FG3M', 'FG3_A': 'FG3A'})

def main():
    data = ROOT / 'data'
    data.mkdir(exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    report = {'started_at': started, 'status': 'failed', 'source': 'SportsDataverse', 'promoted': False}
    try:
        session = requests.Session()
        if os.environ.get('GH_TOKEN'):
            session.headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
        response = session.get('https://api.github.com/repos/sportsdataverse/hoopR-nba-stats-data/commits/main', timeout=45)
        response.raise_for_status()
        commit = response.json()
        revision = commit['sha']
        response = session.get('https://api.github.com/repos/sportsdataverse/hoopR-nba-stats-data/contents/nba_stats/leaguedash/parquet', params={'ref': revision}, timeout=45)
        response.raise_for_status()
        listing = response.json()
        names = {item['name']: item for item in listing}
        report['source_revision'] = revision
        report['available_2027_files'] = [name for name in names if '2027' in name]
        tables, frames = {}, {}
        with tempfile.TemporaryDirectory(dir=data) as directory:
            staging = Path(directory)
            for name, fields in REQUIRED.items():
                kind, measure = name.split('_', 1)
                candidates = [f'{kind}_{measure}_2027.parquet', f'{kind.rstrip("s")}_{measure}_2027.parquet']
                matches = [candidate for candidate in dict.fromkeys(candidates) if candidate in names]
                if len(matches) != 1:
                    raise ValueError(f'Tabella non identificata univocamente: {name}; disponibili: {report["available_2027_files"]}')
                filename = matches[0]
                url = f'https://raw.githubusercontent.com/sportsdataverse/hoopR-nba-stats-data/{revision}/nba_stats/leaguedash/parquet/{filename}'
                response = requests.get(url, timeout=90)
                response.raise_for_status()
                frame = validate(normalize(pd.read_parquet(io.BytesIO(response.content)), kind), KEYS[kind], fields)
                frames[name] = frame
                path = staging / f'{name}.parquet'
                frame.to_parquet(path, index=False)
                tables[name] = {'rows': len(frame), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'source_url': url}
            for kind, keys in KEYS.items():
                base, advanced = frames[f'{kind}_base'], frames[f'{kind}_advanced']
                if set(map(tuple, base[keys].values)) != set(map(tuple, advanced[keys].values)):
                    raise ValueError(f'Copertura incoerente: {kind}')
            snapshot = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            target = data / 'snapshots' / snapshot
            target.parent.mkdir(exist_ok=True)
            staging.rename(target)
            manifest = {'season': '2026-27', 'season_type': 'Regular Season', 'per_mode': 'Totals', 'source': 'NBA Stats tramite SportsDataverse', 'source_revision': revision, 'source_commit_at': commit['commit']['committer']['date'], 'updated_at': datetime.now(timezone.utc).isoformat(), 'snapshot': f'snapshots/{snapshot}', 'tables': tables, 'coverage_note': 'Controlli strutturali superati; completezza calendario e freschezza delle singole tabelle non ancora certificate.'}
            temporary = data / 'current.tmp'
            temporary.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
            os.replace(temporary, data / 'current.json')
            report.update(status='ok', promoted=True, tables=tables)
    except Exception as exc:
        report['error'] = str(exc)
        raise
    finally:
        (data / 'last_attempt.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
