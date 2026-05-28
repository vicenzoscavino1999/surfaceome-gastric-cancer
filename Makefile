.PHONY: help setup phase1-inventory download smoke-test all test

help:
	@echo "Targets:"
	@echo "  setup       - verify repository structure"
	@echo "  phase1-inventory - rebuild lightweight dataset inventory tables"
	@echo "  download    - placeholder for reproducible downloads"
	@echo "  smoke-test  - run lightweight bootstrap and Fase 1 checks"
	@echo "  test        - run unit tests"
	@echo "  all         - placeholder for full workflow"

setup:
	@python src/utils/compare_outputs.py --self-test

phase1-inventory:
	@python scripts/build_dataset_inventory.py

download:
	@echo "Download workflow is not implemented yet. Fase 1 inventory is complete; next is Fase 2 acquisition with checksums."

smoke-test: setup
	@python src/utils/compare_outputs.py --self-test
	@python src/utils/compare_outputs.py --check-phase1-inventory

test:
	@pytest -q

all:
	@echo "Full workflow is not implemented yet. Do not generate rankings before gates are complete."
