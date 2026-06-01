# Fase 13 GPI Evidence Plan

Objetivo: decidir de forma auditable si la omision de evidencia GPI debe tratarse como correccion de universo Fase 4 o como correccion/sensibilidad de scoring Fase 13 verificada como membership-invariant. No implementar credito GPI ni generar `ranking_v2` hasta cerrar este plan por escrito.

## Estado de Partida

- Fase 13 v1 esta activo despues de corregir el bug de normalizacion `Surf/R`.
- `ranking_v0_frozen.tsv` preserva el snapshot pre-fix de normalizacion.
- `ranking_v1_frozen.tsv` preserva el ranking preliminar activo actual.
- El gate agregado positivo `>=5/8 top50` sigue fallando con 3/8, pero el gate causal actual no encuentra misses originales que acusen al pipeline.
- La auditoria GPI actual muestra 67 GPI anchors y 64/67 con `surfaceome_confidence_score` 5 o 6.
- Fase 4 no acredita GPI explicitamente dentro de `surfaceome_confidence_score`; el score es aditivo por fuentes, no una rubrica ordinal 5-8.

## Reglas Duras

1. No tocar pesos, politica de missing data, `T`, ni penalizaciones de shedding/soluble isoform.
2. No elegir el credito GPI mirando donde aterrizan `CEACAM5` o `MSLN`.
3. No llamar "correccion de Fase 4" a un cambio aplicado solo dentro de los 2,650 genes Core+Probable.
4. Si se aplica credito GPI, debe ser universe-wide para todos los genes elegibles con GPI confirmado, no para controles.
5. `GPI` no debe describirse como evidencia experimental; es evidencia fuerte de anclaje/localizacion tipo UniProt/anchor.
6. Separar GPI confirmado por anotacion UniProt directa de GPI inferido/predicho antes de asignar credito.
7. Preservar snapshots: v0 pre-bug, v1 pre-GPI, y solo crear v2 si el gate metodologico lo justifica.

## Paso 0 - Corregir Labels Causales Actuales

Antes de cualquier decision GPI, limpiar etiquetas que contradicen los componentes v1.

- `CEACAM5`: no etiquetar como democion por off-tumor risk si `R_rank_percentile_high_worse=0.471`. Etiqueta propuesta: `GPI/Surf source under-confidence with otherwise strong E/N/P/T`.
- `TACSTD2`: no etiquetar como democion primaria por off-tumor risk si `R_rank_percentile_high_worse=0.601`, comparable a controles recuperados. Etiqueta propuesta: `mid surface confidence plus weaker protein support`.
- `MSLN`: mantener residual biologico/metodologico por shedding/soluble isoform y calibracion GPI/Surf; no tocar `T`.
- `CLDN18` y `FGFR2`: mantener isoform unresolved y biologias de seguridad/topologia como causas principales.
- Registrar en `docs/fase13_diagnostico.md` que esta correccion de labels no cambia scores ni rankings.

Gate de salida: `fase13_positive_control_causal_gate.tsv` y `fase13_diagnostico.md` no deben afirmar una causa que el componente contradice.

## Paso 0.5 - Test de Membresia GPI

Pregunta decisiva:

> Hay genes con GPI confirmado que quedaron fuera de Core+Probable y que habrian entrado si GPI hubiese contado como evidencia?

Este test decide la ruta. No elegir A/B por preferencia.

### Conteos Requeridos

- Numero de genes con GPI confirmado en el pool pre-universo evaluable.
- Numero de genes con GPI confirmado dentro de Core+Probable.
- Numero de genes con GPI confirmado fuera de Core+Probable.
- Para los GPI confirmados fuera de Core+Probable, simular el termino GPI aditivo y contar cuantos cruzarian a Core/Probable.
- Separar GPI confirmado UniProt directo de GPI inferido/predicho con una columna explicita.

### Decision de Ruta

- Si el conteo de GPI confirmados que cambiarian membresia es `0`: no reabrir Fase 4 como narrativa principal. Ruta corta: `Fase 13 scoring correction, membership-invariant`.
- Si el conteo es `>0`: reabrir Fase 4 y re-correr downstream. Ruta larga obligatoria: `Fase 4 evidence-completeness correction`.

Gate de salida: tabla de membresia GPI y decision escrita antes de implementar credito.

## Paso 1 - Regla A Priori del Credito GPI

La regla debe escribirse antes de tocar codigo.

Principio:

> Confirmed GPI anchoring is strong cell-surface anchor evidence, not experimental capture evidence. It should enter as an additive evidence term matched to the closest existing non-experimental anchor/topology evidence in the current Fase 4 scoring function.

Implicaciones:

- No usar floor arbitrario `raw=7` o `raw=8`.
- No decir "semantica de escala 5-8"; la funcion real es aditiva.
- Usar un termino aditivo `+X`, donde `X` se deriva del peso existente para evidencia fuerte no experimental/anchor en Fase 4.
- Aplicar credito pleno solo a GPI confirmado por anotacion UniProt directa.
- GPI inferido/predicho: credito menor o solo bandera, segun decision escrita.
- Implementacion idempotente si se usa correccion de score: no duplicar credito si el mismo hecho ya fue incorporado por otra evidencia equivalente.

Gate de salida: decision fechada en `docs/fase13_diagnostico.md` o decision registry antes de rerun.

## Paso 2A - Ruta Corta si Membership-Invariant

Usar solo si Paso 0.5 demuestra que ningun GPI confirmado cambia membresia.

- No llamarlo correccion de Fase 4.
- Nombre recomendado: `Fase 13 GPI scoring correction, membership-invariant`.
- Aplicar credito GPI a todos los GPI confirmados ya presentes en Core+Probable.
- Mantener `ranking_v1_frozen.tsv` intacto.
- Generar `ranking_v2_frozen.tsv` solo si el credito fue preregistrado.
- Generar sensibilidad `v1` vs `v2`.
- Reportar explicitamente `CEACAM5` y `MSLN` entre movers si se mueven.

Gate de salida: v2 activo solo si la sensibilidad no introduce artefactos obvios en top50.

## Paso 2B - Ruta Larga si Cambia Membresia

Usar si Paso 0.5 encuentra al menos un GPI confirmado que habria entrado al universo.

- Reabrir Fase 4.
- Incorporar GPI confirmado como evidencia de anchor/localizacion en la construccion del universo.
- Recalcular Core+Probable.
- Re-correr downstream Fase 5-13 segun dependencias reales.
- Preservar v1 como snapshot pre-correccion de evidencia.
- Generar v2 como ranking activo despues del rerun completo.

Gate de salida: universo, componentes y ranking v2 reproducidos por workflow.

## Paso 3 - Sensibilidad Con/Sin GPI

Independiente de ruta corta o larga:

- Crear tabla `fase13_gpi_credit_sensitivity.tsv` o equivalente.
- Comparar ranking v1 vs v2.
- Resumir solo GPI anchors:
  - n cambiados.
  - delta de rank mediano/min/max.
  - entradas/salidas top50.
  - `CEACAM5` y `MSLN` reportados explicitamente.
- Auditar genes que entran al top50 por credito GPI:
  - E/N/P/T razonables.
  - no dominados solo por Surf.
  - TME/off-tumor flags visibles.

Gate de salida: sensibilidad documentada; no ocultar movers.

## Paso 4 - Re-verificar Controles por Causa en v2

Re-extraer los 8 controles positivos con componentes:

- `Surf`
- `E`
- `N`
- `R`
- `P`
- `T`
- rank
- score
- causal class

Expectativas:

- `CEACAM5`: deberia mejorar si GPI era causa real de under-confidence; si queda fuera, causa residual debe estar documentada por componentes.
- `MSLN`: puede seguir bajo por `T_rank` y shedding/soluble isoform; eso no es bug si queda documentado.
- `CLDN18`: isoforma unresolved y biologia/safety.
- `FGFR2`: isoforma unresolved y biologia/safety.
- `TACSTD2`: confianza media/no-GPI y soporte proteinico mas debil.

Gate de salida: ningun miss original sin explicacion causal por componente.

## Paso 5 - Gates Finales

Mantener ambos gates visibles:

- Gate agregado preregistrado: `>=5/8 top50`.
- Gate causal: misses originales que acusan al pipeline.

Veredicto permitido:

- `eligible_for_fase14`: no hay bug residual, GPI resuelto por ruta apropiada, ambos gates reportados.
- `blocked_by_scoring_bug`: al menos un miss queda sin explicacion causal o surge bug de implementacion.
- `narrow_claim_required`: no hay bug claro, pero sensibilidad/movers/top50 indican fragilidad fuerte que limita el claim.

Frase esperada si todo cierra:

> No residual scoring bug remains. The Surf/R normalization bug was corrected in v1. The GPI evidence issue was evaluated with a membership test; the selected route was applied universe-wide with an a priori additive rule and reported with/without sensitivity. Remaining control misses are explained by isoform ambiguity, shedding/soluble biology, topology/accessibility, or legitimate evidence strength.

## Paso 6 - Validacion y Freeze

- `python -m pytest -q`
- `.\scripts\smoke_test.ps1`
- `snakemake -s workflow\Snakefile -n --cores 1`
- `snakemake -s workflow\Snakefile --summary`
- Registrar hashes v0, v1 y v2 si existe.
- Confirmar que v1 queda identico al snapshot pre-GPI.
- Actualizar README, REPRODUCIBILITY, release manifest, design decisions, analytical registry, limitations register, reviewer attack surface, provenance.

## Paso 7 - Fase 14

Solo despues del veredicto escrito:

- Leave-one-layer-out.
- Perturbacion de pesos.
- Missing-data sensitivity.
- Risk functional-form sensitivity.
- Control recovery bajo perturbacion.
- Repeticion de estabilidad/rank-resolution con scores reales.

Fase 14 debe correr sobre el ranking activo final de Fase 13: v1 si no se aplica credito GPI, v2 si se aplica y se congela.

