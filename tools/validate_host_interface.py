#!/usr/bin/env python3
"""Validate Agent Machine host-interface envelopes (issue #26).

Schema-validates each HostInterfaceEnvelope (terminal PTY, browser, editor,
agent-tool) against schemas/host-interfaces/host-interface-envelope.schema.json,
then enforces deny-by-default semantics:

- an `allow` result REQUIRES a present, unexpired, unrevoked grant whose kind and
  workspace match the envelope and whose scope covers the requested capabilities;
- the embedded receipt must agree with the envelope (result, grantId, kind,
  workspace) and carry a policyHash + redactionSummary.

Usage: tools/validate_host_interface.py <envelope.json> [...]
Exit 0 iff every envelope is valid.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERR: missing dependency jsonschema (pip install jsonschema)", file=sys.stderr); raise

SCHEMA=Path("schemas/host-interfaces/host-interface-envelope.schema.json")

def grant_valid(env: dict) -> tuple[bool,str]:
    g=env.get("grant")
    if not g: return False,"no grant presented (deny-by-default)"
    if g.get("revoked"): return False,"grant revoked"
    if g["expiresAt"] <= env["decidedAt"]: return False,"grant expired at decision time"
    if g["interfaceKind"] != env["interfaceKind"]: return False,"grant interfaceKind mismatch"
    if g["workspaceId"] != env["workspaceId"]: return False,"grant workspace mismatch"
    scope=set(g.get("scope",[]))
    if "*" not in scope and not set(env["requestedCapabilities"]).issubset(scope):
        return False,"requested capabilities exceed grant scope"
    return True,"ok"

def check(path: Path, schema: dict) -> bool:
    try:
        env=json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"FAIL parse: {path}: {e}", file=sys.stderr); return False
    try:
        jsonschema.validate(env, schema)
    except jsonschema.ValidationError as e:
        print(f"FAIL schema: {path}: {e.message}", file=sys.stderr); return False

    ok=True
    valid,reason=grant_valid(env)
    if env["result"]=="allow" and not valid:
        print(f"FAIL semantic: {path}: result=allow but grant invalid ({reason})", file=sys.stderr); ok=False
    # receipt consistency
    r=env["receipt"]
    if r["result"]!=env["result"]:
        print(f"FAIL semantic: {path}: receipt.result != envelope.result", file=sys.stderr); ok=False
    if r["interfaceKind"]!=env["interfaceKind"] or r["workspaceId"]!=env["workspaceId"]:
        print(f"FAIL semantic: {path}: receipt kind/workspace mismatch", file=sys.stderr); ok=False
    exp_gid=(env.get("grant") or {}).get("grantId")
    if r.get("grantId") != exp_gid:
        print(f"FAIL semantic: {path}: receipt.grantId != envelope grant", file=sys.stderr); ok=False
    return ok

def main() -> int:
    if len(sys.argv)<2:
        print("usage: validate_host_interface.py <envelope.json> [...]", file=sys.stderr); return 2
    schema=json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    ok=True
    for a in sys.argv[1:]:
        if not check(Path(a), schema): ok=False
    if ok: print("OK: all host-interface envelopes valid"); return 0
    return 1

if __name__=="__main__": raise SystemExit(main())
