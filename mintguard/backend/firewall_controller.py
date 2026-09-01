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

from mintguard.db.database import get_session
from mintguard.db.models import Child

logger = logging.getLogger("mintguard.backend.firewall")


class FirewallController:
    """Défense en profondeur : force chaque compte enfant à utiliser uniquement le
    résolveur DNS local (dnsmasq), pour empêcher un contournement du blocage DNS en
    configurant un résolveur externe (ex: 8.8.8.8) directement dans le système ou le
    navigateur. Le blocage DNS lui-même (DNSController) reste la protection primaire.

    Règles posées dans une chaîne dédiée ("MINTGUARD") plutôt que directement dans
    OUTPUT, pour ne jamais toucher aux règles iptables préexistantes de l'utilisateur
    et pouvoir tout retirer proprement (`remove()`).
    """

    CHAIN = "MINTGUARD"
    LOCAL_RESOLVER = "127.0.0.1"

    def _iptables(self, args: list[str]) -> bool:
        try:
            subprocess.run(["iptables"] + args, check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error("Commande iptables échouée (%s): %s", args, e)
            return False

    def _chain_exists(self) -> bool:
        result = subprocess.run(["iptables", "-nL", self.CHAIN], capture_output=True)
        return result.returncode == 0

    def _jump_exists(self) -> bool:
        result = subprocess.run(["iptables", "-C", "OUTPUT", "-j", self.CHAIN], capture_output=True)
        return result.returncode == 0

    def _ensure_chain(self) -> bool:
        if not self._chain_exists() and not self._iptables(["-N", self.CHAIN]):
            return False
        if not self._jump_exists() and not self._iptables(["-I", "OUTPUT", "-j", self.CHAIN]):
            return False
        return True

    def sync_child_dns_restriction(self) -> bool:
        """Régénère les règles depuis la BD (liste actuelle des enfants). Idempotent :
        peut être rappelée à chaque cycle du daemon, comme DNSController.generate_blocklist().
        """
        if not self._ensure_chain():
            return False
        if not self._iptables(["-F", self.CHAIN]):
            return False

        session = get_session()
        try:
            usernames = [c.username for c in session.query(Child).all()]
        finally:
            session.close()

        for username in usernames:
            for proto in ("udp", "tcp"):
                rule = [
                    "-A", self.CHAIN,
                    "-m", "owner", "--uid-owner", username,
                    "-p", proto, "--dport", "53",
                    "!", "-d", self.LOCAL_RESOLVER,
                    "-j", "REJECT",
                ]
                if not self._iptables(rule):
                    return False
        return True

    def remove(self) -> bool:
        """Retire toutes les règles MintGuard (désinstallation). Idempotent : ne pas
        échouer si la chaîne/le jump n'existent déjà plus.
        """
        self._iptables(["-D", "OUTPUT", "-j", self.CHAIN])
        self._iptables(["-F", self.CHAIN])
        return self._iptables(["-X", self.CHAIN])

    def test(self) -> bool:
        """Vérifie que iptables est accessible en lecture (--list), sans modifier l'état."""
        try:
            subprocess.run(["iptables", "-L", "-n"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning("iptables indisponible (normal hors Linux/root): %s", e)
            return False
