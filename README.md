# MintGuard

Français · [English](README.en.md) · [Deutsch](README.de.md) · [Español](README.es.md)

[![CI](https://github.com/tavenamicka/MintGuard/actions/workflows/ci.yml/badge.svg)](https://github.com/tavenamicka/MintGuard/actions/workflows/ci.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

Application de contrôle parental pour Linux Mint — simple et accessible pour des parents non-techniques, avec limitation du temps d'écran, blocage de sites et d'applications, multilingue (FR/EN/DE/ES).

> Version **0.1.1**. Statut : Phase 3 (Sécurité & Intégration) terminée, Phase 4 (Testing & Release) en cours — bascule DNS, iptables, audit de sécurité, audit d'accessibilité et audit du code (2026-10-11) faits. Voir [PROJECT_BRIEF.md](PROJECT_BRIEF.md) pour les spécifications complètes et [CLAUDE_CODE_BRIEFING.md](CLAUDE_CODE_BRIEFING.md) pour le plan d'implémentation par phases.

## Guide utilisateur

Pour les parents : [Français](docs/USER_MANUAL_FR.md) · [English](docs/USER_MANUAL_EN.md) · [Deutsch](docs/USER_MANUAL_DE.md) · [Español](docs/USER_MANUAL_ES.md)

## Architecture

```
Interface GUI (PyQt6, parent)      Icônes de notification (parent / enfant)
        │                                   │
        │ lecture/écriture                  │ lecture seule
        ▼                                   ▼
Base SQLite partagée ◄──────┐   Socket Unix /run/mintguard/status.sock
(groupe mintguard-admin)    │   (statut, authentifié par SO_PEERCRED)
                            │               │
                    Daemon backend (systemd, root)
                       ├── DNS Controller (dnsmasq, blocklist dynamique par enfant)
                       ├── Site Usage Tracker (journal DNS, quota par site)
                       ├── Firewall Controller (iptables)
                       ├── Process Monitor (psutil)
                       └── Session Manager (loginctl)
```

La GUI et le daemon ne communiquent pas directement : la GUI écrit les règles dans la base SQLite, que le daemon relit à chaque cycle. Le socket `status.sock` est le seul canal exposé au compte enfant ; il ne fournit que le statut de l'appelant (temps restant, période de grâce).

Le blocage des sites ne fonctionne que si le résolveur DNS du système est dnsmasq (`/etc/resolv.conf` → `127.0.0.1`). Cette bascule n'est jamais automatique à l'installation : elle se fait depuis le Tableau de bord (bouton « Activer le blocage des sites », qui lance `/usr/lib/mintguard/switch-dns.sh` via pkexec), et le Tableau de bord la signale si elle est défaite.

## Installation (paquet .deb)

Pour installer MintGuard sur un poste, sans cloner le dépôt :

```bash
bash scripts/build-deb.sh                          # produit dist/mintguard_<version>-1_all.deb
sudo apt install ./dist/mintguard_0.1.1-1_all.deb   # apt installe aussi les dépendances système
```

Ouvrez ensuite MintGuard depuis le menu des applications : le Tableau de bord propose « Activer la protection » (démarre le daemon), puis « Activer le blocage des sites » (bascule DNS). Pour réinstaller le même numéro de version, ajoutez `--reinstall`. Désinstallation : `sudo apt remove mintguard` (le DNS d'origine est rétabli), ou `purge` pour supprimer aussi la base et les journaux. Détails : [docs/INSTALLATION.md](docs/INSTALLATION.md).

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

## Pour les contributeurs

Voir [docs/DEV_SETUP.md](docs/DEV_SETUP.md) (setup en 5 min) et [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

MintGuard est distribué sous licence [GNU General Public License v3.0 ou ultérieure](LICENSE) (GPL-3.0-or-later). Voir [docs/LICENSE_COMPLIANCE.md](docs/LICENSE_COMPLIANCE.md) pour la compatibilité des dépendances et [AUTHORS.md](AUTHORS.md) pour les contributeurs.
