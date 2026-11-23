# Stato implementazione

Acquisizione giocatori e squadre indipendente dai quintetti: scripts/refresh_core.py, avvio manuale e finestra giornaliera delle 08:15 italiane tramite core.yml. I controlli di stagione, tipo di competizione, valori Totals, colonne, chiavi uniche e copertura base/avanzate sono mantenuti per entrambe le sezioni.

Quintetti sospesi finché le differenze diagnosticate non sono riconciliate. Non vengono eliminate differenze per ottenere artificialmente un insieme comune. L'app mostra un messaggio dedicato quando una sezione non è presente nel manifesto.

Il successo di una richiesta di esecuzione non prova il successo del download. Consultare data/current.json e data/last_attempt.json. La completezza calendario non è ancora certificata. Nessun hosting dell'app è configurato da questa modifica.
