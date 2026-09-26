.PHONY: install reproduce verify-evidence smoke supplied-smoke test lint security check

install:
	python -m pip install -e ".[dev]"

reproduce:
	MPLCONFIGDIR=.matplotlib python -m business_review.cli reproduce --output-root local-runs/latest

verify-evidence:
	MPLCONFIGDIR=.matplotlib python -m business_review.cli reproduce --output-root .

smoke:
	MPLCONFIGDIR=.matplotlib python -m business_review.cli smoke

supplied-smoke:
	MPLCONFIGDIR=.matplotlib python -m business_review.cli run --input-weekly-kpis examples/weekly_kpis.csv --output-root /tmp/business-review-input
	python -m business_review.cli apply-decisions --claims /tmp/business-review-input/reports/claims.csv --decisions examples/review_decisions.csv --output /tmp/business-review-input/reports/reviewed_claims.csv

test:
	MPLCONFIGDIR=.matplotlib python -m pytest

lint:
	python -m ruff check .
	python -m ruff format --check .

security:
	python scripts/check_sensitive.py

check: lint test security
