import time
import random

_last_request_time: dict[str, float] = {}

def polite_delay(domain: str, min_seconds: float = 2.0, max_seconds: float = 5.0):
    """Never hits the same domain faster than a randomized 2-5s gap."""
    now = time.time()
    last = _last_request_time.get(domain, 0)
    wait = random.uniform(min_seconds, max_seconds) - (now - last)
    if wait > 0:
        time.sleep(wait)
    _last_request_time[domain] = time.time()