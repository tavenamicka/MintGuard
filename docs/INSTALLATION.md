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

## Paquet .deb (release)

Pour installer MintGuard "comme une appli normale" (icône dans le menu, dépendances système gérées par apt, code figé — pas de checkout git à conserver) :

```bash
bash scripts/build-deb.sh
sudo apt install ./dist/mintguard_0.1.0-1_all.deb
```

`apt install` (plutôt que `dpkg -i`) résout automatiquement les dépendances système (`libxcb-cursor0`, `dnsmasq`, `python3-venv`). Le `.deb` généré peut être copié tel quel sur un autre poste Linux Mint/Ubuntu et installé de la même façon, sans avoir besoin de cloner le dépôt dessus.

Comme pour `install.sh`, le service n'est **pas démarré automatiquement** (démarrage volontairement laissé à une action explicite : il change la résolution DNS de toute la machine) :

```bash
sudo systemctl start mintguard-daemon
```

Pour un parent utilisateur final, cette commande n'est plus nécessaire : au premier lancement, le Tableau de bord affiche un bouton **« Activer la protection maintenant »** tant que le daemon ne répond pas, qui déclenche ce même démarrage via une fenêtre de confirmation système (polkit) — voir `mintguard/gui/daemon_control.py`. La commande ci-dessus reste utile pour un usage scripté/technique.

Désinstallation : `sudo apt remove mintguard` (garde BD/logs/config) ou `sudo apt purge mintguard` (supprime tout — équivalent de `uninstall.sh --purge`).

## Installation cible pour le développement (Linux Mint)

Pour tester en conditions réelles sur cette même machine, en éditant le code et en relançant le daemon sans réinstaller (checkout git conservé, install éditable) :

```bash
sudo bash scripts/install.sh
```

Installe : venv dédié (`/opt/mintguard/venv`), config (`/etc/mintguard/config.json`), BD/logs (`/var/lib/mintguard`, `/var/log/mintguard`, permissions restrictives), service systemd (`/etc/systemd/system/mintguard-daemon.service`, activé au démarrage), config dnsmasq (`/etc/dnsmasq.d/mintguard.conf`), et `libxcb-cursor0` (dépendance système de la GUI PyQt6 — sans elle, `mintguard` échoue au démarrage avec `Could not load the Qt platform plugin "xcb"`).

Le service n'est **pas démarré automatiquement** — le script affiche la commande à lancer explicitement (`sudo systemctl start mintguard-daemon`).

**Pas de profil AppArmor ni de règles sudoers** : le confinement par utilisateur via AppArmor est écarté du MVP (risque disproportionné vs. bénéfice, `ProcessMonitor` couvre déjà le blocage d'applications), et le daemon tournant déjà en root via systemd, aucune délégation sudo n'est nécessaire pour la GUI (elle n'écrit qu'en SQLite).

Désinstallation : `sudo bash scripts/uninstall.sh` (ajouter `--purge` pour aussi supprimer BD/logs/config).

## Variables d'environnement utiles (dev)

| Variable | Effet |
|---|---|
| `MINTGUARD_CONFIG_PATH` | Chemin alternatif vers `config.json` (par défaut `/etc/mintguard/config.json`) |
| `LANG` | Langue auto-détectée si `app.language` = `"auto"` dans la config |
