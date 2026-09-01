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

from mintguard.config import get_config
from mintguard.db.database import get_session
from mintguard.db.models import BlockedSite

logger = logging.getLogger("mintguard.backend.dns")


class DNSController:
    """Génère la blocklist DNS pour dnsmasq à partir des sites bloqués en BD."""

    def __init__(self, blocklist_path: Path | None = None):
        self.blocklist_path = blocklist_path or Path(
            get_config().get("dns.blocklist_path", "/var/lib/mintguard-dns/blocklist.hosts")
        )

    def generate_blocklist(self) -> int:
        """Régénère le fichier blocklist.hosts depuis la BD. Retourne le nombre d'entrées écrites."""
        session = get_session()
        try:
            sites = session.query(BlockedSite).filter_by(blocked=True).all()
        finally:
            session.close()

        self.blocklist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.blocklist_path, "w", encoding="utf-8") as f:
            for site in sites:
                f.write(f"0.0.0.0 {site.domain}\n")
        return len(sites)

    def reload_dnsmasq(self) -> bool:
        """Recharge dnsmasq pour appliquer la nouvelle blocklist."""
        try:
            subprocess.run(["systemctl", "reload", "dnsmasq"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error("Échec du rechargement dnsmasq: %s", e)
            return False

    def test(self) -> bool:
        """Vérifie que le contrôleur peut générer une blocklist sans erreur."""
        try:
            self.generate_blocklist()
            return True
        except Exception as e:
            logger.error("Échec du test DNSController: %s", e)
            return False
