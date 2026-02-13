# LOG

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
