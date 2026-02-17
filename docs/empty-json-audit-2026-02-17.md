# Audit JSON Vuoti (`records: []`) - 2026-02-17

## Obiettivo
Verificare se i file `*.extracted.json` senza record siano:

- correttamente vuoti (documenti non-SIR o senza evidenza SIR);
- oppure candidati a riestrazione/controllo manuale.

## Ambito

- Directory analizzata: `analysis_output/`
- Popolazione: tutti i file `*.extracted.json`
- Data analisi: 2026-02-17

## Metodo

1. Enumerazione JSON estratti in `analysis_output/`.
2. Identificazione "vuoti" con questi criteri:
   - `records == []`, oppure
   - `sir_records == []`, oppure
   - JSON vuoto (`{}`/`[]`/`null`).
3. Mapping di ogni JSON vuoto al PDF sorgente in `pdfs/<group>/<stem>.pdf`.
4. Estrazione testo:
   - default con `pdftotext`;
   - fallback OCR se testo troppo corto (`<120` caratteri) con:
     `ocrmypdf --force-ocr --output-type pdf --sidecar ...`
   - sidecar OCR scritto in `tmp/*.ocr.txt`.
5. Ricerca marker SIR nel testo:
   - regex ID: `\bSIR\s*[-_/]?\s*\d{2,}\b`
   - frase: `serious incident report`
   - supporto diagnostico: `incident report`
6. Classificazione:
   - `da ricontrollare`: trovato marker SIR esplicito (`sir_marker_found`);
   - `vuoti probabilmente corretti`: nessun marker SIR esplicito.

## Nota tecnica OCR

Con Ghostscript `10.0.0`, `ocrmypdf --skip-text/--redo-ocr` può fallire (`rc=3`) su PDF con testo preesistente.
Per evitare falsi errori è stato usato:

```bash
ocrmypdf --force-ocr --output-type pdf --sidecar <out.txt> <in.pdf> <out.pdf>
```

## Esito

- JSON estratti totali: `407`
- JSON vuoti analizzati: `71`
- `vuoti probabilmente corretti`: `63`
- `da ricontrollare`: `8`

Artefatti prodotti:

- `tmp/empty_json_probably_correct.tsv`
- `tmp/empty_json_to_review.tsv`

## Lista `da ricontrollare` (8)

1. `pdfs/20230706_frontex-fundamental-rights-officer-publishes-report-for-2022-1/2023.07.06_frontex-fundamental-rights-officer-publishes-report-for-2022-1.pdf`
2. `pdfs/fro-opinion-on-underreporting_10_01_2024_redactions-marked-002a_print-1/fro-opinion-on-underreporting_10_01_2024_redactions-marked-002a_print-1.pdf`
3. `pdfs/pad-2020-00078/Annex_OPLAN_JO_FOA_2018_BCU_update_25.07.2018(1).pdf`
4. `pdfs/pad-2020-00078/Handbook_to_OPLAN_-_maritime_JOs_-_ammendment_No_1-with_track_changes.pdf`
5. `pdfs/pad-2020-00078/Land_Handbook_to_OPLAN_2017.pdf`
6. `pdfs/pad-2020-00215/Email_3.pdf`
7. `pdfs/pad-2020-00215/FRO_Observations_to_draft_OPLAN_Rapid_Border_Intervention_Aegean_2020.pdf`
8. `pdfs/pad-2022-00335/Email_3.pdf`

## Interpretazione operativa

- I 63 file "probabilmente corretti" non mostrano indicatori SIR espliciti nel testo estratto/OCR.
- Gli 8 file "da ricontrollare" contengono marker SIR e sono candidati a:
  - verifica manuale rapida;
  - eventuale riestrazione con `--no-skip-existing`.
