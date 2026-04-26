# Workstation Contracts IPC v0

Status: Draft

This document defines a local, process-to-process IPC used by contract-runner implementations, backend adapters, and agentplane tooling.

Design constraints:

- Local-first: adapters run as child processes.
- Streaming: request/response over stdin/stdout.
- Human-debuggable: newline-delimited JSON (NDJSON) messages.
- Deterministic replay: every run emits a receipt bundle.
- Stable contract: versioned envelopes plus explicit capability negotiation.

## Transport

- Parent runner spawns adapter as a subprocess.
- Runner writes NDJSON messages to adapter stdin.
- Adapter writes NDJSON messages to stdout.
- Adapter writes logs/diagnostics to stderr, never NDJSON.
- All NDJSON lines must be UTF-8 encoded and terminated by `\n`.

## Envelope

Every message is an object with a required envelope.

Fields:

- `v`: protocol version string. For this spec: `ipc.v0`.
- `id`: ULID/UUID string. Unique per message.
- `ts`: RFC3339 timestamp.
- `type`: message type string.
- `replyTo`: optional message id being replied to.
- `trace`: optional tracing object.
- `payload`: type-specific payload object.

Example:

```json
{"v":"ipc.v0","id":"01J...","ts":"2026-04-26T00:00:00Z","type":"hello","payload":{"role":"runner"}}
```

## Message types

Handshake:

- `hello` runner to adapter
- `hello_ack` adapter to runner
- `capabilities` adapter to runner
- `capabilities_ack` runner to adapter

RPC:

- `invoke` runner to adapter
- `result` adapter to runner

Control:

- `cancel` runner to adapter
- `progress` adapter to runner

Errors:

- `error` either direction

## Handshake

Sequence:

1. Runner sends `hello` with supported protocols, a `session` object, and requested `capabilities`.
2. Adapter replies with `hello_ack` selecting a protocol version.
3. Adapter sends `capabilities` describing what it implements.
4. Runner replies `capabilities_ack` selecting optional features.

Handshake gates:

- If protocol negotiation fails, adapter must send `error` with code `IPC_PROTO_MISMATCH` and exit non-zero.

## Capabilities model

Adapters expose capabilities as named operations.

Capability record:

- `name`: operation name, for example `text.caps`.
- `inputSchema` / `outputSchema`: optional JSON Schema `$id` references or inline fragments.
- `timeouts`: suggested timeouts.
- `sideEffects`: classification: `none`, `filesystem`, `network`, or `mutable_state`.

## Invoke/result

`invoke.payload`:

- `op`: capability name.
- `args`: object.
- `timeoutMs`: optional.
- `cwd`: optional working directory.

`result.payload`:

- `ok`: boolean.
- `data`: object when ok.
- `meta`: optional object.

## Error model

`error.payload`:

- `code`: stable string code.
- `message`: short message.
- `details`: optional object.
- `retryable`: boolean.

Error codes are namespaced:

- `IPC_*` for protocol/transport.
- `ADAPTER_*` for adapter-specific failures.
- `CONTRACT_*` for runner/contract failures.

## Deterministic receipts

Every conformance run should produce:

- `run-receipt.json`: top-level metadata, command lines, exit codes, durations.
- `ipc-transcript.ndjson`: full message transcript.

## Security notes

- Tokens/secrets must be passed via environment variables or file descriptors; never embedded in NDJSON unless explicitly allowed by the contract.
- Runners can enforce allowlists for operations and filesystem roots.

## Compatibility with TritRPC

- IPC v0 is local-process oriented.
- TritRPC can be treated as a remote transport for the same operation graph.
- A bridge adapter can map `invoke(op,args)` to TritRPC calls and return `result` or `error`.
