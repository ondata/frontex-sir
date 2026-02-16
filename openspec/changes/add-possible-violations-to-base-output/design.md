## Context

The pipeline needs structured representation of "Possible violation(s) of fundamental rights enquired" sections to support aggregate analyses (counts by violation, legal basis, and assessment). Existing outputs lack a dedicated normalized structure.

## Goals / Non-Goals

**Goals:**
- Add a stable `possible_violations` array to each SIR record.
- Normalize assessment labels for consistent analytics.
- Expose tabular derivatives for DuckDB-friendly aggregation.

**Non-Goals:**
- Full legal ontology and canonical statute mapping.
- Mandatory OCR for all documents in this iteration.
- Retroactive full-corpus reprocessing as part of design scope.

## Decisions

1. **Nested array in JSON record**
   - Rationale: preserves one-to-many relationship between a SIR and violations.
   - Alternative considered: flattened fixed columns; rejected as lossy for multi-violation records.

2. **Normalized assessment enum**
   - Rationale: enables cross-document aggregation.
   - Alternative considered: free-text assessment; rejected due to low comparability.

3. **CSV derivatives (`count` + serialized JSON)**
   - Rationale: maintain compatibility with current CSV-first workflows while keeping detail available.
   - Alternative considered: no CSV support; rejected due to analyst friction.

## Risks / Trade-offs

- [Extraction drift across report templates] -> Keep prompt section matching explicit and conservative.
- [Ambiguous legal basis text] -> Store nullable `legal_basis` and avoid forced mapping.
- [CSV field size growth] -> Use compact JSON serialization and rely on JSON output for deep analysis.

## Migration Plan

1. Update prompt schema/rules.
2. Add Pydantic model and field normalization.
3. Update summary writer columns.
4. Validate on known examples and mixed sample.
5. Update docs with aggregation query.

Rollback:
- Revert prompt/model/writer changes and keep legacy output shape.

## Open Questions

- Should we maintain a controlled vocabulary for `violation_name` in a follow-up?
- Should `summary_totals.json` include aggregate violation counters directly?

