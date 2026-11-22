"""Adatta nomi e seleziona quintetti senza alterare i valori statistici."""
import refresh_secondary as importer

mapping = {'players_base': 'player_stats_base', 'players_advanced': 'player_stats_advanced', 'teams_base': 'team_stats_base', 'teams_advanced': 'team_stats_advanced', 'lineups_base': 'lineups_base', 'lineups_advanced': 'lineups_advanced'}
original_get = importer.requests.Session.get

def get_with_aliases(self, url, *args, **kwargs):
    response = original_get(self, url, *args, **kwargs)
    if '/contents/nba_stats/leaguedash/parquet' in url and response.ok:
        original_json = response.json
        def aliased_json():
            items = original_json()
            if not isinstance(items, list):
                return items
            inverse = {v + '_2027.parquet': k + '_2027.parquet' for k, v in mapping.items()}
            return [dict(item, name=inverse.get(item['name'], item['name'])) for item in items]
        response.json = aliased_json
    return response

original_download = importer.requests.get

def download_with_names(url, *args, **kwargs):
    for local, source in mapping.items():
        url = url.replace('/' + local + '_2027.parquet', '/' + source + '_2027.parquet')
    return original_download(url, *args, **kwargs)

original_normalize = importer.normalize

def normalize_selected(frame, kind):
    if kind == 'lineups':
        columns = {str(c).upper(): c for c in frame.columns}
        if 'GROUP_QUANTITY' in columns:
            quantity = importer.pd.to_numeric(frame[columns['GROUP_QUANTITY']], errors='coerce')
            frame = frame.loc[quantity.eq(5)].copy()
        elif 'GROUP_ID' in columns:
            def five_ids(value):
                parts = [p for p in str(value).split('-') if p]
                return len(parts) == 5 and len(set(parts)) == 5 and all(p.isdigit() for p in parts)
            frame = frame.loc[frame[columns['GROUP_ID']].map(five_ids)].copy()
            frame['group_quantity'] = 5
        else:
            raise ValueError('Impossibile verificare composizione quintetti')
        if frame.empty:
            raise ValueError('Nessun quintetto di cinque giocatori verificabile')
    return original_normalize(frame, kind)

importer.requests.Session.get = get_with_aliases
importer.requests.get = download_with_names
importer.normalize = normalize_selected
if __name__ == '__main__':
    importer.main()
