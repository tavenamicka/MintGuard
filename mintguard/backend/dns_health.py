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
que par la GUI (carte d'alerte), sans privilège.
"""

from pathlib import Path

RESOLV_CONF = Path("/etc/resolv.conf")
MINTGUARD_RESOLVER = "127.0.0.1"


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
