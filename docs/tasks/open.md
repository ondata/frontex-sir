# Open Tasks

## Priorita alta

- [ ] Completare la copertura del backlog PDF con run incrementali (`--max-new-files`) fino a 100% dei file in `pdfs/`.
- [ ] Definire e applicare una QA campionaria su output estratti (controllo manuale su campione per `sir_id`, date, vittime, location, confidence).
- [ ] Aggiungere un report metriche per run (copertura, errori file, record invalidi) basato su output in `analysis_output/`.

## Priorita media

- [ ] Formalizzare una policy di costo/throughput API (batch size, pausa tra chiamate, soglia budget giornaliera).
- [ ] Consolidare il dataset finale per analisi pubblica (summary globale coerente + documentazione query DuckDB).

## Note operative

- Riferimento prodotto: `docs/PRD.md`.
- Quando un task viene avviato, spostarlo in `docs/tasks/in-progress.md`.
