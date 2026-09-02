#!/usr/bin/env bash
# Desinstallation systeme MintGuard (Linux Mint, root requis).
# Par defaut, conserve la BD/logs/config (retrait applicatif uniquement).
# Usage : sudo bash scripts/uninstall.sh [--purge]
set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "Ce script doit etre lance avec sudo." >&2
  exit 1
fi

PURGE=0
if [ "${1:-}" = "--purge" ]; then
  PURGE=1
fi

echo "== Service systemd =="
if systemctl is-active --quiet mintguard-daemon 2>/dev/null; then
  systemctl stop mintguard-daemon
fi
systemctl disable mintguard-daemon 2>/dev/null || true
rm -f /etc/systemd/system/mintguard-daemon.service
systemctl daemon-reload

echo "== Regles firewall (defense en profondeur) =="
# A faire meme sans --purge : contrairement a la BD/logs (donnees inertes), une regle
# iptables oubliee continuerait a bloquer le compte enfant indefiniment apres retrait
# de MintGuard.
iptables -D OUTPUT -j MINTGUARD 2>/dev/null || true
iptables -F MINTGUARD 2>/dev/null || true
iptables -X MINTGUARD 2>/dev/null || true

echo "== dnsmasq =="
rm -f /etc/dnsmasq.d/mintguard.conf

echo "== Icone, entrees de menu et autostart =="
rm -f /usr/share/applications/mintguard.desktop
rm -f /usr/share/icons/hicolor/scalable/apps/mintguard.svg
rm -f /etc/xdg/autostart/mintguard-child-tray.desktop
rm -f /etc/xdg/autostart/mintguard-parent-tray.desktop

echo "== Environnement Python =="
rm -rf /opt/mintguard

if [ "$PURGE" -eq 1 ]; then
  echo "== Purge des donnees (--purge) =="
  rm -rf /var/lib/mintguard /var/lib/mintguard-dns /var/log/mintguard /etc/mintguard
  echo "BD, logs, blocklist DNS et config supprimes."
else
  echo "BD/logs/config conserves dans /var/lib/mintguard, /var/log/mintguard, /etc/mintguard."
  echo "Relancer avec --purge pour tout supprimer."
fi

echo "== Termine =="
