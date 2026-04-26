"""IPC v0 TritRPC bridge adapter skeleton.

This adapter intentionally does not implement real network transport yet. It
exists to prove the IPC-side adapter shape for future TritRPC integration.

Supported operations:
- remote.echo: skeleton remote call shape
- tritrpc.fixture.verify: invokes the local Rust CLI verify helper in dry-run
  mode by default, or execute mode when explicit local paths are provided
- tritrpc.frame.pack: invokes the local Rust CLI pack helper in dry-run mode by
  default, or execute mode when explicit local paths/nonce/key are provided
"""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

IPC_VERSION = "ipc.v0"
HARNESS_ROOT = Path(__file__).resolve().parents[2]
VERIFY_WRAPPER = HARNESS_ROOT / "tools" / "run-tritrpc-rust-cli-check"
PACK_WRAPPER = HARNESS_ROOT / "tools" / "run-tritrpc-frame-pack-check"


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
                "adapter": {"name": "tritrpc-bridge-adapter", "version": "0.3.0"},
                "capabilities": [
                    {
                        "name": "remote.echo",
                        "sideEffects": "network",
                        "timeouts": {"defaultMs": 10000},
                        "remote": {"protocol": "tritrpc", "method": "echo"},
                        "skeletonMode": True,
                    },
                    {
                        "name": "tritrpc.fixture.verify",
                        "sideEffects": "filesystem",
                        "timeouts": {"defaultMs": 30000},
                        "remote": {"protocol": "tritrpc", "method": "fixture.verify"},
                        "wrapper": "tools/run-tritrpc-rust-cli-check",
                        "network": False,
                    },
                    {
                        "name": "tritrpc.frame.pack",
                        "sideEffects": "filesystem",
                        "timeouts": {"defaultMs": 30000},
                        "remote": {"protocol": "tritrpc", "method": "frame.pack"},
                        "wrapper": "tools/run-tritrpc-frame-pack-check",
                        "network": False,
                    },
                ],
            },
        }
    )


def run_fixture_verify(args: dict[str, Any]) -> dict[str, Any]:
    cmd = [sys.executable, str(VERIFY_WRAPPER)]
    receipt = args.get("receipt") or ".workstation/test-reports/tritrpc-rust-cli-check-adapter.json"
    cmd += ["--receipt", str(receipt)]

    if args.get("execute"):
        for key in ["trpc", "fixtures", "nonces"]:
            if not args.get(key):
                raise ValueError(f"execute mode requires {key}")
        cmd += [
            "--execute",
            "--trpc",
            str(args["trpc"]),
            "--fixtures",
            str(args["fixtures"]),
            "--nonces",
            str(args["nonces"]),
        ]

    return run_wrapper(cmd, receipt, "execute" if args.get("execute") else "dry-run")


def run_frame_pack(args: dict[str, Any]) -> dict[str, Any]:
    cmd = [sys.executable, str(PACK_WRAPPER)]
    receipt = args.get("receipt") or ".workstation/test-reports/tritrpc-frame-pack-check-adapter.json"
    cmd += ["--receipt", str(receipt)]

    for key in ["service", "method", "json"]:
        if not args.get(key):
            raise ValueError(f"tritrpc.frame.pack requires {key}")
    cmd += ["--service", str(args["service"]), "--method", str(args["method"]), "--json", str(args["json"])]

    if args.get("nonce"):
        cmd += ["--nonce", str(args["nonce"])]
    if args.get("key"):
        cmd += ["--key", str(args["key"])]

    if args.get("execute"):
        if not args.get("trpc"):
            raise ValueError("execute mode requires trpc")
        cmd += ["--execute", "--trpc", str(args["trpc"])]

    return run_wrapper(cmd, receipt, "execute" if args.get("execute") else "dry-run")


def run_wrapper(cmd: list[str], receipt: str, mode: str) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=HARNESS_ROOT, capture_output=True, text=True, check=False)
    safe_cmd = ["<redacted>" if part and len(part) == 64 and all(c in "0123456789abcdefABCDEF" for c in part) else part for part in cmd]
    data: dict[str, Any] = {
        "command": safe_cmd,
        "exitCode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "receipt": str(receipt),
        "mode": mode,
    }
    if proc.returncode != 0:
        data["ok"] = False
        return data
    try:
        data["receiptPayload"] = json.loads(Path(HARNESS_ROOT / str(receipt)).read_text(encoding="utf-8"))
    except Exception:
        data["receiptPayload"] = None
    data["ok"] = True
    return data


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
            if op == "remote.echo":
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
            if op == "tritrpc.fixture.verify":
                try:
                    data = run_fixture_verify(args)
                except Exception as exc:
                    send_error(msg_id, "TRITRPC_FIXTURE_VERIFY_FAILED", str(exc), retryable=False)
                    continue
                if not data.get("ok"):
                    send_error(msg_id, "TRITRPC_FIXTURE_VERIFY_FAILED", "fixture verify wrapper failed", data, retryable=False)
                    continue
                send({"v": IPC_VERSION, "id": new_id(), "ts": now_rfc3339(), "type": "result", "replyTo": msg_id, "payload": {"ok": True, "data": data}})
                continue
            if op == "tritrpc.frame.pack":
                try:
                    data = run_frame_pack(args)
                except Exception as exc:
                    send_error(msg_id, "TRITRPC_FRAME_PACK_FAILED", str(exc), retryable=False)
                    continue
                if not data.get("ok"):
                    send_error(msg_id, "TRITRPC_FRAME_PACK_FAILED", "frame pack wrapper failed", data, retryable=False)
                    continue
                send({"v": IPC_VERSION, "id": new_id(), "ts": now_rfc3339(), "type": "result", "replyTo": msg_id, "payload": {"ok": True, "data": data}})
                continue
            send_error(msg_id, "ADAPTER_NO_SUCH_OP", "unknown op", {"op": op})
            continue

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
