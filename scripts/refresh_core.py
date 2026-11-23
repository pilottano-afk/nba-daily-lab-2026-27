"""Acquisizione indipendente di giocatori e squadre.
I quintetti non vengono promossi finche la copertura non e riconciliata.
"""
import run_secondary

importer = run_secondary.importer
importer.REQUIRED = {name: fields for name, fields in importer.REQUIRED.items() if not name.startswith('lineups_')}
importer.KEYS = {name: keys for name, keys in importer.KEYS.items() if name != 'lineups'}

if __name__ == '__main__':
    importer.main()
