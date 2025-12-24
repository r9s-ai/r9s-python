from __future__ import annotations

import sys
import threading
import time
from typing import Optional


class Spinner:
    def __init__(self, prefix: str) -> None:
        self._prefix = prefix
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_len = 0
        self.prefix_printed = False

    def start(self) -> None:
        if not self._prefix:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def print_prefix(self) -> None:
        if self.prefix_printed or not self._prefix:
            return
        sys.stdout.write(self._prefix)
        sys.stdout.flush()
        self.prefix_printed = True

    def stop_and_clear(self) -> None:
        if self._thread is None:
            return
        self._stop.set()
        self._thread.join(timeout=0.5)
        self._thread = None
        if self._last_len > 0 and self._prefix:
            sys.stdout.write(
                "\r"
                + self._prefix
                + (" " * self._last_len)
                + "\r"
                + self._prefix
            )
            sys.stdout.flush()
        self._last_len = 0
        self.prefix_printed = True

    def _run(self) -> None:
        frames = ["|", "/", "-", "\\"]
        idx = 0
        while not self._stop.is_set():
            frame = frames[idx % len(frames)]
            anim = f" {frame}"
            self._last_len = len(anim)
            sys.stdout.write("\r" + self._prefix + anim)
            sys.stdout.flush()
            idx += 1
            time.sleep(0.12)

