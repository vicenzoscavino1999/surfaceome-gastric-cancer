# Manual Curation Protocol (Fase 15 / R9)

Status: preregistered 2026-05-31, frozen before any candidate is curated.

This protocol governs the manual curation and coarse tier assignment of Fase 15. It is written and
frozen **before** looking at curation outcomes, so that tier placements are applied by rule, not
chosen after seeing results. It pairs with the machine-readable rules in `config/tiering_rules.yaml`.

## Principles (inherited, not new)

- Curation informs **tiering only**, never numeric scores, unless it reveals a reproducible data or
  mapping bug (then: log bug, fix, rerun downstream â€” `config/exclusion_criteria.yaml`).
- Tiers are coarse and unordered within a tier (DD-031; post-scoring resolution 1/20).
- The active ranking is the frozen `results/rankings/ranking_v2_frozen.tsv`
  (SHA256 `95040edef1b2a50c9ab1d61042856485bbfcac98e9f51d4cb78cbe05c46e9631`).
- Single-evaluator limitation (reviewer attack RA-04): no inter-rater reliability is available; this
  is declared as a limitation, and curation notes are published for external audit.

## Scope (frozen in `config/parameters.yaml` manual_curation)

- Primary: top 30 of `Balanced` (`top_n_primary: 30`).
- Extended only if time allows: top 50 (`top_n_extended_if_time: 50`).
- Two passes: a first pass over the top 30, then a detailed second pass over the top 10.
- Time caps: `max_minutes_per_candidate: 60`; hard cap `90` if strong ambiguity. Record the reason
  if a candidate exceeds 60 minutes.

## Per-candidate procedure

For each candidate, consult the sources in order and record findings in
`results/tables/manual_curation_notes.tsv`:

1. **UniProt** (<=15 min): topology, isoforms, shedding/soluble forms, tissue specificity, disease
   association. Confirm the accessibility class and any `isoform_unresolved` flag.
2. **HPA web** (<=10 min): stomach-cancer IHC, critical normal tissues, subcellular location,
   antibody validation. For TME-flagged genes, judge whether membranous staining is on **tumor
   epithelium** or on **stroma/vasculature** (this is what the preregistered TME rule keys on).
3. **PubMed** (<=20 min): search `"[gene] gastric cancer antibody OR ADC OR CAR-T"`; read the first
   5 relevant abstracts.
4. **ClinicalTrials.gov** (<=10 min): gene/protein + gastric/GEJ/stomach; record phase, modality,
   sponsor.
5. Fill the candidate card (template below).

## Notes table schema (R9)

`results/tables/manual_curation_notes.tsv` columns:

`gene` | `source` | `url_or_id` | `finding` | `implication` | `changes_score` | `curator_date`

`changes_score` is almost always `no`; a `yes` requires a reproducible bug entry in
`docs/design_decisions.md` and a downstream rerun, not a manual score edit.

## Candidate card template (top 20)

```text
Gene/protein:
Target form:
Modalidad plausible:
Prevalence flag:           # Broad / Moderate / Restricted
Por que rankea alto:
Evidencia RNA:
Evidencia proteica:
Evidencia single-cell:     # MVP: SC not_available -> bulk TME flag status
Topologia/ECD:             # accessibility class A-E
Estructura:                # annotation only, not score
Internalizacion/ADC suitability:
Riesgos normales:          # max_risk_organ, risk_interpretation
Evidencia clinica:
Novelty/competition:
Limitacion principal:
Experimento wet-lab recomendado:
Tier asignado + razon de regla:   # which tiering_rules.yaml clause placed it
```

## Tier assignment

Apply `config/tiering_rules.yaml` to each candidate after curation. The placement must cite the
clause that produced it (e.g. "Watchlist: missing_primary_components_ge 3"). Tier assignment is
script-generated into `results/tables/tier_assignments.tsv`; the candidate cards and curation notes
provide the human-readable justification but do not override the rule.

## Outputs

- `results/tables/tier_assignments.tsv` (script-generated, coarse tiers, unordered within tier)
- `results/tables/top20_candidate_cards.md`
- `results/tables/excluded_with_reason.tsv`
- `results/tables/manual_curation_notes.tsv`

## Exit criteria (R9)

- 100% of top 20 have a candidate card.
- 100% of top 30 have at least one curation note.
- Every gene in `tier_assignments.tsv` has a tier and a rule-clause reason.
- The four thin-evidence genes (HLA-DRB3, HLA-DRB4, KIR2DL5A, KIR2DS1) land in Watchlist by rule.
- PECAM1 placement matches the registered a-priori expectation, or any deviation is logged as a
  rule-relevant surprise.
