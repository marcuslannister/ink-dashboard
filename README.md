# Ink Dashboard

A minimal Kindle dashboard for AI subscription usage — turns an old Kindle Touch into an always-on e-ink display showing Claude usage via [OpenUsage](https://github.com/robinebers/openusage).

See [docs/design.md](docs/design.md) for the full design: hardware, architecture, data source, and build steps.

## Usage

Install [OpenUsage](https://github.com/robinebers/openusage) and sign in to Claude:

```bash
brew install --cask openusage
```

Then run the bridge on the same Mac. It needs Python 3 and no packages:

```bash
python3 bridge.py
```

Open `http://<your-mac-lan-ip>:8787/` on the Kindle, or use KUAL → WebLaunch.
The extension lives in `kindle/WebLaunch/` (copy it to `/mnt/us/extensions/WebLaunch/` on firmware 5.3.7.3). Edit `USB_URL` / `LAN_URL` in `bin/start.sh` to match the Mac that runs the bridge.
Find the LAN address with `ipconfig getifaddr en0`.

### Configuration

All configuration is environment variables, because none of it changes at runtime.

| Variable | Default | Purpose |
| --- | --- | --- |
| `INK_HOST` | `0.0.0.0` | Bind address, so the LAN can reach it |
| `INK_PORT` | `8787` | Bind port |
| `INK_PROVIDER` | `claude` | OpenUsage provider to show |
| `INK_OPENUSAGE_URL` | `http://127.0.0.1:6736/v1/limits` | OpenUsage endpoint |

The page serves no credentials, tokens, or raw OpenUsage data — only a title,
a percentage, and reset text per card. It reloads itself every five minutes.

### Tests

```bash
python3 test_bridge.py
```

## Status

Working on a jailbroken Kindle Touch 5.3.7.3 with KUAL and WebLaunch.
Track progress on the [project board](../../projects) and [issues](../../issues).

## License

MIT — see [LICENSE](LICENSE).
