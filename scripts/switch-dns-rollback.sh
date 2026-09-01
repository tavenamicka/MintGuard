#!/usr/bin/env bash
# Annule la bascule DNS effectuee par switch-dns.sh : restaure
# systemd-resolved comme resolveur systeme et remet dnsmasq (MintGuard)
# sur son port de test (5354, sans impact reseau).
#
# Usage : sudo bash scripts/switch-dns-rollback.sh
set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "Ce script doit etre lance avec sudo." >&2
  exit 1
fi

BACKUP_DIR=/var/lib/mintguard/dns-switch-backup
INSTALLED_CONF=/etc/dnsmasq.d/mintguard.conf

if [ ! -d "$BACKUP_DIR" ]; then
  echo "Erreur : aucune sauvegarde trouvee dans $BACKUP_DIR. La bascule n'a" >&2
  echo "peut-etre jamais ete effectuee, ou la sauvegarde a ete supprimee." >&2
  exit 1
fi

echo "== Arret de dnsmasq =="
systemctl stop dnsmasq 2>/dev/null || true
systemctl disable dnsmasq 2>/dev/null || true

echo "== Restauration de mintguard.conf (port 5354, test uniquement) =="
if [ -f "$BACKUP_DIR/mintguard.conf.orig" ]; then
  cp "$BACKUP_DIR/mintguard.conf.orig" "$INSTALLED_CONF"
else
  echo "Sauvegarde de mintguard.conf introuvable, restauration manuelle necessaire." >&2
fi

echo "== Restauration de systemd-resolved =="
if [ -f "$BACKUP_DIR/resolved.conf.orig" ]; then
  cp "$BACKUP_DIR/resolved.conf.orig" /etc/systemd/resolved.conf
else
  sed -i 's/^DNSStubListener=no/DNSStubListener=yes/' /etc/systemd/resolved.conf
fi
systemctl restart systemd-resolved

echo "== Restauration de /etc/resolv.conf (symlink vers systemd-resolved) =="
rm -f /etc/resolv.conf
if [ -f "$BACKUP_DIR/resolv.conf.orig.symlink" ]; then
  ln -s "$(cat "$BACKUP_DIR/resolv.conf.orig.symlink")" /etc/resolv.conf
else
  ln -s /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
fi

echo
echo "== Rollback termine =="
echo "Verification recommandee : resolvectl query example.com"
echo "dnsmasq MintGuard est arrete (pas relance sur le port 5354 automatiquement)."
