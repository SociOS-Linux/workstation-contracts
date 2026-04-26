# IPC v0 reference harness

This directory contains a minimal reference implementation for the local IPC v0 runner/adapter contract.

It is deliberately scoped as a conformance harness:

- it demonstrates the NDJSON stdin/stdout handshake
- it emits deterministic transcript and run receipts
- it includes a small `text.caps` adapter for round-trip tests
- it includes a TritRPC bridge skeleton adapter for remote-transport shape tests
- it includes a dry-run-capable TritRPC Rust CLI wrapper check
- it exposes `tritrpc.fixture.verify` through the bridge adapter as a codec-wrapper operation
- it does not claim to be the production workspace runner or orchestrator

## Quick run

From this directory:

```bash
python -m src.contract_runner.runner \
  --adapter "python -m src.adapters.caps_adapter" \
  --op text.caps \
  --text "hello"
```

TritRPC bridge skeleton run:

```bash
python -m src.contract_runner.runner \
  --adapter "python -m src.adapters.tritrpc_bridge_adapter" \
  --op remote.echo \
  --text "hello"
```

TritRPC fixture verify IPC operation, dry-run wrapper mode:

```bash
python -m src.contract_runner.runner \
  --adapter "python -m src.adapters.tritrpc_bridge_adapter" \
  --op tritrpc.fixture.verify \
  --text "dry-run"
```

TritRPC Rust CLI metadata dry-run:

```bash
tools/run-tritrpc-rust-cli-check
```

TritRPC Rust CLI fixture verification when a local TriTRPC checkout and binary are available:

```bash
tools/run-tritrpc-rust-cli-check \
  --execute \
  --trpc /path/to/trpc \
  --fixtures /path/to/TriTRPC/fixtures/vectors_hex_unary_rich.txt \
  --nonces /path/to/TriTRPC/fixtures/vectors_hex_unary_rich.txt.nonces
```

Outputs are written under:

```text
.workstation/reports/ipc/
```

## Test

```bash
tools/run-tests
```

## Boundary

The production runner/workspace controller may import these semantics, but this directory is only the reference conformance surface for `docs/specs/ipc-v0.md` and `schemas/ipc/v0/envelope.schema.json`.

The TritRPC bridge adapter is skeleton-only. It proves IPC-side capability declaration and invocation mapping for a future real TritRPC client; it does not open network connections.

The Rust CLI check is a codec-wrapper conformance helper. It does not fetch external fixtures and does not vendor TriTRPC fixture bytes.

The `tritrpc.fixture.verify` IPC operation shells out to the local Rust CLI check helper. Its default mode validates pinned metadata only. Execute mode still requires explicit local paths supplied through the helper; no network transport is introduced here.
