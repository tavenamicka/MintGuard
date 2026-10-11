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

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("mintguard.gui.daemon_control")

# Installé par le .deb (et scripts/install.sh), propriété de root : pkexec n'exécute jamais un
# script modifiable par un utilisateur normal (celui du dépôt git par exemple).
SWITCH_DNS_SCRIPT = Path("/usr/lib/mintguard/switch-dns.sh")


def is_daemon_active() -> bool:
    """Le daemon répond-il sur le socket de statut ? Même canal que les trays (voir
    child_tray.query_status) : pas de dépendance à `systemctl` (indisponible/différent hors
    systemd), et c'est la même chose qui compte réellement pour la protection - un service
    `active` dont le socket ne répond pas ne protégerait de toute façon personne."""
    from mintguard.child_tray import query_status

    return query_status() is not None


def start_daemon_via_polkit() -> bool | None:
    """Démarre `mintguard-daemon` via l'agent polkit du bureau (même fenêtre système native
    que la réinitialisation du PIN, voir dialogs.py::_confirm_admin_identity) - remplace la
    commande de terminal `sudo systemctl start mintguard-daemon` que l'installation demandait
    jusqu'ici, hors de portée d'un parent non-technique.

    Retourne `None` si `pkexec` est absent du système (action indisponible), `True`/`False`
    selon que le démarrage a réussi ou a été annulé/a échoué.
    """
    try:
        # Meme delai que _confirm_admin_identity : sans agent polkit graphique, pkexec
        # basculerait sur une invite texte que personne ne voit et attendrait indéfiniment.
        result = subprocess.run(
            ["pkexec", "systemctl", "start", "mintguard-daemon"], capture_output=True, timeout=120
        )
        return result.returncode == 0
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return False


def repair_dns_via_polkit() -> bool | None:
    """Bascule (ou rebascule) le résolveur DNS système vers dnsmasq, via pkexec - voir
    scripts/switch-dns.sh (idempotent, remet l'état précédent si le DNS ne répond plus).

    Même contrat que `start_daemon_via_polkit` : `None` si l'action est indisponible (pkexec
    ou script absent), sinon `True`/`False` selon le résultat.
    """
    if not SWITCH_DNS_SCRIPT.is_file():
        return None
    try:
        result = subprocess.run(["pkexec", str(SWITCH_DNS_SCRIPT)], capture_output=True, timeout=180)
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return False
    if result.returncode != 0:
        logger.warning("Bascule DNS échouée (%s): %s", result.returncode, result.stderr.decode(errors="replace"))
    return result.returncode == 0
