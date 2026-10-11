#!/usr/bin/env bash
# Bascule dnsmasq (MintGuard) en resolveur DNS systeme reel (port 53).
#
# Sans cette bascule, le blocage des sites ne fonctionne pas : dnsmasq tourne
# sur un port de test (5354) que personne n'interroge. Lance par le bouton
# "Reparer le blocage des sites" du Tableau de bord (via pkexec, installe en
# /usr/lib/mintguard/switch-dns.sh), ou a la main.
#
# Idempotent : peut etre relance sans risque, y compris pour reparer une
# bascule defaite (ex: /etc/resolv.conf reecrit a la main ou par
# NetworkManager - constate en usage reel).
#
# Ce script :
#   1. Sauvegarde l'etat d'origine (une seule fois, pour le rollback).
#   2. Ecrit /etc/dnsmasq.d/mintguard.conf en port 53. Les serveurs amont sont
#      lus dans /run/NetworkManager/no-stub-resolv.conf, que NetworkManager tient
#      a jour a chaque changement de reseau (portable qui passe d'un Wi-Fi a
#      l'autre) - auparavant les serveurs du moment etaient figes dans la conf,
#      et le DNS cessait de fonctionner sur tout autre reseau. Repli sur des
#      serveurs detectes (ou passes en argument) si NetworkManager est absent.
#   3. Desactive le stub listener de systemd-resolved (127.0.0.53:53).
#   4. Interdit a NetworkManager de reecrire /etc/resolv.conf (rc-manager=unmanaged).
#   5. Fait pointer /etc/resolv.conf vers 127.0.0.1 (dnsmasq) et redemarre dnsmasq.
#   6. Verifie qu'un nom se resout ; sinon remet /etc/resolv.conf tel qu'il etait
#      (la machine ne doit jamais rester sans DNS a cause de ce script).
#
# Rollback complet : sudo bash scripts/switch-dns-rollback.sh
#
# Usage : sudo bash scripts/switch-dns.sh [serveur_amont ...]
set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "Ce script doit etre lance avec sudo." >&2
  exit 1
fi

BACKUP_DIR=/var/lib/mintguard/dns-switch-backup
INSTALLED_CONF=/etc/dnsmasq.d/mintguard.conf
NM_RESOLV_FILE=/run/NetworkManager/no-stub-resolv.conf
NM_CONF=/etc/NetworkManager/conf.d/90-mintguard-dns.conf

if [ ! -f "$INSTALLED_CONF" ]; then
  echo "Erreur : $INSTALLED_CONF absent. MintGuard n'est pas installe correctement." >&2
  exit 1
fi

echo "== Sauvegarde de l'etat actuel (pour rollback) =="
mkdir -p "$BACKUP_DIR"
if [ ! -f "$BACKUP_DIR/resolved.conf.orig" ] && [ -f /etc/systemd/resolved.conf ]; then
  cp /etc/systemd/resolved.conf "$BACKUP_DIR/resolved.conf.orig"
fi
if [ ! -f "$BACKUP_DIR/mintguard.conf.orig" ]; then
  cp "$INSTALLED_CONF" "$BACKUP_DIR/mintguard.conf.orig"
fi
if [ ! -e "$BACKUP_DIR/resolv.conf.orig.symlink" ] && [ -L /etc/resolv.conf ]; then
  readlink /etc/resolv.conf > "$BACKUP_DIR/resolv.conf.orig.symlink"
fi
echo "Sauvegarde dans $BACKUP_DIR"

echo "== Serveurs DNS amont =="
# Chaque detection se termine par `|| true` : avec pipefail, un maillon en echec
# (resolvectl inactif, grep sans resultat) arreterait sinon tout le script (set -e).
# Adresses IPv4 non-locales uniquement : 127.x (stub systemd-resolved, dnsmasq
# lui-meme) ne sont jamais un amont valable.
extract_ips() { grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}' | grep -v '^127\.' | sort -u || true; }

FALLBACK_SERVERS="$*"
if [ -z "$FALLBACK_SERVERS" ]; then
  FALLBACK_SERVERS="$(resolvectl status 2>/dev/null | grep -A2 'Current DNS Server\|DNS Servers' | extract_ips || true)"
fi
if [ -z "$FALLBACK_SERVERS" ]; then
  FALLBACK_SERVERS="$(nmcli -t -f IP4.DNS dev show 2>/dev/null | extract_ips || true)"
fi
if [ -z "$FALLBACK_SERVERS" ]; then
  # Relance apres une premiere bascule : resolved est desactive, mais la conf
  # precedente contient deja les bons serveurs.
  FALLBACK_SERVERS="$(grep -E '^server=[0-9]' "$INSTALLED_CONF" 2>/dev/null | extract_ips || true)"
fi

USE_NM_RESOLV_FILE=0
if [ -d /run/NetworkManager ] && command -v nmcli >/dev/null 2>&1; then
  USE_NM_RESOLV_FILE=1
  echo "Serveurs amont suivis dynamiquement : $NM_RESOLV_FILE (NetworkManager)"
fi
if [ "$USE_NM_RESOLV_FILE" -eq 0 ] && [ -z "$FALLBACK_SERVERS" ]; then
  echo "Impossible de detecter les serveurs DNS amont." >&2
  echo "Relancez en les passant en argument : sudo bash switch-dns.sh 1.1.1.1 9.9.9.9" >&2
  exit 1
fi

echo "== Ecriture de $INSTALLED_CONF (port 53) =="
{
  echo "# Genere par switch-dns.sh - resolveur systeme reel (port 53)"
  echo "# Sauvegarde de la version precedente : $BACKUP_DIR/mintguard.conf.orig"
  echo "listen-address=127.0.0.1"
  echo "port=53"
  echo
  if [ "$USE_NM_RESOLV_FILE" -eq 1 ]; then
    # dnsmasq relit ce fichier automatiquement des qu'il change.
    echo "resolv-file=$NM_RESOLV_FILE"
  else
    echo "no-resolv"
    for ip in $FALLBACK_SERVERS; do
      echo "server=$ip"
    done
  fi
  echo
  echo "conf-file=/var/lib/mintguard-dns/blocklist.conf"
  echo
  # Canari DoH de Firefox : NXDOMAIN ici desactive son DNS-over-HTTPS
  # automatique, qui contournerait sinon tout le blocage (voir
  # etc/dnsmasq.d/mintguard.conf).
  echo "server=/use-application-dns.net/"
  echo
  # log-queries + troncature par cycle (voir etc/dnsmasq.d/mintguard.conf).
  echo "log-queries"
  echo "log-facility=/var/log/mintguard/dns.log"
} > "$INSTALLED_CONF"

echo "== Desactivation du stub listener systemd-resolved =="
if [ -f /etc/systemd/resolved.conf ]; then
  if grep -q '^DNSStubListener=' /etc/systemd/resolved.conf; then
    sed -i 's/^DNSStubListener=.*/DNSStubListener=no/' /etc/systemd/resolved.conf
  else
    sed -i '/^\[Resolve\]/a DNSStubListener=no' /etc/systemd/resolved.conf
  fi
  if systemctl is-active --quiet systemd-resolved; then
    systemctl restart systemd-resolved
  fi
fi

if [ -d /etc/NetworkManager/conf.d ]; then
  echo "== NetworkManager : ne plus reecrire /etc/resolv.conf =="
  printf '# Pose par MintGuard (switch-dns.sh) - retire par switch-dns-rollback.sh\n[main]\nrc-manager=unmanaged\n' > "$NM_CONF"
  nmcli general reload conf 2>/dev/null || systemctl reload NetworkManager 2>/dev/null || true
fi

echo "== Redirection de /etc/resolv.conf vers 127.0.0.1 =="
PREVIOUS_RESOLV="$(mktemp)"
PREVIOUS_WAS_SYMLINK=""
if [ -L /etc/resolv.conf ]; then
  PREVIOUS_WAS_SYMLINK="$(readlink /etc/resolv.conf)"
else
  cp /etc/resolv.conf "$PREVIOUS_RESOLV" 2>/dev/null || true
fi
rm -f /etc/resolv.conf
echo "nameserver 127.0.0.1" > /etc/resolv.conf

echo "== Demarrage de dnsmasq (port 53) =="
systemctl enable dnsmasq >/dev/null 2>&1 || true
systemctl restart dnsmasq

echo "== Verification =="
RESOLVED=0
for _ in 1 2 3 4 5; do
  if timeout 5 getent ahosts debian.org >/dev/null 2>&1; then
    RESOLVED=1
    break
  fi
  sleep 1
done
if [ "$RESOLVED" -eq 0 ]; then
  echo "La resolution DNS ne fonctionne pas apres la bascule : /etc/resolv.conf est remis tel qu'il etait." >&2
  rm -f /etc/resolv.conf
  if [ -n "$PREVIOUS_WAS_SYMLINK" ]; then
    ln -s "$PREVIOUS_WAS_SYMLINK" /etc/resolv.conf
  else
    cp "$PREVIOUS_RESOLV" /etc/resolv.conf
  fi
  rm -f "$PREVIOUS_RESOLV"
  exit 2
fi
rm -f "$PREVIOUS_RESOLV"

echo
echo "== Bascule terminee : le blocage des sites est actif =="
echo "En cas de probleme reseau : sudo bash switch-dns-rollback.sh"
