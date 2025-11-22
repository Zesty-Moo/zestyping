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
    description: str = ""  # short human-friendly label for this host
    samples: Deque[PingSample] = field(default_factory=lambda: deque(maxlen=60))

    def set_count(self, n: int):
        """Adjust the sliding window length, preserving the most recent samples."""
        old = list(self.samples)
        self.samples = deque(old[-n:], maxlen=n)
        self.count = n

    def reset(self):
        """Clear all samples but keep the configured window size."""
        self.samples = deque(maxlen=self.count)

    def add(self, s: PingSample):
        """Append a new sample to this host's history."""
        self.samples.append(s)

    def last(self) -> Optional[PingSample]:
        """Return the most recent sample, or None if there are no samples."""
        return self.samples[-1] if self.samples else None

    def counts(self) -> Tuple[int, int, float]:
        """
        Return (sent, recv, loss_pct).
        loss_pct is 0–100, where 100 means total loss (or no samples yet).
        """
        sent = len(self.samples)
        recv = sum(1 for s in self.samples if s.success)
        loss_pct = (1.0 - (recv / sent)) * 100.0 if sent > 0 else 100.0
        return sent, recv, round(loss_pct, 1)

    # ---------- latency helpers / analytics foundation ----------

    def _latency_values(self) -> List[float]:
        """Return list of successful latency values in ms."""
        return [
            s.latency_ms
            for s in self.samples
            if s.success and s.latency_ms is not None
        ]

    def latency_stats(self) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Min, Avg (rounded), Max latency in ms for successful pings.
        This keeps the original behavior used by the UI.
        """
        lats: List[float] = self._latency_values()
        if not lats:
            return None, None, None
        mn = min(lats)
        avg = statistics.mean(lats)
        mx = max(lats)
        return mn, round(avg), mx

    def latency_sigma(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Return (mean, stdev) for successful latencies.

        - mean: arithmetic mean of successful latencies
        - stdev: population standard deviation (pstdev);
          if fewer than 2 samples, stdev = None
        """
        lats = self._latency_values()
        if not lats:
            return None, None
        if len(lats) < 2:
            # Only one value -> mean is defined, stdev is not meaningful
            return statistics.mean(lats), None
        mean = statistics.mean(lats)
        stdev = statistics.pstdev(lats)
        return mean, stdev

    def count_above_sigma(self, k: float = 1.0) -> int:
        """
        Count how many successful samples are above mean + k * stdev.
        If stdev is None or 0 (no variance), returns 0.
        Useful for basic outlier detection.
        """
        mean, stdev = self.latency_sigma()
        if mean is None or stdev is None or stdev == 0:
            return 0
        threshold = mean + k * stdev
        lats = self._latency_values()
        return sum(1 for v in lats if v > threshold)

    def series(self):
        """
        Return (xs, ys) where:
        - xs: timestamps (epoch seconds)
        - ys: latency in ms for successes, or None for failures (for plotting)
        """
        xs, ys = [], []
        for s in self.samples:
            xs.append(s.ts)
            ys.append(s.latency_ms if s.success else None)
        return xs, ys
