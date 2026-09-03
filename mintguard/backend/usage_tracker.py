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
from datetime import date

import psutil

from mintguard.db.database import get_session
from mintguard.db.models import Child, DailyUsage

logger = logging.getLogger("mintguard.backend.usage_tracker")

# États loginctl (systemd-logind) correspondant à une session réellement en cours — par
# opposition à "closing"/"closed", une session qui n'a pas fini de se terminer proprement.
_LOGIND_ACTIVE_STATES = {"active", "online"}


class UsageTracker:
    """Cumule le temps de session des enfants dans `DailyUsage`, lu ensuite par le Dashboard.

    Même principe que ProcessMonitor/Scheduler (voir SUIVI.md, décision d'architecture
    Semaine 5) : pas de vrai canal IPC, le daemon écrit dans la BD partagée à chaque cycle et
    la GUI la relit — un délai de quelques secondes est imperceptible pour ce besoin.
    """

    def get_active_usernames(self) -> set[str]:
        """Comptes actuellement connectés au système (toutes sessions confondues).

        Croise psutil (utmp) avec loginctl/systemd-logind : trouvé en usage réel qu'après une
        fermeture forcée (`SessionManager.terminate_user_session`, ex: fin de plage horaire),
        l'entrée utmp du compte enfant peut rester "connectée" alors que la session
        systemd-logind est déjà "closing" — le Dashboard continuait alors à faire défiler le
        temps d'utilisation d'un enfant qui n'était plus réellement connecté. loginctl reflète
        l'état réel de la session, utmp seul ne suffit pas dans ce cas.
        """
        utmp_usernames = {self._plain_username(u.name) for u in psutil.users()}
        if not utmp_usernames:
            return utmp_usernames
        logind_usernames = self._logind_active_usernames()
        if logind_usernames is None:
            # loginctl indisponible (hors Linux, erreur, systemd absent) : retombe sur utmp
            # seul plutôt que de ne plus jamais compter aucun temps.
            return utmp_usernames
        return utmp_usernames & logind_usernames

    @staticmethod
    def _logind_active_usernames() -> set[str] | None:
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

    @staticmethod
    def _plain_username(username: str | None) -> str | None:
        if not username:
            return None
        # psutil renvoie "DOMAINE\\utilisateur" sous Windows ; sans effet sous Linux (cible réelle).
        return username.rsplit("\\", 1)[-1]

    def record_tick(self, elapsed_seconds: float) -> None:
        """Ajoute `elapsed_seconds` au cumul du jour de chaque enfant actuellement connecté.

        Appelé une fois par cycle du daemon (voir daemon.py::run_cycle) avec l'intervalle
        écoulé depuis le tour précédent — pas une mesure exacte seconde par seconde, mais
        cohérente avec la fréquence de contrôle déjà en place pour ProcessMonitor/Scheduler.
        """
        active_usernames = self.get_active_usernames()
        if not active_usernames:
            return

        session = get_session()
        try:
            children = session.query(Child).filter(Child.username.in_(active_usernames)).all()
            if not children:
                return
            today = date.today().isoformat()
            for child in children:
                row = session.query(DailyUsage).filter_by(child_id=child.id, date=today).first()
                if row is None:
                    row = DailyUsage(child_id=child.id, date=today, seconds_used=0)
                    session.add(row)
                row.seconds_used += int(elapsed_seconds)
            session.commit()
        finally:
            session.close()

    def get_seconds_used_today(self, child_id: int) -> int:
        """Lu par le Dashboard (GUI) — aucun appel psutil, simple lecture BD."""
        session = get_session()
        try:
            today = date.today().isoformat()
            row = session.query(DailyUsage).filter_by(child_id=child_id, date=today).first()
            return row.seconds_used if row is not None else 0
        finally:
            session.close()

    def test(self) -> bool:
        """Vérifie que la liste des sessions actives est accessible."""
        try:
            list(psutil.users())
            return True
        except Exception as e:
            logger.error("Échec du test UsageTracker: %s", e)
            return False
