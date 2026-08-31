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

logger = logging.getLogger("mintguard.backend.apparmor")

PROFILE_NAME = "mintguard-restrict-child"
PROFILE_PATH = Path("/etc/apparmor.d") / PROFILE_NAME


class AppArmorController:
    """Charge/décharge le profil AppArmor confinant les applications enfant (Phase 3)."""

    def load_profile(self) -> bool:
        try:
            subprocess.run(["apparmor_parser", "-r", str(PROFILE_PATH)], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error("Échec du chargement du profil AppArmor: %s", e)
            return False

    def test(self) -> bool:
        """Vérifie que apparmor_parser est disponible, sans charger de profil."""
        try:
            subprocess.run(["apparmor_parser", "--version"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning("AppArmor indisponible (normal hors Linux Mint): %s", e)
            return False
