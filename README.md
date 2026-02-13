# Frontex SIR Extractor (Guida pratica per giornalisti)

Questo progetto serve a trasformare i PDF dei **Serious Incident Reports (SIR)** di Frontex in dati strutturati (JSON/CSV), utili per analisi giornalistiche.

Non devi programmare: il flusso base è in 2 comandi.

## Cosa fa, in parole semplici

1. Scarica i pacchetti ZIP pubblicati da Frontex.
2. Estrae i PDF in cartelle ordinate.
3. Legge ogni PDF con Gemini e produce un output strutturato con:
   - ID del SIR
   - date
   - luogo
   - morti/feriti/dispersi (confermati o possibili)
   - citazione testuale di evidenza
   - pagine del PDF usate come fonte

Per cercare i file ZIP da scaricare, usa questa pagina:
https://prd.frontex.europa.eu/?form-fields%5Bsearch%5D

Su quella pagina cerca: **Serious Incident Reports**.

## Cosa NON fa

- Non fa OCR locale.
- Non usa `pdftotext`.
- Non modifica i PDF originali.

La lettura del documento avviene caricando direttamente il PDF su Gemini.

## File principali (in root)

- `process_sir_zips.sh`  
  Scarica ZIP ed estrae PDF.
- `zip_urls.txt`  
  Elenco URL ZIP da scaricare (uno per riga).
- `extract_sir_pdf_gemini.py`  
  Estrae i dati strutturati dai PDF con Gemini.

## Requisiti minimi

- Ambiente Python già pronto in `.venv`
- Variabile API:

```bash
export GEMINI_API_KEY="la-tua-chiave"
```

## Flusso standard (2 passi)

### 1) Scarica ZIP ed estrai PDF

```bash
./process_sir_zips.sh zip_urls.txt
```

Risultato:
- ZIP in `rawdata/`
- PDF in `pdfs/<nome-zip>/`

### 2) Estrai dati strutturati dai PDF

```bash
source .venv/bin/activate
python extract_sir_pdf_gemini.py pdfs --output-dir analysis_output
```

Risultato:
- JSON per ogni PDF in `analysis_output/<cartella>/`
- `summary.csv` e `summary_totals.json` per ogni cartella
- `summary.csv` e `summary_totals.json` globali in `analysis_output/`

## Logica di skip (per non rifare lavoro già fatto)

Lo script `extract_sir_pdf_gemini.py` salta automaticamente:

1. **Cartella già completata**  
   Se trova `analysis_output/<cartella>/summary.csv`, considera quella cartella già processata e la salta.

2. **Singolo file già processato**  
   Se trova `<nomefile>.extracted.json`, salta quel PDF.

Se vuoi forzare la riesecuzione:

```bash
python extract_sir_pdf_gemini.py pdfs --output-dir analysis_output --no-skip-existing
```

## Come legge i PDF e crea l'output strutturato

In pratica:

1. Carica il PDF binario su Gemini File API.
2. Invia al modello un prompt con uno schema JSON preciso da rispettare.
3. Valida il JSON con Pydantic (controllo formale dei campi).
4. Scrive file `.extracted.json` e i summary CSV/JSON.

Questo approccio è utile anche per PDF senza testo OCR incorporato.

## Prompt usato (testo completo)

Questo è il prompt che lo script invia a Gemini insieme al PDF:

```text
Sei un analista OSINT/data-journalism.
Analizza questo documento PDF contenente uno o più Serious Incident Reports Frontex.

Obiettivo: quantificare vittime per ciascun SIR presente nel documento.

Restituisci SOLO JSON valido, senza markdown, con questa struttura:
{
  "records": [
    {
      "sir_id": "12345/2021",
      "report_date": "YYYY-MM-DD or null",
      "incident_date": "YYYY-MM-DD or null",
      "location_details": "string or null",
      "dead_confirmed": 0 or null,
      "injured_confirmed": 0 or null,
      "missing_confirmed": 0 or null,
      "dead_possible_min": 0 or null,
      "dead_possible_max": 0 or null,
      "note_contesto": "string or null",
      "evidenza_testuale": "breve citazione dal documento",
      "confidenza": "alta|media|bassa",
      "evidence_pages": [1, 2]
    }
  ]
}

Regole:
- Identifica ogni blocco "Serious Incident Report no. XXXXX/YYYY".
- Dai priorità ai campi Dead/Injured/Missing persons nel form.
- Se i campi non hanno numeri, usa Details / Information/Allegations / Assessment.
- Non inventare numeri.
- Distingui confermato vs possibile/non confermato.
- Se impossibile estrarre un valore, usa null.
- sir_id deve essere nel formato XXXXX/YYYY.
- evidence_pages: numeri di pagina del PDF dove hai trovato le informazioni.
```

Nel codice si trova in `extract_sir_pdf_gemini.py`, funzione `build_prompt()`.

## Esempio di output: summary_totals.json

Generato processando i 3 ZIP in `zip_urls.txt`:

- `https://prd.frontex.europa.eu/wp-content/uploads/pad-2025-00427.zip` (SIR 2017)
- `https://prd.frontex.europa.eu/wp-content/uploads/pad-2025-00419.zip` (SIR 2021)
- `https://prd.frontex.europa.eu/wp-content/uploads/pad-2025-00475.zip` (SIR 2022/2024)

```json
{
  "generated_at_utc": "2026-02-13T07:23:16.169626+00:00",
  "model": "gemini-2.5-flash",
  "input_path": "pdfs",
  "files_processed": 14,
  "files_failed": 0,
  "records_total": 30,
  "dead_confirmed_total": 59,
  "injured_confirmed_total": 23,
  "missing_confirmed_total": 9,
  "dead_possible_total_min": 8,
  "dead_possible_total_max": 120
}
```

## Dove guardare i risultati

- Vista sintetica globale: `analysis_output/summary.csv`
- Totali globali: `analysis_output/summary_totals.json`
- Dettaglio per batch: `analysis_output/<cartella>/summary.csv`
- Dettaglio per documento: `analysis_output/<cartella>/<file>.extracted.json`

## Nota su Git LFS

I file PDF e ZIP sono tracciati con [Git LFS](https://git-lfs.com/). Sono documenti statici pubblicati da Frontex: non cambiano nel tempo e non ha senso versionarli. LFS li archivia separatamente, tenendo nel repository solo puntatori leggeri ed evitando di appesantire la storia dei commit.

Per clonare il repo con i file binari inclusi è sufficiente avere `git-lfs` installato: il download avviene in automatico durante `git clone` o `git pull`.

## Struttura cartelle

```text
frontex/
├── process_sir_zips.sh
├── zip_urls.txt
├── extract_sir_pdf_gemini.py
├── rawdata/              # ZIP scaricati
├── pdfs/                 # PDF estratti dagli ZIP
└── analysis_output/      # Output strutturati
```

## Nota operativa

Ogni PDF viene inviato a Gemini: considera tempi di esecuzione e costi API in base al numero di file.

## Librerie e strumenti usati (con link)

### Python

- `google-genai`  
  Link: https://github.com/googleapis/python-genai  
  Perche utile: e il client ufficiale usato per caricare i PDF su Gemini File API e ottenere la risposta del modello in JSON.

- `pydantic`  
  Link: https://docs.pydantic.dev/latest/  
  Perche utile: valida la struttura dei dati estratti (campi obbligatori, tipi, vincoli), riducendo errori nei risultati finali.

- `argparse` (standard library)  
  Link: https://docs.python.org/3/library/argparse.html  
  Perche utile: gestisce i parametri da riga di comando (`--output-dir`, `--skip-existing`, `--model`, ecc.).

- `pathlib` (standard library)  
  Link: https://docs.python.org/3/library/pathlib.html  
  Perche utile: gestisce percorsi e cartelle in modo robusto (input PDF, output JSON/CSV, skip per cartella).

### Script download (shell)

- `curl`  
  Link: https://curl.se/docs/  
  Perche utile: scarica gli ZIP Frontex dagli URL nel file `zip_urls.txt`.

- `unzip`
  Link: https://infozip.sourceforge.net/UnZip.html
  Perche utile: estrae i PDF dagli ZIP mantenendo una struttura ordinata in `pdfs/<nome-zip>/`.

## Note finali

Questo è un primo esperimento esplorativo.

Il modello usato è `gemini-2.5-flash`: non è il più potente disponibile, ma permette di fare test iniziali a costo zero grazie al piano gratuito di Google AI Studio.

Non è stata ancora fatta nessuna verifica della qualità dei dati estratti, né automatica né manuale. I risultati vanno trattati come bozza da validare.
