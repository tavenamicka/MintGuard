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
import os
import subprocess
import tempfile
from pathlib import Path

from mintguard.config import get_config
from mintguard.db.database import get_session
from mintguard.db.models import BlockedSite
from mintguard.utils.validators import is_valid_domain

logger = logging.getLogger("mintguard.backend.dns")

HEADER = (
    "# Fichier généré par MintGuard — ne pas éditer à la main.\n"
    "# Régénéré à chaque changement de la liste des sites bloqués (voir Réglages > Sites).\n"
)


class DNSController:
    """Génère la blocklist DNS pour dnsmasq à partir des sites bloqués en BD.

    Format `address=/domaine/0.0.0.0` (fragment de configuration dnsmasq) et NON un fichier
    hosts (`addn-hosts`) : un fichier hosts ne matche que le nom exact, donc bloquer
    « youtube.com » laissait « www.youtube.com » parfaitement accessible — c'est-à-dire le
    site lui-même dans un navigateur. `address=/youtube.com/` couvre le domaine ET tous ses
    sous-domaines, ce qu'attend un parent qui coche « youtube.com ».

    Contrepartie : dnsmasq ne relit PAS ses fichiers de configuration sur SIGHUP (`systemctl
    reload`), seulement les fichiers hosts — d'où `restart_dnsmasq()`. Pour que ce redémarrage
    reste rare, `apply()` ne l'exécute que si le contenu de la blocklist a réellement changé
    (auparavant le daemon rechargeait dnsmasq toutes les 30 s même sans aucun changement).
    """

    def __init__(self, blocklist_path: Path | None = None):
        self.blocklist_path = blocklist_path or Path(
            get_config().get("dns.blocklist_path", "/var/lib/mintguard-dns/blocklist.conf")
        )

    # -- Contenu ----------------------------------------------------------

    def _blocked_domains(self) -> list[str]:
        """Domaines bloqués en BD, revalidés avant écriture.

        Défense en profondeur : la GUI valide déjà la saisie du parent (`is_valid_domain`),
        mais cette blocklist est injectée telle quelle dans la configuration d'un dnsmasq
        tournant en root. Une valeur en BD contenant un espace ou un retour à la ligne
        (import, édition manuelle de la BD, régression d'un futur appelant) écrirait des
        directives dnsmasq arbitraires ; au mieux dnsmasq refuse de démarrer, au pire la
        configuration réseau est détournée. On filtre ici, au dernier moment.
        """
        session = get_session()
        try:
            domains = [s.domain for s in session.query(BlockedSite).filter_by(blocked=True).all()]
        finally:
            session.close()

        valid = []
        for domain in domains:
            if is_valid_domain(domain):
                valid.append(domain.strip().lower())
            else:
                logger.warning("Domaine invalide ignoré dans la blocklist: %r", domain)
        return sorted(set(valid))

    @staticmethod
    def _render(domains: list[str]) -> str:
        return HEADER + "".join(f"address=/{domain}/0.0.0.0\n" for domain in domains)

    def _current_content(self) -> str | None:
        try:
            return self.blocklist_path.read_text(encoding="utf-8")
        except OSError:
            return None

    def _write(self, content: str) -> None:
        """Écriture atomique (fichier temporaire + `os.replace`).

        dnsmasq peut lire le fichier au moment exact où le daemon le réécrit : une écriture
        directe l'exposerait à une blocklist tronquée (donc à des sites débloqués), ou à un
        refus de démarrage sur une ligne coupée en deux.
        """
        directory = self.blocklist_path.parent
        directory.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".blocklist-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            # dnsmasq tourne en utilisateur non-privilégié et doit pouvoir lire ce fichier
            # (mkstemp crée en 0600) — il ne contient aucune donnée sensible.
            os.chmod(tmp_path, 0o644)
            os.replace(tmp_path, self.blocklist_path)
        except BaseException:
            Path(tmp_path).unlink(missing_ok=True)
            raise

    # -- API --------------------------------------------------------------

    def generate_blocklist(self) -> int:
        """Régénère le fichier de blocklist depuis la BD. Retourne le nombre d'entrées écrites."""
        domains = self._blocked_domains()
        self._write(self._render(domains))
        return len(domains)

    def apply(self) -> bool:
        """Régénère la blocklist et redémarre dnsmasq *uniquement* si son contenu a changé.

        Retourne True si un redémarrage a eu lieu. Appelée à chaque cycle DNS du daemon :
        sans cette comparaison, dnsmasq était redémarré toutes les 30 s en pure perte (cache
        DNS vidé, bruit dans les logs, coupure de résolution de quelques dizaines de ms).
        """
        content = self._render(self._blocked_domains())
        if content == self._current_content():
            return False
        self._write(content)
        return self.restart_dnsmasq()

    def restart_dnsmasq(self) -> bool:
        """Redémarre dnsmasq pour appliquer la nouvelle blocklist.

        `restart` et non `reload` : SIGHUP ne fait relire à dnsmasq que les fichiers hosts,
        jamais ses fichiers de configuration (dont fait partie la blocklist depuis le passage
        au format `address=/domaine/`).
        """
        try:
            subprocess.run(["systemctl", "restart", "dnsmasq"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error("Échec du redémarrage de dnsmasq: %s", e)
            return False

    def test(self) -> bool:
        """Vérifie que le contrôleur peut générer une blocklist sans erreur."""
        try:
            self.generate_blocklist()
            return True
        except Exception as e:
            logger.error("Échec du test DNSController: %s", e)
            return False
