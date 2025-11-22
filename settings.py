import json, os

DEFAULTS = {
    "hosts": ["8.8.8.8", "1.1.1.1", "google.com"],
    "interval_s": 1.0,
    "timeout_ms": 1000,
    "count": 60,
}

class Settings:
    PATH = os.path.join(os.path.dirname(__file__), "config.json")

    def __init__(
        self,
        hosts=None,
        interval_s=1.0,
        timeout_ms=1000,
        count=60,
        host_descriptions=None,
    ):
        self.hosts = hosts if hosts is not None else list(DEFAULTS["hosts"])
        self.interval_s = float(interval_s)
        self.timeout_ms = int(timeout_ms)
        self.count = int(count)
        # NEW: optional mapping host -> description
        self.host_descriptions = host_descriptions if host_descriptions is not None else {}

    @classmethod
    def load(cls):
        try:
            with open(cls.PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            count_val = data.get("count", data.get("window", DEFAULTS["count"]))
            hosts = data.get("hosts", DEFAULTS["hosts"])
            host_desc = data.get("host_descriptions", {})
            return Settings(
                hosts=hosts,
                interval_s=data.get("interval_s", DEFAULTS["interval_s"]),
                timeout_ms=data.get("timeout_ms", DEFAULTS["timeout_ms"]),
                count=count_val,
                host_descriptions=host_desc,
            )
        except Exception:
            return Settings()

    def save(self):
        # Ensure descriptions only for current hosts
        desc_map = {h: self.host_descriptions.get(h, "") for h in self.hosts}
        with open(self.PATH, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "hosts": self.hosts,
                    "interval_s": self.interval_s,
                    "timeout_ms": self.timeout_ms,
                    "count": self.count,
                    "host_descriptions": desc_map,
                },
                f,
                indent=2,
            )
