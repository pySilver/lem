"""What a device's subscription to the board's notifications may name: an endpoint only on https,
at a push service a browser hands out, so that no request to the server can make it post to
another address; and the device's kind in short, from its browser's user agent (`push.refusal`
and `push.device_of` on `main`).

The services: Apple's `*.push.apple.com`, Google's `fcm.googleapis.com` (Chrome, Edge's Chromium
builds on Android), Mozilla's `updates.push.services.mozilla.com` and Microsoft's
`*.notify.windows.com` (https://blog.pushpad.xyz/2022/03/what-are-the-browser-push-services/).
"""

import contextlib
import ipaddress
import re
from urllib.parse import SplitResult, urlsplit

# The longest endpoint a subscription may have, in characters.
LONGEST = 2048
HOSTS = ("fcm.googleapis.com", "updates.push.services.mozilla.com")
DOMAINS = (".push.apple.com", ".notify.windows.com")
HTTPS = 443
DEVICES = (
    ("iPhone", "iPhone"),
    ("iPad", "iPad"),
    ("Android", "Android"),
    ("Macintosh|Mac OS X", "Mac"),
    ("Windows", "Windows"),
    ("Linux|X11", "Linux"),
)
BROWSERS = (
    ("Edg/", "Edge"),
    ("Firefox/|FxiOS/", "Firefox"),
    ("Chrome/|CriOS/", "Chrome"),
    ("Safari/|AppleWebKit/", "Safari"),
)


def a_service(host: str) -> bool:
    """Whether `host` is a push service a browser uses."""
    if host in HOSTS:
        return True
    return any(under(host, domain) for domain in DOMAINS)


def under(host: str, domain: str) -> bool:
    """Whether `host` is a name under `domain`."""
    return host.endswith(domain) and len(host) > len(domain)


def an_address(host: str) -> bool:
    """Whether `host` is an IP address, which no push service is."""
    with contextlib.suppress(ValueError):
        ipaddress.ip_address(host)
        return True
    return False


def plain(parts: SplitResult) -> bool:
    """Whether an address is https on its usual port, with no user and no password."""
    try:
        port = parts.port
    except ValueError:
        return False
    if parts.username or parts.password:
        return False
    return parts.scheme == "https" and port in {None, HTTPS}


def refusal(endpoint: object) -> str | None:
    """None when the endpoint is taken, else the line that says why not."""
    if not isinstance(endpoint, str) or not endpoint or len(endpoint) > LONGEST:
        return "The subscription has no endpoint of at most 2048 characters."
    parts = urlsplit(endpoint)
    if not plain(parts):
        return (
            "The subscription's endpoint is not https on its usual port, "
            "as every push service's is."
        )
    host = (parts.hostname or "").lower()
    if an_address(host):
        return "The subscription's endpoint is an IP address, and a push service has a name."
    if not a_service(host):
        return (
            f"{host} is no push service a browser uses (Apple's *.push.apple.com, "
            "Google's fcm.googleapis.com, Mozilla's updates.push.services.mozilla.com, "
            "Microsoft's *.notify.windows.com)."
        )
    return None


def device_of(agent: str) -> str:
    """A browser's user agent in short: the device and the browser, `iPhone · Safari`."""
    device = next(
        (name for pattern, name in DEVICES if re.search(pattern, agent)), "a device"
    )
    browser = next(
        (name for pattern, name in BROWSERS if re.search(pattern, agent)), "a browser"
    )
    return f"{device} · {browser}"
