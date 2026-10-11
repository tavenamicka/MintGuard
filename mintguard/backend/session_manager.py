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

import json
import logging
import subprocess

from mintguard.utils.validators import is_valid_username

logger = logging.getLogger("mintguard.backend.session")

# États loginctl (systemd-logind) correspondant à une session réellement en cours — par
# opposition à "closing"/"closed", une session qui n'a pas fini de se terminer proprement.
_LOGIND_ACTIVE_STATES = {"active", "online"}


def logind_active_usernames() -> set[str] | None:
    """Comptes ayant au moins une session systemd-logind en cours, ou None si loginctl est
    indisponible (hors Linux, erreur, timeout) - à l'appelant de choisir son repli."""
    try:
        result = subprocess.run(
            ["loginctl", "list-sessions", "--output=json"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        sessions = json.loads(result.stdout)
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
        json.JSONDecodeError,
    ) as e:
        logger.warning("loginctl indisponible, filtrage par état de session ignoré: %s", e)
        return None
    return {s["user"] for s in sessions if s.get("state") in _LOGIND_ACTIVE_STATES}


class SessionManager:
    """Gère la fermeture de session enfant via loginctl (fin de plage horaire autorisée)."""

    def terminate_user_session(self, username: str) -> bool:
        # Le nom vient de la BD et est passé à une commande privilégiée : on refuse tout ce
        # qui ne ressemble pas à un compte Linux plutôt que de laisser `loginctl` interpréter
        # une valeur inattendue (un nom commençant par « - » deviendrait une option).
        if not is_valid_username(username):
            logger.error("Nom d'utilisateur invalide, session non fermée: %r", username)
            return False
        try:
            subprocess.run(["loginctl", "terminate-user", username], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error("Échec de la fermeture de session pour %s: %s", username, e)
            return False

    def logged_in_usernames(self) -> set[str] | None:
        """Voir `logind_active_usernames()` - exposé ici pour que Scheduler (et ses tests,
        via un faux SessionManager) n'ait qu'une seule dépendance système à simuler."""
        return logind_active_usernames()

    def test(self) -> bool:
        """Vérifie que loginctl est accessible (liste des sessions), sans rien terminer."""
        try:
            subprocess.run(["loginctl", "list-sessions"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning("loginctl indisponible (normal hors Linux): %s", e)
            return False
