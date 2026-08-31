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

import psutil

from mintguard.db.database import get_session
from mintguard.db.models import ActivityLog, BlockedApp, Child

logger = logging.getLogger("mintguard.backend.process_monitor")


class ProcessMonitor:
    """Surveille les processus en cours et termine les applications bloquées."""

    def get_blocked_app_names(self) -> set[str]:
        session = get_session()
        try:
            apps = session.query(BlockedApp).filter_by(enabled=True).all()
            return {app.app_name.lower() for app in apps}
        finally:
            session.close()

    def check_and_kill(self) -> list[str]:
        """Parcourt les processus actifs, termine ceux qui sont bloqués. Retourne les noms tués."""
        blocked_names = self.get_blocked_app_names()
        if not blocked_names:
            return []

        killed = []
        for proc in psutil.process_iter(["pid", "name", "username"]):
            proc_name = (proc.info.get("name") or "").lower()
            if proc_name in blocked_names:
                try:
                    proc.kill()
                    killed.append(proc_name)
                    child_id = self._child_id_for_username(proc.info.get("username"))
                    self._log_action(child_id, "app_blocked", proc_name)
                except psutil.Error as e:
                    logger.warning("Impossible de terminer %s: %s", proc_name, e)
        return killed

    def _child_id_for_username(self, username: str | None) -> int | None:
        """Associe le processus tué à l'enfant propriétaire de la session (pour le Dashboard)."""
        if not username:
            return None
        # psutil renvoie "DOMAINE\\utilisateur" sous Windows ; sans effet sous Linux (cible réelle).
        plain_username = username.rsplit("\\", 1)[-1]
        session = get_session()
        try:
            child = session.query(Child).filter_by(username=plain_username).first()
            return child.id if child else None
        finally:
            session.close()

    def _log_action(self, child_id: int | None, action: str, details: str) -> None:
        session = get_session()
        try:
            session.add(ActivityLog(child_id=child_id, action=action, details=details))
            session.commit()
        finally:
            session.close()

    def test(self) -> bool:
        """Vérifie que la liste des processus est accessible."""
        try:
            list(psutil.process_iter(["pid", "name"]))
            return True
        except Exception as e:
            logger.error("Échec du test ProcessMonitor: %s", e)
            return False
