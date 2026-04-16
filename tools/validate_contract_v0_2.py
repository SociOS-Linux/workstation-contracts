#!/usr/bin/env python3
import json, re, sys
from pathlib import Path

try:
    import jsonschema
except Exception:
    print("ERR: missing dependency jsonschema. Install with: python -m pip install jsonschema", file=sys.stderr)
    raise

DIGEST_RE = re.compile(r"@sha256:[0-9a-f]{64}$")


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    if len(sys.argv) < 2:
        print("Usage: tools/validate_contract_v0_2.py <contract.json> [<contract2.json>...]", file=sys.stderr)
        return 2

    schema = load_json(Path("schemas/workstation-contract.v0.2.schema.json"))
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
            backend = lane["backend"]
            btype = backend["type"]

            if btype == "container":
                img = backend["container"]["image"]
                if not DIGEST_RE.search(img):
                    ok = False
                    print(f"FAIL semantic: {p}: lane '{lane['name']}' container.image must be digest-pinned (@sha256:<64hex>)", file=sys.stderr)

            if btype == "nix":
                nix_backend = backend["nix"]
                installable = nix_backend["installable"]
                flake = nix_backend["flake"]
                if not flake.strip():
                    ok = False
                    print(f"FAIL semantic: {p}: lane '{lane['name']}' nix.flake must be non-empty", file=sys.stderr)
                if "#" not in installable and not installable.startswith(".#"):
                    ok = False
                    print(f"FAIL semantic: {p}: lane '{lane['name']}' nix.installable should point at an explicit flake installable", file=sys.stderr)
                if lane.get("promotion", {}).get("requiresStagePass") and "stage" not in lane:
                    ok = False
                    print(f"FAIL semantic: {p}: lane '{lane['name']}' requires stage pass but no stage block is defined", file=sys.stderr)

    if ok:
        print("OK: all v0.2 contracts valid")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
