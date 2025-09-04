
import re, ipaddress

RE_LAST_OCT_RANGE = re.compile(r'^(\d+\.\d+\.\d+)\.(\d+)-(\d+)$')
RE_BRACKET_RANGE  = re.compile(r'^(\d+\.\d+\.\d+)\.\[(\d+)-(\d+)\]$')
RE_IP_RANGE_FULL  = re.compile(r'^(\d+\.\d+\.\d+\.\d+)-(\d+\.\d+\.\d+\.\d+)$')

def _expand_last_octet(prefix, a, b, limit):
    a, b = int(a), int(b)
    if a > b: a, b = b, a
    out = []
    for x in range(a, b+1):
        if 0 <= x <= 255:
            out.append(f"{prefix}.{x}")
            if len(out) >= limit: break
    return out

def _expand_ip_range_full(a, b, limit):
    try:
        a_ip = ipaddress.IPv4Address(a)
        b_ip = ipaddress.IPv4Address(b)
    except Exception:
        return []
    if int(a_ip) > int(b_ip):
        a_ip, b_ip = b_ip, a_ip
    out = []
    cur = int(a_ip); end = int(b_ip)
    while cur <= end and len(out) < limit:
        out.append(str(ipaddress.IPv4Address(cur)))
        cur += 1
    return out

def parse_hosts(text, limit=4096):
    if not text: return []
    tokens = [t for t in re.split(r'[\s,;]+', text.strip()) if t]
    results = []
    for tok in tokens:
        if len(results) >= limit: break
        if '/' in tok:
            try:
                for ip in ipaddress.ip_network(tok, strict=False).hosts():
                    results.append(str(ip))
                    if len(results) >= limit: break
                continue
            except Exception:
                pass
        m = RE_IP_RANGE_FULL.match(tok)
        if m:
            results.extend(_expand_ip_range_full(m.group(1), m.group(2), limit - len(results))); continue
        m = RE_LAST_OCT_RANGE.match(tok)
        if m:
            results.extend(_expand_last_octet(m.group(1), m.group(2), m.group(3), limit - len(results))); continue
        m = RE_BRACKET_RANGE.match(tok)
        if m:
            results.extend(_expand_last_octet(m.group(1), m.group(2), m.group(3), limit - len(results))); continue
        results.append(tok)
    out, seen = [], set()
    for r in results:
        if r not in seen:
            seen.add(r); out.append(r)
            if len(out) >= limit: break
    return out
