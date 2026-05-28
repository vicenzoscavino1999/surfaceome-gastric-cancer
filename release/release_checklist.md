# Release Checklist

## Data

- [ ] `config/datasets.yaml` complete.
- [ ] Raw checksums complete.
- [ ] Processed checksums complete where applicable.
- [ ] Data availability limitations documented.

## Code

- [ ] `workflow/` dry-run works.
- [ ] `make smoke-test` works.
- [ ] Unit tests pass.
- [ ] Scoring specification tests pass.

## Results

- [ ] Rankings include config hash and dataset freeze hash.
- [ ] Sensitivity outputs generated.
- [ ] Candidate cards generated for top candidates.
- [ ] Figures regenerate from workflow.

## Documentation

- [ ] `README.md`
- [ ] `REPRODUCIBILITY.md`
- [ ] `docs/design_decisions.md`
- [ ] `docs/analytical_decisions_registry.md`
- [ ] `docs/reviewer_attack_surface.md`

## Publication

- [ ] GitHub release.
- [ ] Zenodo DOI.
- [ ] DOI added to manuscript.
