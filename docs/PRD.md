# PRD - Frontex SIR Extraction Pipeline

## 1) Obiettivo prodotto

Costruire una pipeline ripetibile che trasformi i PDF dei Serious Incident Reports (SIR) di Frontex in dati strutturati (JSON/CSV) affidabili per analisi giornalistica, auditing e ricerca.

## 2) Contesto e problema

I documenti SIR sono pubblicati in formato eterogeneo (ZIP/PDF), spesso in grandi volumi, e non sono immediatamente interrogabili.
Senza una pipeline strutturata:
- il recupero dei file e la normalizzazione richiedono lavoro manuale;
- l'estrazione dei campi chiave (vittime, date, luogo, evidenze) non e scalabile;
- non ci sono metriche consolidate per monitorare copertura, errori e qualita.

## 3) Utenti target

- Giornalisti data-driven che devono analizzare eventi e trend.
- Ricercatori/attivisti che devono fare controlli longitudinali.
- Maintainer tecnici che devono mantenere una pipeline stabile, idempotente e con costi API controllabili.

## 4) Stato attuale (baseline al 16 febbraio 2026)

- `sir_documents.jsonl`: 96 documenti indicizzati.
- `pdfs/**/*.pdf`: 418 PDF disponibili.
- `analysis_output/**/*.extracted.json`: 29 PDF gia estratti.
- Supporto incrementale gia presente: `--max-new-files N` per processare nuovi file a blocchi.

## 5) Scope

### In scope (v1)

1. Discovery e aggiornamento sorgenti:
- scraping metadati/URL da PRD Frontex in `zip_urls.txt` e `sir_documents.jsonl`.

2. Ingestion file:
- download ZIP/PDF in `rawdata/`;
- estrazione PDF in `pdfs/<batch>/` con logica idempotente.

3. Estrazione strutturata:
- invio PDF a Gemini;
- validazione con Pydantic;
- output per file (`<pdf>.extracted.json`) e summary CSV/JSON.

4. Elaborazione incrementale:
- processamento per blocchi (`--max-new-files`);
- skip automatico dei file gia processati.

5. Dataset analitico minimo:
- campi SIR principali (ID, date, vittime, location, confidence, evidenze) pronti per query DuckDB.

### Out of scope (v1)

- OCR locale custom.
- Geocoding automatico end-to-end con pipeline GIS.
- UI/dashboard di consultazione.
- Verifica qualitativa completa su tutto il corpus.

## 6) Requisiti funzionali

- RF1: `fetch_sir_zip_urls.py --dry-run` deve permettere verifica senza scrittura.
- RF2: `process_sir_zips.sh` deve gestire sia ZIP sia PDF diretti.
- RF3: `extract_sir_pdf_gemini.py` deve saltare output gia esistenti (default).
- RF4: `--max-new-files N` deve processare al massimo N nuovi file per run.
- RF5: output validati via schema Pydantic; record invalidi tracciati.
- RF6: summary per cartella e globale disponibili nei run completi.
- RF7: supporto prompt versionabile (`--prompt-path`) per A/B test.

## 7) Requisiti non funzionali

- RNF1: idempotenza su fetch/download/extract per evitare rilavorazioni.
- RNF2: tracciabilita run tramite file di output e log.
- RNF3: controllo costo/throughput API (modello configurabile, pausa tra chiamate).
- RNF4: riproducibilita locale con `.venv` e variabili ambiente standard.

## 8) Metriche di successo

- Copertura estrazione: `extracted_json / pdf_totali`.
- Tasso errori file: `files_failed / files_processed`.
- Qualita record: `records_invalid_skipped / records_total`.
- Completezza campi chiave (SIR id, date, location, vittime, confidence).
- Costo medio stimato per PDF e tempo medio per batch.

Target operativo iniziale:
- completare progressivamente il backlog con batch incrementali;
- mantenere `files_failed = 0` nei run standard;
- mantenere `records_invalid_skipped` basso e monitorato.

## 9) Vincoli e dipendenze

- Dipendenza da API Gemini e relative quote/costi.
- Necessita `GEMINI_API_KEY`.
- Artefatti binari grandi (ZIP/PDF) gestiti con Git LFS.

## 10) Rischi principali

- Variabilita output LLM su PDF ambigui o scansioni difficili.
- Rate limit/API failure durante batch grandi.
- Qualita non uniforme del campo location (precisione/geocodabilita).

Mitigazioni:
- run incrementali piccoli (`--max-new-files`);
- retry e throttling;
- revisione periodica di prompt e schema;
- controllo campionario manuale.

## 11) Milestone operative

1. Stabilizzazione pipeline incrementale (completata).
2. Smaltimento backlog PDF a blocchi con monitoraggio metriche.
3. QA campionaria su output e tuning prompt/modello.
4. Consolidamento dataset finale per analisi pubblica.

## 12) Definition of Done (v1)

La v1 e completata quando:
- l'intero corpus PDF disponibile e processato almeno una volta;
- output strutturato e summary sono coerenti e interrogabili con DuckDB;
- metriche minime (copertura, errori, record invalidi) sono disponibili e aggiornate;
- la procedura operativa e documentata in modo eseguibile da terzi.
