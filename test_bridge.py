#!/usr/bin/env python3
"""Self-check for the bridge's two pieces of real logic: reset text and card derivation.

Run with: python3 test_bridge.py
"""

from datetime import datetime, timedelta, timezone

from bridge import build_cards, format_reset, render

NOW = datetime(2026, 9, 5, 12, 0, 0, tzinfo=timezone.utc)


def iso(**kwargs):
    return (NOW + timedelta(**kwargs)).isoformat().replace("+00:00", "Z")


def test_format_reset():
    assert format_reset(iso(hours=2, minutes=48), NOW) == "Reset in 2h 48m"
    assert format_reset(iso(minutes=12), NOW) == "Reset in 12m"
    assert format_reset(iso(days=2, hours=3), NOW) == "Reset in 2d 3h"
    # A window that already lapsed must not render a negative countdown.
    assert format_reset(iso(hours=-1), NOW) == "Reset now"
    assert format_reset(None, NOW) == ""


def test_build_cards():
    limits = {
        "providers": {
            "claude": {
                "stale": False,
                "resources": {
                    "session": {"used": 16, "resetsAt": iso(hours=2, minutes=48)},
                    "weekly": {"used": 3, "resetsAt": iso(days=6)},
                },
            }
        }
    }
    cards, stale = build_cards(limits, "claude", NOW)
    assert not stale
    assert [c["title"] for c in cards] == ["SESSION", "WEEKLY"]
    assert cards[0]["percent"] == 16
    assert cards[0]["reset"] == "Reset in 2h 48m"
    assert cards[1]["percent"] == 3

    # An absent provider yields no cards rather than raising.
    assert build_cards(limits, "codex", NOW) == ([], False)

    # Out-of-range and missing values are clamped, never crash the page.
    odd = {"providers": {"claude": {"resources": {"session": {"used": 140}, "weekly": {}}}}}
    cards, _ = build_cards(odd, "claude", NOW)
    assert cards[0]["percent"] == 100
    assert cards[1]["percent"] is None


def test_render():
    cards, stale = build_cards(
        {"providers": {"claude": {"stale": True, "resources": {"session": {"used": 16}}}}},
        "claude",
        NOW,
    )
    html = render(cards, stale, datetime(2026, 9, 5, 19, 30))
    assert "16%" in html and "width: 16%" in html
    assert 'http-equiv="refresh" content="300"' in html
    # The Claude mark is inlined, so the Kindle never needs a second request.
    assert html.count('<img src="data:image/png;base64,') == len(cards)
    assert "http://" not in html and "https://" not in html
    assert "Updated 19:30" in html and "STALE" in html
    # No upstream payload leaks into the served page.
    assert "resetsAt" not in html and "utilization" not in html

    assert "No Claude data" in render([], False, NOW)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok {name}")
    print("all passed")
