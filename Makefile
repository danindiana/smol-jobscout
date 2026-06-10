.PHONY: setup run ui test smoke lint eval serve diagrams
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

# Render docs/diagrams/*.dot to .svg and .png (needs graphviz `dot`).
diagrams:
	@for f in docs/diagrams/*.dot; do \
		b=$${f%.dot}; \
		dot -Tsvg $$f -o $$b.svg && dot -Tpng -Gdpi=140 $$f -o $$b.png && echo "rendered $$b"; \
	done
