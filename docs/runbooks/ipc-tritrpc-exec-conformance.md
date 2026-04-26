# IPC TritRPC Execute Conformance Runbook

Status: Draft

## Purpose

This runbook documents the final execute-mode conformance lane for IPC v0 to TritRPC v1 fixture verification.

The lane proves that:

1. `workstation-contracts` IPC v0 can invoke `tritrpc.fixture.verify` through the bridge adapter.
2. The bridge adapter can shell out to the Rust CLI wrapper helper.
3. The wrapper can execute a real local `trpc verify` command against pinned TritRPC fixture files.
4. The result emits IPC receipts and TritRPC wrapper receipts.

## External source

Canonical external source:

```text
https://github.com/SocioProphet/TriTRPC.git
```

Pinned commit:

```text
58741244057ed1346676c7b95c9a1ec940f12952
```

Fixture files:

```text
fixtures/vectors_hex_unary_rich.txt
fixtures/vectors_hex_unary_rich.txt.nonces
```

## Local sequence

From a clean checkout of `workstation-contracts`:

```bash
mkdir -p _deps
git clone https://github.com/SocioProphet/TriTRPC.git _deps/TriTRPC
cd _deps/TriTRPC
git checkout 58741244057ed1346676c7b95c9a1ec940f12952
cargo build -p tritrpc_v1 --bin trpc
```

Then from `reference/ipc-v0`:

```bash
python -m src.contract_runner.runner \
  --adapter "python -m src.adapters.tritrpc_bridge_adapter" \
  --out .workstation/reports/ipc-tritrpc-exec \
  --op tritrpc.fixture.verify \
  --args-json '{"execute":true,"trpc":"../../_deps/TriTRPC/target/debug/trpc","fixtures":"../../_deps/TriTRPC/fixtures/vectors_hex_unary_rich.txt","nonces":"../../_deps/TriTRPC/fixtures/vectors_hex_unary_rich.txt.nonces","receipt":".workstation/test-reports/tritrpc-rust-cli-check-exec.json"}'
```

## Expected receipts

IPC run receipt:

```text
reference/ipc-v0/.workstation/reports/ipc-tritrpc-exec/run-receipt.json
```

TritRPC wrapper receipt:

```text
reference/ipc-v0/.workstation/test-reports/tritrpc-rust-cli-check-exec.json
```

## Boundary

- `workstation-contracts` does not vendor fixture bytes.
- CI checks out TriTRPC source at a pinned commit during execution.
- No network transport is implemented.
- No auth/session protocol is introduced.
- This is codec/fixture verification only.

## Future hardening

- Pin GitHub Actions by commit SHA rather than tag.
- Cache the Rust target directory by TriTRPC commit hash.
- Emit uploaded CI artifacts for the receipts.
- Add a follow-on adapter mode for `tritrpc.frame.pack`.
