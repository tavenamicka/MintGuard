# MintGuard

[Français](README.md) · [Deutsch](README.de.md) · [Español](README.es.md)

[![CI](https://github.com/tavenamicka/MintGuard/actions/workflows/ci.yml/badge.svg)](https://github.com/tavenamicka/MintGuard/actions/workflows/ci.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

Parental control app for Linux Mint — simple and accessible for non-technical parents, with screen-time limits and website and app blocking, available in 4 languages (FR/EN/DE/ES).

> Status: Phase 3 (Security & Integration) complete, Phase 4 (Testing & Release) in progress — DNS switch, iptables, security audit and accessibility audit validated. See [PROJECT_BRIEF.md](PROJECT_BRIEF.md) for the full specification and [CLAUDE_CODE_BRIEFING.md](CLAUDE_CODE_BRIEFING.md) for the phased implementation plan (both in French).

## Overview

Screenshots of the parent interface, taken with fictional data. The interface itself is displayed in your language (French, English, German or Spanish).

| Dashboard | Settings: time limit | Reports |
|---|---|---|
| ![Dashboard: protection active, time slot and time used today](docs/screenshots/tableau-de-bord.png) | ![Settings: time slot and daily limit per day](docs/screenshots/reglages-temps.png) | ![Reports for the last 7 days](docs/screenshots/rapports.png) |

## Install MintGuard (parents)

No computer skills needed: just follow these 5 steps, in order. Allow 10 minutes.

**Before you start**, check that:
- your computer runs **Linux Mint** (or Ubuntu) and is connected to the Internet;
- you know the **password** you type to log in;
- each child has **their own account** on the computer (this is how MintGuard knows who is using it).

1. **Download the installation file.** Open the [releases page](https://github.com/tavenamicka/MintGuard/releases/latest), scroll down to "Assets" and click the file `mintguard_0.1.0-1_all.deb`. It is saved in the **Downloads** folder.
2. **Start the installation.** In the Downloads folder, double-click that file. A window opens: click **Install**, type your password, then wait until it finishes (about one minute).
3. **Open MintGuard.** Click the computer's menu (bottom left), type "MintGuard" and click the icon.
4. **Answer the assistant's questions.** It asks for your child's first name, their age (to pick suitable settings) and a **PIN code** of 4 digits. Write this code down on paper: it protects your settings.
5. **Turn on protection.** If the message "Protection isn't active yet" appears, click **"Activate protection now"** and type your password. Done: MintGuard will restart by itself every time the computer starts.

Having trouble? See the [installation guide](docs/INSTALLATION.en.md), which explains what to do step by step.

## User guide

For parents: [Français](docs/USER_MANUAL_FR.md) · [English](docs/USER_MANUAL_EN.md) · [Deutsch](docs/USER_MANUAL_DE.md) · [Español](docs/USER_MANUAL_ES.md)

## Architecture

```
GUI (PyQt6, parent)
        │  D-Bus / Socket
Backend daemon (systemd, root)
   ├── DNS Controller (dnsmasq)
   ├── Firewall Controller (iptables)
   ├── Process Monitor (psutil)
   └── Session Manager (loginctl)
```

## Installation (development)

```bash
python -m venv .venv
source .venv/bin/activate    # .venv\Scripts\activate (Windows)
pip install -e .
pip install -r requirements.txt
```

## Running the tests

```bash
pytest tests/ -v
pytest tests/ --cov=mintguard
```

## Running the app (dev)

```bash
mintguard              # GUI
python -m mintguard.daemon   # daemon (does not need root in dev)
```

In development, the configuration file path can be overridden:

```bash
export MINTGUARD_CONFIG_PATH=/tmp/mintguard-config.json
```

Without this variable, MintGuard tries to read `/etc/mintguard/config.json` and falls back to default values if absent (see [etc/config.json.example](etc/config.json.example)).

## Project structure

See [PROJECT_BRIEF.md](PROJECT_BRIEF.md), section "Structure de Répertoires" (in French).

## For contributors

See [docs/DEV_SETUP.md](docs/DEV_SETUP.md) (5-minute setup) and [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MintGuard is distributed under the [GNU General Public License v3.0 or later](LICENSE) (GPL-3.0-or-later). See [docs/LICENSE_COMPLIANCE.md](docs/LICENSE_COMPLIANCE.md) for dependency compatibility and [AUTHORS.md](AUTHORS.md) for contributors.
