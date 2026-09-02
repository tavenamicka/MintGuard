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

logger = logging.getLogger("mintguard.gui.daemon_control")


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
    jusqu'ici, hors de portée d'un parent non-technique (voir SUIVI.md).

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
