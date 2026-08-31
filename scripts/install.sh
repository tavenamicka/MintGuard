#!/usr/bin/env bash
# Installation systeme MintGuard (Linux Mint, root requis).
#
# Perimetre volontairement limite au "sur" pour cette passe (Phase 3) :
#   - venv dedie + paquet installe (editable, pointe vers ce checkout)
#   - service systemd installe et ACTIVE au demarrage, mais PAS demarre
#     (le daemon n'est lance qu'a la demande explicite de l'utilisateur,
#     voir le message final)
#   - dnsmasq.conf installe en l'etat (port 5353, PAS le resolveur
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

echo "== Repertoires de donnees =="
install -d -m 755 /etc/mintguard
install -d -m 700 -o root -g root /var/lib/mintguard
install -d -m 700 -o root -g root /var/log/mintguard

echo "== Configuration =="
if [ ! -f /etc/mintguard/config.json ]; then
  install -m 644 "$REPO_ROOT/etc/config.json.example" /etc/mintguard/config.json
  echo "config.json cree depuis config.json.example"
else
  echo "config.json existant conserve (non ecrase)"
fi

echo "== Environnement Python dedie ($VENV_DIR) =="
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -e "$REPO_ROOT" -q
"$VENV_DIR/bin/pip" install -r "$REPO_ROOT/requirements.txt" -q
echo "Paquet installe (editable -> $REPO_ROOT)"

echo "== dnsmasq =="
if ! command -v dnsmasq >/dev/null 2>&1; then
  echo "dnsmasq absent, installation..."
  apt-get update -qq && apt-get install -y -qq dnsmasq
fi
install -m 644 "$REPO_ROOT/etc/dnsmasq.d/mintguard.conf" /etc/dnsmasq.d/mintguard.conf
echo "mintguard.conf installe (port 5353 - resolveur systeme non touche, voir SUIVI.md)"

echo "== Service systemd =="
install -m 644 "$REPO_ROOT/etc/systemd/mintguard-daemon.service" /etc/systemd/system/mintguard-daemon.service
systemctl daemon-reload
systemctl enable mintguard-daemon.service
echo "Service installe et active au demarrage (PAS lance maintenant)"

cat <<'EOF'

== Installation terminee ==

Le daemon n'est PAS encore lance. Pour le demarrer explicitement :
    sudo systemctl start mintguard-daemon
    sudo systemctl status mintguard-daemon
    sudo journalctl -u mintguard-daemon -f

Pour l'interface graphique parent (compte utilisateur normal, pas root) :
    /opt/mintguard/venv/bin/mintguard
EOF
