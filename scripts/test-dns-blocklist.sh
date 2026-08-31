#!/usr/bin/env bash
# Test isole du blocage DNS : instance dnsmasq temporaire sur le port 5353,
# NE TOUCHE PAS au resolveur systeme (systemd-resolved reste actif normalement).
# Usage : sudo bash scripts/test-dns-blocklist.sh
set -euo pipefail

BLOCKLIST=/tmp/mintguard_blocklist_test.hosts
PIDFILE=/tmp/mintguard_test_dnsmasq.pid
LOGFILE=/tmp/mintguard_test_dnsmasq.log

if [ "$EUID" -ne 0 ]; then
  echo "Ce script doit etre lance avec sudo." >&2
  exit 1
fi

if [ ! -f "$BLOCKLIST" ]; then
  echo "Blocklist de test introuvable ($BLOCKLIST)." >&2
  echo "Genere-la d'abord (deja fait normalement lors du test precedent)." >&2
  exit 1
fi

echo "--- Blocklist de test ---"
cat "$BLOCKLIST"

echo "--- Demarrage dnsmasq de test (port 5353, PAS le resolveur systeme) ---"
dnsmasq --no-daemon --listen-address=127.0.0.1 --port=5353 \
  --addn-hosts="$BLOCKLIST" --pid-file="$PIDFILE" --log-queries \
  > "$LOGFILE" 2>&1 &
DNSMASQ_PID=$!

cleanup() {
  echo "--- Arret dnsmasq de test ---"
  kill "$DNSMASQ_PID" 2>/dev/null || true
  wait "$DNSMASQ_PID" 2>/dev/null || true
}
trap cleanup EXIT

sleep 1

echo "--- Domaine BLOQUE (tiktok.com) : doit renvoyer 0.0.0.0 ---"
dig @127.0.0.1 -p 5353 tiktok.com +short

echo "--- Domaine NON bloque (example.com) : doit renvoyer une vraie IP ---"
dig @127.0.0.1 -p 5353 example.com +short

echo "--- Log dnsmasq (requetes recues) ---"
cat "$LOGFILE"
