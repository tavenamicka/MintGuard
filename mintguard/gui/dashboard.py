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

from datetime import datetime

from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from mintguard.db.database import get_session
from mintguard.db.models import ActivityLog, BlockedSite, Child, TimeRule
from mintguard.gui.widgets import Card, heading, small_label
from mintguard.locales.loader import I18nLoader


class DashboardScreen(QWidget):
    """Écran 1 (Dashboard) — vue d'ensemble en un coup d'œil, cf. PROJECT_BRIEF.md 'Écrans Principaux'.

    Note d'architecture : le blocage de sites (BlockedSite) est global à la machine, pas par
    enfant (un seul résolveur DNS pour tout le poste) — seule la limite de temps (TimeRule) est
    propre à l'enfant sélectionné. Le statut « Protection: ACTIVE » n'a pas encore de source live
    (pas d'IPC GUI↔daemon avant la Semaine 5) : il reflète la présence de règles configurées en BD.
    """

    def __init__(self, i18n: I18nLoader, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._build_ui()
        self.reload()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(heading(self.i18n("dashboard.title"), "h1"))

        layout.addWidget(small_label(self.i18n("dashboard.child_select")))
        self.child_combo = QComboBox()
        self.child_combo.currentIndexChanged.connect(self._refresh)
        layout.addWidget(self.child_combo)

        self.status_card = Card()
        self.status_label = heading("", "h3")
        self.status_card.add(self.status_label)
        layout.addWidget(self.status_card)

        self.window_card = Card()
        self.window_label = QLabel("")
        self.window_label.setWordWrap(True)
        self.window_card.add(self.window_label)
        layout.addWidget(self.window_card)

        self.restriction_card = Card()
        self.restriction_card.add(small_label(self.i18n("dashboard.last_restriction")))
        self.restriction_value = QLabel("")
        self.restriction_value.setWordWrap(True)
        self.restriction_card.add(self.restriction_value)
        layout.addWidget(self.restriction_card)

        layout.addStretch(1)

        actions_row = QHBoxLayout()
        self.settings_button = QPushButton(self.i18n("common.settings"))
        self.settings_button.clicked.connect(self.open_settings)
        actions_row.addWidget(self.settings_button)

        self.reports_button = QPushButton(self.i18n("common.reports"))
        self.reports_button.setObjectName("secondary")
        self.reports_button.clicked.connect(self.open_reports)
        actions_row.addWidget(self.reports_button)
        layout.addLayout(actions_row)

    # -- Data loading -----------------------------------------------------

    def reload(self) -> None:
        """Recharge la liste des enfants depuis la BD (ex: après fermeture des Settings)."""
        previous_id = self.selected_child_id
        self.child_combo.blockSignals(True)
        self.child_combo.clear()
        session = get_session()
        try:
            children = session.query(Child).order_by(Child.name).all()
            for child in children:
                self.child_combo.addItem(child.name, child.id)
        finally:
            session.close()

        if previous_id is not None:
            index = self.child_combo.findData(previous_id)
            if index >= 0:
                self.child_combo.setCurrentIndex(index)
        self.child_combo.blockSignals(False)
        self._refresh()

    @property
    def selected_child_id(self):
        return self.child_combo.currentData()

    def _refresh(self) -> None:
        child_id = self.selected_child_id
        if child_id is None:
            self.status_label.setText(self.i18n("dashboard.no_children"))
            self.status_label.setObjectName("warning")
            self.status_label.style().unpolish(self.status_label)
            self.status_label.style().polish(self.status_label)
            self.window_label.setText("")
            self.restriction_value.setText("")
            self.settings_button.setEnabled(False)
            self.reports_button.setEnabled(False)
            return

        self.settings_button.setEnabled(True)
        self.reports_button.setEnabled(True)
        active = self._is_protection_active(child_id)
        self.status_label.setText(
            self.i18n("dashboard.protection_active" if active else "dashboard.protection_inactive")
        )
        self.status_label.setObjectName("success" if active else "warning")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

        self.window_label.setText(self._today_window_text(child_id))
        self.restriction_value.setText(self._last_restriction_text(child_id))

    def _is_protection_active(self, child_id: int) -> bool:
        session = get_session()
        try:
            has_time_rule = session.query(TimeRule).filter_by(child_id=child_id, enabled=True).count() > 0
            has_blocked_site = session.query(BlockedSite).filter_by(blocked=True).count() > 0
            return has_time_rule or has_blocked_site
        finally:
            session.close()

    def _today_window_text(self, child_id: int) -> str:
        today = datetime.now().weekday()
        session = get_session()
        try:
            rule = (
                session.query(TimeRule)
                .filter_by(child_id=child_id, day_of_week=today, enabled=True)
                .first()
            )
            # Extraire les valeurs pendant que la session est ouverte : après close(), les
            # attributs ne sont accessibles que par chance (tant qu'aucun commit ne les a
            # expirés) — mieux vaut ne pas dépendre de ce détail d'implémentation SQLAlchemy.
            window = (rule.start_hour, rule.end_hour) if rule is not None else None
        finally:
            session.close()
        if window is None:
            return self.i18n("dashboard.no_rule_today")
        start_hour, end_hour = window
        return self.i18n("dashboard.today_window").format(start_hour.strftime("%H:%M"), end_hour.strftime("%H:%M"))

    def _last_restriction_text(self, child_id: int) -> str:
        session = get_session()
        try:
            log = (
                session.query(ActivityLog)
                .filter((ActivityLog.child_id == child_id) | (ActivityLog.child_id.is_(None)))
                .order_by(ActivityLog.timestamp.desc())
                .first()
            )
            entry = (log.action, log.details, log.timestamp) if log is not None else None
        finally:
            session.close()
        if entry is None:
            return self.i18n("dashboard.no_restrictions")

        action, details, timestamp = entry
        time_str = timestamp.strftime("%H:%M")
        if action == "app_blocked":
            label = self.i18n("dashboard.restriction_app_blocked").format(details or "?")
        elif action == "time_limit_hit":
            label = self.i18n("dashboard.restriction_time_limit_hit")
        else:
            label = action
        return f"{label} ({time_str})"

    # -- Actions ------------------------------------------------------------

    def open_settings(self) -> None:
        from mintguard.gui.settings import SettingsWindow

        dialog = SettingsWindow(self.i18n, self.selected_child_id, self)
        dialog.exec()
        self.reload()

    def open_reports(self) -> None:
        from mintguard.gui.reports import ReportsWindow

        dialog = ReportsWindow(self.i18n, self.selected_child_id, self)
        dialog.exec()
