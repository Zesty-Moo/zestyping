# analytics.py
from typing import Dict, List, Optional, Tuple
from models import HostStats
import statistics


def compute_basic_stats(st: HostStats) -> Dict:
    """
    Basic metrics: mean, stdev, >1σ, >2σ, etc.
    """
    lats = [s.latency_ms for s in st.samples if s.success and s.latency_ms is not None]
    if not lats:
        return {
            "mean": None,
            "stdev": None,
            "above_1sigma": 0,
            "above_2sigma": 0,
        }

    mean = statistics.mean(lats)
    stdev = statistics.pstdev(lats) if len(lats) > 1 else 0

    above_1 = sum(1 for x in lats if x > mean + stdev)
    above_2 = sum(1 for x in lats if x > mean + 2 * stdev)

    return {
        "mean": mean,
        "stdev": stdev,
        "above_1sigma": above_1,
        "above_2sigma": above_2,
    }


def longest_loss_streak(st: HostStats) -> int:
    """
    Return the longest number of consecutive failed responses.
    """
    longest = 0
    current = 0

    for s in st.samples:
        if not s.success:
            current += 1
            longest = max(longest, current)
        else:
            current = 0

    return longest


def analyze_host(st: HostStats) -> Dict:
    """
    Master analysis entry point.
    Returns all analytics in one dictionary.
    """
    basic = compute_basic_stats(st)
    loss_streak = longest_loss_streak(st)

    return {
        **basic,
        "longest_loss_streak": loss_streak,
    }
