"""Diagnosi senza promozione di snapshot o modifica delle tabelle."""
import io
import json
import os
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import requests

session = requests.Session()
if os.environ.get('GH_TOKEN'):
    session.headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
response = session.get('https://api.github.com/repos/sportsdataverse/hoopR-nba-stats-data/commits/main', timeout=45)
response.raise_for_status()
revision = response.json()['sha']
report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'source_revision': revision, 'promoted': False, 'tables': {}}
frames = {}
for measure in ['base', 'advanced']:
    url = f'https://raw.githubusercontent.com/sportsdataverse/hoopR-nba-stats-data/{revision}/nba_stats/leaguedash/parquet/lineups_{measure}_2027.parquet'
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    frame = pd.read_parquet(io.BytesIO(response.content))
    frame.columns = frame.columns.str.upper()
    details = {'source_url': url, 'rows_before_filter': len(frame), 'columns': list(frame.columns)}
    for column in ['GROUP_QUANTITY', 'SEASON', 'SEASON_TYPE', 'PER_MODE']:
        if column in frame:
            details[column] = frame[column].astype(str).value_counts(dropna=False).to_dict()
    if 'GROUP_QUANTITY' in frame:
        frame = frame.loc[pd.to_numeric(frame['GROUP_QUANTITY'], errors='coerce').eq(5)].copy()
    def canonical(value):
        parts = [p for p in str(value).split('-') if p]
        return '-'.join(sorted(parts)) if len(parts) == 5 and len(set(parts)) == 5 and all(p.isdigit() for p in parts) else None
    frame['CANONICAL_GROUP'] = frame['GROUP_ID'].map(canonical)
    details['invalid_group_ids'] = int(frame['CANONICAL_GROUP'].isna().sum())
    details['rows_after_filter'] = len(frame)
    details['duplicate_raw_keys'] = int(frame.duplicated(['TEAM_ID', 'GROUP_ID']).sum())
    details['duplicate_canonical_keys'] = int(frame.duplicated(['TEAM_ID', 'CANONICAL_GROUP']).sum())
    report['tables'][measure] = details
    frames[measure] = frame
for mode, column in [('raw', 'GROUP_ID'), ('canonical', 'CANONICAL_GROUP')]:
    keys = ['TEAM_ID', column]
    base, advanced = frames['base'], frames['advanced']
    left = set(map(tuple, base[keys].values))
    right = set(map(tuple, advanced[keys].values))
    differences = {'base_only_count': len(left-right), 'advanced_only_count': len(right-left), 'common_count': len(left & right)}
    for label, frame, selected in [('base_only', base, left-right), ('advanced_only', advanced, right-left)]:
        mask = frame[keys].apply(tuple, axis=1).isin(selected)
        fields = [c for c in ['TEAM_ID', 'GROUP_ID', 'GROUP_NAME', 'GP', 'MIN', 'POSS', 'CANONICAL_GROUP'] if c in frame]
        differences[label + '_examples'] = json.loads(frame.loc[mask, fields].head(10).to_json(orient='records'))
        if 'MIN' in frame:
            differences[label + '_minutes_sum'] = float(pd.to_numeric(frame.loc[mask, 'MIN'], errors='coerce').sum())
    if not base.duplicated(keys).any() and not advanced.duplicated(keys).any():
        shared = base.merge(advanced, on=keys, suffixes=('_base', '_advanced'), validate='one_to_one')
        for field in ['GP', 'MIN']:
            if field+'_base' in shared and field+'_advanced' in shared:
                delta = (pd.to_numeric(shared[field+'_base'], errors='coerce') - pd.to_numeric(shared[field+'_advanced'], errors='coerce')).abs()
                differences[field + '_different_common_rows'] = int(delta.gt(0.001).sum())
    report[mode] = differences
path = Path(__file__).resolve().parents[1] / 'reports'
path.mkdir(exist_ok=True)
(path/'lineup_diagnosis.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
