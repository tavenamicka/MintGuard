# MintGuard - Application de controle parental pour Linux Mint
# Copyright (C) 2026 Mickael Tavenart
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Le système interroge-t-il réellement dnsmasq (MintGuard) ?

Le blocage des sites repose entièrement sur ce point : si /etc/resolv.conf désigne un autre
serveur (8.8.8.8, la box, le stub systemd-resolved...), dnsmasq tourne pour rien et aucun site
n'est bloqué - tout en laissant le Tableau de bord afficher "Protection active". Constaté en
usage réel : /etc/resolv.conf réécrit à la main pendant une panne,
blocage silencieusement inopérant pendant des semaines.

Lecture seule d'un fichier lisible par tous : utilisable aussi bien par le daemon (journal)
que par la GUI (carte d'alerte), sans privilège. `repair_resolver()` ci-dessous est l'exception
volontaire : le daemon tourne déjà en root, donc rien ne justifie de laisser la panne dépendre
d'un parent qui pense à ouvrir le Tableau de bord et cliquer "réparer".
"""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("mintguard.backend.dns_health")

RESOLV_CONF = Path("/etc/resolv.conf")
MINTGUARD_RESOLVER = "127.0.0.1"

# Installé par le .deb (et scripts/install.sh), propriété de root : jamais un script modifiable
# par l'utilisateur appelant. Même script que gui.daemon_control.repair_dns_via_polkit (qui
# l'exécute via pkexec pour un clic parent) - on ne duplique pas sa logique (détection des
# serveurs amont, bascule, vérification + rollback si le DNS ne répond plus) en Python.
SWITCH_DNS_SCRIPT = Path("/usr/lib/mintguard/switch-dns.sh")


def system_resolver_uses_mintguard(path: Path = RESOLV_CONF) -> bool | None:
    """True si tous les `nameserver` du fichier désignent dnsmasq, False sinon, None si le
    fichier est illisible (état inconnu : l'appelant ne doit pas alerter à tort)."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    nameservers = [
        parts[1]
        for line in content.splitlines()
        if (parts := line.split()) and parts[0] == "nameserver" and len(parts) > 1
    ]
    return bool(nameservers) and all(ns == MINTGUARD_RESOLVER for ns in nameservers)


def repair_resolver() -> bool:
    """Relance switch-dns.sh pour réparer la dérive détectée par
    `system_resolver_uses_mintguard`. Script idempotent et déjà testé en conditions réelles :
    il remet lui-même l'état précédent si le DNS ne répond plus après la bascule, donc un échec
    ici ne laisse jamais la machine sans résolution DNS."""
    if not SWITCH_DNS_SCRIPT.is_file():
        return False
    try:
        subprocess.run([str(SWITCH_DNS_SCRIPT)], check=True, capture_output=True, timeout=60)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
        logger.error("Réparation DNS automatique échouée: %s", e)
        return False
    logger.info("Réparation DNS automatique réussie (%s)", SWITCH_DNS_SCRIPT)
    return True
