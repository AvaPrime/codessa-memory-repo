from __future__ import annotations

import math
import time


class RateLimiter:
    def __init__(self, *, requests_per_minute: int) -> None:
        if requests_per_minute < 1:
            raise ValueError("requests_per_minute must be >= 1")
        self.requests_per_minute = requests_per_minute
        self._state: dict[str, tuple[int, int]] = {}

    def check(self, key: str, *, now: float | None = None) -> tuple[bool, int]:
        ts = time.time() if now is None else now
        window = int(ts // 60)
        prev = self._state.get(key)
        if prev is None or prev[0] != window:
            self._state[key] = (window, 1)
            return True, 0

        count = prev[1]
        if count >= self.requests_per_minute:
            retry_after = max(1, int(math.ceil((window + 1) * 60 - ts)))
            return False, retry_after

        self._state[key] = (window, count + 1)
        return True, 0
