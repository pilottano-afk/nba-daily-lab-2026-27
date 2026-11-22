"""Adatta i nomi locali alle tabelle pubblicate dalla fonte."""
import refresh_secondary as importer

mapping = {'players_base': 'player_stats_base', 'players_advanced': 'player_stats_advanced', 'teams_base': 'team_stats_base', 'teams_advanced': 'team_stats_advanced', 'lineups_base': 'lineups_base', 'lineups_advanced': 'lineups_advanced'}
# Il nucleo di importazione usa nomi locali; il solo elenco dei file viene
# adattato senza modificare contenuti, controlli o metadati della fonte.
original_get = importer.requests.Session.get

def get_with_aliases(self, url, *args, **kwargs):
    response = original_get(self, url, *args, **kwargs)
    if '/contents/nba_stats/leaguedash/parquet' in url and response.ok:
        original_json = response.json
        def aliased_json():
            items = original_json()
            if not isinstance(items, list):
                return items
            result = []
            inverse = {v + '_2027.parquet': k + '_2027.parquet' for k, v in mapping.items()}
            for item in items:
                entry = dict(item)
                if entry.get('name') in inverse:
                    entry['name'] = inverse[entry['name']]
                result.append(entry)
            return result
        response.json = aliased_json
    return response

original_download = importer.requests.get

def download_with_names(url, *args, **kwargs):
    for local, source in mapping.items():
        url = url.replace('/' + local + '_2027.parquet', '/' + source + '_2027.parquet')
    return original_download(url, *args, **kwargs)

importer.requests.Session.get = get_with_aliases
importer.requests.get = download_with_names
if __name__ == '__main__':
    importer.main()
