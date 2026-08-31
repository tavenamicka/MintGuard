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

logger = logging.getLogger("mintguard.backend.firewall")


class FirewallController:
    """Gère les règles iptables pour bloquer l'accès réseau des enfants (Phase 3)."""

    def apply_rules(self, rules: list[str]) -> bool:
        """Applique une liste de règles iptables. Stub à implémenter en Phase 3."""
        try:
            for rule in rules:
                subprocess.run(["iptables"] + rule.split(), check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error("Échec de l'application des règles firewall: %s", e)
            return False

    def test(self) -> bool:
        """Vérifie que iptables est accessible en lecture (--list), sans modifier l'état."""
        try:
            subprocess.run(["iptables", "-L", "-n"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning("iptables indisponible (normal hors Linux/root): %s", e)
            return False
