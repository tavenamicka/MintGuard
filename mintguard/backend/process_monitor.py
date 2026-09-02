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
from datetime import date

import psutil

from mintguard.db.database import get_session
from mintguard.db.models import ActivityLog, AppDailyUsage, BlockedApp, Child

logger = logging.getLogger("mintguard.backend.process_monitor")


class ProcessMonitor:
    """Surveille les processus en cours et termine les applications bloquées.

    Deux régimes par application (voir `BlockedApp.daily_budget_minutes`) : sans quota,
    blocage total et immédiat (comportement historique) ; avec quota, l'application peut
    tourner jusqu'à épuisement de son temps cumulé du jour (`AppDailyUsage`), puis est tuée.
    """

    def get_blocked_apps(self) -> list[BlockedApp]:
        session = get_session()
        try:
            return session.query(BlockedApp).filter_by(enabled=True).all()
        finally:
            session.close()

    def get_child_ids_by_username(self) -> dict[str, int]:
        session = get_session()
        try:
            return {c.username: c.id for c in session.query(Child).all()}
        finally:
            session.close()

    def check_and_kill(self, elapsed_seconds: float = 0.0) -> list[str]:
        """Termine les applications bloquées tournant sous un compte enfant. Retourne les
        noms tués.

        Filtré par utilisateur, pas seulement par nom : trouvé à l'audit de sécurité (voir
        SUIVI.md) — sans ce filtre, un processus du même nom tournant sous le compte PARENT (ou
        tout autre compte du système) était tué aussi, dommage collatéral non intentionnel.

        `elapsed_seconds` (temps écoulé depuis le cycle précédent, cf. `daemon.py::run_cycle`)
        n'est utilisé que pour les applications à quota : les applications à blocage total sont
        tuées dès qu'elles sont vues, comme avant.
        """
        blocked_apps = self.get_blocked_apps()
        if not blocked_apps:
            return []
        # Un seul chargement par cycle : la version précédente rouvrait une session de BD
        # pour retrouver l'enfant à chaque processus tué (`_child_id_for_username`), alors
        # que la correspondance nom -> id est la même pour tout le cycle.
        child_ids = self.get_child_ids_by_username()
        if not child_ids:
            return []

        # Ligne child_id-specifique prioritaire sur la ligne globale (child_id=None) du meme
        # nom d'appli, pour ce meme enfant.
        rules_by_name: dict[str, dict[int | None, BlockedApp]] = defaultdict(dict)
        for app in blocked_apps:
            rules_by_name[app.app_name.lower()][app.child_id] = app

        killed: list[str] = []
        events: list[tuple[int, str]] = []
        budgeted_running: dict[tuple[int, str], list[psutil.Process]] = defaultdict(list)

        for proc in psutil.process_iter(["pid", "name", "username"]):
            proc_name = (proc.info.get("name") or "").lower()
            child_id = child_ids.get(self._plain_username(proc.info.get("username")))
            if child_id is None or proc_name not in rules_by_name:
                continue
            candidates = rules_by_name[proc_name]
            rule = candidates.get(child_id) or candidates.get(None)
            if rule is None:
                continue
            if rule.daily_budget_minutes is None:
                if self._kill(proc, proc_name):
                    killed.append(proc_name)
                    events.append((child_id, f"Application bloquée : {proc_name}"))
                continue
            budgeted_running[(child_id, proc_name)].append(proc)

        if budgeted_running and elapsed_seconds > 0:
            exceeded = self._accumulate_app_usage(budgeted_running.keys(), elapsed_seconds, rules_by_name)
            for key in exceeded:
                child_id, proc_name = key
                for proc in budgeted_running[key]:
                    if self._kill(proc, proc_name):
                        killed.append(proc_name)
                rule = rules_by_name[proc_name].get(child_id) or rules_by_name[proc_name].get(None)
                budget = rule.daily_budget_minutes if rule else "?"
                events.append((child_id, f"Quota atteint : {proc_name} ({budget} min/jour)"))

        # Un seul commit pour tous les événements de ce cycle (fermer une application en tue
        # souvent plusieurs d'un coup : onglets, processus de rendu...).
        if events:
            self._log_actions(events)
        return killed

    @staticmethod
    def _kill(proc: "psutil.Process", proc_name: str) -> bool:
        try:
            proc.kill()
            return True
        except psutil.Error as e:
            logger.warning("Impossible de terminer %s: %s", proc_name, e)
            return False

    def _accumulate_app_usage(
        self,
        keys,
        elapsed_seconds: float,
        rules_by_name: dict[str, dict[int | None, BlockedApp]],
    ) -> set[tuple[int, str]]:
        """Incrémente `AppDailyUsage` pour chaque `(child_id, app_name)` en cours d'exécution ce
        cycle (une fois par clé, pas par processus individuel — plusieurs processus du même nom
        ne doivent pas consommer le quota plus vite). Retourne les clés dont le cumul atteint ou
        dépasse le quota de leur règle."""
        today = date.today().isoformat()
        exceeded: set[tuple[int, str]] = set()
        session = get_session()
        try:
            for child_id, app_name in keys:
                row = session.query(AppDailyUsage).filter_by(child_id=child_id, app_name=app_name, date=today).first()
                if row is None:
                    row = AppDailyUsage(child_id=child_id, app_name=app_name, date=today, seconds_used=0)
                    session.add(row)
                row.seconds_used += int(elapsed_seconds)

                rule = rules_by_name[app_name].get(child_id) or rules_by_name[app_name].get(None)
                if rule is not None and rule.daily_budget_minutes is not None:
                    if row.seconds_used >= rule.daily_budget_minutes * 60:
                        exceeded.add((child_id, app_name))
            session.commit()
        finally:
            session.close()
        return exceeded

    @staticmethod
    def _plain_username(username: str | None) -> str | None:
        if not username:
            return None
        # psutil renvoie "DOMAINE\\utilisateur" sous Windows ; sans effet sous Linux (cible réelle).
        return username.rsplit("\\", 1)[-1]

    def _log_actions(self, events: list[tuple[int, str]]) -> None:
        """Journalise les événements (blocage total ou quota atteint) de ce cycle (une seule
        transaction)."""
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
