# Ink Dashboard

> A minimal Kindle dashboard for AI subscription usage.

## Goal

Turn an old Kindle into an always-on e-ink display for AI usage information. The first version will show Claude subscription usage through OpenUsage.

## Hardware

- **Device:** Amazon Kindle Touch
- **Model number:** D01200
- **Generation:** 4th generation
- **Community nickname:** K5
- **Display:** 6-inch grayscale e-ink
- **Native resolution:** 600 × 800
- **Dashboard orientation:** Landscape, 800 × 600
- **Connection:** Local Wi-Fi

## Version 1 scope

Version 1 displays only one provider:

- **Provider:** Claude
- **Cards:** Session and Weekly
- **Interaction:** None
- **Refresh:** Automatically every five minutes
- **Network:** Local LAN only

Codex and additional dashboard pages can be added after the Claude version is working reliably.

## Visual design

The screen uses two large cards placed side by side:

| Session | Weekly |
| --- | --- |
| Five-hour usage window | Seven-day usage window |
| Reset countdown | Reset countdown |
| Large usage percentage | Large usage percentage |
| Solid monochrome progress bar | Solid monochrome progress bar |

Design requirements:

- Black, white, and grayscale only
- Large bold percentage values
- Heavy monospace or pixel-style font
- Rounded card borders
- Compact reset text
- High contrast for the Kindle display
- No charts, gradients, shadows, animations, menus, or buttons
- No touch or page-switching controls

## Architecture

```text
Claude Code or Claude Desktop
            ↓
      OpenUsage on Mac
            ↓
  Local Ink Dashboard bridge
            ↓
 Simple HTML on the local LAN
            ↓
 WebLaunch on the Kindle Touch
```

## Data source

[OpenUsage](https://github.com/robinebers/openusage) runs on macOS and reads the existing Claude login. It supplies:

- Five-hour session usage
- Seven-day weekly usage
- Usage percentages
- Reset timestamps
- Data freshness information

OpenUsage refreshes its cache every five minutes and exposes a read-only API at:

```text
http://127.0.0.1:6736/v1/limits
```

This API is available only on the Mac itself. Ink Dashboard will read it locally and expose only the rendered dashboard page to the trusted LAN.

Install OpenUsage with:

```bash
brew install --cask openusage
```

## Dashboard bridge

The bridge service on the Mac will:

1. Read Claude data from the OpenUsage local API.
2. Calculate friendly reset text such as `Reset in 2h 48m`.
3. Generate an old-browser-compatible HTML page.
4. Listen on a configurable LAN address, such as `http://192.168.0.10:8787/`.
5. Refresh the browser every five minutes.
6. Serve no credentials, tokens, transcripts, or raw OpenUsage data.

The HTML should use simple server-rendered markup and CSS. It should avoid CSS Grid, complex JavaScript, external fonts, and HTTPS dependencies.

Browser refresh:

```html
<meta http-equiv="refresh" content="300">
```

## Kindle software

[WebLaunch](https://github.com/PaulFreund/WebLaunch) is a KUAL extension designed for the Kindle Touch. It opens a configured URL without the standard browser toolbar.

Expected location:

```text
/mnt/us/extensions/WebLaunch/
```

Example `settings.js`. Replace the address with your own — find it with
`ipconfig getifaddr en0`:

```javascript
var settings = {
    url: 'http://192.168.0.10:8787/',
    title: 'Ink Dashboard',
    hideStatusbar: true,
    enableWireless: true,
    powerButtonClose: true,
    enablePreventScreenSaver: true,
    landscape: true
};
```

## Prerequisites

- macOS 15 or later
- OpenUsage installed and successfully reading Claude usage
- Kindle Touch connected to the same LAN
- Kindle jailbreak compatible with its exact firmware
- KUAL installed — *optional*, see below
- WebLaunch installed — *optional*, see below

KUAL and WebLaunch are not required to show the dashboard. The Kindle Touch has a
built-in browser, and this page is already written for it. KUAL and WebLaunch only
remove the browser toolbar and keep the screen awake. Version 1 works without them.

Do not update the Kindle firmware before checking its current version. The correct jailbreak method depends on that version.

## Next steps

1. Check the Kindle firmware under **Home → Menu → Settings → Menu → Device Info**.
2. Select the correct jailbreak method for that firmware.
3. Install KUAL and WebLaunch.
4. Confirm OpenUsage returns Claude data on the Mac.
5. Implement the small dashboard bridge.
6. Test the 800 × 600 layout in a desktop browser.
7. Open the LAN dashboard URL through WebLaunch.
8. Tune font size, margins, borders, and refresh behavior on the physical Kindle.

## References

- [OpenUsage](https://github.com/robinebers/openusage)
- [OpenUsage local HTTP API](https://github.com/robinebers/openusage/blob/main/docs/local-http-api.md)
- [OpenUsage Claude provider](https://github.com/robinebers/openusage/blob/main/docs/providers/claude.md)
- [WebLaunch](https://github.com/PaulFreund/WebLaunch)
- [Kindle Touch hacking guide](https://wiki.mobileread.com/wiki/Kindle_Touch_Hacking)
