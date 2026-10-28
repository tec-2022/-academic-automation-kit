# Academic Automation Kit

<img src="assets/app-icon.png" alt="Academic Automation Kit" width="88" />

[Español](README.md) · **English** · [Sponsor](https://github.com/sponsors/tec-2022)

[![Academic Automation Kit presentation](docs/media/demo.gif)](docs/media/demo.mp4)

> The linked video is a promotional teaser, not a recording of the desktop UI. See [the interface design notes](docs/UI_DESIGN.md) for the screen flow and design references.

A safety-first toolkit that audits and prepares student computers for academic work. It favors transparent diagnostics, explicit confirmation and conservative system changes.

## Highlights

- Career-oriented software profiles and requirement checks.
- Safe preparation workflows for Windows development machines.
- MySQL/Laragon conflict diagnostics.
- Optional local AI setup.
- CLI and graphical interface.
- Redesigned desktop UI with persistent sidebar navigation, clearer software tables and progress feedback.
- Career setup can stop its queue safely between packages; it never attempts to terminate an installer halfway through.
- Five keyboard-accessible pages (Ctrl+1 to Ctrl+5), without third-party GUI dependencies.
- No automatic Temp cleanup during installations. Optional cleanup targets only this application's own stale cache files, never system-wide Temp directories.
- The separate MySQL setup binds to localhost by default; LAN access requires an explicit `-AllowLan` option.

## Quick start

```bash
python toolkit.py --help
python start_gui.py
```

Review every proposed system change before applying it. See the [Spanish documentation](README.md), [contribution guide](CONTRIBUTING.md) and [security policy](SECURITY.md).

## License

[MIT](LICENSE).
