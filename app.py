"""Interfaccia di consultazione: nessuna chiamata live a NBA Stats."""
import hashlib
import json
from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st
from analytics import combine, per_game, percentiles

ROOT = Path(__file__).resolve().parent / 'data'
st.set_page_config(page_title='NBA Daily Lab', page_icon='🏀', layout='wide')
st.title('NBA Daily Lab · 2026/27')
st.caption('Giocatori, squadre e quintetti · stagione regolare · fonte NBA Stats')

attempt_path = ROOT / 'last_attempt.json'
if attempt_path.exists():
    attempt = json.loads(attempt_path.read_text())
    if attempt.get('status') == 'failed':
        st.warning('Ultimo tentativo di aggiornamento non riuscito. Se disponibile, viene mostrata l’ultima acquisizione valida.')
        with st.expander('Dettagli acquisizione'):
            st.write(attempt)
manifest_path = ROOT / 'current.json'
if not manifest_path.exists():
    st.info('Prima acquisizione valida non ancora disponibile. Non vengono mostrati dati dimostrativi.')
    st.link_button('Controlla acquisizione su GitHub', 'https://github.com/pilottano-afk/nba-daily-lab-2026-27/actions')
    st.stop()

try:
    manifest = json.loads(manifest_path.read_text())
    folder = (ROOT / manifest['snapshot']).resolve()
    if not folder.is_relative_to((ROOT / 'snapshots').resolve()):
        raise ValueError('Percorso acquisizione non valido')
    st.caption('Ultima acquisizione riuscita: ' + manifest['updated_at'] + ' · orario UTC')
    st.caption('La data di acquisizione non certifica la completezza delle ultime partite.')
    kind = st.sidebar.radio('Sezione', ['Giocatori', 'Squadre', 'Quintetti'])
    prefix = {'Giocatori': 'players', 'Squadre': 'teams', 'Quintetti': 'lineups'}[kind]
    frames = []
    for suffix in ['base', 'advanced']:
        name = f'{prefix}_{suffix}'
        path = folder / f'{name}.parquet'
        if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['tables'][name]['sha256']:
            raise ValueError('Controllo integrità dati non riuscito')
        frames.append(pd.read_parquet(path))
    frame = combine(*frames, prefix)
except (OSError, ValueError, KeyError) as exc:
    st.error(f'Impossibile caricare i dati verificati: {exc}')
    st.stop()

minimum = st.sidebar.number_input('Minuti totali minimi', min_value=0, value=50 if prefix == 'lineups' else 100, step=10)
frame = frame.loc[pd.to_numeric(frame['MIN'], errors='coerce') >= minimum].copy()
team_column = next((c for c in ['TEAM_ABBREVIATION', 'TEAM_NAME'] if c in frame), None)
if team_column:
    teams = st.sidebar.multiselect('Squadre', sorted(frame[team_column].dropna().unique()))
    if teams:
        frame = frame.loc[frame[team_column].isin(teams)].copy()
label = {'players': 'PLAYER_NAME', 'teams': 'TEAM_NAME', 'lineups': 'GROUP_NAME'}[prefix]
search = st.sidebar.text_input('Cerca nome')
if search:
    frame = frame.loc[frame[label].str.contains(search, case=False, regex=False, na=False)].copy()
mode = st.sidebar.radio('Statistiche di conteggio', ['Totali', 'Per partita'])
if mode == 'Per partita':
    frame = per_game(frame)
st.caption(f'Soglia: {minimum} minuti totali. I filtri definiscono anche la popolazione dei percentili. Le percentuali NBA restano frazioni: 0,5 equivale al 50%.')
if frame.empty:
    st.info('Nessun risultato con questi filtri.')
    st.stop()
metrics = [c for c in ['PTS', 'REB', 'AST', 'MIN', 'NET_RATING', 'OFF_RATING', 'DEF_RATING', 'TS_PCT', 'EFG_PCT', 'PACE', 'TOV'] if c in frame]
metric = st.selectbox('Statistica da confrontare', metrics)
lower = st.checkbox('Valori più bassi migliori', value=metric in ['DEF_RATING', 'TOV'])
frame['PERCENTILE'] = percentiles(frame, metric, lower)
ordered = frame.sort_values(metric, ascending=lower, na_position='last')
st.subheader(f'{kind} · {len(frame)} risultati')
st.caption('Percentile 100 = valore migliore nel gruppo filtrato; parità con rango medio. Con meno di due valori il percentile non viene calcolato. I giocatori trasferiti possono avere righe distinte per squadra.')
display_columns = list(dict.fromkeys([label] + ([team_column] if team_column else []) + ['GP'] + metrics + ['PERCENTILE']))
st.dataframe(ordered[display_columns], hide_index=True, use_container_width=True)
st.download_button('Scarica tabella filtrata', ordered.to_csv(index=False).encode('utf-8'), file_name=f'nba_{prefix}_2026-27.csv', mime='text/csv')
plot = ordered.head(15).copy()
plot['ETICHETTA'] = plot[label].astype(str) + (' · ' + plot[team_column].astype(str) if team_column and label != team_column else '')
chart = alt.Chart(plot).mark_bar().encode(x=alt.X(f'{metric}:Q', scale=alt.Scale(zero=True), title=metric), y=alt.Y('ETICHETTA:N', sort=plot['ETICHETTA'].tolist(), title=None), tooltip=['ETICHETTA', metric, 'PERCENTILE']).properties(height=max(240, len(plot) * 28))
st.altair_chart(chart, use_container_width=True)
with st.expander('Fonte e metodologia'):
    st.write('Statistiche stagionali aggregate NBA Stats. Rating e percentuali non vengono ricalcolati facendo medie delle singole righe. La modalità per partita divide solo i conteggi per GP. Nessuna inferenza causale dai quintetti con pochi minuti.')
    st.json(manifest)
