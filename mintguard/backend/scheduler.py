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
from datetime import datetime

from mintguard.backend.session_manager import SessionManager
from mintguard.db.database import get_session
from mintguard.db.models import ActivityLog, Child, DailyUsage, TimeRule

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

    def get_minutes_remaining(self, child_id: int, now: datetime | None = None) -> int | None:
        """Minutes avant la fin de la fenêtre active pour cet enfant, ou avant l'épuisement de
        son quota quotidien si la règle active en a un (le plus petit des deux l'emporte).

        Réutilise le même chargement de règles que `get_active_rule()`, mais calcule une
        durée au lieu d'un booléen (utilisé par `StatusServer` pour le tray enfant).
        `None` = aucune règle aujourd'hui (accès libre, pas une coupure). `0` = déjà hors de
        toute fenêtre, ou quota épuisé (le prochain cycle de `check_all_children` va couper).
        """
        now = now or datetime.now()
        day_of_week = now.weekday()

        db_session = get_session()
        try:
            rules = (
                db_session.query(TimeRule)
                .filter_by(child_id=child_id, day_of_week=day_of_week, enabled=True)
                .all()
            )
            seconds_used = None
            if any(r.daily_budget_minutes is not None for r in rules):
                usage_row = (
                    db_session.query(DailyUsage)
                    .filter_by(child_id=child_id, date=now.date().isoformat())
                    .first()
                )
                seconds_used = usage_row.seconds_used if usage_row is not None else 0
        finally:
            db_session.close()

        if not rules:
            return None
        current_time = now.time()
        for rule in rules:
            if rule.start_hour <= current_time <= rule.end_hour:
                end_dt = datetime.combine(now.date(), rule.end_hour)
                window_remaining = max(0, int((end_dt - now).total_seconds() // 60))
                if rule.daily_budget_minutes is None:
                    return window_remaining
                budget_remaining = max(0, rule.daily_budget_minutes * 60 - (seconds_used or 0)) // 60
                return min(window_remaining, budget_remaining)
        return 0

    def check_all_children(self, now: datetime | None = None) -> list[str]:
        """Vérifie chaque enfant; ferme la session de ceux hors plage horaire autorisée, ou
        dont le quota quotidien de la règle active (si elle en a un) est épuisé.

        Toutes les règles et tout l'usage du jour sont chargés en une seule requête chacun :
        la version précédente rouvrait deux sessions de BD par enfant (`get_active_rule` +
        `_has_any_rule_today`) à chaque passage, soit 2N connexions par minute sur une BD
        SQLite partagée avec la GUI, pour une poignée de lignes qui tiennent en mémoire.
        """
        now = now or datetime.now()
        db_session = get_session()
        try:
            children = [(c.id, c.username) for c in db_session.query(Child).all()]
            rules_today: dict[int, list[TimeRule]] = defaultdict(list)
            for rule in (
                db_session.query(TimeRule).filter_by(day_of_week=now.weekday(), enabled=True).all()
            ):
                rules_today[rule.child_id].append(rule)
            usage_today: dict[int, int] = {
                row.child_id: row.seconds_used
                for row in db_session.query(DailyUsage).filter_by(date=now.date().isoformat()).all()
            }
        finally:
            db_session.close()

        terminated = []
        current_time = now.time()
        for child_id, username in children:
            rules = rules_today.get(child_id)
            if not rules:
                # Aucune règle aujourd'hui = pas de restriction (accès libre), pas un blocage.
                continue
            matched = next((r for r in rules if r.start_hour <= current_time <= r.end_hour), None)
            if matched is None:
                if self.session_manager.terminate_user_session(username):
                    terminated.append(username)
                    self._log_action(child_id, "time_limit_hit", "Auto-logout: outside allowed hours")
                continue
            if matched.daily_budget_minutes is not None:
                used_seconds = usage_today.get(child_id, 0)
                if used_seconds >= matched.daily_budget_minutes * 60:
                    if self.session_manager.terminate_user_session(username):
                        terminated.append(username)
                        self._log_action(
                            child_id,
                            "daily_budget_hit",
                            f"Auto-logout: daily budget of {matched.daily_budget_minutes} min reached",
                        )
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
