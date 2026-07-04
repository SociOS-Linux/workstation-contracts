# Agent Machine host-interface conformance

Conformance contracts (not a production broker) for the secure host-interface layer that
connects local **terminal PTY**, **browser**, **editor**, and **agent-tool** surfaces to an
internal Podman-backed Agent Machine.

## Envelope

`schemas/host-interfaces/host-interface-envelope.schema.json` defines the broker envelope
(`host-interfaces/envelope/v1`) with embedded `$defs` for the **grant** (`host-interfaces/grant/v1`)
and the **receipt** (`host-interfaces/receipt/v1`).

Access is **deny-by-default**: an `allow` result requires a present, unexpired, unrevoked grant
whose `interfaceKind`/`workspaceId` match and whose `scope` covers the requested capabilities.

## Receipt

Every decision carries a receipt with **workspace id, interface kind, policy hash, grant id,
allow/deny result, and a redaction summary** (redacted field names + count).

## Fixtures

- `fixtures/host-interfaces/good/` — terminal-pty / browser / editor / agent-tool (hermes) allow
  cases, plus deny-by-default, grant-expired, and grant-revoked deny cases.
- `fixtures/host-interfaces/bad/` — `allow` claimed without a valid grant (missing / expired /
  revoked) — the validator must reject these.
- `fixtures/host-interfaces/transcript/broker-handshake.ndjson` — a deterministic IPC transcript
  showing the broker handshake and capability negotiation.

## Validate

```
make validate-host-interfaces   # good must pass, bad must fail
```

Also runs as part of `make validate`.

## Notes

- The agent-tool broker is **tool-agnostic** (identified by `toolId`); `hermes` is the example.
  Per the estate's OpenClaw purge, no OpenClaw is hardcoded and no tool code is vendored.
- No production runner, no secrets, and no local machine paths are committed.
