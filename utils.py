
import subprocess, sys, re, math
WIN = sys.platform.startswith('win')
WIN_RE_FULL = re.compile(r"Reply from\s+([\d\.:a-fA-F]+):.*time[=<]?\s*(\d+)\s*ms.*TTL[=\s]?\s*(\d+)", re.IGNORECASE)
WIN_RE_TIME = re.compile(r"Reply from\s+([\d\.:a-fA-F]+):.*time[=<]?\s*(\d+)\s*ms", re.IGNORECASE)
POSIX_RE = re.compile(r"bytes from\s+([\d\.:a-fA-F]+).*time[=\s]\s*([\d\.]+)\s*ms.*ttl[=\s]\s*(\d+)", re.IGNORECASE)
POSIX_RE_TIME = re.compile(r"bytes from\s+([\d\.:a-fA-F]+).*time[=\s]\s*([\d\.]+)\s*ms", re.IGNORECASE)
def ping_host(host: str, timeout_ms: int = 1000):
    if WIN: cmd = ["ping", "-n", "1", "-w", str(timeout_ms), host]
    else: cmd = ["ping", "-c", "1", "-W", str(max(1, math.ceil(timeout_ms/1000))), host]
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=(timeout_ms/1000 + 2)); out = cp.stdout
    except Exception: return {"success": False, "latency_ms": None, "ip": None, "ttl": None}
    if WIN:
        for line in out.splitlines():
            m=WIN_RE_FULL.search(line)
            if m: ip,lat,ttl=m.group(1),int(m.group(2)),int(m.group(3)); return {"success": True,"latency_ms":lat,"ip":ip,"ttl":ttl}
            m2=WIN_RE_TIME.search(line)
            if m2: ip,lat=m2.group(1),int(m2.group(2)); return {"success": True,"latency_ms":lat,"ip":ip,"ttl":None}
        return {"success": False, "latency_ms": None, "ip": None, "ttl": None}
    for line in out.splitlines():
        m=POSIX_RE.search(line)
        if m: ip,lat,ttl=m.group(1),float(m.group(2)),int(m.group(3)); return {"success": True,"latency_ms":lat,"ip":ip,"ttl":ttl}
        m2=POSIX_RE_TIME.search(line)
        if m2: ip,lat=m2.group(1),float(m.group(2)); return {"success": True,"latency_ms":lat,"ip":ip,"ttl":None}
    return {"success": False, "latency_ms": None, "ip": None, "ttl": None}
