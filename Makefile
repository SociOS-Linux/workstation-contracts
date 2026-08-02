VENV ?= .venv
PY ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip

.PHONY: help doctor venv deps validate validate-fog-node check-fog-node-host validate-host-interfaces validate-workspace-ops validate-model-plane validate-inference-emitter validate-live-receipts clean

help:
	@echo "Targets:"
	@echo "  make doctor              - print repo identity + key paths"
	@echo "  make deps                - create/update .venv and install requirements"
	@echo "  make validate            - validate example contracts and conformance fixtures"
	@echo "  make validate-fog-node   - offline: validate the fog-node contract + emit receipt"
	@echo "  make check-fog-node-host - runtime: check THIS host's fog-node conformance (fog node only)"
	@echo "  make validate-host-interfaces - validate Agent Machine host-interface envelopes (good pass / bad fail)"
	@echo "  make validate-workspace-ops - validate workspace-ops fixtures and conformance"
	@echo "  make validate-model-plane - validate Model Plane conformance (receipt/unsigned-model/residency; good pass / bad fail)"
	@echo "  make validate-inference-emitter - self-test the InferenceReceipt emitter + hash-chained ledger"
	@echo "  make validate-live-receipts - validate the committed real-completion receipt ledger"
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
	@echo "--- Validating fog-node contract (offline, CI-safe) ---"
	$(PY) tools/check_fog_node.py --check-contract contracts/fog-node.contract.json --receipt evidence/fog-node.check-receipt.json
	@echo "--- Validating host-interface envelopes ---"
	@$(MAKE) --no-print-directory validate-host-interfaces PY=$(PY)
	@echo "--- Validating seam registry (13 seams) ---"
	$(PY) tools/validate_seam_registry.py
	@echo "--- Validating Model Plane conformance (T7-19) ---"
	@$(MAKE) --no-print-directory validate-model-plane PY=$(PY)
	@echo "--- Validating InferenceReceipt emitter (hash-chained ledger self-test) ---"
	$(PY) tools/inference_receipt_emitter.py --selftest
	@echo "--- Validating LIVE inference receipts (real completions) ---"
	$(PY) tools/validate_live_receipts.py

validate-inference-emitter:
	$(PY) tools/inference_receipt_emitter.py --selftest

validate-live-receipts:
	$(PY) tools/validate_live_receipts.py

validate-model-plane:
	@echo "GOOD model-plane fixtures (must pass):"
	$(PY) tools/validate_model_plane.py conformance/model-plane/good/*.json
	@echo "BAD model-plane fixtures (must fail as a CONFORMANCE rejection, exit 1):"
	@for f in conformance/model-plane/bad/*.json; do \
		$(PY) tools/validate_model_plane.py "$$f" >/dev/null 2>&1; rc=$$?; \
		if [ $$rc -eq 1 ]; then \
			echo "OK: rejected as expected: $$f"; \
		elif [ $$rc -eq 0 ]; then \
			echo "ERR: expected conformance failure but validated: $$f"; \
			exit 1; \
		else \
			echo "ERR: usage/infra error (exit $$rc), not a conformance rejection: $$f"; \
			exit 1; \
		fi; \
	done

validate-host-interfaces:
	@echo "GOOD host-interface envelopes (must pass):"
	$(PY) tools/validate_host_interface.py fixtures/host-interfaces/good/*.json
	@echo "BAD host-interface envelopes (must fail):"
	@for f in fixtures/host-interfaces/bad/*.json; do \
		if $(PY) tools/validate_host_interface.py "$$f" >/dev/null 2>&1; then \
			echo "ERR: expected failure but validated: $$f"; \
			exit 1; \
		else \
			echo "OK: failed as expected: $$f"; \
		fi; \
	done

validate-fog-node:
	$(PY) tools/check_fog_node.py --check-contract contracts/fog-node.contract.json --receipt evidence/fog-node.check-receipt.json

check-fog-node-host:
	@echo "Runtime host check — run this ON a fog node, not in CI."
	$(PY) tools/check_fog_node.py --check-host --receipt evidence/fog-node.check-receipt.json

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
