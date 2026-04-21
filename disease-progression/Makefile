.PHONY: install data notebooks test lint clean model-cards help

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install package in editable mode with dev dependencies
	pip install -e ".[dev]"

data: ## Generate synthetic patient cohorts via Synthea loader
	python -m disease_progression.data.synthea_loader --module cvd --n_patients 5000
	python -m disease_progression.data.synthea_loader --module diabetes --n_patients 5000

notebooks: ## Launch Jupyter notebook server
	jupyter notebook notebooks/

test: ## Run test suite with pytest
	pytest tests/ -v

lint: ## Lint source and test files with ruff
	ruff check src/ tests/

format: ## Auto-format source and test files with ruff
	ruff format src/ tests/

clean: ## Remove build artifacts and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/

model-cards: ## Generate model cards for all trained models
	python -c "from disease_progression.evaluation.model_card import generate_all; generate_all('configs/default.yaml')"
