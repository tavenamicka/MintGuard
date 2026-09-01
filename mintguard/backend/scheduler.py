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
from collections import defaultdict
from datetime import datetime, time as dt_time

from mintguard.backend.session_manager import SessionManager
from mintguard.db.database import get_session
from mintguard.db.models import ActivityLog, Child, TimeRule

logger = logging.getLogger("mintguard.backend.scheduler")


class Scheduler:
    """Vérifie les règles horaires par enfant et déclenche la fermeture de session hors plage."""

    def __init__(self, session_manager: SessionManager | None = None):
        self.session_manager = session_manager or SessionManager()

    def get_active_rule(self, child_id: int, now: datetime | None = None) -> TimeRule | None:
        now = now or datetime.now()
        day_of_week = now.weekday()  # 0=Lundi, 6=Dimanche

        db_session = get_session()
        try:
            rules = (
                db_session.query(TimeRule)
                .filter_by(child_id=child_id, day_of_week=day_of_week, enabled=True)
                .all()
            )
            for rule in rules:
                if rule.start_hour <= now.time() <= rule.end_hour:
                    return rule
            return None
        finally:
            db_session.close()

    def check_all_children(self, now: datetime | None = None) -> list[str]:
        """Vérifie chaque enfant; ferme la session de ceux hors plage horaire autorisée.

        Toutes les règles du jour sont chargées en une seule requête : la version précédente
        rouvrait deux sessions de BD par enfant (`get_active_rule` + `_has_any_rule_today`)
        à chaque passage, soit 2N connexions par minute sur une BD SQLite partagée avec la
        GUI, pour une poignée de lignes qui tiennent en mémoire.
        """
        now = now or datetime.now()
        db_session = get_session()
        try:
            children = [(c.id, c.username) for c in db_session.query(Child).all()]
            rules_today: dict[int, list[tuple[dt_time, dt_time]]] = defaultdict(list)
            for rule in (
                db_session.query(TimeRule).filter_by(day_of_week=now.weekday(), enabled=True).all()
            ):
                rules_today[rule.child_id].append((rule.start_hour, rule.end_hour))
        finally:
            db_session.close()

        terminated = []
        current_time = now.time()
        for child_id, username in children:
            windows = rules_today.get(child_id)
            if not windows:
                # Aucune règle aujourd'hui = pas de restriction (accès libre), pas un blocage.
                continue
            if any(start <= current_time <= end for start, end in windows):
                continue
            if self.session_manager.terminate_user_session(username):
                terminated.append(username)
                self._log_action(child_id, "time_limit_hit", "Auto-logout: outside allowed hours")
        return terminated

    def _log_action(self, child_id: int, action: str, details: str) -> None:
        db_session = get_session()
        try:
            db_session.add(ActivityLog(child_id=child_id, action=action, details=details))
            db_session.commit()
        finally:
            db_session.close()

    def test(self) -> bool:
        """Vérifie que la vérification des règles s'exécute sans erreur (BD vide OK)."""
        try:
            self.check_all_children()
            return True
        except Exception as e:
            logger.error("Échec du test Scheduler: %s", e)
            return False
