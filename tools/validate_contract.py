#!/usr/bin/env python3
import json, re, sys
from pathlib import Path

try:
    import jsonschema
except Exception:
    print("ERR: missing dependency jsonschema. Install with: python -m pip install jsonschema", file=sys.stderr)
    raise

DIGEST_RE = re.compile(r"@sha256:[0-9a-f]{64}$")
SENTINEL = "@sha256:REPLACE_WITH_DIGEST"

FORBIDDEN_RUN_PATTERNS = [
    (
        re.compile(r"sourceosctl\s+agent-machine\s+mounts\s+plan[^\n]*--dev-root\s+(?:\$HOME|~)(?:\s|$)"),
        "Agent Machine must not use $HOME or ~ as the dev/code root; use ~/dev or an explicit repo allowlist root.",
    ),
    (
        re.compile(r"sourceosctl\s+agent-machine\s+mounts\s+plan[^\n]*--docs-root\s+(?:\$HOME|~)(?:\s|$)"),
        "Agent Machine must not use $HOME or ~ as the document root; use ~/Documents/SourceOS/agent-output.",
    ),
    (
        re.compile(r"sourceosctl\s+agent-machine\s+mounts\s+plan[^\n]*--downloads-root\s+~/Downloads(?:\s|$)"),
        "Browser downloads must use scoped ~/Downloads/SourceOS/agent-downloads, not the whole host Downloads directory.",
    ),
    (
        re.compile(r"sourceosctl\s+office\s+inspect\s+[^\n]*(?:NoteStore\.sqlite|group\.com\.apple\.notes|Photos\.photoslibrary|Voice\s*Memos|VoiceMemos|Reminders)", re.IGNORECASE),
        "Office/App integrations must use future App Doors; raw Apple app databases/libraries must not be inspected or mounted by default.",
    ),
]

REQUIRED_EVIDENCE_BY_LABEL = {
    "sourceos.agent_machine": "agent-machine.mount.evidence",
    "sourceos.office_plane": "office.artifact.evidence",
}

def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))

def iter_steps(doc):
    for lane in doc["spec"]["lanes"]:
        for step in lane.get("steps", []):
            yield lane, step

def main():
    if len(sys.argv) < 2:
        print("Usage: tools/validate_contract.py <contract.json> [<contract2.json>...]", file=sys.stderr)
        return 2

    schema = load_json(Path("schemas/workstation-contract.v0.1.schema.json"))

    ok = True
    for arg in sys.argv[1:]:
        p = Path(arg)
        doc = load_json(p)

        try:
            jsonschema.validate(doc, schema)
        except jsonschema.ValidationError as e:
            ok = False
            print(f"FAIL schema: {p}: {e.message}", file=sys.stderr)
            continue

        labels = doc.get("metadata", {}).get("labels", {})

        for lane in doc["spec"]["lanes"]:
            b = lane["backend"]
            if b["type"] == "container":
                img = b["container"]["image"]

                # Allow sentinel ONLY for examples (keeps CI green while we bootstrap the real digest).
                if str(p).startswith("examples/") and img.endswith(SENTINEL):
                    print(f"WARN: {p}: lane '{lane['name']}' uses sentinel digest; replace with real sha256 when truth-lane image exists.", file=sys.stderr)
                    continue

                if not DIGEST_RE.search(img):
                    ok = False
                    print(f"FAIL semantic: {p}: lane '{lane['name']}' container.image must be digest-pinned (@sha256:<64hex>)", file=sys.stderr)

            evidence_emit = set(lane.get("evidence", {}).get("emit", []))
            for label, required_evidence in REQUIRED_EVIDENCE_BY_LABEL.items():
                if labels.get(label) == "true" and required_evidence not in evidence_emit:
                    ok = False
                    print(
                        f"FAIL semantic: {p}: lane '{lane['name']}' must emit {required_evidence} when {label}=true",
                        file=sys.stderr,
                    )

        for lane, step in iter_steps(doc):
            run = step.get("run", "")
            for pattern, message in FORBIDDEN_RUN_PATTERNS:
                if pattern.search(run):
                    ok = False
                    print(
                        f"FAIL semantic: {p}: step '{step.get('name', '<unnamed>')}' in lane '{lane['name']}': {message}",
                        file=sys.stderr,
                    )

    if ok:
        print("OK: all contracts valid")
        return 0
    return 1

if __name__ == "__main__":
    raise SystemExit(main())

