.DEFAULT_GOAL := help

# Interpreter used by the test targets. Prefers the project venv so `make test`
# does not silently run against whatever `python` happens to be on PATH (which
# is what it did before, and which will not have the project's dependencies).
# Override explicitly: `make PYTHON=/usr/bin/python3 test`
PYTHON ?= $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)

# Directories under lint/format. Previously only core/ and tests/, which left
# domains/, examples/ and scripts/ unchecked — around a tenth of the findings
# fixed in the companion PR lived in those unlinted directories.
LINT_PATHS := core/ tests/ domains/ examples/ scripts/

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install dependencies (sift-kg + optional molecular validation)
	bash scripts/setup.sh

setup-all: ## Install all dependencies including optional (RDKit, Biopython)
	bash scripts/setup.sh --all

test: ## Run unit tests (fast, no external deps)
	$(PYTHON) -m pytest tests/ -m unit -v

test-integration: ## Run integration tests (needs sift-kg)
	$(PYTHON) -m pytest tests/ -m integration -v

test-e2e: ## Run end-to-end pipeline tests (needs sift-kg)
	$(PYTHON) -m pytest tests/ -m e2e -v

test-all: ## Run all test tiers
	$(PYTHON) -m pytest tests/ -v

lint: ## Run linter
	ruff check $(LINT_PATHS)

format: ## Format code
	ruff format $(LINT_PATHS)

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	rm -rf .pytest_cache .ruff_cache

regression: ## Run regression suite against baselines
	$(PYTHON) tests/regression/run_regression.py

regression-update: ## Update V2 baselines from current output
	$(PYTHON) tests/regression/run_regression.py --update-baselines

regression-check: ## Quick validation of existing output (no extraction)
	$(PYTHON) tests/regression/run_regression.py --skip-extraction
