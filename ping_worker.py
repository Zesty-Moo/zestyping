
import threading, time
from typing import Dict, Optional, List
from queue import Queue
from models import PingSample
from utils import ping_host
class HostWorker(threading.Thread):
    def __init__(self, host: str, interval_s: float, timeout_ms: int, max_count: Optional[int], sample_queue: Queue, stop_event: threading.Event):
        super().__init__(daemon=True); self.host=host; self.interval_s=interval_s; self.timeout_ms=timeout_ms
        self.max_count=max_count; self.seq=0; self.sample_queue=sample_queue; self.stop_event=stop_event
    def run(self):
        next_tick=time.time()
        while not self.stop_event.is_set():
            if self.max_count is not None and self.seq >= self.max_count: break
            res=ping_host(self.host, timeout_ms=self.timeout_ms)
            self.sample_queue.put(PingSample(ts=time.time(), host=self.host, success=res["success"], latency_ms=res.get("latency_ms"), ip=res.get("ip"), ttl=res.get("ttl"), seq=self.seq))
            self.seq += 1
            next_tick += self.interval_s; self.stop_event.wait(timeout=max(0, next_tick - time.time()))
class HostManager:
    def __init__(self, sample_queue: Queue):
        self.sample_queue=sample_queue; self.workers: Dict[str, HostWorker] = {}; self.stop_events: Dict[str, threading.Event] = {}
    def start_host(self, host: str, interval_s: float, timeout_ms: int, max_count: Optional[int] = None):
        if host in self.workers: return
        ev=threading.Event(); w=HostWorker(host, interval_s, timeout_ms, max_count, self.sample_queue, ev)
        self.stop_events[host]=ev; self.workers[host]=w; w.start()
    def stop_host(self, host: str):
        if host in self.workers:
            self.stop_events[host].set(); self.workers[host].join(timeout=1.5)
            del self.workers[host]; del self.stop_events[host]
    def stop_all(self):
        for h in list(self.workers.keys()): self.stop_host(h)
    def cleanup_finished(self) -> List[str]:
        dead=[h for h,w in self.workers.items() if not w.is_alive()]
        for h in dead: self.workers.pop(h, None); self.stop_events.pop(h, None)
        return dead
    def running_hosts(self): return [h for h,w in self.workers.items() if w.is_alive()]
