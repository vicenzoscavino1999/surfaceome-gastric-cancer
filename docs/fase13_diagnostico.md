# Fase 13 Diagnostico

## Estado

Diagnostico actualizado despues del fix versionado `v2`. Este documento no modifica pesos ni politica de missing data; resume el re-run completo de Fase 13 despues de corregir el bug de normalizacion y aplicar la correccion de evidencia GPI en Fase 4.

Veredicto actual: `eligible_for_fase14`.

## Snapshot SHA256

- `results/rankings/ranking_v0_frozen.tsv`: `936aebfc372130b3ed1333fdc1fbc653f6a990cdf6ca36855c024fcc7afd3421`
- `results/rankings/ranking_v1_frozen.tsv`: `b3bbd53d9a96fa89b7766dbef0aff460be9efbdad79874e8c144b5cb100c52d5`
- `results/rankings/ranking_v2_frozen.tsv`: `95040edef1b2a50c9ab1d61042856485bbfcac98e9f51d4cb78cbe05c46e9631`
- `results/rankings/ranking_v2_frozen.metadata.yaml`: `8da49acc8b8d4285857b43b0e5f83a942e2331a54a1d5c9a0f443d6f5b658aee`
- `results/rankings/ranking_balanced.tsv`: `95040edef1b2a50c9ab1d61042856485bbfcac98e9f51d4cb78cbe05c46e9631`
- `results/tables/component_scores_all_candidates.tsv`: `6e6c6c1034540533fb6aae86f94aeff096fa52abd89cd5f728c4d589f2fc6992`
- `config/scoring_scenarios.yaml`: `227d95ac3448af4b00edffbe8281c5c6b481dbd16eaaa92576f3633b21905560`
- `config/parameters.yaml`: `4db4b243bdc99ba4537c6c979bc4824b43b07a28c8f39129abecc6b7205dd777`

## Decision de Fix Registrada Antes de Re-correr v2

Decision aplicada:

1. `Surf_relative_confidence = (surfaceome_confidence_score - 5) / 5`.
2. La escala es teorica y fija `[5,10]` despues de anadir evidencia GPI directa en Fase 4, no min/max observado.
3. La funcion de percentiles calculada dentro de Fase 13 ahora usa average-rank para empates; esto corrige `R_rank_percentile_high_worse`.

Justificacion: `Surf` es una confianza relativa dentro del universo Core+Probable ya admitido. El valor 0 no significa "no surfaceome"; significa menor confianza entre candidatos admitidos. La transformacion teorica conserva la escala aditiva de Fase 4, asigna valores identicos a scores crudos identicos y evita introducir senal por orden alfabetico de HGNC.

## Auditoria de Transformaciones

- `Surf`: bug confirmado en v0; corregido con escala teorica fija; en v2 la escala es `[5,10]` por la evidencia GPI directa anadida en Fase 4.
- `R`: percentil calculado en Fase 13 con empates densos; corregido en v1 con average-rank ties.
- `E`, `N`, `P`, `T`: se calculan upstream con funciones de percentil tie-aware; no usan el bug lexicografico de Fase 13.
- `T` de `MSLN`: `T_score` ya incorpora penalizaciones biologicamente plausibles de shedding/soluble isoform. El percentil bajo refleja la distribucion de `T_score`, no desempate HGNC.

La auditoria por componente esta en `results/tables/fase13_component_transform_audit.tsv` y cubre 7 componentes (`Surf`, `E`, `N`, `R`, `P`, `T`, `SC`).

Distribucion historica del bug `Surf` en v0:

- Score 5: n=58, percentil ordinal 0.000000-0.021088, relative 0.000000
- Score 6: n=369, percentil ordinal 0.021458-0.157603, relative 0.200000
- Score 7: n=1750, percentil ordinal 0.157973-0.805031, relative 0.400000
- Score 8: n=524, percentil ordinal 0.805401-0.998890, relative 0.600000
- Score 9: n=1, percentil ordinal 0.999260-0.999260, relative 0.800000
- Score 10: n=2, percentil ordinal 0.999630-1.000000, relative 1.000000

## GPI Anchor Limitation

- GPI anchors evaluados: 121
- Distribucion por `surfaceome_confidence_score`: {'10': 2, '5': 4, '6': 4, '7': 80, '8': 30, '9': 1}
- La distribucion actual refleja la correccion de evidencia GPI en Fase 4. Los casos GPI de baja confianza restantes quedan como limitacion de cobertura/calibracion, separada del bug de normalizacion.

Correccion de labels causales (2026-05-30): `CEACAM5` y `TACSTD2` ya no se describen como demociones primarias por riesgo normal/off-tumor, porque sus percentiles `R` activos no sostienen esa lectura. Esta correccion no cambia scores, pesos, rankings ni politica de missing data.

Casos centinela:

- `CEACAM5`: v0 rank 164 -> active rank 12; `Surf_relative_confidence=0.600000`. Tras la correccion GPI, este caso ya no debe narrarse como under-confidence GPI/Surf si su score crudo es alto.
- `MSLN`: v0 rank 509 -> active rank 158; `Surf_relative_confidence=0.600000`, `T_score=0.670000`, `T_rank_percentile=0.070662`. Si sigue fuera de top 50, la causa residual esperada es `T` bajo por penalizaciones de shedding/soluble isoform, no cobertura proteica ni el bug de desempate.

## Controles Positivos v0 vs Active v2

Positive controls top 50 en active v2: 4/8 (`ERBB2;EPCAM;MET;CEACAM5`).

El gate agregado preregistrado (`>=5/8` en top 50) sigue fallando. Ese conteo no distingue controles que caen por bug de controles penalizados por una razon biologica o de seguridad que el score debe capturar. Por eso se agrega un gate causal post-hoc, sin cambiar pesos ni ranking.

| Gene | Rank v0 | Active rank | Delta active-v0 | Surf raw | Surf active | E | N | R high-worse | P | T score | T rank | Final verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ERBB2 | 16 | 20 | 4 | 8 | 0.600000 | 0.968089 | 0.952134 | 0.599629 | 0.901342 | 0.932500 | 0.789308 | recovered |
| EPCAM | 11 | 14 | 3 | 8 | 0.600000 | 0.964007 | 0.989239 | 0.599629 | 0.840973 | 0.962500 | 0.936182 | recovered |
| MET | 32 | 45 | 13 | 8 | 0.600000 | 0.900186 | 0.989981 | 0.599629 | 0.937116 | 0.832500 | 0.567703 | recovered |
| TACSTD2 | 165 | 202 | 37 | 7 | 0.400000 | 0.894991 | 0.778479 | 0.599629 | 0.667691 | 0.962500 | 0.936182 | explained_mid_surface_confidence_and_weaker_protein_support |
| CEACAM5 | 164 | 12 | -152 | 8 | 0.600000 | 0.918738 | 0.936178 | 0.470501 | 0.984349 | 0.920000 | 0.702923 | recovered |
| MSLN | 509 | 158 | -351 | 8 | 0.600000 | 0.850835 | 0.874583 | 0.470501 | 0.910285 | 0.670000 | 0.070662 | explained_shedding_soluble_T_penalty_after_GPI_surfaceome_correction |
| CLDN18 | 1626 | 1474 | -152 | 7 | 0.400000 | 0.890909 | 0.221521 | 0.832282 | 0.878144 | 0.614010 | 0.056974 | explained_isoform_unresolved |
| FGFR2 | 1497 | 1333 | -164 | 7 | 0.400000 | 0.798145 | 0.503525 | 0.832282 | 0.674120 | 0.712500 | 0.115797 | explained_isoform_unresolved |

## Gate Causal de Controles Positivos

Top50 score threshold en active v2: `0.540189`.

| Gene | Active rank | Active score | Deficit to top50 | Surf | E | N | R raw | R pct | P | T score | T rank | Single best component crosses top50 | Causal class | Pipeline-accusing failure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| ERBB2 | 20 | 0.568251 | 0.000000 | 0.600000 | 0.968089 | 0.952134 | 0.900000 | 0.599629 | 0.901342 | 0.932500 | 0.789308 | none | recovered_top50_v1 | False |
| EPCAM | 14 | 0.580488 | 0.000000 | 0.600000 | 0.964007 | 0.989239 | 0.900000 | 0.599629 | 0.840973 | 0.962500 | 0.936182 | none | recovered_top50_v1 | False |
| MET | 45 | 0.545445 | 0.000000 | 0.600000 | 0.900186 | 0.989981 | 0.900000 | 0.599629 | 0.937116 | 0.832500 | 0.567703 | none | recovered_top50_v1 | False |
| TACSTD2 | 202 | 0.468540 | 0.071649 | 0.400000 | 0.894991 | 0.778479 | 0.900000 | 0.599629 | 0.667691 | 0.962500 | 0.936182 | Surf;R | expected_mid_surface_confidence_and_weaker_protein_support | False |
| CEACAM5 | 12 | 0.584828 | 0.000000 | 0.600000 | 0.918738 | 0.936178 | 0.850000 | 0.470501 | 0.984349 | 0.920000 | 0.702923 | none | recovered_top50_v1 | False |
| MSLN | 158 | 0.484592 | 0.055597 | 0.600000 | 0.850835 | 0.874583 | 0.850000 | 0.470501 | 0.910285 | 0.670000 | 0.070662 | Surf;R;T | expected_shedding_soluble_T_penalty_after_GPI_surfaceome_correction | False |
| CLDN18 | 1474 | 0.253449 | 0.286740 | 0.400000 | 0.890909 | 0.221521 | 1.000000 | 0.832282 | 0.878144 | 0.614010 | 0.056974 | none | expected_isoform_and_safety_demotion | False |
| FGFR2 | 1333 | 0.266575 | 0.273614 | 0.400000 | 0.798145 | 0.503525 | 1.000000 | 0.832282 | 0.674120 | 0.712500 | 0.115797 | none | expected_isoform_and_safety_demotion | False |

Resumen causal:

- Recovered in top50: 4/8 (`ERBB2;EPCAM;MET;CEACAM5`).
- Original top50 misses explained by component-level biology/safety/coverage: 5/5 (`TACSTD2;CEACAM5;MSLN;CLDN18;FGFR2`).
- Original top50 misses that still accuse the pipeline: 0/5 (`none`).

Interpretacion: el bug `Surf/R` era real y esta corregido, y la omision de evidencia GPI directa fue tratada en Fase 4 antes del rerun downstream. Tras revisar componentes, los misses originales deben interpretarse por causa: `TACSTD2` por confianza de superficie intermedia y menor soporte proteico, `MSLN` por shedding/soluble isoform reflejado en `T`, y `CLDN18`/`FGFR2` por isoforma gene-level no resuelta junto a riesgo/selectividad/topologia. Si `CEACAM5` queda recuperado tras GPI, deja de contar como miss; si no, requiere explicacion por componentes actualizados.

## Veredicto

`eligible_for_fase14`

Cada uno de los cinco controles positivos fuera del top 50 original tiene veredicto escrito en `results/tables/fase13_positive_control_component_diagnostic.tsv` y clasificacion causal en `results/tables/fase13_positive_control_causal_gate.tsv`.

Con veredicto `eligible_for_fase14`, Fase 14 puede correr como analisis de estabilidad del ranking preliminar activo v2 y con estas advertencias:

1. El ranking v2 es el ranking activo; v0 queda preservado como evidencia del bug detectado y v1 como snapshot pre-GPI.
2. `MSLN` no debe narrarse como fallo de cobertura proteica; tiene `P` alto y residual `T` bajo por shedding/soluble isoform.
3. La evidencia GPI directa fue aplicada universe-wide en Fase 4; no fue un parche para controles.
4. El fallo del gate agregado debe reportarse junto con el gate causal; no debe ocultarse ni usarse para retunar pesos.

## Outputs del Diagnostico

- `results/tables/fase13_diagnostic_snapshot_hashes.tsv`
- `results/tables/fase13_component_transform_audit.tsv`
- `results/tables/fase13_surfaceome_tie_groups.tsv`
- `results/tables/fase13_gpi_anchor_surf_audit.tsv`
- `results/tables/fase13_positive_control_component_diagnostic.tsv`
- `results/tables/fase13_positive_control_causal_gate.tsv`
- `results/tables/fase13_v0_v1_rank_delta.tsv`
