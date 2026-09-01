#!/usr/bin/env bash
# Test isole du blocage DNS : instance dnsmasq temporaire sur le port 5354,
# NE TOUCHE PAS au resolveur systeme (systemd-resolved reste actif normalement).
# Usage : sudo bash scripts/test-dns-blocklist.sh
set -euo pipefail

BLOCKLIST=/tmp/mintguard_blocklist_test.conf
PIDFILE=/tmp/mintguard_test_dnsmasq.pid
LOGFILE=/tmp/mintguard_test_dnsmasq.log

if [ "$EUID" -ne 0 ]; then
  echo "Ce script doit etre lance avec sudo." >&2
  exit 1
fi

if [ ! -f "$BLOCKLIST" ]; then
  echo "Blocklist de test introuvable ($BLOCKLIST)." >&2
  echo "Genere-la, par exemple :" >&2
  echo "  printf 'address=/tiktok.com/0.0.0.0\\n' > $BLOCKLIST" >&2
  exit 1
fi

echo "--- Blocklist de test ---"
cat "$BLOCKLIST"

echo "--- Demarrage dnsmasq de test (port 5354, PAS le resolveur systeme) ---"
dnsmasq --no-daemon --listen-address=127.0.0.1 --port=5354 \
  --conf-file="$BLOCKLIST" --pid-file="$PIDFILE" --log-queries \
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
dig @127.0.0.1 -p 5354 tiktok.com +short

echo "--- SOUS-DOMAINE du domaine bloque (www.tiktok.com) : doit AUSSI renvoyer 0.0.0.0 ---"
# Le cas que l'ancien format hosts (addn-hosts) laissait passer : c'est
# pourtant le nom que tape reellement un navigateur.
dig @127.0.0.1 -p 5354 www.tiktok.com +short

echo "--- Domaine NON bloque (example.com) : doit renvoyer une vraie IP ---"
dig @127.0.0.1 -p 5354 example.com +short

echo "--- Log dnsmasq (requetes recues) ---"
cat "$LOGFILE"
