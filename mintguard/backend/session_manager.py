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

logger = logging.getLogger("mintguard.backend.session")


class SessionManager:
    """Gère la fermeture de session enfant via loginctl (fin de plage horaire autorisée)."""

    def terminate_user_session(self, username: str) -> bool:
        try:
            subprocess.run(["loginctl", "terminate-user", username], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error("Échec de la fermeture de session pour %s: %s", username, e)
            return False

    def test(self) -> bool:
        """Vérifie que loginctl est accessible (liste des sessions), sans rien terminer."""
        try:
            subprocess.run(["loginctl", "list-sessions"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning("loginctl indisponible (normal hors Linux): %s", e)
            return False
