# Design Decisions

All decisions below are recorded before data execution unless marked otherwise.

| ID | Date | Phase | Decision | Rationale | Alternatives | Downstream impact | Status |
|---|---|---|---|---|---|---|---|
| DD-001 | 2026-05-28 | Bootstrap | Target reproducibility tier is `gate+expected` at project start. | Full 10/10 requires Docker, CI, audit, and release evidence that cannot be honestly claimed at bootstrap. | `gate`, `10/10` | Sets minimum implementation expectations. | frozen |
| DD-002 | 2026-05-28 | Fase 0 | Controls are declared before downloads/rankings. | Prevents score tuning to recover known targets. | Define controls after first ranking | Controls become validation gates. | frozen |
| DD-003 | 2026-05-28 | Fase 0 | PTPRC and PECAM1 are TME/off-tumor penalty controls, not non-surface controls. | Both are cell-surface markers; failure should reflect target context, not surfaceome membership. | Treat all controls as negative surfaceome controls | Avoids invalid assertions. | frozen |
| DD-004 | 2026-05-28 | Fase 0 | Balanced MVP weights exclude SC until scRNA passes quality gate. | Prevents fake precision from unavailable or weak single-cell annotations. | Impute SC, force SC as required | MVP can proceed while flagging TME risk separately. | frozen |
| DD-005 | 2026-05-28 | Fase 0B | Initial novelty decision is `go_with_narrower_claim`. | Search pass found close gastric/GEJ/GSRCC target-prioritization and ADC papers plus pan-cancer surfaceome frameworks. No single work found yet with the planned combination of auditable surfaceome MCDA, preregistered controls, isoform handling, batch diagnostics, missing-data policy, stability analysis, and reproducibility release. | `go`, `pivot` | Proceed only with a methodology-forward, reproducibility-forward claim; avoid broad first-in-field claims. | frozen_pending_manual_scholar_check |
| DD-006 | 2026-05-28 | Fase 0B | Deep research report reviewed and incorporated as supporting landscape evidence. | The report supports continuing with a narrowed computational/reproducibility claim and adds comparators/benchmarks missing from the initial table. | Ignore report, replace landscape entirely | Adds comparator papers and secondary benchmark controls; keeps `go_with_narrower_claim`. | frozen |

## Pending Decisions

- Manual Google Scholar verification for Fase 0B.
- Primary expression matrix after download and batch diagnostic.
- Whether scRNA enters the main score or remains an annotation/limitation.
- Whether final manuscript title should explicitly target "beyond HER2/CLDN18.2" or keep broader STAD/GAC surfaceome framing.
