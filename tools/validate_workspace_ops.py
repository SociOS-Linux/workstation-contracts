#!/usr/bin/env python3
"""
Workspace Operations contract validator.

Validates fixture files against their JSON Schema definitions under
schemas/workspace-ops/ and applies semantic rules that enforce:

- Terminal commands must not use --no-audit.
- Browser capture must not combine capture-scope=none with a web-capture step.
- Local agent execution must always have a prior policy gate
  (--no-policy-gate is rejected).
- Workspace-ops conformance lanes must emit required evidence keys
  based on their sourceos.* labels.

Usage:
    python tools/validate_workspace_ops.py <fixture.json> [<fixture2.json>...]

Exits 0 when all fixtures are valid, 1 on any failure.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print(
        "ERR: missing dependency jsonschema. Install with: pip install jsonschema",
        file=sys.stderr,
    )
    raise


# ---------------------------------------------------------------------------
# Schema registry
# ---------------------------------------------------------------------------

SCHEMA_DIR = Path("schemas/workspace-ops")

_SCHEMA_CACHE: dict[str, dict] = {}


def _load_schema(name: str) -> dict:
    if name not in _SCHEMA_CACHE:
        path = SCHEMA_DIR / name
        _SCHEMA_CACHE[name] = json.loads(path.read_text(encoding="utf-8"))
    return _SCHEMA_CACHE[name]


# Map schema-version strings to schema filenames.
SCHEMA_VERSION_MAP = {
    "workspace-ops/local-operation-log/v1": "local-operation-log.schema.json",
    "workspace-ops/terminal-session/v1": "terminal-session.schema.json",
    "workspace-ops/terminal-command/v1": "terminal-command.schema.json",
    "workspace-ops/browser-session/v1": "browser-session.schema.json",
    "workspace-ops/web-capture/v1": "web-capture.schema.json",
    "workspace-ops/transfer-operation/v1": "transfer-operation.schema.json",
    "workspace-ops/local-agent-execution/v1": "local-agent-execution.schema.json",
    "workspace-ops/capability-profile/v1": "capability-profile.schema.json",
    "workspace-ops/diagnostic-redaction/v1": "diagnostic-redaction.schema.json",
    "workspace-ops/provisional-artifact-id/v1": "provisional-artifact-id.schema.json",
}


# ---------------------------------------------------------------------------
# Semantic rules applied to WorkstationContract conformance fixtures
# ---------------------------------------------------------------------------

WORKSPACE_OPS_LABEL = "sourceos.workspace_ops"

# (pattern, error_message)
FORBIDDEN_STEP_PATTERNS: list[tuple[re.Pattern, str]] = [
    (
        re.compile(
            r"workspace-ops\s+terminal-command\s+run[^\n]*--no-audit"
        ),
        "Terminal command must not use --no-audit; audit-disabled sessions cannot participate in workspace operation evidence chains.",
    ),
    (
        re.compile(
            r"workspace-ops\s+web-capture\s+take[^\n]*--capture-scope\s+none"
        ),
        "Browser web-capture step must not use --capture-scope none; use an explicit-urls or allowed-origins scope.",
    ),
    (
        re.compile(
            r"workspace-ops\s+local-agent-execution\s+run[^\n]*--no-policy-gate"
        ),
        "Local agent execution must not use --no-policy-gate; all LocalAgentExecution operations require a prior PolicyGateRecord.",
    ),
]

# Label -> required evidence key mapping for workspace-ops lanes.
REQUIRED_EVIDENCE_BY_LABEL: dict[str, str] = {
    "sourceos.terminal_command": "terminal.command.evidence",
    "sourceos.browser_session": "browser.capture.evidence",
    "sourceos.local_agent_execution": "agent.execution.evidence",
    "sourceos.file_conflict": "file.conflict.evidence",
}


# ---------------------------------------------------------------------------
# Fixture validator (workspace-ops schema documents)
# ---------------------------------------------------------------------------


def _validate_fixture(path: Path, doc: dict, ok: bool) -> bool:
    schema_version = doc.get("schemaVersion", "")
    schema_file = SCHEMA_VERSION_MAP.get(schema_version)
    if schema_file is None:
        # Not a workspace-ops typed fixture; skip schema validation.
        return ok

    schema = _load_schema(schema_file)
    try:
        jsonschema.validate(doc, schema)
    except jsonschema.ValidationError as e:
        print(f"FAIL schema: {path}: {e.message}", file=sys.stderr)
        return False

    return ok


# ---------------------------------------------------------------------------
# WorkstationContract semantic validator (conformance fixtures)
# ---------------------------------------------------------------------------


def _iter_steps(doc: dict):
    for lane in doc.get("spec", {}).get("lanes", []):
        for step in lane.get("steps", []):
            yield lane, step


def _validate_workstation_contract(path: Path, doc: dict, ok: bool) -> bool:
    if doc.get("kind") != "WorkstationContract":
        return ok

    labels = doc.get("metadata", {}).get("labels", {})

    # Only apply workspace-ops rules to contracts that opt in.
    if labels.get(WORKSPACE_OPS_LABEL) != "true":
        return ok

    for lane in doc.get("spec", {}).get("lanes", []):
        evidence_emit = set(lane.get("evidence", {}).get("emit", []))

        for label, required_evidence in REQUIRED_EVIDENCE_BY_LABEL.items():
            if labels.get(label) == "true" and required_evidence not in evidence_emit:
                ok = False
                print(
                    f"FAIL semantic: {path}: lane '{lane['name']}' must emit "
                    f"'{required_evidence}' when {label}=true",
                    file=sys.stderr,
                )

    for lane, step in _iter_steps(doc):
        run = step.get("run", "")
        for pattern, message in FORBIDDEN_STEP_PATTERNS:
            if pattern.search(run):
                ok = False
                print(
                    f"FAIL semantic: {path}: step '{step.get('name', '<unnamed>')}' "
                    f"in lane '{lane['name']}': {message}",
                    file=sys.stderr,
                )

    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Usage: tools/validate_workspace_ops.py <fixture.json> [<fixture2.json>...]",
            file=sys.stderr,
        )
        return 2

    ok = True
    for arg in sys.argv[1:]:
        p = Path(arg)
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"FAIL parse: {p}: {e}", file=sys.stderr)
            ok = False
            continue

        ok = _validate_fixture(p, doc, ok)
        ok = _validate_workstation_contract(p, doc, ok)

    if ok:
        print("OK: all workspace-ops fixtures valid")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
