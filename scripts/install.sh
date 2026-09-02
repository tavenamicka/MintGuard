#!/usr/bin/env bash
# Installation systeme MintGuard (Linux Mint, root requis).
#
# Perimetre volontairement limite au "sur" pour cette passe (Phase 3) :
#   - venv dedie + paquet installe (editable, pointe vers ce checkout)
#   - service systemd installe et ACTIVE au demarrage, mais PAS demarre
#     (le daemon n'est lance qu'a la demande explicite de l'utilisateur,
#     voir le message final)
#   - dnsmasq.conf installe en l'etat (port 5354, PAS le resolveur
#     systeme - aucun impact reseau tant que la bascule n'est pas faite
#     separement, voir SUIVI.md)
#   - repertoires de donnees/logs/config avec permissions restrictives
#
# PAS dans ce script (voir SUIVI.md pour la justification) :
#   - profil AppArmor (confinement par utilisateur ecarte du MVP)
#   - regles iptables (n'ont de sens qu'apres la bascule du resolveur
#     DNS systeme, decision separee et explicite de l'utilisateur)
#
# Usage : sudo bash scripts/install.sh
set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "Ce script doit etre lance avec sudo." >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR=/opt/mintguard/venv
ADMIN_GROUP=mintguard-admin

echo "== Groupe parent =="
# La GUI tourne en utilisateur normal (pas root), mais doit pouvoir lire/
# ecrire la meme BD SQLite que le daemon (root). 700 root:root bloquerait
# aussi le parent, pas seulement l'enfant. Un groupe dedie limite l'acces
# au(x) compte(s) parent explicitement ajoute(s), l'enfant (pas dans ce
# groupe) reste sans acces.
groupadd -f "$ADMIN_GROUP"
if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ]; then
  usermod -aG "$ADMIN_GROUP" "$SUDO_USER"
  echo "Utilisateur '$SUDO_USER' ajoute au groupe $ADMIN_GROUP (deconnexion/reconnexion necessaire pour que ca prenne effet)"
else
  echo "Aucun utilisateur parent detecte (lance en root direct ?) - ajoutez-le manuellement :"
  echo "  sudo usermod -aG $ADMIN_GROUP <votre_compte>"
fi

echo "== Repertoires de donnees =="
install -d -m 755 /etc/mintguard
install -d -o root -g "$ADMIN_GROUP" /var/lib/mintguard
chmod 2770 /var/lib/mintguard   # setgid : les nouveaux fichiers heritent du groupe mintguard-admin
install -d -m 700 -o root -g root /var/log/mintguard
# Repertoire separe pour la blocklist DNS (pas de donnees sensibles) :
# dnsmasq tourne en utilisateur non-privilegie et ne peut pas traverser
# /var/lib/mintguard (2770, reserve BD/PIN) meme si le fichier lui-meme
# etait lisible - voir SUIVI.md Phase 3 (5e defaut de conception).
install -d -m 755 -o root -g root /var/lib/mintguard-dns
# dnsmasq REFUSE de demarrer si un `conf-file=` pointe sur un fichier absent.
# Le daemon regenere ce fichier a son premier cycle, mais dnsmasq peut demarrer
# avant lui (Requires= dans l'unite systemd) : on cree donc une blocklist vide
# des l'installation. Les .hosts d'anciennes installations (format hosts, qui
# ne bloquait pas les sous-domaines) sont retires.
if [ ! -f /var/lib/mintguard-dns/blocklist.conf ]; then
  echo "# Blocklist MintGuard (vide - regeneree par le daemon)" > /var/lib/mintguard-dns/blocklist.conf
  chmod 644 /var/lib/mintguard-dns/blocklist.conf
fi
rm -f /var/lib/mintguard-dns/blocklist.hosts /var/lib/mintguard/blocklist.hosts

echo "== Configuration =="
if [ ! -f /etc/mintguard/config.json ]; then
  install -m 644 "$REPO_ROOT/etc/config.json.example" /etc/mintguard/config.json
  echo "config.json cree depuis config.json.example"
else
  echo "config.json existant conserve (non ecrase)"
fi

echo "== Dependance systeme GUI (Qt/xcb) =="
# Sans libxcb-cursor0, la GUI (PyQt6) echoue au demarrage avec "Could not load the Qt
# platform plugin xcb" - le daemon (teste en continu en Phase 3) n'en a pas besoin, seule
# la GUI parent, d'ou une decouverte tardive au premier vrai lancement graphique (Phase 4).
if ! dpkg -s libxcb-cursor0 >/dev/null 2>&1; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq libxcb-cursor0
fi

echo "== Environnement Python dedie ($VENV_DIR) =="
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/pip" install --upgrade pip -q
# ATTENTION (constat d'audit de securite Phase 3, voir SUIVI.md) : install editable = le
# daemon root execute du code Python directement depuis $REPO_ROOT, qui appartient a un
# compte utilisateur normal (pas root). Volontairement conserve ainsi pour l'instant : ce
# script sert au developpement/test actif sur cible reelle (modifier le code, relancer le
# daemon, sans reinstallation), pas encore a une vraie installation chez une famille. Avant
# une release Phase 4, remplacer par une copie figee du code dans un emplacement root-only
# (ex: paquet/wheel installe normalement, ou `cp -r` vers /opt/mintguard/src) pour que le
# daemon ne depende plus d'un repertoire modifiable par un compte non-root.
"$VENV_DIR/bin/pip" install -e "$REPO_ROOT" -q
"$VENV_DIR/bin/pip" install -r "$REPO_ROOT/requirements.txt" -q
echo "Paquet installe (editable -> $REPO_ROOT)"

echo "== dnsmasq =="
if [ ! -d /etc/dnsmasq.d ]; then
  # dnsmasq-base (le binaire seul) peut deja etre present sans le paquet
  # complet -> /etc/dnsmasq.d absent tant que "dnsmasq" (pas juste
  # "dnsmasq-base") n'est pas installe.
  echo "Paquet dnsmasq (config complete) absent, installation..."
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq dnsmasq
fi
if [ -d /var/lib/mintguard/dns-switch-backup ]; then
  # scripts/switch-dns.sh a deja bascule ce dnsmasq en resolveur systeme reel
  # (port 53, /etc/resolv.conf -> 127.0.0.1) : c'est le service qui fait
  # fonctionner tout le reseau de la machine, pas juste une conf par defaut
  # inutilisee. L'arreter, ou ecraser sa conf (port 53 + serveurs amont
  # detectes a la bascule) par le gabarit de test (port 5354), casserait la
  # resolution DNS de la machine entiere (constat direct lors du packaging
  # .deb, voir SUIVI.md, entree "Paquet .deb" -- ce script partage le meme
  # defaut, corrige ici a la meme occasion).
  echo "Bascule DNS deja active (dns-switch-backup present) - dnsmasq et mintguard.conf non touches."
else
  # Le paquet dnsmasq demarre parfois son service avec la conf par defaut
  # (port 53) au moment de l'installation -> conflit possible avec
  # systemd-resolved. On l'arrete/desactive avant d'installer notre conf
  # (port 5354) ; il sera (re)demarre par la dependance Requires= du
  # service mintguard-daemon quand l'utilisateur le lancera explicitement.
  systemctl stop dnsmasq 2>/dev/null || true
  systemctl disable dnsmasq 2>/dev/null || true
  systemctl reset-failed dnsmasq 2>/dev/null || true
  install -m 644 "$REPO_ROOT/etc/dnsmasq.d/mintguard.conf" /etc/dnsmasq.d/mintguard.conf
  echo "mintguard.conf installe (port 5354 - resolveur systeme non touche, voir SUIVI.md)"
fi

# Mise a niveau d'une installation existante : l'ancien chemin de blocklist
# (format hosts) reste dans /etc/mintguard/config.json et ferait ecrire le
# daemon a cote de ce que lit dnsmasq.
if [ -f /etc/mintguard/config.json ]; then
  python3 - /etc/mintguard/config.json <<'PYEOF'
import json
import sys

path = sys.argv[1]
with open(path) as f:
    config = json.load(f)
dns = config.setdefault("dns", {})
if dns.get("blocklist_path", "").endswith(".hosts"):
    dns["blocklist_path"] = "/var/lib/mintguard-dns/blocklist.conf"
    with open(path, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")
    print("blocklist_path migre vers blocklist.conf dans", path)
PYEOF
fi

echo "== Icone et entrees de menu =="
# Gabarits partages avec le paquet .deb (packaging/deb/), pas dupliques - voir build-deb.sh.
install -D -m 644 "$REPO_ROOT/packaging/deb/mintguard.desktop" /usr/share/applications/mintguard.desktop
install -D -m 644 "$REPO_ROOT/packaging/deb/mintguard.svg" /usr/share/icons/hicolor/scalable/apps/mintguard.svg
install -D -m 644 "$REPO_ROOT/packaging/deb/mintguard-child-tray.desktop" /etc/xdg/autostart/mintguard-child-tray.desktop
install -D -m 644 "$REPO_ROOT/packaging/deb/mintguard-parent-tray.desktop" /etc/xdg/autostart/mintguard-parent-tray.desktop

echo "== Service systemd =="
install -m 644 "$REPO_ROOT/etc/systemd/mintguard-daemon.service" /etc/systemd/system/mintguard-daemon.service
systemctl daemon-reload
systemctl enable mintguard-daemon.service
echo "Service installe et active au demarrage (PAS lance maintenant)"

cat <<EOF

== Installation terminee ==

Le daemon n'est PAS encore lance. Pour le demarrer explicitement :
    sudo systemctl start mintguard-daemon
    sudo systemctl status mintguard-daemon
    sudo journalctl -u mintguard-daemon -f

Pour l'interface graphique parent (compte utilisateur normal, pas root) :
    /opt/mintguard/venv/bin/mintguard

IMPORTANT si vous venez d'etre ajoute au groupe $ADMIN_GROUP a l'instant :
deconnexion/reconnexion necessaire (ou 'newgrp $ADMIN_GROUP' dans le shell
courant) pour que la GUI ait acces en lecture/ecriture a la BD partagee.
EOF
