.DEFAULT_GOAL := help

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install dependencies (sift-kg + optional molecular validation)
	bash scripts/setup.sh

setup-all: ## Install all dependencies including optional (RDKit, Biopython)
	bash scripts/setup.sh --all

test: ## Run unit tests
	python -m pytest tests/test_unit.py -v

lint: ## Run linter
	ruff check scripts/ tests/

format: ## Format code
	ruff format scripts/ tests/

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	rm -rf .pytest_cache .ruff_cache

regression: ## Run regression suite against baselines
	python tests/regression/run_regression.py

regression-update: ## Update V2 baselines from current output
	python tests/regression/run_regression.py --update-baselines

regression-check: ## Quick validation of existing output (no extraction)
	python tests/regression/run_regression.py --skip-extraction
