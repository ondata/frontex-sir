## Context

SIR PDFs expose location details with heterogeneous phrasing and precision. Current base output stores location mainly as free text, which makes consistent filtering, grouping, and geocoding difficult.

## Goals / Non-Goals

**Goals:**
- Introduce normalized location fields in base extraction output.
- Keep additive/backward-compatible schema behavior.
- Enable downstream aggregation and map-ready filtering.

**Non-Goals:**
- Full geocoding pipeline implementation.
- GIS product integration.
- Historical bulk backfill as part of this design.

## Decisions

1. **Additive schema extension in `SirRecord`**
   - Rationale: keeps current consumers working while enabling richer outputs.
   - Alternative considered: replacing `location_details` entirely; rejected due to compatibility risk.

2. **Prompt rubric-driven normalization**
   - Rationale: normalize semantic quality (`precision_level`, `geocodable`) directly at extraction time.
   - Alternative considered: post-processing classifier; rejected for higher complexity and drift risk.

3. **CSV summary includes location columns**
   - Rationale: maintain analysis parity between JSON records and tabular summaries.
   - Alternative considered: JSON-only location details; rejected because current workflow relies heavily on CSV.

## Risks / Trade-offs

- [LLM ambiguity on location parsing] -> Strengthen prompt rubrics and validate on mixed sample.
- [Overconfident geocodable classification] -> Enforce strict `yes/no` criteria and null defaults.
- [Schema sprawl] -> Keep fields tightly scoped to explicit extraction and uncertainty notes.

## Migration Plan

1. Update prompt with location schema/rules.
2. Extend `SirRecord` and validators.
3. Extend summary writer columns.
4. Run sample extraction and inspect distribution with DuckDB.
5. Update docs and runbooks.

Rollback:
- Revert added fields in prompt/model/writer and rerun extraction.

## Open Questions

- Should lat/lon support explicit DMS-to-decimal conversion in this phase or remain strict decimal-only?
- Should we add location quality metrics to `summary_totals.json` in a follow-up?

