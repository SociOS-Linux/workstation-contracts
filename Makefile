VENV ?= .venv
PY ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip

.PHONY: venv deps validate clean

venv:
	python3 -m venv $(VENV)
	$(PIP) install -U pip setuptools wheel

deps: venv
	$(PIP) install -r requirements.txt

validate:
	$(PY) tools/validate_contract.py examples/pixi-dev.json
	$(PY) tools/validate_contract.py examples/truth-lane-container.json

clean:
	rm -rf $(VENV) __pycache__ .pytest_cache
.PHONY: help doctor

help:
@echo "Targets:"
@echo "  make deps      - create/update .venv and install requirements"
@echo "  make validate   - validate examples + conformance (if present)"
@echo "  make clean     - remove venv and caches"
@echo "  make doctor    - print repo identity + paths"

doctor:
@echo "repo: workstation-contracts"
@echo "pwd:  $$(pwd)"
@echo "python: $$(command -v python3 || true)"
@echo "make:   $$(command -v make || true)"
@echo "venv:   $(VENV)"
@echo "schema: schemas/workstation-contract.v0.1.schema.json"
