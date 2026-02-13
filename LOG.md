# LOG

## 2026-02-13

- Creato repo pubblico `ondata/frontex-sir` con Git LFS per PDF e ZIP
- Pipeline operativa: `process_sir_zips.sh` + `extract_sir_pdf_gemini.py`
- Processati 3 ZIP Frontex (14 PDF, 30 SIR): 59 morti confermati, 9 dispersi, fino a 120 possibili morti
- Modello usato: `gemini-2.5-flash` (piano gratuito)
- Aggiunto `CLAUDE.md` con guida operativa
- Discussion aperta in `ondata/attivita` (Idee #107)
- Prompt esterno: spostato prompt in `prompts/extract_sir.txt`, aggiunto flag `--prompt-path` per versionamento e A/B testing
