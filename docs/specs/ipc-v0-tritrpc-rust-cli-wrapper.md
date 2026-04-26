# IPC v0 TritRPC Rust CLI Wrapper Path

Status: Draft

## Purpose

This document selects the next honest codec-wrapper path for IPC v0 ↔ TritRPC v1 conformance.

The canonical TriTRPC repository exposes both Go and Rust CLIs with `trpc pack` and `trpc verify` commands. The Rust CLI is the preferred wrapper target for the next conformance tranche because it imports the repo-local `tritrpc_v1` crate directly and exposes fixture verification through `tritrpc_v1_tests::verify_file`.

## Source observation

Canonical source:

```text
SocioProphet/TriTRPC
```

Pinned inspection commit:

```text
58741244057ed1346676c7b95c9a1ec940f12952
```

Relevant Rust path:

```text
rust/tritrpc_v1/src/bin/trpc.rs
```

The Rust CLI exposes:

```text
trpc pack --service S --method M --json path.json --nonce HEX --key HEX
trpc verify --fixtures fixtures/vectors_hex_unary_rich.txt --nonces fixtures/vectors_hex_unary_rich.txt.nonces
```

## Why Rust first

The Go CLI exists and exposes a comparable `pack|verify` surface, but the inspected Go file imports:

```text
github.com/example/tritrpcv1
```

That placeholder import makes it less suitable as the first wrapper target.

The Rust CLI imports the repo-local crate:

```text
tritrpc_v1
```

That makes the Rust CLI a cleaner candidate for a subprocess codec wrapper.

## Wrapper contract

The IPC bridge should call the Rust CLI as a codec subprocess, not as a network client.

Allowed wrapper operations:

1. `trpc verify` against a pinned fixture path and nonce file.
2. `trpc pack` with explicit service, method, payload JSON, nonce, and key.

Disallowed in this tranche:

- network transport
- auth/session logic
- remote invocation
- implicit fixture fetching
- vendoring fixture bytes into workstation-contracts

## IPC-side mapping

Future IPC operation examples:

```text
tritrpc.fixture.verify
tritrpc.frame.pack
```

`tritrpc.fixture.verify` should consume:

- fixture reference manifest
- local checkout path or explicit fixture path
- nonce path
- CLI path

`tritrpc.frame.pack` should consume:

- service
- method
- payload JSON path
- nonce hex
- key hex
- CLI path

## Receipt expectations

Each wrapper execution must emit a receipt recording:

- CLI path
- source repo/commit used
- command arguments with secrets redacted where needed
- fixture path / nonce path when verifying
- stdout/stderr paths
- exit code
- status

## Follow-on implementation

A next PR should add a Python stdlib wrapper script under:

```text
reference/ipc-v0/tools/run-tritrpc-rust-cli-check
```

The script should run in dry-run/check mode unless an explicit local TriTRPC checkout and CLI path are provided.
