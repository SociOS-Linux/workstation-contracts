"""IPC v0 reference runner for workstation-contracts conformance.

This is intentionally a small reference harness, not the production runner.
It demonstrates:
- deterministic NDJSON transcript capture
- explicit hello/capabilities handshake
- invoke/result round trip
- run receipt emission
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Iterator, TextIO

IPC_VERSION = "ipc.v0"


def now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def new_id() -> str:
    return uuid.uuid4().hex


@dataclass
class IPCMessage:
    v: str
    id: str
    ts: str
    type: str
    payload: dict[str, Any]
    replyTo: str | None = None

    def to_dict(self) -> dict[str, Any]:
        msg: dict[str, Any] = {
            "v": self.v,
            "id": self.id,
            "ts": self.ts,
            "type": self.type,
            "payload": self.payload,
        }
        if self.replyTo:
            msg["replyTo"] = self.replyTo
        return msg


class NDJSONWriter:
    def __init__(self, fp: BinaryIO, transcript_fp: TextIO | None = None):
        self.fp = fp
        self.transcript_fp = transcript_fp

    def send(self, msg: IPCMessage) -> None:
        line = json.dumps(msg.to_dict(), separators=(",", ":"), ensure_ascii=False)
        self.fp.write((line + "\n").encode("utf-8"))
        self.fp.flush()
        if self.transcript_fp:
            self.transcript_fp.write(line + "\n")
            self.transcript_fp.flush()


class NDJSONReader:
    def __init__(self, fp: BinaryIO, transcript_fp: TextIO | None = None):
        self.fp = fp
        self.transcript_fp = transcript_fp

    def __iter__(self) -> Iterator[dict[str, Any]]:
        for raw in self.fp:
            try:
                line = raw.decode("utf-8").strip("\n")
            except UnicodeDecodeError:
                continue
            if not line:
                continue
            if self.transcript_fp:
                self.transcript_fp.write(line + "\n")
                self.transcript_fp.flush()
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def require_envelope(msg: dict[str, Any]) -> None:
    for key in ["v", "id", "ts", "type", "payload"]:
        if key not in msg:
            raise ValueError(f"missing required IPC envelope field: {key}")
    if msg["v"] != IPC_VERSION:
        raise ValueError(f"unsupported IPC version: {msg['v']}")


def spawn_adapter(cmd: list[str], env: dict[str, str] | None = None) -> subprocess.Popen[bytes]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        env=merged_env,
    )


def handshake(writer: NDJSONWriter, reader: NDJSONReader, requested_caps: list[str]) -> dict[str, Any]:
    hello_id = new_id()
    writer.send(
        IPCMessage(
            v=IPC_VERSION,
            id=hello_id,
            ts=now_rfc3339(),
            type="hello",
            payload={
                "role": "runner",
                "protocols": [IPC_VERSION],
                "requestedCapabilities": requested_caps,
                "session": {"pid": os.getpid()},
            },
        )
    )

    caps: dict[str, Any] | None = None
    for msg in reader:
        require_envelope(msg)
        msg_type = msg["type"]
        if msg_type == "hello_ack":
            continue
        if msg_type == "capabilities":
            caps = msg["payload"]
            writer.send(
                IPCMessage(
                    v=IPC_VERSION,
                    id=new_id(),
                    ts=now_rfc3339(),
                    type="capabilities_ack",
                    replyTo=msg["id"],
                    payload={"accepted": requested_caps},
                )
            )
            break
        if msg_type == "error":
            raise RuntimeError(f"adapter error during handshake: {msg['payload']}")

    if caps is None:
        raise RuntimeError("handshake failed: adapter did not send capabilities")
    return caps


def invoke(writer: NDJSONWriter, reader: NDJSONReader, op: str, args: dict[str, Any], timeout_ms: int = 10_000) -> dict[str, Any]:
    req_id = new_id()
    writer.send(
        IPCMessage(
            v=IPC_VERSION,
            id=req_id,
            ts=now_rfc3339(),
            type="invoke",
            payload={"op": op, "args": args, "timeoutMs": timeout_ms},
        )
    )

    started = time.monotonic()
    for msg in reader:
        require_envelope(msg)
        if msg.get("replyTo") != req_id:
            continue
        if msg["type"] == "result":
            return msg["payload"]
        if msg["type"] == "error":
            raise RuntimeError(f"adapter returned error: {msg['payload']}")
        if (time.monotonic() - started) * 1000 > timeout_ms:
            raise TimeoutError(f"timed out waiting for result op={op}")

    raise RuntimeError("adapter process ended before replying")


def main() -> int:
    parser = argparse.ArgumentParser(prog="ipc-v0-reference-runner")
    parser.add_argument("--adapter", required=True, help="Adapter command, e.g. 'python -m src.adapters.caps_adapter'")
    parser.add_argument("--out", default=".workstation/reports/ipc", help="Output directory for receipts")
    parser.add_argument("--op", default="text.caps")
    parser.add_argument("--text", default="hello world")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = out_dir / "ipc-transcript.ndjson"
    run_receipt_path = out_dir / "run-receipt.json"

    adapter_cmd = shlex.split(args.adapter)
    proc = spawn_adapter(adapter_cmd)
    assert proc.stdin is not None and proc.stdout is not None

    with transcript_path.open("w", encoding="utf-8") as transcript_fp:
        writer = NDJSONWriter(proc.stdin, transcript_fp=transcript_fp)
        reader = NDJSONReader(proc.stdout, transcript_fp=transcript_fp)
        caps = handshake(writer, reader, requested_caps=[args.op])
        result = invoke(writer, reader, op=args.op, args={"text": args.text})

    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=2)

    receipt = {
        "v": "run-receipt.v0",
        "ts": now_rfc3339(),
        "adapter": adapter_cmd,
        "capabilities": caps,
        "invocation": {"op": args.op, "args": {"text": args.text}},
        "result": result,
        "exitCode": proc.returncode,
        "transcript": str(transcript_path),
    }
    run_receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
