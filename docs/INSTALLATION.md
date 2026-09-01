# Installation — MintGuard

## Environnement de développement (toute plateforme)

```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e .
pip install -r requirements.txt
pytest tests/ -v
```

Les contrôleurs backend qui dépendent d'outils Linux (`iptables`, `loginctl`, `apparmor_parser`) échouent proprement hors Linux — c'est attendu en dev (voir `mintguard/backend/*.py`, méthode `test()`).

## Installation cible (Linux Mint)

```bash
sudo bash scripts/install.sh
```

Installe : venv dédié (`/opt/mintguard/venv`), config (`/etc/mintguard/config.json`), BD/logs (`/var/lib/mintguard`, `/var/log/mintguard`, permissions restrictives), service systemd (`/etc/systemd/system/mintguard-daemon.service`, activé au démarrage), config dnsmasq (`/etc/dnsmasq.d/mintguard.conf`), et `libxcb-cursor0` (dépendance système de la GUI PyQt6 — sans elle, `mintguard` échoue au démarrage avec `Could not load the Qt platform plugin "xcb"`, voir `SUIVI.md`).

Le service n'est **pas démarré automatiquement** — le script affiche la commande à lancer explicitement (`sudo systemctl start mintguard-daemon`).

**Pas de profil AppArmor ni de règles sudoers** : voir `SUIVI.md` (entrée Phase 3) pour la justification — le confinement par utilisateur via AppArmor est écarté du MVP (risque disproportionné vs. bénéfice, `ProcessMonitor` couvre déjà le blocage d'applications), et le daemon tournant déjà en root via systemd, aucune délégation sudo n'est nécessaire pour la GUI (elle n'écrit qu'en SQLite).

Désinstallation : `sudo bash scripts/uninstall.sh` (ajouter `--purge` pour aussi supprimer BD/logs/config).

## Variables d'environnement utiles (dev)

| Variable | Effet |
|---|---|
| `MINTGUARD_CONFIG_PATH` | Chemin alternatif vers `config.json` (par défaut `/etc/mintguard/config.json`) |
| `LANG` | Langue auto-détectée si `app.language` = `"auto"` dans la config |
