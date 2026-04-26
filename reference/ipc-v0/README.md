# IPC v0 reference harness

This directory contains a minimal reference implementation for the local IPC v0 runner/adapter contract.

It is deliberately scoped as a conformance harness:

- it demonstrates the NDJSON stdin/stdout handshake
- it emits deterministic transcript and run receipts
- it includes a small `text.caps` adapter for round-trip tests
- it does not claim to be the production workspace runner or orchestrator

## Quick run

From this directory:

```bash
python -m src.contract_runner.runner \
  --adapter "python -m src.adapters.caps_adapter" \
  --op text.caps \
  --text "hello"
```

Outputs are written under:

```text
.workstation/reports/ipc/
```

## Test

```bash
python -m pytest
```

## Boundary

The production runner/workspace controller may import these semantics, but this directory is only the reference conformance surface for `docs/specs/ipc-v0.md` and `schemas/ipc/v0/envelope.schema.json`.
