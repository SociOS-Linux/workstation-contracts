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

def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))

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

    if ok:
        print("OK: all contracts valid")
        return 0
    return 1

if __name__ == "__main__":
    raise SystemExit(main())

