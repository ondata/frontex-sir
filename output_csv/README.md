# output_csv — Schema dati

CSV relazionali generati da `build_sir_csv.py` a partire dai file `.extracted.json` in `analysis_output/`.

Prodotti con:

```bash
python3 build_sir_csv.py --input-dir analysis_output --output-dir output_csv
```

Le due tabelle sono collegabili tramite il campo `record_uid`.

---

## `sir_records.csv`

Una riga per ogni `SirRecord` estratto dai PDF.

| nome_campo | tipo | descrizione | valore_esempio |
|---|---|---|---|
| `record_uid` | intero | Chiave primaria progressiva, unica per tutto il dataset | `1` |
| `batch` | stringa | Nome della cartella batch di origine (corrisponde al nome dello ZIP o PDF sorgente) | `10957_2024-final-sir-cat1` |
| `source_file` | stringa | Path relativo del PDF sorgente | `pdfs/10957_2024-final-sir-cat1/10957_2024-final-sir-cat.1.pdf` |
| `record_index` | intero | Indice del record all'interno del PDF (utile quando un PDF contiene più SIR) | `0` |
| `model` | stringa | Modello Gemini usato per l'estrazione | `gemini-2.5-flash` |
| `generated_at_utc` | datetime (ISO 8601) | Timestamp UTC dell'estrazione | `2026-02-16T16:42:51.651813+01:00` |
| `sir_id` | stringa | ID del Serious Incident Report nel formato `DDDDD/YYYY` | `10957/2024` |
| `report_date` | data (ISO 8601) | Data del rapporto | `2024-09-13` |
| `incident_date` | stringa | Data dell'incidente (può essere approssimativa o un range) | `2024-02-15` |
| `location_details` | stringa | Descrizione estesa del luogo estratta dal PDF | `The incident involved a group of 20 nationals detained in Serbia, transferred to the Serbia-Bulgaria border...` |
| `where_clear` | stringa | Luogo sintetico e leggibile ricavato dal modello | `Serbia-Bulgaria border area, near Pirot, Serbia` |
| `location_text_raw` | stringa | Testo grezzo della localizzazione così come appare nel PDF | `Serbia-Bulgaria border, Pirot, Bulgaria` |
| `country_or_area` | stringa | Paese o area geografica di riferimento | `Serbia, Bulgaria` |
| `location_type` | stringa (`sea / land / facility / mixed / unknown`) | Tipo di luogo | `land` |
| `precision_level` | stringa (`exact / approximate / broad / unknown`) | Granularità della localizzazione | `approximate` |
| `geocodable` | booleano | Se il luogo è sufficientemente preciso per essere geocodificato | `true` |
| `geocodable_query` | stringa | Query suggerita per la geocodifica (es. con Nominatim) | `Serbia-Bulgaria border near Pirot` |
| `lat` | decimale | Latitudine (se fornita direttamente dal modello, altrimenti vuota) | _(vuoto)_ |
| `lon` | decimale | Longitudine (se fornita direttamente dal modello, altrimenti vuota) | _(vuoto)_ |
| `uncertainty_note` | stringa | Nota del modello sull'incertezza della localizzazione | _(vuoto)_ |
| `dead_confirmed` | intero | Numero di morti confermati | `0` |
| `injured_confirmed` | intero | Numero di feriti confermati | `1` |
| `missing_confirmed` | intero | Numero di dispersi confermati | `0` |
| `dead_possible_min` | intero | Stima minima di morti possibili | `0` |
| `dead_possible_max` | intero | Stima massima di morti possibili | `0` |
| `possible_violations_count` | intero | Numero di possibili violazioni dei diritti fondamentali elencate (0 se nessuna) | `4` |
| `context_note` | stringa | Nota contestuale prodotta dal modello per riassumere l'incidente | `A group of 20 nationals was detained in Serbia and allegedly subjected to ill-treatment...` |
| `libyan_coast_guard_involved` | booleano | Se la guardia costiera libica è coinvolta nell'incidente | `false` |
| `evidence_quote` | stringa | Citazione testuale dal PDF usata come evidenza principale | `During a screening interview performed by Frontex, a screened person stated that...` |
| `confidence` | stringa (`high / medium / low`) | Grado di affidabilità dell'estrazione secondo il modello | `medium` |
| `evidence_pages` | stringa | Pagine del PDF usate come fonte, separate da virgola | `1,2,3,4,5` |

---

## `violations.csv`

Una riga per ogni possibile violazione dei diritti fondamentali associata a un SirRecord.
Collegata a `sir_records.csv` tramite `record_uid`.

| nome_campo | tipo | descrizione | valore_esempio |
|---|---|---|---|
| `record_uid` | intero | Chiave esterna → `sir_records.record_uid` | `1` |
| `sir_id` | stringa | ID del SIR (per join alternativo senza passare per `record_uid`) | `10957/2024` |
| `source_file` | stringa | Path del PDF sorgente (per join alternativo) | `pdfs/10957_2024-final-sir-cat1/10957_2024-final-sir-cat.1.pdf` |
| `violation_index` | intero | Posizione della violazione nella lista (0-based) | `0` |
| `violation_name` | stringa | Nome della violazione identificata | `Prohibition of collective expulsion` |
| `legal_basis` | stringa | Base legale citata (può essere vuota) | `Article 4 of Protocol No. 4 to the ECHR` |
| `assessment` | stringa (`likely / possible / unclear / not_stated`) | Valutazione del modello sulla probabilità della violazione | `unclear` |

---

## Esempio di join con DuckDB

```sql
-- Record con le violazioni associate
SELECT r.sir_id, r.incident_date, r.country_or_area,
       v.violation_name, v.assessment
FROM 'output_csv/sir_records.csv' r
JOIN 'output_csv/violations.csv' v ON r.record_uid = v.record_uid
ORDER BY r.incident_date DESC
LIMIT 20;
```

---

## Deduplica: logica dei due SQL

Nel dataset possono esserci più righe per lo stesso `sir_id` (stesso SIR ripubblicato in batch diversi, più documenti collegati, o aggiornamenti nello stesso PDF).

### 1) Deduplica `strict` (una riga per `sir_id`)

Script: `docs/output_csv_dedup.sql`

Output:
- `output_csv/sir_records_dedup.csv`
- `output_csv/violations_dedup.csv`

Logica:
- Tiene una sola riga per ogni `sir_id`.
- Ranking qualità per scegliere la riga migliore:
  - priorità a file non `email` e non report annuali
  - maggiore completezza dei campi principali
  - `confidence` più alta (`high > medium > low`)
  - `report_date` / `incident_date` più recenti
  - impatto umano più alto (`dead + injured + missing`)
  - tie-break deterministico su `source_file` e `record_index`

Uso:

```bash
duckdb :memory: ".read docs/output_csv_dedup.sql"
```

Quando usarla:
- statistiche aggregate “headline”
- conteggi senza duplicati per SIR

### 2) Deduplica `conservative` (più righe se cambia l'evento)

Script: `docs/output_csv_dedup_conservative.sql`

Output:
- `output_csv/sir_records_conservative.csv`
- `output_csv/violations_conservative.csv`
- `output_csv/sir_records_conservative_groups.csv` (tabella audit dei gruppi/firme)

Logica:
- Per ogni `sir_id`, costruisce una `event_signature` con:
  - `report_date`, `incident_date`
  - `country_or_area`, `where_clear`, `location_type`
  - `dead_confirmed`, `injured_confirmed`, `missing_confirmed`
  - `possible_violations_count`
- Se la firma cambia, mantiene una riga separata (quindi più versioni dello stesso `sir_id`).
- Dentro ogni coppia (`sir_id`, `event_signature`) applica lo stesso ranking qualità della versione `strict`.

Uso:

```bash
duckdb :memory: ".read docs/output_csv_dedup_conservative.sql"
```

Quando usarla:
- analisi evolutive (update dello stesso SIR nel tempo)
- casi investigativi in cui non vuoi perdere varianti sostanziali
