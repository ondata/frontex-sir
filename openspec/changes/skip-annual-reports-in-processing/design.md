## Context

The extraction corpus includes annual reports and publication artifacts that are not SIR records. Running these through Gemini adds cost and noise. Existing skip logic handles already-processed files and completed groups, but not non-SIR annual report filtering.

## Goals / Non-Goals

**Goals:**
- Prevent API calls for annual-report PDFs.
- Keep filtering safe (no broad `report`-based skipping).
- Expose skip behavior in logs and totals.

**Non-Goals:**
- Full semantic document classification.
- Content-based ML/OCR classification.
- Changes to SIR extraction schema itself.

## Decisions

1. **Pattern-based pre-API filter**
   - Rationale: simple, deterministic, low overhead.
   - Alternative considered: semantic classifier; rejected due to complexity/cost.

2. **Negative safety guard for generic report token**
   - Rationale: avoid dropping valid files like `Final_Report`.
   - Alternative considered: broad regex on `report`; rejected as unsafe.

3. **CLI override for edge cases**
   - Rationale: keeps behavior flexible for manual investigations.
   - Alternative considered: hardcoded always-on skip; rejected due to reduced control.

## Risks / Trade-offs

- [Pattern misses some annual-report variants] -> Extend pattern set iteratively from observed corpus.
- [False positives from aggressive regex] -> Keep conservative matching and validate against known SIR filenames.
- [Operator confusion on skip behavior] -> Emit explicit skip log and counters in totals.

## Migration Plan

1. Add annual-report detector helper.
2. Add CLI flags and default behavior.
3. Add skip counters in group/global totals.
4. Update README with behavior and override flag.
5. Validate with mixed annual+SIR sample.

Rollback:
- Disable filter path and remove counters/flags.

## Open Questions

- Should non-annual but clearly non-SIR templates (for example handbooks) be filtered by a second-stage rule?
- Should skipped-file lists be emitted in a structured sidecar report?

