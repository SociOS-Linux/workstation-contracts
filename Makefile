VENV ?= .venv
PY ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip

.PHONY: help doctor venv deps validate validate-workspace-ops clean

help:
	@echo "Targets:"
	@echo "  make doctor              - print repo identity + key paths"
	@echo "  make deps                - create/update .venv and install requirements"
	@echo "  make validate            - validate example contracts and conformance fixtures"
	@echo "  make validate-workspace-ops - validate workspace-ops fixtures and conformance"
	@echo "  make clean               - remove venv and caches"

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
	@for f in conformance/good/*.json; do \
		echo "VALID (good): $$f"; \
		$(PY) tools/validate_contract.py "$$f"; \
	done
	@for f in conformance/bad/*.json; do \
		echo "INVALID (bad): $$f"; \
		if $(PY) tools/validate_contract.py "$$f" >/dev/null 2>&1; then \
			echo "ERR: expected failure but validated: $$f"; \
			exit 1; \
		else \
			echo "OK: failed as expected: $$f"; \
		fi; \
	done

validate-workspace-ops:
	@echo "--- Validating workspace-ops fixture files ---"
	@for f in fixtures/workspace-ops/*.json; do \
		echo "FIXTURE: $$f"; \
		$(PY) tools/validate_workspace_ops.py "$$f"; \
	done
	@echo "--- Validating workspace-ops conformance good fixtures ---"
	@for f in conformance/good/terminal-command-ok.json \
	           conformance/good/browser-capture-ok.json \
	           conformance/good/local-agent-execution-ok.json \
	           conformance/good/file-conflict-ok.json; do \
		echo "VALID (good): $$f"; \
		$(PY) tools/validate_workspace_ops.py "$$f"; \
	done
	@echo "--- Validating workspace-ops conformance bad fixtures ---"
	@for f in conformance/bad/terminal-no-audit.json \
	           conformance/bad/browser-unscoped-capture.json \
	           conformance/bad/agent-execution-no-policy-gate.json; do \
		echo "INVALID (bad): $$f"; \
		if $(PY) tools/validate_workspace_ops.py "$$f" >/dev/null 2>&1; then \
			echo "ERR: expected failure but validated: $$f"; \
			exit 1; \
		else \
			echo "OK: failed as expected: $$f"; \
		fi; \
	done
