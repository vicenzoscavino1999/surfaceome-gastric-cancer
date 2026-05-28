# Notebook-to-Pipeline Protocol

Notebooks are exploratory only. Main paper outputs must come from `workflow/` and `src/`.

If a notebook finding changes the pipeline:

1. Preserve the notebook output.
2. Add an entry in `docs/design_decisions.md` with notebook path, heading/cell, finding, and proposed change.
3. Implement the change in `src/` or `workflow/`.
4. Rerun affected downstream rules.
5. Generate a diff against the latest frozen ranking.
6. If the top 20 changes, update `docs/analytical_decisions_registry.md`.

No manuscript result may depend on a manual notebook-only step.
