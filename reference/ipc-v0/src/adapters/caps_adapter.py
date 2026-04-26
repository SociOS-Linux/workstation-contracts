"""IPC v0 reference adapter.

Implements:
- hello/capabilities handshake
- `text.caps`, which uppercases input text
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


def error(reply_to: str | None, code: str, message: str, details: dict[str, Any] | None = None, retryable: bool = False) -> None:
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


def main() -> int:
    negotiated = False
    caps_sent = False

    for raw in sys.stdin:
        line = raw.strip("\n")
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        if msg.get("v") != IPC_VERSION:
            error(None, "IPC_PROTO_MISMATCH", "unsupported protocol", {"got": msg.get("v")})
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
            send(
                {
                    "v": IPC_VERSION,
                    "id": new_id(),
                    "ts": now_rfc3339(),
                    "type": "capabilities",
                    "payload": {
                        "adapter": {"name": "caps-adapter", "version": "0.1.0"},
                        "capabilities": [
                            {
                                "name": "text.caps",
                                "sideEffects": "none",
                                "timeouts": {"defaultMs": 10000},
                            }
                        ],
                    },
                }
            )
            caps_sent = True
            continue

        if msg_type == "capabilities_ack":
            continue

        if msg_type == "invoke":
            if not (negotiated and caps_sent):
                error(msg_id, "IPC_STATE", "invoke before handshake")
                continue

            payload = msg.get("payload") or {}
            op = payload.get("op")
            op_args = payload.get("args") or {}

            if op != "text.caps":
                error(msg_id, "ADAPTER_NO_SUCH_OP", "unknown op", {"op": op})
                continue

            text = op_args.get("text")
            if not isinstance(text, str):
                error(msg_id, "ADAPTER_BAD_INPUT", "text must be string")
                continue

            send(
                {
                    "v": IPC_VERSION,
                    "id": new_id(),
                    "ts": now_rfc3339(),
                    "type": "result",
                    "replyTo": msg_id,
                    "payload": {"ok": True, "data": {"text": text.upper()}},
                }
            )
            continue

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
