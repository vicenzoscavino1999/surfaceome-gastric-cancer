.PHONY: help setup download smoke-test all test

help:
	@echo "Targets:"
	@echo "  setup       - verify repository structure"
	@echo "  download    - placeholder for reproducible downloads"
	@echo "  smoke-test  - run lightweight bootstrap checks"
	@echo "  test        - run unit tests"
	@echo "  all         - placeholder for full workflow"

setup:
	@python src/utils/compare_outputs.py --self-test

download:
	@echo "Download workflow is not implemented yet. Complete Fase 0B first."

smoke-test: setup
	@python src/utils/compare_outputs.py --self-test

test:
	@pytest -q

all:
	@echo "Full workflow is not implemented yet. Do not generate rankings before gates are complete."
