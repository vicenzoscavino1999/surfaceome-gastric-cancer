# Fase 13 GPI Membership Route Audit

## Scope

This diagnostic implements Paso 0.5 of `docs/fase13_gpi_evidence_membership_plan.md`. It does not change Fase 4, component scores, weights, missing-data policy, `ranking_v1_frozen.tsv`, or any downstream ranking.

Confirmed GPI means the UniProt reviewed human `Lipidation` field contains `GPI-anchor`. Subcellular-location-only GPI annotations are tracked separately and are not counted as confirmed direct lipid evidence for the route gate.

## Tested Terms

Two non-final additive simulations were evaluated only to decide membership routing:

1. `plus1_anchor_support`: score +1, support source +1, anchor true, strong-evidence flag unchanged.
2. `plus2_strong_anchor`: score +2, support source +1, anchor true, strong-evidence flag true.

These are route tests, not a selected scoring rule. If either test changes Core+Probable membership for confirmed direct GPI genes, GPI cannot be patched only inside Fase 13.
If the current Fase 4 universe already contains `uniprot_gpi_anchor=true`, the audit does not add another simulated credit and reports an idempotence status instead.

## Counts

- Confirmed UniProt lipid GPI symbols: 134
- Subcellular-only GPI symbols: 6
- Confirmed GPI already Core+Probable: 119
- Confirmed GPI outside Core+Probable: 15
- Confirmed GPI already integrated in current Fase 4: 134
- Confirmed outside entering under plus1 anchor/support: 0
- Confirmed outside entering under plus2 strong-anchor: 0
- Current category distribution among confirmed GPI: ambiguous_membrane_or_surface_context:15, core_surfaceome:118, probable_surfaceome:1

## Route Decision

`fase4_gpi_evidence_correction_applied`

Reason: Confirmed UniProt lipid GPI anchors are already integrated in the current Fase 4 universe; this audit is now an idempotence check rather than a pre-correction route simulation.

## Membership Changers

- plus1 anchor/support changers: `none`
- plus2 strong-anchor changers: `none`

## Outputs

- `results/tables/fase13_gpi_membership_route_audit.tsv`
- `results/tables/fase13_gpi_membership_route_summary.tsv`
