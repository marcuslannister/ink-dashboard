# Context

The ubiquitous language for Ink Dashboard. Use these terms in code, commits,
issues, and documentation. Do not invent synonyms.

## Domain terms

**Ink Dashboard** — the whole product. An old Kindle shows AI usage as an
always-on e-ink display.

**bridge** — the program on the Mac (`bridge.py`). It reads OpenUsage, builds one
HTML page, and serves that page to the LAN. It holds no database and no state.

**OpenUsage** — the third-party macOS app that reads your Claude login and
publishes usage. It listens on `127.0.0.1` only. The bridge is necessary because
the Kindle cannot reach that address.

**provider** — one AI service inside the OpenUsage response: `claude`, `codex`,
or `grok`. Version 1 shows `claude` only.

**resource** — one usage window inside a provider: `session` or `weekly`. Each
resource carries a used percentage and a reset time.

**card** — one box on the screen. A card shows a title, a percentage, a bar, and
reset text. The screen holds exactly two cards, side by side.

**Session** — the card for the five-hour window.

**Weekly** — the card for the seven-day window.

**reset text** — the short countdown on a card, such as `Reset in 2h 48m`.

**stale** — OpenUsage reports that its own data is old. The page marks this in
the footer. It does not hide the cards.

## Device terms

**Kindle Touch** — the display. Model D01200, 4th generation, firmware 5.3.7.3.
Its screen is 600 × 800 in portrait. The bridge serves the 800 × 600 page
scaled to 0.75 for it at `/?k=1`.

**K5** — the MobileRead nickname for the Kindle Touch generation. Jailbreak and
MKK packages use this name, not "Touch".

**jailbreak** — the hack that opens the device to custom software. It is
installed and confirmed.

**MKK** (MobileRead Kindlet Kit) — the developer certificate and bridge that let
custom Kindlets run. The K5 jailbreak bundles it. Note that MKK has its own
"bridge", which is *not* the Ink Dashboard bridge. Always say which one you mean.

**Kindlet** — a Java app on the Kindle, packaged as `.azw2`. KUAL is a Kindlet.

**KUAL** — a launcher Kindlet. It starts other tools. **Optional.**

**WebLaunch** — a KUAL extension. It opens a URL with no browser toolbar.
**Optional.**

## Decisions that shape the language

KUAL and WebLaunch are *convenience*, not *display*. The Kindle's built-in
browser shows the dashboard. Do not describe KUAL as a requirement.

The bridge serves a *page*, not an API. It exposes no credentials, no tokens, and
no raw OpenUsage payload — only the derived values a card shows.

The target browser is Kindle WebKit from 2011. Avoid CSS Grid, Flexbox, complex
JavaScript, external fonts, and HTTPS. Use tables for layout.
