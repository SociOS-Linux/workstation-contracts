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
