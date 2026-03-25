.PHONY: install lint test notebooks app clean

install:
	pip install -e ".[dev]"

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

test:
	pytest tests/ -v --tb=short

notebooks:
	jupyter nbconvert --execute --to notebook --inplace notebooks/01_synthetic_cohort.ipynb
	jupyter nbconvert --execute --to notebook --inplace notebooks/02_risk_classification.ipynb
	jupyter nbconvert --execute --to notebook --inplace notebooks/03_disease_progression.ipynb
	jupyter nbconvert --execute --to notebook --inplace notebooks/04_failure_modes.ipynb
	jupyter nbconvert --execute --to notebook --inplace notebooks/05_underwriting_report.ipynb

app:
	streamlit run app/app.py

clean:
	rm -rf build/ dist/ *.egg-info .mypy_cache .ruff_cache .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
