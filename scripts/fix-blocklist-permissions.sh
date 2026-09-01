#!/usr/bin/env bash
# Corrige le 5e defaut de conception trouve en Phase 3 : dnsmasq tourne
# en utilisateur non-privilegie (ex: uid 999, groupe nogroup sur
# Debian/Ubuntu) et ne peut pas traverser /var/lib/mintguard (2770,
# reserve BD/PIN) pour lire blocklist.hosts - meme si le fichier lui
# meme est lisible. Resultat : aucun site n'etait jamais bloque malgre
# une blocklist generee correctement (voir SUIVI.md Phase 3).
#
# Ce script deplace la blocklist dans un repertoire separe et
# mondialement traversable (/var/lib/mintguard-dns, sans donnees
# sensibles), et met a jour la configuration deja installee pour
# pointer dessus. A lancer une seule fois sur un systeme deja installe
# avant ce correctif (une nouvelle install via install.sh cree deja le
# bon repertoire).
#
# Usage : sudo bash scripts/fix-blocklist-permissions.sh
set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "Ce script doit etre lance avec sudo." >&2
  exit 1
fi

NEW_DIR=/var/lib/mintguard-dns
OLD_BLOCKLIST=/var/lib/mintguard/blocklist.hosts
CONFIG=/etc/mintguard/config.json
DNSMASQ_CONF=/etc/dnsmasq.d/mintguard.conf

echo "== Creation de $NEW_DIR (755 root:root, mondialement traversable) =="
install -d -m 755 -o root -g root "$NEW_DIR"

if [ -f "$OLD_BLOCKLIST" ]; then
  echo "== Suppression de l'ancienne blocklist (sera regeneree par le daemon) =="
  rm -f "$OLD_BLOCKLIST"
fi

echo "== Mise a jour de $CONFIG =="
if [ -f "$CONFIG" ]; then
  python3 - "$CONFIG" <<'PYEOF'
import json
import sys

path = sys.argv[1]
with open(path) as f:
    config = json.load(f)
config.setdefault("dns", {})["blocklist_path"] = "/var/lib/mintguard-dns/blocklist.conf"
with open(path, "w") as f:
    json.dump(config, f, indent=2)
    f.write("\n")
PYEOF
  echo "blocklist_path mis a jour dans $CONFIG"
else
  echo "Attention : $CONFIG introuvable, rien a mettre a jour." >&2
fi

echo "== Mise a jour de $DNSMASQ_CONF =="
if [ -f "$DNSMASQ_CONF" ]; then
  sed -i 's#^addn-hosts=.*#conf-file=/var/lib/mintguard-dns/blocklist.conf#' "$DNSMASQ_CONF"
  sed -i 's#^conf-file=.*#conf-file=/var/lib/mintguard-dns/blocklist.conf#' "$DNSMASQ_CONF"
  echo "conf-file mis a jour dans $DNSMASQ_CONF"
else
  echo "Attention : $DNSMASQ_CONF introuvable, rien a mettre a jour." >&2
fi

echo "== Redemarrage du daemon (regenere la blocklist au nouvel emplacement) =="
systemctl restart mintguard-daemon

echo "== Redemarrage de dnsmasq =="
# Un simple reload (SIGHUP) ne relit que les fichiers hosts deja connus,
# pas dnsmasq.conf - insuffisant ici puisque le CHEMIN d'addn-hosts a
# change. Un restart complet est necessaire pour qu'il decouvre le
# nouveau chemin.
systemctl restart dnsmasq

echo
echo "== Correctif applique =="
echo "Verification recommandee (apres quelques secondes, le temps du cycle du daemon) :"
echo "  cat /var/lib/mintguard-dns/blocklist.conf"
echo "  dig +short @127.0.0.1 <domaine_bloque>   # doit renvoyer 0.0.0.0"
