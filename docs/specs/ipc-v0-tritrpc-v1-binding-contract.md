# IPC v0 ↔ TritRPC v1 Binding Contract

Status: Draft

## Purpose

This document defines the binding boundary between the local IPC v0 subprocess adapter model and the stable TritRPC v1 codec/fixture surface.

The current `SocioProphet/TriTRPC` repository exposes TritRPC v1 as a deterministic frame, codec, and fixture parity surface across Python reference code plus Go/Rust ports. It does not yet expose a high-level network client API that workstation-contracts can honestly bind to as a remote call client.

Therefore, the correct first binding is:

```text
IPC invoke/result
  -> TritRPC request model
  -> TritRPC frame codec / canonical fixture parity
  -> future transport client
```

not:

```text
IPC invoke/result
  -> fake network RPC client
```

## Source-of-truth expectations

The binding must treat `SocioProphet/TriTRPC` as the source of truth for:

- TritRPC v1 frame layout
- canonical encoding
- fixture vectors
- AEAD/AAD behavior
- Go/Rust/Python parity
- integration readiness gates

The binding must not redefine TritRPC v1 framing locally.

## Layers

### 1. IPC adapter layer

Owned by `SociOS-Linux/workstation-contracts` reference harness.

Responsibilities:

- receive IPC v0 `invoke` messages
- validate local IPC envelope
- map configured IPC operation names to TritRPC service/method names
- call a codec/transport binding interface
- convert binding output to IPC `result` or `error`
- emit IPC transcript receipts

### 2. TritRPC codec layer

Owned by `SocioProphet/TriTRPC`.

Responsibilities:

- construct canonical TritRPC v1 frames
- parse canonical TritRPC v1 frames
- verify fixture parity
- preserve canonical JSON/hash requirements where applicable

### 3. Transport layer

Not defined here.

Future implementations may use:

- local subprocess CLI wrapper
- Unix socket
- TCP/TLS
- QUIC
- agentplane-mediated transport

Transport must not change TritRPC frame canonicality.

## Minimum binding interface

A future real binding should expose an interface equivalent to:

```python
class TritRPCBinding:
    def pack_request(self, service: str, method: str, payload: bytes, aux: bytes | None = None) -> bytes: ...
    def parse_response(self, frame: bytes) -> dict: ...
    def invoke_frame(self, frame: bytes, timeout_ms: int) -> bytes: ...
```

Where:

- `pack_request` and `parse_response` are codec-level functions.
- `invoke_frame` is transport-level and may be absent in codec-only mode.

## Skeleton adapter compatibility

The current IPC TritRPC bridge skeleton is compatible with this contract because it:

- declares `remote.echo` as a network-side capability
- marks itself as `skeletonMode`
- does not open network connections
- emits deterministic IPC result receipts
- keeps real TritRPC client binding as a follow-on

## Required evidence before real transport binding

Before enabling network-capable TritRPC bridge behavior, we require:

1. TriTRPC v1 repository `make verify` passing on the referenced commit.
2. Identified codec API or CLI wrapper path.
3. Explicit method map from IPC op names to TritRPC service/method names.
4. Authentication and policy handoff design.
5. Error mapping table:
   - IPC errors
   - TritRPC codec errors
   - transport errors
   - remote application errors
6. Agentplane run/replay receipt references when remote execution is agent-governed.

## Error mapping draft

| Source | Example | IPC error code |
| --- | --- | --- |
| IPC envelope invalid | missing payload | `IPC_BAD_ENVELOPE` |
| TritRPC frame invalid | non-canonical frame | `TRITRPC_BAD_FRAME` |
| TritRPC fixture mismatch | parity failure | `TRITRPC_FIXTURE_MISMATCH` |
| transport unavailable | connect failure | `TRITRPC_TRANSPORT_UNAVAILABLE` |
| remote timeout | deadline exceeded | `TRITRPC_TIMEOUT` |
| remote application error | service-specific failure | `TRITRPC_REMOTE_ERROR` |

## Non-goals

- no network transport implementation in this document
- no auth/session design in this document
- no replacement of TritRPC v1 spec
- no duplication of fixture vectors into workstation-contracts

## Follow-on work

- add an IPC bridge fixture that references a pinned TriTRPC fixture vector
- add a subprocess CLI wrapper option if TriTRPC exposes a stable CLI pack/verify path
- add agentplane-mediated transport binding design
- add error mapping tests
