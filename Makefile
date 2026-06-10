.PHONY: setup run ui test smoke lint eval serve
Q ?= How many postings mention Python?

setup:
	python3 -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -e ".[dev,ui]"

run:
	jobscout "$(Q)"

ui:
	python -m smol_jobscout.ui

test:
	pytest

smoke:
	pytest -m integration

lint:
	ruff check src tests

eval:
	python scripts/eval.py

serve: ui
