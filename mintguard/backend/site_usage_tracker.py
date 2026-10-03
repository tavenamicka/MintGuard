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
import re
from datetime import date
from pathlib import Path

from mintguard.backend.site_categories import domain_matches
from mintguard.backend.usage_tracker import UsageTracker
from mintguard.config import get_config
from mintguard.db.database import session_scope
from mintguard.db.models import BlockedSite, Child, SiteDailyUsage

logger = logging.getLogger("mintguard.backend.site_usage_tracker")

# Format syslog de dnsmasq (log-queries) : "<prefixe date/pid> query[A] www.example.com from
# 127.0.0.1". re.search (pas de match sur la ligne entiere) pour rester insensible au prefixe
# exact, et [A-Z]+ generique (A/AAAA/HTTPS/PTR...) plutot qu'une liste de types - le bruit non
# pertinent (ex: requetes PTR) ne correspondra simplement a aucun domaine enregistre en aval,
# donc rester permissif ici est sans risque.
_QUERY_LINE_RE = re.compile(r"query\[\S+\]\s+(\S+)\s+from\b")


def resolve_active_child_id(usage_tracker: UsageTracker) -> int | None:
    """Determine l'unique enfant actuellement connecte, ou None si ambigu (aucun enfant actif,
    ou plusieurs simultanement - changement rapide d'utilisateur). Distinct de
    UsageTracker.record_tick(), qui credite TOUS les enfants actifs a la fois pour le temps
    d'ecran : ce choix ne convient pas au decompte du temps par site (voir SiteUsageTracker),
    ou attribuer une visite au mauvais enfant serait plus genant qu'un cycle non compte."""
    active_usernames = usage_tracker.get_active_usernames()
    if not active_usernames:
        return None
    with session_scope() as session:
        matched = session.query(Child).filter(Child.username.in_(active_usernames)).all()
    return matched[0].id if len(matched) == 1 else None


class SiteUsageTracker:
    """Accumule SiteDailyUsage a partir des requetes DNS journalisees par dnsmasq
    (log-queries), pour les sites a quota (BlockedSite.daily_budget_minutes non None).

    Vie privee : `log-queries` journalise le trafic DNS de TOUTE la machine (parents compris),
    ce qui l'a fait desactiver par defaut a l'origine (voir etc/dnsmasq.d/mintguard.conf). Le
    fichier est desormais lu PUIS TRONQUE a chaque appel de poll() (cadence
    monitoring.process_check_interval, ~5s par defaut) - au plus quelques secondes
    d'historique DNS brut restent sur disque a tout instant, jamais un historique de
    navigation complet ou illimite.
    """

    def __init__(self, log_path: Path | None = None):
        self.log_path = log_path or Path(get_config().get("dns.query_log_path", "/var/log/mintguard/dns.log"))

    def poll(self, elapsed_seconds: float, active_child_id: int | None) -> None:
        """A appeler une fois par cycle du daemon (voir daemon.py::run_cycle), avec
        l'intervalle ecoule depuis le tour precedent et l'enfant actif resolu ce cycle (voir
        resolve_active_child_id). Le fichier de log est toujours lu et tronque, meme si
        active_child_id est None - la troncature est une protection vie privee
        inconditionnelle, independante du decompte de quota."""
        queried_domains = self._read_and_truncate()
        if active_child_id is None or not queried_domains:
            return

        budgeted_domains = self._budgeted_domains()
        matched = {
            domain for domain in budgeted_domains if any(domain_matches(q, domain) for q in queried_domains)
        }
        if matched:
            self._accumulate(active_child_id, matched, elapsed_seconds)

    def _read_and_truncate(self) -> set[str]:
        try:
            with open(self.log_path, "r+", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                f.seek(0)
                f.truncate(0)
        except FileNotFoundError:
            return set()
        except OSError as e:
            logger.warning("Lecture/troncature du log dnsmasq impossible: %s", e)
            return set()

        domains = set()
        for line in lines:
            match = _QUERY_LINE_RE.search(line)
            if match:
                domains.add(match.group(1).rstrip("."))
        return domains

    @staticmethod
    def _budgeted_domains() -> list[str]:
        with session_scope() as session:
            rows = (
                session.query(BlockedSite)
                .filter(BlockedSite.blocked.is_(True), BlockedSite.daily_budget_minutes.isnot(None))
                .all()
            )
            return [row.domain for row in rows]

    @staticmethod
    def _accumulate(child_id: int, domains: set[str], elapsed_seconds: float) -> None:
        today = date.today().isoformat()
        with session_scope() as session:
            for domain in domains:
                row = session.query(SiteDailyUsage).filter_by(child_id=child_id, domain=domain, date=today).first()
                if row is None:
                    row = SiteDailyUsage(child_id=child_id, domain=domain, date=today, seconds_used=0)
                    session.add(row)
                row.seconds_used += int(elapsed_seconds)
            session.commit()

    def test(self) -> bool:
        """Verifie que le chemin du log est accessible en lecture (ou absent, ce qui est un
        etat normal tant qu'aucune requete n'a encore ete journalisee)."""
        try:
            self.log_path.parent.exists()
            return True
        except Exception as e:
            logger.error("Échec du test SiteUsageTracker: %s", e)
            return False
