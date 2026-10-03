# Installation — MintGuard

Français · [English](INSTALLATION.en.md) · [Deutsch](INSTALLATION.de.md) · [Español](INSTALLATION.es.md)

## Installation pour les parents (sans connaissances techniques)

Ce guide vous accompagne pas à pas. Si une étape ne se passe pas comme prévu, allez directement à « Si quelque chose ne marche pas » plus bas : aucune de ces situations n'est grave, et rien ne risque d'être abîmé.

**Avant de commencer**, vérifiez que :
- votre ordinateur fonctionne sous **Linux Mint** (ou Ubuntu) et est connecté à Internet ;
- vous connaissez le **mot de passe** que vous tapez pour ouvrir votre session ;
- chaque enfant a **son propre compte** sur l'ordinateur.

### Étape 1 — Télécharger le fichier d'installation

1. Ouvrez la [page des versions de MintGuard](https://github.com/tavenamicka/MintGuard/releases/latest).
2. Descendez jusqu'à la zone **« Assets »**.
3. Cliquez sur `mintguard_0.1.0-1_all.deb`. Ce fichier est le « programme d'installation » : l'extension `.deb` est celle des installateurs sous Linux Mint.

Le fichier est enregistré dans le dossier **Téléchargements**.

### Étape 2 — Installer

1. Ouvrez le dossier **Téléchargements** et double-cliquez sur le fichier `mintguard…deb`.
2. Une fenêtre du gestionnaire de logiciels s'ouvre. Cliquez sur **Installer**.
3. Tapez votre mot de passe, puis validez. Attendez la fin, environ une minute.

*Le double-clic n'ouvre rien ?* Faites un clic droit sur le fichier, puis **Ouvrir avec** et **Installer des paquets (GDebi)**. Si cela ne marche toujours pas, utilisez l'**autre méthode** décrite plus bas.

### Étape 3 — Ouvrir MintGuard

Cliquez sur le menu de l'ordinateur (en bas à gauche), tapez « MintGuard » puis cliquez sur l'icône.

### Étape 4 — Répondre aux questions de l'assistant

Au premier lancement, MintGuard vous guide. Il vous demande :
- le **prénom** de votre enfant et le **nom de son compte** sur l'ordinateur ;
- un **profil** selon son âge (6-12 ans ou 13-18 ans) : vous pourrez tout modifier ensuite ;
- un **code PIN** (4 chiffres ou plus). Notez-le sur papier et rangez-le : il protège vos réglages, et vos enfants ne doivent pas le connaître.

### Étape 5 — Activer la protection

Si le message **« La protection n'est pas encore activée »** s'affiche, cliquez sur **« Activer la protection maintenant »**, puis tapez votre mot de passe. La protection est alors en marche et redémarre toute seule avec l'ordinateur.

Pour la suite (régler les horaires, bloquer des sites ou des applications), lisez le guide : [Français](USER_MANUAL_FR.md) · [English](USER_MANUAL_EN.md) · [Deutsch](USER_MANUAL_DE.md) · [Español](USER_MANUAL_ES.md).

### Autre méthode : installer avec le terminal

À n'utiliser que si le double-clic ne fonctionne pas. Le **terminal** est une fenêtre où l'on donne des instructions à l'ordinateur en les tapant.

1. Appuyez en même temps sur les touches `Ctrl`, `Alt` et `T` : le terminal s'ouvre.
2. Copiez-collez cette ligne, puis appuyez sur `Entrée` :

```bash
cd ~/Téléchargements
```

3. Copiez-collez celle-ci, puis `Entrée` :

```bash
sudo apt install ./mintguard_0.1.0-1_all.deb
```

4. Le terminal demande votre mot de passe. **Rien ne s'affiche pendant que vous le tapez, pas même des points : c'est normal.** Tapez-le quand même, puis appuyez sur `Entrée`.
5. Si on vous demande de confirmer, tapez `O` (ou `Y`) puis `Entrée`. Attendez le retour du message de saisie (la ligne se termine par `$`) : l'installation est terminée.

(`sudo` signifie « exécuter en tant qu'administrateur », et `apt` est l'outil qui installe les programmes sous Linux Mint.)

### Si quelque chose ne marche pas

| Ce que vous voyez | Ce qui se passe | Quoi faire |
|---|---|---|
| MintGuard n'apparaît pas dans le menu | Le menu n'est pas encore mis à jour. | Fermez votre session puis rouvrez-la, ou redémarrez l'ordinateur. |
| Un message parle de « dépendances » ou d'un paquet introuvable | L'ordinateur n'a pas pu télécharger un élément dont MintGuard a besoin. | Vérifiez que vous êtes connecté à Internet, puis recommencez l'installation. |
| Le message « La protection n'est pas encore activée » revient | La protection ne s'est pas lancée. | Cliquez à nouveau sur « Activer la protection maintenant ». Si cela échoue, ouvrez le terminal et tapez `sudo systemctl start mintguard-daemon`. |
| Vous avez oublié le code PIN | Cela arrive souvent, et il existe une solution. | Dans la fenêtre du code PIN, cliquez sur « Code oublié ? » (voir le guide utilisateur). |
| Vous voulez désinstaller | — | Dans le terminal, tapez `sudo apt remove mintguard` (vos réglages sont gardés) ou `sudo apt purge mintguard` (tout est supprimé). |

Si rien de cela ne règle votre problème, demandez de l'aide à la personne qui vous a conseillé MintGuard, ou ouvrez une demande sur la [page des problèmes](https://github.com/tavenamicka/MintGuard/issues).

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
