# NBA Daily Lab 2026/27

Progetto pubblico nuovo, separato dai precedenti progetti LBA ed EuroLeague.

## Stato reale
Interfaccia Streamlit e acquisizione implementate. La presenza del codice non certifica dati disponibili: una prima acquisizione completa deve riuscire. Nessun sito e ancora distribuito su un servizio di hosting. L'app non sostituisce mai i dati mancanti con esempi sintetici.

## Avvio app
```sh
pip install -r requirements-app.txt
streamlit run app.py
```

Tre sezioni: giocatori, squadre, quintetti. Filtri per squadra, nome e minuti totali; conteggi totali o per partita; tabella esportabile CSV; confronto dei primi 15 risultati; percentili sul gruppo filtrato. Le percentuali NBA sono visualizzate come frazioni. Per giocatori trasferiti la granularita puo essere giocatore/squadra, non necessariamente una sola riga per persona.

## Dati e controlli
```sh
python -m unittest discover -s tests
python scripts/refresh.py --season 2026-27
```
Sei tabelle Parquet stagionali: giocatori, squadre e quintetti, statistiche base e avanzate. Solo regular season 2026-27. Fonte NBA Stats tramite nba_api. data/current.json punta all'ultimo snapshot completo. Risposte vuote, colonne mancanti, identificatori duplicati e disallineamento base/avanzate impediscono la promozione. In caso di errore resta disponibile lo snapshot precedente. data/last_attempt.json distingue l'ultimo tentativo dall'ultimo successo. L'app verifica le impronte dei file prima di leggerli. I timestamp indicano l'acquisizione, non l'ultima partita inclusa.

## Aggiornamento
GitHub Actions tenta alle 06:00 e 07:00 UTC e procede solo quando in Europe/Rome sono le 08: gestisce l'ora legale. Eventuali ritardi GitHub possono far saltare la finestra: non e una garanzia di disponibilita alle 08:00. Avvio manuale disponibile. Ricaricamento intera stagione, non ancora incrementale.

Repository pubblico: vengono usati runner standard GitHub, senza servizi aggiuntivi a pagamento configurati. Pubblicare il codice non equivale ad autorizzare la redistribuzione dei dati NBA: verificare i termini prima di un lancio pubblico dell'app.

## Limiti attuali
Prima acquisizione da verificare; nessuna certificazione delle partite incluse; tracking/hustle non ancora acquisiti; dipendenze non ancora bloccate a versioni esatte; snapshot storici senza politica di pulizia; interfaccia non ancora distribuita online. La verifica applicazione esegue test di calcolo e un controllo di avvio Streamlit; non sostituisce una verifica visiva nel browser.
