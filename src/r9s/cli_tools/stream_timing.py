from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ChatTiming:
    r9s_phase_ms: Optional[float]
    upstream_phase_ms: Optional[float]
    ttft_ms: Optional[float]
    total_ms: float
    tps: Optional[float]
    probe_seen: bool


def timing_enabled(args: Any) -> bool:
    if getattr(args, "timing", False):
        return True
    return os.getenv("R9S_TIMING", "").strip() == "1"


def format_timing_line(timing: ChatTiming) -> str:
    def fmt_ms(value: Optional[float]) -> str:
        if value is None:
            return "-"
        return f"{value:.1f}ms"

    def fmt_tps(value: Optional[float]) -> str:
        if value is None:
            return "-"
        return f"{value:.2f}token/s"

    return (
        "timing: "
        f"r9s={fmt_ms(timing.r9s_phase_ms)} "
        f"upstream={fmt_ms(timing.upstream_phase_ms)} "
        f"ttft={fmt_ms(timing.ttft_ms)} "
        f"total={timing.total_ms:.1f}ms "
        f"tps={fmt_tps(timing.tps)} "
        f"probe={'hit' if timing.probe_seen else 'miss'}"
    )


def probe_headers(enabled: bool) -> Optional[dict[str, str]]:
    if not enabled:
        return None
    return {"X-NextRouter-SSE-Probe": "r9s"}


def iter_sse_blocks(response: Any):
    boundaries = (b"\r\n\r\n", b"\n\n", b"\r\r")
    buffer = bytearray()

    def find_boundary() -> Optional[tuple[int, bytes]]:
        best_idx: Optional[int] = None
        best_boundary: Optional[bytes] = None
        for boundary in boundaries:
            idx = buffer.find(boundary)
            if idx == -1:
                continue
            if best_idx is None or idx < best_idx:
                best_idx = idx
                best_boundary = boundary
        if best_idx is None or best_boundary is None:
            return None
        return best_idx, best_boundary

    for chunk in response.iter_bytes():
        buffer += chunk
        while True:
            hit = find_boundary()
            if hit is None:
                break
            idx, boundary = hit
            block = bytes(buffer[:idx])
            del buffer[: idx + len(boundary)]
            yield block

    if buffer:
        yield bytes(buffer)


def parse_sse_block(block: bytes) -> tuple[Optional[dict], bool]:
    text = block.decode("utf-8", errors="replace")
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    server_event: dict = {"id": None, "event": None, "data": None, "retry": None}
    data = ""
    publish = False
    probe = False

    for line in lines:
        if not line:
            continue
        if line.startswith(":"):
            if line[1:].lstrip() == "R9S PROCESSING":
                probe = True
            continue

        delim = line.find(":")
        if delim <= 0:
            continue
        field = line[:delim]
        value = line[delim + 1 :] if delim < len(line) - 1 else ""
        if value.startswith(" "):
            value = value[1:]

        if field == "data":
            data += value + "\n"
            publish = True
        elif field == "event":
            server_event["event"] = value
            publish = True
        elif field == "id":
            server_event["id"] = value
            publish = True
        elif field == "retry":
            server_event["retry"] = int(value) if value.isdigit() else None
            publish = True

    if not publish:
        return None, probe

    if not data:
        return None, probe

    data = data[:-1]
    parsed_data: Any = data
    data_is_primitive = data.isnumeric() or data in ("true", "false", "null")
    data_is_json = data.startswith(("{", "[", '"'))
    if data_is_primitive or data_is_json:
        try:
            parsed_data = json.loads(data)
        except Exception:
            parsed_data = data
    server_event["data"] = parsed_data

    return server_event, probe


@dataclass
class StreamTimingState:
    enabled: bool
    t0: float
    t_probe: Optional[float] = None
    t_first_data: Optional[float] = None
    t_done: Optional[float] = None
    probe_seen: bool = False

    @classmethod
    def start(cls, enabled: bool) -> "StreamTimingState":
        return cls(enabled=enabled, t0=time.perf_counter())

    def mark_probe(self, now: float) -> None:
        if self.probe_seen:
            return
        self.probe_seen = True
        self.t_probe = now

    def mark_first_data(self, now: float) -> None:
        if self.t_first_data is None:
            self.t_first_data = now

    def mark_done(self, now: float) -> None:
        self.t_done = now

    def finalize(self, *, output_tokens: int) -> Optional[ChatTiming]:
        if not self.enabled:
            return None

        t_done = self.t_done or time.perf_counter()
        r9s_phase_ms = (
            (self.t_probe - self.t0) * 1000.0 if self.t_probe is not None else None
        )
        upstream_phase_ms = (
            (self.t_first_data - self.t_probe) * 1000.0
            if self.t_first_data is not None and self.t_probe is not None
            else None
        )
        ttft_ms = (
            (self.t_first_data - self.t0) * 1000.0
            if self.t_first_data is not None
            else None
        )
        tps: Optional[float] = None
        if (
            output_tokens
            and self.t_first_data is not None
            and t_done > self.t_first_data
        ):
            tps = output_tokens / (t_done - self.t_first_data)

        return ChatTiming(
            r9s_phase_ms=r9s_phase_ms,
            upstream_phase_ms=upstream_phase_ms,
            ttft_ms=ttft_ms,
            total_ms=(t_done - self.t0) * 1000.0,
            tps=tps,
            probe_seen=self.probe_seen,
        )
