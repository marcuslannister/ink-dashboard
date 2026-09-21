#!/usr/bin/env python3
"""Ink Dashboard bridge: read OpenUsage locally, serve plain HTML to an old Kindle browser.

Stdlib only. Run it on the Mac that has OpenUsage installed:

    python3 bridge.py

Configuration is environment only, because none of it changes at runtime:

    INK_HOST            bind address                     (default 0.0.0.0, so the LAN can reach it)
    INK_PORT            bind port                        (default 8787)
    INK_PROVIDERS       providers to rotate through, csv (default claude,codex)
    INK_OPENUSAGE_URL   OpenUsage endpoint               (default http://127.0.0.1:6736/v1/limits)
"""

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

OPENUSAGE_URL = os.environ.get("INK_OPENUSAGE_URL", "http://127.0.0.1:6736/v1/limits")
PROVIDERS = [p.strip() for p in os.environ.get("INK_PROVIDERS", "claude,codex").split(",") if p.strip()] or ["claude"]
HOST = os.environ.get("INK_HOST", "0.0.0.0")
PORT = int(os.environ.get("INK_PORT", "8787"))

# The Kindle reloads itself on this interval, which also sets how often the
# provider rotation below advances. OpenUsage refreshes its own cache every 5
# min regardless, so a faster interval just re-polls the same cached values.
REFRESH_SECONDS = 60

CARDS = (("session", "SESSION"), ("weekly", "WEEKLY"))


def current_provider(now=None):
    """Pick a provider from PROVIDERS by wall-clock time, so rotation needs no stored state."""
    now = time.time() if now is None else now
    return PROVIDERS[int(now // REFRESH_SECONDS) % len(PROVIDERS)]


def fetch_limits(url=OPENUSAGE_URL, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


def format_reset(resets_at, now=None):
    """Turn an ISO 8601 instant into compact text such as 'Reset in 2h 48m'."""
    if not resets_at:
        return ""
    now = now or datetime.now(timezone.utc)
    seconds = int((datetime.fromisoformat(resets_at) - now).total_seconds())
    if seconds <= 0:
        return "Reset now"
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60
    if days:
        return f"Reset in {days}d {hours}h"
    if hours:
        return f"Reset in {hours}h {minutes}m"
    return f"Reset in {minutes}m"


def build_cards(limits, provider=None, now=None):
    """Derive only the two values each card shows.

    Nothing from OpenUsage is passed through raw, which keeps the promise in
    docs/design.md that the LAN page exposes no credentials or upstream payload.
    """
    provider = provider or current_provider()
    provider_data = limits.get("providers", {}).get(provider) or {}
    resources = provider_data.get("resources", {})
    cards = []
    for key, title in CARDS:
        resource = resources.get(key)
        if resource is None:  # absent entirely; present-but-empty still gets a card
            continue
        used = resource.get("used")
        cards.append(
            {
                "title": title,
                "percent": None if used is None else max(0, min(100, int(round(used)))),
                "reset": format_reset(resource.get("resetsAt"), now),
            }
        )
    return cards, bool(provider_data.get("stale"))


# The Claude mark, a 44px grayscale PNG inlined as a data URI. It is embedded rather
# than linked because the Kindle can reach the bridge on the LAN and nothing else.
# Data URIs work on the Touch's 2011 WebKit; inline SVG does not.
CLAUDE_MARK = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAACwAAAAsCAQAAAC0jZKKAAABlUlEQVR42t1XC5WEMAysg0hAQiVUAhJ"
    "WQiUgoRKQgIRKQAISkHCX/kJadunt7WXf3ZUHjwYyCcOkH6X+W9PKKq92NZFlwp5Hq34F1qmPfHDgYn"
    "PfBx4ugYdXcp4fAs/Ps7qyXAZk9B7wXr2z9hnXEWhhlqnh0zWBFL4dAuk+bDgM2SDaPPV9hAHqm+xxC"
    "b3Sj9mY63wCnlnYjXzWKxUsd8Q0xEClbZUeDkEuPZUYysFUOZfG8zX0feYruoCcx0FHAID87AhYaHCM"
    "tm5LeS+MAEN2roZuru7EEERHm3s231lmCYHh9JdcLbNUSy14cNZET0oAyMOeQFOd6hogaXFqctDEtGX"
    "XwK5uvm+iGmABPYkmgNeZA/YD9Bh7I7PwTHeGcGi+MpchhtfeLV5Vvt6quptPvjsfD8rhMJ7PMtrwo4"
    "CyUs0d4NPyXvBxDKWjZoOuDs+x4R3Qkp6YZxT8d9uPUCH288TkJlYgYiUtNgiJDZuCA/0bpiaRyVRs+"
    "hdbsIgtscQWhYLLWMGF91u2CmKbG7Ht2G9snyzHtSz3CeEIAAAAAElFTkSuQmCC"
)

# The ChatGPT mark, derived from chatgpt.com/favicon.ico: cropped to the glyph's bounding
# box (the source favicon has a wide transparent margin), resized to 44px, then rebuilt as
# a black-ink alpha mask — same convention as CLAUDE_MARK — so it stays transparent outside
# the glyph rather than carrying the favicon's baked-in opaque white backing tile.
CODEX_MARK = (
    "data:image/png;base64,"
    "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"
)

MARKS = {"claude": CLAUDE_MARK, "codex": CODEX_MARK}

STYLE = """
* { margin: 0; padding: 0; }
body { width: 800px; height: 600px; background: #fff; color: #000;
       font-family: monospace; -webkit-text-size-adjust: none; }
table { width: 800px; border-collapse: separate; border-spacing: 16px; }
td { width: 50%; vertical-align: top; padding: 20px;
     border: 5px solid #000; -webkit-border-radius: 18px; border-radius: 18px; }
.title { font-size: 26px; font-weight: bold; letter-spacing: 3px; }
.title img { vertical-align: middle; margin-right: 10px; }
/* A card holds ~326px. Monospace advances ~0.6em, so "100%" needs 4 x 0.6 x size.
   Keep .pct at or below 130px or a full card overflows. */
.pct { font-size: 100px; font-weight: bold; line-height: 1.05; }
.reset { font-size: 22px; }
.bar { height: 32px; border: 4px solid #000; margin: 12px 0; }
.fill { height: 32px; background: #000; }
.foot { padding: 0 20px; font-size: 17px; }
.msg { padding: 60px 20px; font-size: 32px; font-weight: bold; }
"""

# The Kindle variant of the page: same markup, plus the scale and portrait
# orientation WebLaunch's start.sh used to inject on the device. Serving it
# from the bridge lets the native meta refresh update the page live instead
# of leaving a launch-time snapshot on the Kindle.
KINDLE_STYLE = (
    "html{overflow:hidden}body{-webkit-transform:scale(0.75);-webkit-transform-origin:0 0;}"
)
KINDLE_SCRIPT = (
    '<script type="text/javascript">'
    'try{kindle.dev.setOrientation("portrait");}catch(e){}</script>'
)


def _page(body, mark=CLAUDE_MARK, kindle=False):
    return (
        "<!DOCTYPE html>\n<html><head>"
        '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">'
        f'<meta http-equiv="refresh" content="{REFRESH_SECONDS}">'
        f'<link rel="icon" href="{mark}">'
        "<title>Ink Dashboard</title>"
        f"<style>{STYLE}{KINDLE_STYLE if kindle else ''}</style>"
        f"{KINDLE_SCRIPT if kindle else ''}"
        f"</head><body>{body}</body></html>\n"
    )


def render(cards, stale=False, now=None, provider="claude", kindle=False):
    now = now or datetime.now()
    mark = MARKS.get(provider, CLAUDE_MARK)
    cells = []
    for card in cards:
        percent = card["percent"]
        # A missing percentage still gets a card, so the layout never reflows on the Kindle.
        shown = "--" if percent is None else str(percent)
        cells.append(
            f'<td><div class="title">'
            f'<img src="{mark}" width="28" height="28" alt="">{card["title"]}</div>'
            f'<div class="pct">{shown}%</div>'
            f'<div class="bar"><div class="fill" style="width: {percent or 0}%;"></div></div>'
            f'<div class="reset">{card["reset"]}</div></td>'
        )
    if not cells:
        return _page(f'<div class="msg">No {provider.title()} data</div>', mark, kindle)
    footer = f"{provider.upper()} &middot; Updated " + now.strftime("%H:%M") + (
        " &middot; STALE" if stale else ""
    )
    return _page(
        f"<table><tr>{''.join(cells)}</tr></table>"
        f'<div class="foot">{footer}</div>',
        mark,
        kindle,
    )


def render_error(kindle=False):
    """Generic on purpose: the exception text can name internal URLs, the page is on the LAN."""
    return _page('<div class="msg">No data from OpenUsage</div>', kindle=kindle)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path, _, query = self.path.partition("?")
        if path not in ("/", "/index.html"):
            self.send_error(404)
            return
        # ?k=1 asks for the Kindle variant.
        kindle = "k" in parse_qs(query)
        try:
            provider = current_provider()
            cards, stale = build_cards(fetch_limits(), provider)
            html = render(cards, stale, provider=provider, kindle=kindle)
        except Exception as error:  # a dead OpenUsage must not kill an always-on display
            print(f"openusage read failed: {error}", file=sys.stderr)
            html = render_error(kindle)
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"ink-dashboard on http://{HOST}:{PORT}/ reading {OPENUSAGE_URL}")
    HTTPServer((HOST, PORT), Handler).serve_forever()
