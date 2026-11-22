"""Verifica file e struttura della fonte secondaria senza promuovere dati nell'app."""
import io
import json
import os
from pathlib import Path
from datetime import datetime, timezone
import requests
import pandas as pd

REPO = 'sportsdataverse/hoopR-nba-stats-data'
FOLDERS = ['nba_stats/leaguedash/parquet', 'nba_stats/lineups/parquet']

def main():
    session = requests.Session()
    session.headers['Accept'] = 'application/vnd.github+json'
    if os.environ.get('GH_TOKEN'):
        session.headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'season_requested': '2026-27', 'season_end_year': 2027, 'source_repository': REPO, 'promoted': False, 'folders': []}
    for folder in FOLDERS:
        entry = {'path': folder, 'files': []}
        report['folders'].append(entry)
        try:
            response = session.get(f'https://api.github.com/repos/{REPO}/contents/{folder}', timeout=45)
            response.raise_for_status()
            listing = response.json()
            if not isinstance(listing, list):
                raise ValueError('Elenco file non valido')
            candidates = [item for item in listing if item.get('type') == 'file' and item['name'].endswith('.parquet') and ('2027' in item['name'] or '2026-27' in item['name'])]
            entry['listing_count'] = len(listing)
            entry['candidate_count'] = len(candidates)
            entry['available_season_filename_examples'] = [item['name'] for item in listing[-12:]]
            for item in candidates[:20]:
                result = {'name': item['name'], 'url': item['download_url'], 'git_blob_sha': item['sha']}
                entry['files'].append(result)
                try:
                    download = requests.get(item['download_url'], timeout=90)
                    download.raise_for_status()
                    frame = pd.read_parquet(io.BytesIO(download.content))
                    result['rows'] = len(frame)
                    result['columns'] = list(frame.columns)
                    result['season_values'] = {column: [str(value) for value in frame[column].drop_duplicates().head(10)] for column in frame if column.lower() in ['season', 'season_year', 'season_type', 'measure_type', 'per_mode']}
                except Exception as exc:
                    result['error'] = str(exc)
        except Exception as exc:
            entry['error'] = str(exc)
    destination = Path(__file__).resolve().parents[1] / 'reports'
    destination.mkdir(exist_ok=True)
    (destination / 'secondary_source.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
