# IPC v0 TritRPC Bridge Adapter

Status: Draft skeleton

## Purpose

IPC v0 is the local runner-to-adapter protocol. TritRPC is the remote/service transport used elsewhere in the SocioProphet/SourceOS stack.

The bridge adapter maps local IPC invocations onto remote TritRPC calls while preserving the IPC envelope and receipt semantics.

## Boundary

This document defines the adapter boundary only.

It does not define:

- the TritRPC wire protocol
- service discovery
- authentication
- authorization
- remote sandboxing

Those belong in the TritRPC / agentplane / policy layers.

## Mapping

IPC request:

```json
{
  "type": "invoke",
  "payload": {
    "op": "remote.echo",
    "args": {"text": "hello"}
  }
}
```

Bridge behavior:

1. Validate IPC envelope.
2. Map `payload.op` to a configured TritRPC method.
3. Send `payload.args` to the TritRPC client implementation.
4. Convert the remote response to IPC `result`.
5. Convert remote failures to IPC `error`.

## Capability model

The bridge exposes configured capabilities in the normal IPC `capabilities` message.

Example capability:

```json
{
  "name": "remote.echo",
  "sideEffects": "network",
  "timeouts": {"defaultMs": 10000},
  "remote": {
    "protocol": "tritrpc",
    "method": "echo"
  }
}
```

## Skeleton mode

The current reference adapter is intentionally skeleton-only. It does not open network connections.

Instead, it supports:

- handshake
- capability declaration
- safe `remote.echo` dry-run invocation
- deterministic IPC transcript generation through the reference runner

## Follow-on

- plug in the real TritRPC client library
- add authentication/policy handoff
- add remote error-code mapping
- add replayable transcript fixtures
- add agentplane run/replay receipt references
