# NBA Daily Lab 2026/27

Progetto nuovo, separato dai precedenti progetti LBA ed EuroLeague.

## Stato reale
Prima base di acquisizione implementata. Nessuna dashboard ancora pubblicata. Il corretto download della stagione 2026/27 deve essere confermato da una prima esecuzione riuscita: codice presente non significa dati disponibili.

## Dati
Sei tabelle stagionali: giocatori, squadre e quintetti, ciascuna con statistiche base e avanzate. Regular season 2026-27, valori Totals. Fonte: NBA Stats tramite nba_api. Nessun dato dimostrativo sostituisce risposte vuote o errori.

## Esecuzione
```sh
pip install -r requirements.txt
python -m unittest discover -s tests
python scripts/refresh.py --season 2026-27
```

Il file data/current.json punta all'ultimo snapshot completo. I dati sono in Parquet. Risposte vuote, colonne mancanti, identificatori duplicati e disallineamento tra tabelle base e avanzate impediscono la promozione. In caso di errore lo snapshot valido precedente resta disponibile. data/last_attempt.json distingue l'ultimo tentativo dall'ultimo successo. I timestamp indicano l'acquisizione, non la data dell'ultima partita inclusa.

## Aggiornamento
GitHub Actions prevede due attivazioni UTC, alle 06:00 e 07:00, e procede solo quando in Europe/Rome sono le 08. Gestisce cosi l'ora legale. Le pianificazioni GitHub possono essere ritardate: non e una garanzia di pubblicazione alle 08:00. Avvio manuale disponibile. Per ora si ricarica l'intera stagione; non e ancora un import incrementale per partita.

Il repository e privato: Actions usa le quote del piano GitHub. Nessun servizio a pagamento aggiuntivo e configurato e non si deve abilitare spesa oltre quota senza autorizzazione. Prima della distribuzione pubblica verificare diritti e termini dei dati NBA.

## Passi successivi
Verifica prima acquisizione reale; controllo calendario/partite incluse; blocco versione dipendenze dopo verifica; tracking e hustle; percentili con soglie esplicite; interfaccia di consultazione; politica di conservazione snapshot.
