from __future__ import annotations

import sys
import threading
import time
from typing import Optional


class LoadingSpinner:
    """Context manager for displaying a loading animation."""

    def __init__(self, message: str = "Loading") -> None:
        self.message = message
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def _animate(self) -> None:
        dots = 0
        while self.running:
            sys.stdout.write(f"\r{self.message}{'.' * dots}   ")
            sys.stdout.flush()
            dots = (dots + 1) % 4
            time.sleep(0.5)
        sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
        sys.stdout.flush()

    def __enter__(self) -> "LoadingSpinner":
        self.running = True
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)


class Spinner:
    def __init__(self, prefix: str) -> None:
        self._prefix = prefix
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_len = 0
        self.prefix_printed = False

    def start(self) -> None:
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
        if self._last_len > 0:
            if self._prefix:
                sys.stdout.write(
                    "\r" + self._prefix + (" " * self._last_len) + "\r" + self._prefix
                )
            else:
                sys.stdout.write("\r" + (" " * self._last_len) + "\r")
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
            sys.stdout.write("\r" + (self._prefix or "") + anim)
            sys.stdout.flush()
            idx += 1
            time.sleep(0.12)
