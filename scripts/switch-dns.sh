#!/usr/bin/env bash
# Bascule dnsmasq (MintGuard) en resolveur DNS systeme reel (port 53).
#
# ATTENTION : ce script coupe le DNS pendant quelques secondes et modifie
# la configuration reseau du systeme (systemd-resolved + /etc/resolv.conf).
# Une erreur laisse la machine sans resolution DNS jusqu'a rollback.
# A lancer uniquement depuis un acces local (clavier/ecran ou console),
# pas via une session SSH qui dependrait elle-meme du DNS en cours de
# bascule (une session SSH deja ouverte par IP n'est pas affectee, mais
# soyez prudent).
#
# Avant cette bascule : dnsmasq (MintGuard) tourne sur 127.0.0.1:5354,
# aucun impact reseau (voir SUIVI.md, install.sh). Ce script :
#   1. Recupere les serveurs DNS amont actuels (ceux fournis par le
#      resolveur systeme, typiquement via DHCP) pour que dnsmasq puisse
#      continuer a relayer les domaines non bloques.
#   2. Reecrit /etc/dnsmasq.d/mintguard.conf en port 53 avec ces serveurs
#      amont explicites (necessaire : on ne pourra plus compter sur le
#      relais ambiant via systemd-resolved une fois celui-ci desactive).
#   3. Desactive le stub listener de systemd-resolved (127.0.0.53:53) -
#      sinon conflit de port avec dnsmasq.
#   4. Fait pointer /etc/resolv.conf vers 127.0.0.1 (dnsmasq).
#   5. (Re)demarre dnsmasq sur le port 53.
#
# Rollback : sudo bash scripts/switch-dns-rollback.sh
#
# Usage : sudo bash scripts/switch-dns.sh
set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "Ce script doit etre lance avec sudo." >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR=/var/lib/mintguard/dns-switch-backup
INSTALLED_CONF=/etc/dnsmasq.d/mintguard.conf

if [ ! -f "$INSTALLED_CONF" ]; then
  echo "Erreur : $INSTALLED_CONF absent. Lancez d'abord 'sudo bash scripts/install.sh'." >&2
  exit 1
fi

echo "== Sauvegarde de l'etat actuel (pour rollback) =="
mkdir -p "$BACKUP_DIR"
if [ ! -f "$BACKUP_DIR/resolved.conf.orig" ]; then
  cp /etc/systemd/resolved.conf "$BACKUP_DIR/resolved.conf.orig"
fi
if [ ! -f "$BACKUP_DIR/mintguard.conf.orig" ]; then
  cp "$INSTALLED_CONF" "$BACKUP_DIR/mintguard.conf.orig"
fi
if [ ! -e "$BACKUP_DIR/resolv.conf.orig.symlink" ] && [ -L /etc/resolv.conf ]; then
  readlink /etc/resolv.conf > "$BACKUP_DIR/resolv.conf.orig.symlink"
fi
echo "Sauvegarde dans $BACKUP_DIR"

echo "== Detection des serveurs DNS amont actuels =="
UPSTREAM_SERVERS="$(resolvectl status 2>/dev/null | grep -A2 'Current DNS Server\|DNS Servers' | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | sort -u || true)"
if [ -z "$UPSTREAM_SERVERS" ]; then
  echo "Impossible de detecter les serveurs DNS amont automatiquement." >&2
  echo "Verifiez avec 'resolvectl status' et relancez, ou passez-les en argument :" >&2
  echo "  sudo bash scripts/switch-dns.sh 1.1.1.1 8.8.8.8" >&2
  if [ "$#" -eq 0 ]; then
    exit 1
  fi
  UPSTREAM_SERVERS="$*"
fi
echo "Serveurs amont retenus :"
echo "$UPSTREAM_SERVERS"

echo "== Reecriture de $INSTALLED_CONF (port 53 + amont explicite) =="
{
  echo "# Genere par switch-dns.sh - resolveur systeme reel (port 53)"
  echo "# Sauvegarde de la version precedente : $BACKUP_DIR/mintguard.conf.orig"
  echo "listen-address=127.0.0.1"
  echo "port=53"
  echo
  for ip in $UPSTREAM_SERVERS; do
    echo "server=$ip"
  done
  echo
  echo "addn-hosts=/var/lib/mintguard-dns/blocklist.hosts"
  echo
  echo "log-queries"
  echo "log-facility=/var/log/mintguard/dns.log"
} > "$INSTALLED_CONF"

echo "== Desactivation du stub listener systemd-resolved =="
if grep -q '^DNSStubListener=' /etc/systemd/resolved.conf; then
  sed -i 's/^DNSStubListener=.*/DNSStubListener=no/' /etc/systemd/resolved.conf
else
  sed -i '/^\[Resolve\]/a DNSStubListener=no' /etc/systemd/resolved.conf
fi
systemctl restart systemd-resolved

echo "== Redirection de /etc/resolv.conf vers 127.0.0.1 =="
rm -f /etc/resolv.conf
echo "nameserver 127.0.0.1" > /etc/resolv.conf

echo "== Demarrage de dnsmasq (port 53) =="
systemctl restart dnsmasq
systemctl enable dnsmasq

echo
echo "== Bascule terminee =="
echo "Verification recommandee :"
echo "  resolvectl query example.com    # doit resoudre normalement"
echo "  resolvectl query tiktok.com     # doit renvoyer 0.0.0.0 si dans la blocklist"
echo
echo "En cas de probleme reseau : sudo bash $REPO_ROOT/scripts/switch-dns-rollback.sh"
