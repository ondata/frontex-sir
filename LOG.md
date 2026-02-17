# LOG

## 2026-02-17

- Diagnosi output vuoti: 59/118 JSON con `records:[]`; cause: (1) SIR con ID solo numerico senza anno, (2) PDF scansionati con SIR reali, (3) non-SIR correttamente vuoti
- Fix prompt `prompts/extract_sir.txt`: accetta SIR senza formato `XXXXX/YYYY`; ID solo numerico → costruisce `NUM/ANNO` da `report_date`
- Fix validazione `extract_sir_pdf_gemini.py`: `SIR_ID_PATTERN` ora `\d+/\d{4}`, campo `sir_id` diventa `Optional[str]`
- Eliminati 14 batch di output (10 all-empty + 4 misti) per riprocessamento con nuovo prompt; rimasti 29 JSON validi
- Audit completo JSON vuoti su `analysis_output/`: 71 vuoti analizzati con `pdftotext` + OCR fallback (sidecar in `tmp/`), esito `63 probabilmente corretti` / `8 da ricontrollare`; report: `docs/empty-json-audit-2026-02-17.md`, liste: `tmp/empty_json_probably_correct.tsv` e `tmp/empty_json_to_review.tsv`

## 2026-02-16

- Creato `docs/PRD.md` dedotto dallo stato reale del progetto (obiettivi, scope, requisiti, metriche, rischi, DoD)
- Creati `docs/tasks/open.md` e `docs/tasks/in-progress.md` per avviare la gestione operativa del backlog
- Creato `docs/phases/phases.md` con fase corrente, milestone e baseline numerica (96 documenti, 418 PDF, 29 estratti)

## 2026-02-15

- Aggiunta modalità incrementale `--max-new-files N` a `extract_sir_pdf_gemini.py`: processa N PDF nuovi per run, salta già estratti, non scrive summary parziali
- Processati 10 nuovi PDF con modalità incrementale (0 errori)
- README: aggiunta sezione dedicata alla modalità incrementale con esempio d'uso

## 2026-02-13

- Creato repo pubblico `ondata/frontex-sir` con Git LFS per PDF e ZIP
- Pipeline operativa: `process_sir_zips.sh` + `extract_sir_pdf_gemini.py`
- Processati 3 ZIP Frontex (14 PDF, 30 SIR): 59 morti confermati, 9 dispersi, fino a 120 possibili morti
- Modello usato: `gemini-2.5-flash` (piano gratuito)
- Aggiunto `CLAUDE.md` con guida operativa
- Discussion aperta in `ondata/attivita` (Idee #107)
- Prompt esterno: spostato prompt in `prompts/extract_sir.txt`, aggiunto flag `--prompt-path` per versionamento e A/B testing
- Documento requisiti modelli: creato `docs/model-requirements.md` con specifiche tecniche, costi stimate e raccomandazioni per scalare
- Corretto `docs/model-requirements.md`: prezzi (Flash $0.30/$2.50, Pro $1.25/$10 per 1M token), limite File API (2GB, non 10MB), Gemini 3 Flash non più preview
- Aggiunto `fetch_sir_zip_urls.py`: scraper per raccogliere tutti gli ZIP SIR da PRD Frontex (96 doc, 20 pagine); append idempotente su `zip_urls.txt` — issue #1
- Aggiunto campo `libyan_coast_guard_involved` (bool|null) a prompt, Pydantic model e CSV — issue #2
- `fetch_sir_zip_urls.py` aggiornato: raccoglie metadati completi (titolo, data, lingua, tag, URL) e scrive `sir_documents.jsonl` (96 doc) oltre a `zip_urls.txt`
- `process_sir_zips.sh` aggiornato: gestisce PDF diretti (oltre ai ZIP), nome cartella senza punti
