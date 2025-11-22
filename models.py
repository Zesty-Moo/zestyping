from dataclasses import dataclass, field
from collections import deque
from typing import Deque, Optional, Tuple, List
import statistics

@dataclass
class PingSample:
    ts: float
    host: str
    success: bool
    latency_ms: Optional[float] = None
    ip: Optional[str] = None
    ttl: Optional[int] = None
    seq: int = 0

@dataclass
class HostStats:
    host: str
    count: int = 60
    description: str = ""  # <= NEW: optional, short description for this host
    samples: Deque[PingSample] = field(default_factory=lambda: deque(maxlen=60))

    def set_count(self, n: int):
        old = list(self.samples)
        self.samples = deque(old[-n:], maxlen=n)
        self.count = n

    def reset(self):
        self.samples = deque(maxlen=self.count)

    def add(self, s: PingSample):
        self.samples.append(s)

    def last(self) -> Optional[PingSample]:
        return self.samples[-1] if self.samples else None

    def counts(self) -> Tuple[int,int,float]:
        sent = len(self.samples)
        recv = sum(1 for s in self.samples if s.success)
        loss_pct = (1.0 - (recv / sent)) * 100.0 if sent > 0 else 100.0
        return sent, recv, round(loss_pct, 1)

    def latency_stats(self) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        lats: List[float] = [s.latency_ms for s in self.samples if s.success and s.latency_ms is not None]
        if not lats:
            return None, None, None
        return min(lats), round(statistics.mean(lats)), max(lats)

    def series(self):
        xs, ys = [], []
        for s in self.samples:
            xs.append(s.ts)
            ys.append(s.latency_ms if s.success else None)
        return xs, ys
