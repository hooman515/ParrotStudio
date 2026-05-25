from __future__ import annotations

from collections import deque
from statistics import median


class RollingMedian:
    def __init__(self, size: int = 50) -> None:
        self.values: deque[int] = deque(maxlen=size)

    def add(self, value: int) -> int:
        self.values.append(value)
        return int(median(self.values))
