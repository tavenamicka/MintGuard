# Installation — MintGuard

## Installation pour les parents (sans connaissances techniques)

**Ce qu'il vous faut** : un ordinateur sous Linux Mint (ou Ubuntu), connecté à Internet, et le mot de passe de votre session. Chaque enfant doit avoir son propre compte sur l'ordinateur.

### Étape 1 — Télécharger

Rendez-vous sur la [page des versions](https://github.com/tavenamicka/MintGuard/releases/latest) et téléchargez le fichier se terminant par `.deb` (par exemple `mintguard_0.1.0-1_all.deb`). Il se retrouve dans le dossier **Téléchargements**.

### Étape 2 — Installer

Double-cliquez sur le fichier. Le gestionnaire de logiciels s'ouvre : cliquez sur **Installer**, saisissez votre mot de passe, puis patientez jusqu'à la fin (environ une minute, une connexion Internet est nécessaire).

Si le double-clic n'ouvre pas le gestionnaire, faites un clic droit sur le fichier, puis **Ouvrir avec → Installer des paquets (GDebi)** ou, à défaut, utilisez le terminal : ouvrez-le avec `Ctrl + Alt + T` et tapez (en adaptant le nom du fichier) :

```bash
cd ~/Téléchargements
sudo apt install ./mintguard_0.1.0-1_all.deb
```

### Étape 3 — Première utilisation

1. Ouvrez **MintGuard** depuis le menu des applications.
2. Suivez l'assistant : prénom de l'enfant, nom de son compte, profil par âge, code PIN (notez-le !).
3. Si le Tableau de bord affiche **« La protection n'est pas encore activée »**, cliquez sur **« Activer la protection maintenant »** et confirmez avec votre mot de passe. La protection se relance ensuite seule à chaque démarrage de l'ordinateur.

La suite est expliquée dans le guide utilisateur : [Français](USER_MANUAL_FR.md) · [English](USER_MANUAL_EN.md) · [Deutsch](USER_MANUAL_DE.md) · [Español](USER_MANUAL_ES.md).

### Si ça ne marche pas

| Problème | Que faire |
|---|---|
| MintGuard n'apparaît pas dans le menu | Fermez puis rouvrez votre session, ou redémarrez l'ordinateur. |
| Une erreur de dépendances s'affiche à l'installation | Vérifiez la connexion Internet, puis relancez l'installation avec la commande `sudo apt install ./mintguard_0.1.0-1_all.deb` (cf. étape 2). |
| Le bandeau « protection pas activée » revient | Cliquez à nouveau sur « Activer la protection maintenant ». Si cela échoue : `sudo systemctl start mintguard-daemon` dans un terminal. |
| Le code PIN est oublié | Utilisez « Code PIN oublié ? » dans la fenêtre de saisie (voir le guide utilisateur). |
| Vous voulez désinstaller | `sudo apt remove mintguard` (garde vos réglages) ou `sudo apt purge mintguard` (supprime tout). |

---

# Installation technique (développeurs et administrateurs)

## Environnement de développement (toute plateforme)

```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e .
pip install -r requirements.txt
pytest tests/ -v
```

Les contrôleurs backend qui dépendent d'outils Linux (`iptables`, `loginctl`, `apparmor_parser`) échouent proprement hors Linux — c'est attendu en dev (voir `mintguard/backend/*.py`, méthode `test()`).

## Construire le paquet .deb soi-même

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

Pour un parent utilisateur final, cette commande n'est plus nécessaire : au premier lancement, le Tableau de bord affiche un bouton **« Activer la protection maintenant »** tant que le daemon ne répond pas, qui déclenche ce même démarrage via une fenêtre de confirmation système (polkit). La commande ci-dessus reste utile pour un usage scripté/technique.

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
