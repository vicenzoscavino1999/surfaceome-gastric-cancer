# Fase 13 -> Fase 14: Plan Corregido de Diagnostico

Objetivo: cerrar el diagnostico de Fase 13 antes de correr Fase 14. Este plan no cambia pesos, no cambia politica de missing data y no re-fit del score. El diagnostico explica el comportamiento del ranking congelado; solo si encuentra un bug reproducible se corrige el pipeline y se re-corre downstream completo con nueva version.

Estado actual que motiva el diagnostico:

- Fase 13 genero ranking preliminar MVP, no tiering final.
- `SC=not_available`, no imputado.
- Positive controls top 50 Balanced: 3/8 (`ERBB2`, `EPCAM`, `MET`).
- Top 20 con `P` missing: 4 (`KIR2DS1`, `KIR2DL5A`, `HLA-A`, `HLA-DRB4`).
- Top 20 con >=3 componentes MVP missing: 3 (`KIR2DS1`, `KIR2DL5A`, `HLA-DRB4`).
- `PECAM1` aparece alto como control TME/off-tumor; esto no es un control intracelular negativo, sino un surface marker de compartimento equivocado.
- `CEACAM5` y `MSLN` muestran `Surf` anormalmente bajo para controles canonicos de superficie; esta es la primera hipotesis a diagnosticar.

## Reglas

1. No cambiar pesos para recuperar positivos.
2. No cambiar politica de missing para demotar genes delgados.
3. No cambiar la definicion de `Surf` despues de ver resultados sin abrir una nueva version explicitamente congelada.
4. No correr Fase 14 hasta cerrar este diagnostico por escrito.
5. No llamar "publicable" a este gate. El veredicto permitido es uno de:
   - `eligible_for_fase14`
   - `blocked_by_scoring_bug`
   - `narrow_claim_required`
6. Manual curation puede cambiar anotaciones y veredicto narrativo, no scores numericos, salvo bug reproducible.

## Enmienda 2026-05-29 - Fix v1 Registrado

La auditoria encontro un bug real en v0: `Surf_rank_percentile` convertia una variable ordinal discreta (`surfaceome_confidence_score` con valores 5, 6, 7, 8) en percentiles con desempate lexicografico HGNC. Esto inyectaba senal alfabetica y hacia que genes con identica evidencia de superficie recibieran valores distintos.

Correccion aprobada antes de interpretar v1:

- `Surf` se reemplaza por `Surf_relative_confidence = (surfaceome_confidence_score - 5) / 3`.
- La escala es teorica fija `[5,8]`, no min/max observado del universo actual.
- El nombre de columna debe expresar semantica (`Surf_relative_confidence`), no solo metodo (`minmax`).
- El valor 0 significa menor confianza relativa dentro del universo Core+Probable ya admitido, no ausencia de superficie.
- Antes del re-run se auditan transformaciones compartidas `*_rank_percentile`; `E`, `N`, `P` y `T` vienen de scripts upstream con empates tie-aware, mientras que `R` se calcula dentro de Fase 13 y pasa a usar average-rank ties.
- No se cambia peso, politica de missing data ni definicion de controles.
- `ranking_v0_frozen.tsv` queda preservado como snapshot pre-fix; `ranking_v1_frozen.tsv` es la nueva version preliminar activa.
- Cada uno de los cinco controles positivos fuera del top 50 original debe recibir veredicto final escrito. `MSLN` requiere rama explicita: si queda bajo tras corregir `Surf`, separar residuo `T` de bug de desempate. En v1, `T_score` ya es 0.67 y el bajo `T_rank_percentile` se documenta como efecto de distribucion/penalizaciones biologicamente plausibles de shedding/soluble isoform, no como bug lexicografico.
- Si no quedan bugs reproducibles pero la recuperacion de positivos sigue baja, no basta el conteo agregado: debe abrirse un gate causal por componente antes de decidir entre `narrow_claim_required` y `eligible_for_fase14`.

## Enmienda 2026-05-29 - Gate Causal Post-fix

Despues de aplicar v1, la recuperacion agregada de positivos siguio en 3/8 top 50. Ese conteo no distingue errores del pipeline de demociones correctas por seguridad, isoforma, shedding o cobertura/calibracion. Se agrega un gate causal post-hoc, sin cambiar pesos ni ranking:

- Mantener reportado el gate agregado preregistrado como fallido.
- Crear `results/tables/fase13_positive_control_causal_gate.tsv`.
- Para cada control fuera del top 50, registrar componentes, contribuciones, deficit contra el score top50, componentes que lo cruzarian si fueran optimos, causa biologica/metodologica y si acusa o no al pipeline.
- Solo usar `eligible_for_fase14` si los cinco misses originales tienen explicacion causal y `pipeline_accusing_failure=0`.
- Si hay >=1 miss sin explicacion causal, volver a diagnosticar el componente correspondiente antes de Fase 14.

## Paso 0 - Snapshot Inmutable

Antes de diagnosticar, registrar hashes para demostrar que el ranking no fue re-fit durante la revision.

- [ ] Calcular SHA256 de:
  - `results/rankings/ranking_v0_frozen.tsv`
  - `results/rankings/ranking_balanced.tsv`
  - `results/tables/component_scores_all_candidates.tsv`
  - `config/scoring_scenarios.yaml`
  - `config/parameters.yaml`
- [ ] Crear `docs/fase13_diagnostico.md` como bitacora viva.
- [ ] Registrar en `docs/analytical_decisions_registry.md` que el diagnostico se corre sobre ranking congelado, sin re-fit.
- [ ] Guardar los hashes en la bitacora.

Gate de salida: ranking congelado identificado por SHA256 y bitacora abierta.

## Gate 0 - Auditoria de `Surf` Antes de Clasificar Controles

Este es el primer gate porque `Surf` es la capa base del ranking. Dos controles positivos canonicos tienen `Surf` bajo:

- `CEACAM5`: `Surf_rank_percentile` ~0.056, con `E/N/P` altos y `T` razonable.
- `MSLN`: `Surf_rank_percentile` ~0.116 y `T_rank_percentile` ~0.071, pese a `accessibility_class=A` y GPI capturado.

Preguntas:

- [ ] En `data/processed/surfaceome_universe.tsv`, revisar para `CEACAM5` y `MSLN`:
  - `surfaceome_confidence_score`
  - `surface_support_source_count`
  - `surface_support_sources`
  - `in_tcsa`
  - `in_cspa`
  - `in_surfy`
  - `uniprot_extracellular_topology`
  - `uniprot_transmembrane`
  - `uniprot_signal_peptide`
  - `go_surface_or_plasma_membrane`
  - `hpa_plasma_membrane`
  - `secreted_only_flag`
  - `interpretation_flags`
- [ ] Auditar todos los genes `gpi_anchor_present=true` en `data/processed/topology_isoforms_ecd.tsv` contra `surfaceome_confidence_score`.
- [ ] Calcular distribucion de `Surf` para GPI anchors versus 1TM/multipass.
- [ ] Revisar si Fase 4 penaliza involuntariamente GPI/secreted/lipid-anchored proteins.
- [ ] Revisar si Fase 13 usa `Surf_rank_percentile` de v0 de forma correcta y no invierte, trunca o mezcla columnas; si se confirma bug, registrar nueva columna semantica `Surf_relative_confidence` para v1.

Veredictos posibles:

- `Surf_bug_confirmed`: error de parsing/codigo/columna o inconsistencia con la definicion congelada. Bloquear, corregir Fase 4 o Fase 13 segun corresponda, re-correr downstream completo y generar nueva version de ranking.
- `Surf_design_limitation`: la definicion congelada explica el resultado, pero subpondera una clase biologica real como GPI anchors. No tocar el ranking v0; registrar limitacion mayor y decidir si se abre una nueva definicion/version.
- `Surf_expected_by_definition`: la baja confianza esta justificada por evidencia fuente insuficiente y no contradice la definicion. Continuar diagnostico.

Gate de salida: no avanzar a clasificar controles hasta decidir si `Surf` es confiable o si el ranking queda bloqueado.

## Paso 1 - Tabla Multicausal de los 8 Positivos

No forzar cada control a una sola categoria. Registrar causa primaria y causas secundarias.

Controles: `ERBB2`, `EPCAM`, `MET`, `TACSTD2`, `CEACAM5`, `MSLN`, `CLDN18`, `FGFR2`.

- [ ] Extraer desde `component_scores_all_candidates.tsv` y `ranking_balanced.tsv`:
  - rank Balanced
  - score Balanced
  - `Surf_rank_percentile` en v0 y `Surf_relative_confidence` en v1 si se abre version corregida
  - `E_rank_percentile`
  - `N_rank_percentile`
  - `R_rank_percentile_high_worse`
  - `P_rank_percentile`
  - `T_rank_percentile`
  - `missing_mvp_score_components`
  - `available_weight_sum`
  - `tme_contamination_risk`
  - `accessibility_class`
  - `isoform_resolution_status`
  - `risk_interpretation`
- [ ] Clasificar cada control con:
  - `primary_explanation`
  - `secondary_explanations`
  - `bug_suspected=true/false`
  - `followup_required`

Categorias permitidas:

| Categoria | Firma esperada | Interpretacion |
|---|---|---|
| `isoform_unresolved` | CLDN18.2/FGFR2b gene-level only | Esperado; no prueba isoforma especifica |
| `normal_risk_or_low_selectivity` | `R` alto y/o `N` bajo | Puede ser democion biologica/safety |
| `low_surfaceome_confidence` | `Surf` bajo en control canonico | Auditar Fase 4/Surf; posible bug o limitacion |
| `topology_component_low_or_unexpected` | `T` bajo pese a evidencia GPI/ECD | Auditar Fase 9 formula/topology mapping |
| `protein_or_data_coverage` | `P` missing o cobertura parcial | Limitacion documentable |
| `control_expectation_too_strict` | Target valido pero no necesariamente top 50 pan-STAD | Revisar expectativa preregistrada, no pesos |
| `scoring_bug` | Componentes fuertes y rank bajo sin explicacion | Bloquea avance |

Gate de salida:

- Si `scoring_bug` o `Surf_bug_confirmed` >=1: `blocked_by_scoring_bug`.
- Si no hay bug pero hay limitacion fuerte de diseno: `narrow_claim_required`.
- Si los fallos estan explicados por isoforma, risk, coverage o expectativas: continuar.

## Paso 2 - PECAM1/PTPRC y Cadena TME

No reportar "0 negativos" de forma generica. Separar dos clases:

- Negativos intracelulares/secretados/no surfaceome: `ACTB`, `GAPDH`, `H3C1`, `TOMM20`, `CALR`, `ALB`. Deben quedar fuera del top 100 y/o fuera de Core+Probable.
- Controles de superficie pero compartimento equivocado: `PTPRC`, `PECAM1`. Pueden rankear como surfaceome; deben quedar marcados como TME/off-tumor para impedir claims de target epitelial tumoral.

Checks:

- [ ] Confirmar `PECAM1` y `PTPRC` en `tme_contamination_flags.tsv`.
- [ ] Confirmar `tme_contamination_risk` en `component_scores_all_candidates.tsv`.
- [ ] Confirmar que `tiering_annotations_all_candidates.tsv` contiene `high_TME_flag` o bandera equivalente.
- [ ] Documentar que Fase 15 aun no existe: la cadena esta preparada, pero la democion final debe implementarse y testearse en tiering.

Gate de salida: si la flag TME no se propaga a anotaciones pre-tiering, hay bug de integracion Fase 8 -> Fase 13/15 pendiente.

## Paso 3 - Genes Delgados y Missing Data

Los genes top 20 con >=3 missing no rankean por `Surf+E`; en el estado actual rankean con `E;N;R;P` missing, principalmente por evidencia disponible en `Surf` y `T`.

Genes actuales: `KIR2DS1`, `KIR2DL5A`, `HLA-DRB4`.

- [ ] Listar componentes presentes y `available_weight_sum`.
- [ ] Flaggear `available_weight_sum < 0.50`.
- [ ] Confirmar que `tiering_annotations_all_candidates.tsv` los marca como `tier2_watchlist_missingness_only` o equivalente.
- [ ] Ejecutar sensibilidad de missing ya preregistrada: `exclude_and_renormalize` versus imputacion p25/p50/p75.
- [ ] Documentar si colapsan o se mantienen bajo imputacion.

Regla: no cambiar la politica de missing despues de ver estos genes. La sensibilidad reporta fragilidad; no reescribe el ranking v0.

## Paso 4 - Top 10 como Anotacion Interna Preliminar

La clasificacion de novedad no debe convertirse en juicio clinico sin fuentes. Antes de Fase 12/candidate cards, solo puede ser una anotacion interna preliminar.

- [ ] Listar top 10 Balanced.
- [ ] Clasificar de forma preliminar:
  - `preregistered_positive_control`
  - `known_target_or_well_characterized`
  - `plausible_non_obvious_hypothesis`
  - `likely_TME_or_immune_surface_signal`
  - `thin_evidence_missing_dependent`
- [ ] Registrar que la clasificacion reproducible de clinica/druggability queda diferida a Fase 12/candidate cards.

Gate de salida: si top 10 esta dominado por genes conocidos/TME/thin-evidence, el claim debe estrecharse hacia metodo/reproducibilidad y no descubrimiento fuerte.

## Paso 5 - Veredicto de Elegibilidad para Fase 14

Escribir una tabla de conteo en `docs/fase13_diagnostico.md`:

| Categoria final | Conteo | Genes | Implicacion |
|---|---:|---|---|
| `isoform_unresolved` | TBD | TBD | Esperado, no prueba isoforma |
| `normal_risk_or_low_selectivity` | TBD | TBD | Democion biologica/safety |
| `low_surfaceome_confidence` | TBD | TBD | Decide si bug o limitacion |
| `topology_component_low_or_unexpected` | TBD | TBD | Auditar Fase 9/T component |
| `protein_or_data_coverage` | TBD | TBD | Limitacion documentable |
| `scoring_bug` | TBD | TBD | Debe ser 0 para avanzar |

Veredicto permitido:

- `eligible_for_fase14`: bug=0, `Surf` auditado, TME/missing documentados, claims acotados.
- `blocked_by_scoring_bug`: bug reproducible o inconsistencia de `Surf/T` que afecta el ranking.
- `narrow_claim_required`: no hay bug claro, pero la recuperacion de controles o el sesgo de capas obliga a un claim mas estrecho.

Gate maestro: no correr Fase 14 sin este veredicto escrito.

## Paso 6 - Regresion y Freeze del Diagnostico

- [ ] `python -m pytest -q`
- [ ] `.\scripts\smoke_test.ps1`
- [ ] `snakemake -s workflow\Snakefile -n --cores 1`
- [ ] Recalcular SHA256 de `ranking_v0_frozen.tsv` y confirmar que no cambio desde Paso 0.
- [ ] Registrar hash final del diagnostico.

Gate de salida: bitacora cerrada, ranking congelado intacto, veredicto escrito.

## Despues de `eligible_for_fase14`

Solo despues del diagnostico:

- Leave-one-layer-out.
- Perturbacion de pesos.
- Control recovery bajo perturbacion.
- Missing-data sensitivity formal.
- Risk functional-form sensitivity.
- Repeticion post-scoring de resolucion de ranking.

Fase 14 no debe usarse para tapar un problema de Fase 13. Primero se diagnostica, luego se perturba.
