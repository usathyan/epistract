.DEFAULT_GOAL := help

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install dependencies (sift-kg + optional molecular validation)
	bash scripts/setup.sh

setup-all: ## Install all dependencies including optional (RDKit, Biopython)
	bash scripts/setup.sh --all

test: ## Run unit tests (fast, no external deps)
	python -m pytest tests/ -m unit -v

test-integration: ## Run integration tests (needs sift-kg)
	python -m pytest tests/ -m integration -v

test-e2e: ## Run end-to-end pipeline tests (needs sift-kg)
	python -m pytest tests/ -m e2e -v

test-all: ## Run all test tiers
	python -m pytest tests/ -v

lint: ## Run linter
	ruff check core/ tests/

format: ## Format code
	ruff format core/ tests/

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	rm -rf .pytest_cache .ruff_cache
