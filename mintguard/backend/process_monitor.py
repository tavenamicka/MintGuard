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

    def get_child_ids_by_username(self) -> dict[str, int]:
        session = get_session()
        try:
            return {c.username: c.id for c in session.query(Child).all()}
        finally:
            session.close()

    def check_and_kill(self) -> list[str]:
        """Termine les processus bloqués tournant sous un compte enfant. Retourne les noms tués.

        Filtré par utilisateur, pas seulement par nom : trouvé à l'audit de sécurité (voir
        SUIVI.md) — sans ce filtre, un processus du même nom tournant sous le compte PARENT (ou
        tout autre compte du système) était tué aussi, dommage collatéral non intentionnel.
        """
        blocked_names = self.get_blocked_app_names()
        if not blocked_names:
            return []
        # Un seul chargement par cycle : la version précédente rouvrait une session de BD
        # pour retrouver l'enfant à chaque processus tué (`_child_id_for_username`), alors
        # que la correspondance nom -> id est la même pour tout le cycle.
        child_ids = self.get_child_ids_by_username()
        if not child_ids:
            return []

        killed = []
        events: list[tuple[int | None, str]] = []
        for proc in psutil.process_iter(["pid", "name", "username"]):
            proc_name = (proc.info.get("name") or "").lower()
            username = self._plain_username(proc.info.get("username"))
            if proc_name in blocked_names and username in child_ids:
                try:
                    proc.kill()
                except psutil.Error as e:
                    logger.warning("Impossible de terminer %s: %s", proc_name, e)
                    continue
                killed.append(proc_name)
                events.append((child_ids[username], proc_name))

        # Un seul commit pour tous les processus tués de ce cycle (fermer une application
        # en tue souvent plusieurs d'un coup : onglets, processus de rendu...).
        if events:
            self._log_actions(events)
        return killed

    @staticmethod
    def _plain_username(username: str | None) -> str | None:
        if not username:
            return None
        # psutil renvoie "DOMAINE\\utilisateur" sous Windows ; sans effet sous Linux (cible réelle).
        return username.rsplit("\\", 1)[-1]

    def _log_actions(self, events: list[tuple[int | None, str]]) -> None:
        """Journalise les applications bloquées de ce cycle (une seule transaction)."""
        session = get_session()
        try:
            session.add_all(
                ActivityLog(child_id=child_id, action="app_blocked", details=details)
                for child_id, details in events
            )
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
