# IPC v0 reference harness

This directory contains a minimal reference implementation for the local IPC v0 runner/adapter contract.

It is deliberately scoped as a conformance harness:

- it demonstrates the NDJSON stdin/stdout handshake
- it emits deterministic transcript and run receipts
- it includes a small `text.caps` adapter for round-trip tests
- it includes a TritRPC bridge skeleton adapter for remote-transport shape tests
- it includes dry-run-capable TritRPC Rust CLI wrapper checks for fixture verification and frame packing
- it exposes `tritrpc.fixture.verify` and `tritrpc.frame.pack` through the bridge adapter as codec-wrapper operations
- it supports explicit JSON invoke arguments via `--args-json` or `--args-file`
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
  --args-json '{"receipt":".workstation/test-reports/tritrpc-rust-cli-check-ipc.json"}'
```

TritRPC fixture verify IPC operation, execute mode with explicit local paths:

```bash
python -m src.contract_runner.runner \
  --adapter "python -m src.adapters.tritrpc_bridge_adapter" \
  --op tritrpc.fixture.verify \
  --args-json '{"execute":true,"trpc":"/path/to/trpc","fixtures":"/path/to/TriTRPC/fixtures/vectors_hex_unary_rich.txt","nonces":"/path/to/TriTRPC/fixtures/vectors_hex_unary_rich.txt.nonces"}'
```

TritRPC frame pack IPC operation, dry-run wrapper mode:

```bash
python -m src.contract_runner.runner \
  --adapter "python -m src.adapters.tritrpc_bridge_adapter" \
  --op tritrpc.frame.pack \
  --args-json '{"service":"hyper.v1","method":"AddVertex_a.REQ","json":"fixtures/payload-addvertex-a.json","receipt":".workstation/test-reports/tritrpc-frame-pack-ipc.json"}'
```

TritRPC frame pack IPC operation, execute mode with explicit local paths and caller-supplied nonce/key:

```bash
python -m src.contract_runner.runner \
  --adapter "python -m src.adapters.tritrpc_bridge_adapter" \
  --op tritrpc.frame.pack \
  --args-json '{"execute":true,"trpc":"/path/to/trpc","service":"hyper.v1","method":"AddVertex_a.REQ","json":"fixtures/payload-addvertex-a.json","nonce":"000000000000000000000000000000000000000000000000","key":"0000000000000000000000000000000000000000000000000000000000000000"}'
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

TritRPC frame pack helper, dry-run mode:

```bash
tools/run-tritrpc-frame-pack-check \
  --service hyper.v1 \
  --method AddVertex_a.REQ \
  --json fixtures/payload-addvertex-a.json
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

The Rust CLI helpers are codec-wrapper conformance helpers. They do not fetch external fixtures and do not vendor TriTRPC fixture bytes.

The `tritrpc.fixture.verify` IPC operation shells out to the local Rust CLI check helper. Its default mode validates pinned metadata only. Execute mode requires explicit local paths supplied through the invoke arguments; no network transport is introduced here.

The `tritrpc.frame.pack` IPC operation shells out to the local frame-pack helper. Its default mode validates payload and argument shape only. Execute mode requires an explicit local `trpc` path plus caller-provided payload, nonce, and key; the key is redacted in receipts.
