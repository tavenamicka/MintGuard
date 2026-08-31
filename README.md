# MintGuard

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

Application de contrôle parental pour Linux Mint — simple et accessible pour des parents non-techniques, avec limitation du temps d'écran, blocage de sites et d'applications, multilingue (FR/EN/DE/ES).

> Statut : Phase 1 (Fondations) en cours. Voir [PROJECT_BRIEF.md](PROJECT_BRIEF.md) pour les spécifications complètes et [CLAUDE_CODE_BRIEFING.md](CLAUDE_CODE_BRIEFING.md) pour le plan d'implémentation par phases.

## Architecture

```
Interface GUI (PyQt6, parent)
        │  D-Bus / Socket
Daemon backend (systemd, root)
   ├── DNS Controller (dnsmasq)
   ├── Firewall Controller (iptables)
   ├── Process Monitor (psutil)
   └── Session Manager (loginctl)
```

## Installation (développement)

```bash
python -m venv .venv
source .venv/bin/activate    # ou .venv\Scripts\activate sous Windows
pip install -e .
pip install -r requirements.txt
```

## Lancer les tests

```bash
pytest tests/ -v
pytest tests/ --cov=mintguard
```

## Lancer l'application (dev)

```bash
mintguard              # GUI
python -m mintguard.daemon   # daemon (ne nécessite pas root en dev)
```

En développement, le chemin du fichier de configuration peut être surchargé :

```bash
export MINTGUARD_CONFIG_PATH=/tmp/mintguard-config.json
```

Sans cette variable, MintGuard tente de lire `/etc/mintguard/config.json` et retombe sur les valeurs par défaut si absent (voir [etc/config.json.example](etc/config.json.example)).

## Structure du projet

Voir [PROJECT_BRIEF.md](PROJECT_BRIEF.md) section "Structure de Répertoires".

## Licence

MintGuard est distribué sous licence [GNU General Public License v3.0 ou ultérieure](LICENSE) (GPL-3.0-or-later). Voir [docs/LICENSE_COMPLIANCE.md](docs/LICENSE_COMPLIANCE.md) pour la compatibilité des dépendances et [AUTHORS.md](AUTHORS.md) pour les contributeurs.
