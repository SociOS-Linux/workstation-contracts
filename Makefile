VENV ?= .venv
PY ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip

.PHONY: help doctor venv deps validate clean

help:
	@echo "Targets:"
	@echo "  make doctor   - print repo identity + key paths"
	@echo "  make deps     - create/update .venv and install requirements"
	@echo "  make validate  - validate example contracts"
	@echo "  make clean    - remove venv and caches"

doctor:
	@echo "repo: workstation-contracts"
	@echo "pwd:  $$(pwd)"
	@echo "python3: $$(command -v python3 || true)"
	@echo "make:    $$(command -v make || true)"
	@echo "venv:    $(VENV)"
	@echo "schema:  schemas/workstation-contract.v0.1.schema.json"

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
