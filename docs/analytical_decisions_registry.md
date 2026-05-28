# Analytical Decisions Registry

This registry tracks researcher degrees of freedom that could alter the top 20 ranking.

| ID | Decision | Alternatives considered | Chosen | Rationale | Sensitivity tested | Impact on top 20 |
|---|---|---|---|---|---|---|
| AD-01 | Surfaceome universe definition | CSPA only / CSPA+GO / union / intersection / UniProt-led curated set | Versioned multi-source definition in `config/surfaceome_universe_definition.yaml` | Balance specificity with recovery of clinically relevant controls | Planned: strict vs broad | TBD after Fase 14 |
| AD-02 | Normal tissue risk aggregation | mean / max / weighted max / cumulative | `max_weighted_organ_penalty` | Conservative for off-tumor risk | Planned: R_max, R_max_plus_breadth, R_sum_capped | TBD after Fase 14 |
| AD-03 | Missing data handling | exclude gene / impute / penalize / exclude-and-renormalize | exclude-and-renormalize with tier restrictions | Avoids automatic penalty for absent coverage while limiting Tier 1 inflation | Planned: p25/p50/p75 imputation comparison | TBD after Fase 14 |
| AD-04 | scRNA in main score | required / optional / annotation only | optional; absent in MVP unless quality gate passes | Avoids weak cell annotations driving ranking | Planned: with-SC vs no-SC if data available | TBD |
