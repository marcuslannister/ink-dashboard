# Changelog

## Unreleased

- Serve a Kindle variant of the page at `/?k=1`: the bridge injects the portrait scale and orientation WebLaunch used to apply on the device, so the native meta refresh updates the screen live instead of leaving a launch-time snapshot.
- WebLaunch now loads the live bridge URL directly: `bin/start.sh` probes USB, then LAN, and rewrites `bin/dash.html` as a bootstrap redirect to the chosen URL. The upstream loader (`index.html`, `pillowHelper.js`, `settings.js`) is gone — Mesquite 5.3.7.3 does not support its `createContentWindow` API, but renders widget content directly.
