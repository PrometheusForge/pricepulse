from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse

def is_allowed(url: str, user_agent: str = "PricePulseBot/1.0") -> bool:
    """Checks robots.txt before any request. Fails CLOSED (blocks) if
    robots.txt can't be read, rather than assuming permission."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception:
        return False
    return rp.can_fetch(user_agent, url)