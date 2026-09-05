#!/usr/bin/env python3
"""Ink Dashboard bridge: read OpenUsage locally, serve plain HTML to an old Kindle browser.

Stdlib only. Run it on the Mac that has OpenUsage installed:

    python3 bridge.py

Configuration is environment only, because none of it changes at runtime:

    INK_HOST            bind address        (default 0.0.0.0, so the LAN can reach it)
    INK_PORT            bind port           (default 8787)
    INK_PROVIDER        OpenUsage provider  (default claude)
    INK_OPENUSAGE_URL   OpenUsage endpoint  (default http://127.0.0.1:6736/v1/limits)
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

OPENUSAGE_URL = os.environ.get("INK_OPENUSAGE_URL", "http://127.0.0.1:6736/v1/limits")
PROVIDER = os.environ.get("INK_PROVIDER", "claude")
HOST = os.environ.get("INK_HOST", "0.0.0.0")
PORT = int(os.environ.get("INK_PORT", "8787"))

# The Kindle reloads itself on this interval; OpenUsage refreshes its own cache every 5 min.
REFRESH_SECONDS = 300

CARDS = (("session", "SESSION"), ("weekly", "WEEKLY"))


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


def build_cards(limits, provider=PROVIDER, now=None):
    """Derive only the two values each card shows.

    Nothing from OpenUsage is passed through raw, which keeps the promise in
    docs/design.md that the LAN page exposes no credentials or upstream payload.
    """
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


def _page(body):
    return (
        "<!DOCTYPE html>\n<html><head>"
        '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">'
        f'<meta http-equiv="refresh" content="{REFRESH_SECONDS}">'
        f'<link rel="icon" href="{CLAUDE_MARK}">'
        "<title>Ink Dashboard</title>"
        f"<style>{STYLE}</style>"
        f"</head><body>{body}</body></html>\n"
    )


def render(cards, stale=False, now=None):
    now = now or datetime.now()
    cells = []
    for card in cards:
        percent = card["percent"]
        # A missing percentage still gets a card, so the layout never reflows on the Kindle.
        shown = "--" if percent is None else str(percent)
        cells.append(
            f'<td><div class="title">'
            f'<img src="{CLAUDE_MARK}" width="28" height="28" alt="">{card["title"]}</div>'
            f'<div class="pct">{shown}%</div>'
            f'<div class="bar"><div class="fill" style="width: {percent or 0}%;"></div></div>'
            f'<div class="reset">{card["reset"]}</div></td>'
        )
    if not cells:
        return _page('<div class="msg">No Claude data</div>')
    footer = now.strftime("%H:%M") + (" &middot; STALE" if stale else "")
    return _page(
        f"<table><tr>{''.join(cells)}</tr></table>"
        f'<div class="foot">Updated {footer}</div>'
    )


def render_error():
    """Generic on purpose: the exception text can name internal URLs, the page is on the LAN."""
    return _page('<div class="msg">No data from OpenUsage</div>')


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            self.send_error(404)
            return
        try:
            cards, stale = build_cards(fetch_limits())
            html = render(cards, stale)
        except Exception as error:  # a dead OpenUsage must not kill an always-on display
            print(f"openusage read failed: {error}", file=sys.stderr)
            html = render_error()
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
