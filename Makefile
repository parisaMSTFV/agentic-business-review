.PHONY: install reproduce smoke test lint security check

install:
	python -m pip install -e ".[dev]"

reproduce:
	MPLCONFIGDIR=.matplotlib python -m business_review.cli reproduce

smoke:
	MPLCONFIGDIR=.matplotlib python -m business_review.cli smoke

test:
	MPLCONFIGDIR=.matplotlib python -m pytest

lint:
	python -m ruff check .

security:
	python scripts/check_sensitive.py

check: lint test security
