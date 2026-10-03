# MintGuard

[![CI](https://github.com/tavenamicka/MintGuard/actions/workflows/ci.yml/badge.svg)](https://github.com/tavenamicka/MintGuard/actions/workflows/ci.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

Application de contrôle parental pour Linux Mint — simple et accessible pour des parents non-techniques, avec limitation du temps d'écran, blocage de sites et d'applications, multilingue (FR/EN/DE/ES).

> Statut : Phase 3 (Sécurité & Intégration) terminée, Phase 4 (Testing & Release) en cours — bascule DNS, iptables, audit de sécurité et audit d'accessibilité validés. Voir [PROJECT_BRIEF.md](PROJECT_BRIEF.md) pour les spécifications complètes et [CLAUDE_CODE_BRIEFING.md](CLAUDE_CODE_BRIEFING.md) pour le plan d'implémentation par phases.

## Aperçu

Captures de l'interface parent, réalisées sur des données fictives.

| Tableau de bord | Réglages : limite de temps | Rapports |
|---|---|---|
| ![Tableau de bord : protection active, plage horaire et temps utilisé aujourd'hui](docs/screenshots/tableau-de-bord.png) | ![Réglages : plage horaire et limite quotidienne par jour](docs/screenshots/reglages-temps.png) | ![Rapports des 7 derniers jours](docs/screenshots/rapports.png) |

## Installer MintGuard (parents)

Pas besoin d'être à l'aise avec l'informatique : il suffit de suivre ces 5 étapes, dans l'ordre. Comptez 10 minutes.

**Avant de commencer**, vérifiez que :
- votre ordinateur fonctionne sous **Linux Mint** (ou Ubuntu) et est connecté à Internet ;
- vous connaissez le **mot de passe** que vous tapez pour ouvrir votre session ;
- chaque enfant a **son propre compte** sur l'ordinateur (c'est ainsi que MintGuard sait qui l'utilise).

1. **Téléchargez le fichier d'installation.** Ouvrez la [page des versions](https://github.com/tavenamicka/MintGuard/releases/latest), descendez jusqu'à « Assets » et cliquez sur le fichier `mintguard_0.1.0-1_all.deb`. Il est enregistré dans le dossier **Téléchargements**.
2. **Lancez l'installation.** Dans le dossier Téléchargements, double-cliquez sur ce fichier. Une fenêtre s'ouvre : cliquez sur **Installer**, tapez votre mot de passe, puis attendez la fin (environ une minute).
3. **Ouvrez MintGuard.** Cliquez sur le menu de l'ordinateur (en bas à gauche), tapez « MintGuard » et cliquez sur l'icône.
4. **Répondez aux questions de l'assistant.** Il vous demande le prénom de votre enfant, son âge (pour choisir des réglages adaptés) et un **code PIN** à 4 chiffres. Notez ce code sur papier : il protège vos réglages.
5. **Activez la protection.** Si le message « La protection n'est pas encore activée » apparaît, cliquez sur **« Activer la protection maintenant »** et tapez votre mot de passe. C'est fait : MintGuard se remettra en route tout seul à chaque démarrage.

Un souci ? Consultez le [guide d'installation](docs/INSTALLATION.md), qui explique quoi faire pas à pas.

## Guide utilisateur

Pour les parents : [Français](docs/USER_MANUAL_FR.md) · [English](docs/USER_MANUAL_EN.md) · [Deutsch](docs/USER_MANUAL_DE.md) · [Español](docs/USER_MANUAL_ES.md)

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

## Pour les contributeurs

Voir [docs/DEV_SETUP.md](docs/DEV_SETUP.md) (setup en 5 min) et [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

MintGuard est distribué sous licence [GNU General Public License v3.0 ou ultérieure](LICENSE) (GPL-3.0-or-later). Voir [docs/LICENSE_COMPLIANCE.md](docs/LICENSE_COMPLIANCE.md) pour la compatibilité des dépendances et [AUTHORS.md](AUTHORS.md) pour les contributeurs.
