"""IPC v0 TritRPC bridge adapter skeleton.

This adapter intentionally does not implement real network transport yet. It
exists to prove the IPC-side adapter shape for future TritRPC integration.
"""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

IPC_VERSION = "ipc.v0"


def now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def new_id() -> str:
    return uuid.uuid4().hex


def send(msg: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(msg, separators=(",", ":"), ensure_ascii=False) + "\n")
    sys.stdout.flush()


def send_error(reply_to: str | None, code: str, message: str, details: dict[str, Any] | None = None, retryable: bool = False) -> None:
    payload: dict[str, Any] = {"code": code, "message": message, "retryable": retryable}
    if details is not None:
        payload["details"] = details
    msg: dict[str, Any] = {
        "v": IPC_VERSION,
        "id": new_id(),
        "ts": now_rfc3339(),
        "type": "error",
        "payload": payload,
    }
    if reply_to:
        msg["replyTo"] = reply_to
    send(msg)


def send_capabilities() -> None:
    send(
        {
            "v": IPC_VERSION,
            "id": new_id(),
            "ts": now_rfc3339(),
            "type": "capabilities",
            "payload": {
                "adapter": {"name": "tritrpc-bridge-adapter", "version": "0.1.0"},
                "capabilities": [
                    {
                        "name": "remote.echo",
                        "sideEffects": "network",
                        "timeouts": {"defaultMs": 10000},
                        "remote": {"protocol": "tritrpc", "method": "echo"},
                        "skeletonMode": True,
                    }
                ],
            },
        }
    )


def main() -> int:
    negotiated = False

    for raw in sys.stdin:
        line = raw.strip("\n")
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        if msg.get("v") != IPC_VERSION:
            send_error(None, "IPC_PROTO_MISMATCH", "unsupported protocol", {"got": msg.get("v")})
            return 2

        msg_type = msg.get("type")
        msg_id = msg.get("id")

        if msg_type == "hello":
            negotiated = True
            send(
                {
                    "v": IPC_VERSION,
                    "id": new_id(),
                    "ts": now_rfc3339(),
                    "type": "hello_ack",
                    "replyTo": msg_id,
                    "payload": {"role": "adapter", "selected": IPC_VERSION},
                }
            )
            send_capabilities()
            continue

        if msg_type == "capabilities_ack":
            continue

        if msg_type == "invoke":
            if not negotiated:
                send_error(msg_id, "IPC_STATE", "invoke before handshake")
                continue
            payload = msg.get("payload") or {}
            op = payload.get("op")
            args = payload.get("args") or {}
            if op != "remote.echo":
                send_error(msg_id, "ADAPTER_NO_SUCH_OP", "unknown op", {"op": op})
                continue
            send(
                {
                    "v": IPC_VERSION,
                    "id": new_id(),
                    "ts": now_rfc3339(),
                    "type": "result",
                    "replyTo": msg_id,
                    "payload": {
                        "ok": True,
                        "data": {
                            "skeletonMode": True,
                            "transport": "tritrpc",
                            "method": "echo",
                            "args": args,
                        },
                    },
                }
            )
            continue

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
