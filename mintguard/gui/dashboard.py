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
from datetime import time as dt_time

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

from mintguard.backend.usage_tracker import UsageTracker
from mintguard.db.database import get_session
from mintguard.db.models import ActivityLog, BlockedSite, Child, TimeRule
from mintguard.gui.widgets import Card, heading, small_label
from mintguard.locales.loader import I18nLoader
from mintguard.utils.formatters import format_duration, format_percentage, utc_to_local

# Cadence de rafraîchissement du Dashboard pendant qu'il reste affiché — même principe que le
# daemon (voir SUIVI.md, décision d'architecture Semaine 5) : la BD partagée tient lieu de canal
# GUI<->daemon, un délai de quelques secondes est imperceptible pour ce besoin.
_LIVE_REFRESH_INTERVAL_MS = 5000


class DashboardScreen(QWidget):
    """Écran 1 (Dashboard) — vue d'ensemble en un coup d'œil, cf. PROJECT_BRIEF.md 'Écrans Principaux'.

    Note d'architecture : le blocage de sites (BlockedSite) est global à la machine, pas par
    enfant (un seul résolveur DNS pour tout le poste) — seule la limite de temps (TimeRule) est
    propre à l'enfant sélectionné. Le statut « Protection: ACTIVE » reflète la présence de règles
    configurées en BD, pas un signal live du daemon (pas de bus D-Bus — voir SUIVI.md). Le temps
    utilisé aujourd'hui, lui, vient bien du daemon (`UsageTracker`, table `DailyUsage`) : un
    QTimer relit la BD toutes les `_LIVE_REFRESH_INTERVAL_MS` pour que la barre avance pendant
    que le parent regarde l'écran, sans canal IPC dédié.
    """

    def __init__(self, i18n: I18nLoader, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._usage_tracker = UsageTracker()
        self._build_ui()
        self.reload()

        self._live_refresh_timer = QTimer(self)
        self._live_refresh_timer.timeout.connect(self._refresh)
        self._live_refresh_timer.start(_LIVE_REFRESH_INTERVAL_MS)

    def _build_ui(self) -> None:
        # Thème "Néon" appliqué globalement (voir mintguard/main_gui.py, styles.py::DARK_COLORS).
        layout = QVBoxLayout(self)
        layout.addWidget(heading(self.i18n("dashboard.title"), "h1"))

        layout.addWidget(small_label(self.i18n("dashboard.child_select")))
        selector_row = QHBoxLayout()
        self.child_combo = QComboBox()
        self.child_combo.currentIndexChanged.connect(self._refresh)
        selector_row.addWidget(self.child_combo, stretch=1)

        self.add_child_button = QPushButton(self.i18n("dashboard.add_child"))
        self.add_child_button.setObjectName("secondary")
        self.add_child_button.clicked.connect(self.open_add_child)
        selector_row.addWidget(self.add_child_button)
        layout.addLayout(selector_row)

        self.status_card = Card()
        self.status_label = heading("", "h3")
        self.status_card.add(self.status_label)
        layout.addWidget(self.status_card)

        self.window_card = Card()
        self.window_label = QLabel("")
        self.window_label.setWordWrap(True)
        self.window_card.add(self.window_label)
        layout.addWidget(self.window_card)

        self.usage_card = Card()
        self.usage_card.add(small_label(self.i18n("dashboard.time_today")))
        self.usage_bar = QProgressBar()
        self.usage_bar.setTextVisible(False)
        self.usage_card.add(self.usage_bar)
        self.usage_value = QLabel("")
        self.usage_card.add(self.usage_value)
        layout.addWidget(self.usage_card)

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
            self.usage_card.hide()
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

        window = self._today_rule_window(child_id)
        self.window_label.setText(self._today_window_text(window))
        self._refresh_usage(child_id, window)
        self.restriction_value.setText(self._last_restriction_text(child_id))

    def _is_protection_active(self, child_id: int) -> bool:
        session = get_session()
        try:
            has_time_rule = session.query(TimeRule).filter_by(child_id=child_id, enabled=True).count() > 0
            has_blocked_site = session.query(BlockedSite).filter_by(blocked=True).count() > 0
            return has_time_rule or has_blocked_site
        finally:
            session.close()

    def _today_rule_window(self, child_id: int) -> tuple[dt_time, dt_time] | None:
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
            return (rule.start_hour, rule.end_hour) if rule is not None else None
        finally:
            session.close()

    def _today_window_text(self, window: tuple[dt_time, dt_time] | None) -> str:
        if window is None:
            return self.i18n("dashboard.no_rule_today")
        start_hour, end_hour = window
        return self.i18n("dashboard.today_window").format(start_hour.strftime("%H:%M"), end_hour.strftime("%H:%M"))

    def _refresh_usage(self, child_id: int, window: tuple[dt_time, dt_time] | None) -> None:
        """Barre de progression du temps utilisé aujourd'hui — seulement quand une plage horaire
        est définie pour aujourd'hui (sinon pas de "maximum" auquel comparer, cf. accès libre)."""
        if window is None:
            self.usage_card.hide()
            return

        start_hour, end_hour = window
        limit_seconds = self._seconds_since_midnight(end_hour) - self._seconds_since_midnight(start_hour)
        used_seconds = self._usage_tracker.get_seconds_used_today(child_id)

        self.usage_card.show()
        self.usage_bar.setValue(format_percentage(used_seconds, limit_seconds))
        self.usage_value.setText(
            self.i18n("dashboard.time_used_of_limit").format(
                format_duration(used_seconds), format_duration(limit_seconds)
            )
        )

    @staticmethod
    def _seconds_since_midnight(value: dt_time) -> int:
        return value.hour * 3600 + value.minute * 60 + value.second

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
        time_str = utc_to_local(timestamp).strftime("%H:%M")
        if action == "app_blocked":
            label = self.i18n("dashboard.restriction_app_blocked").format(details or "?")
        elif action == "time_limit_hit":
            label = self.i18n("dashboard.restriction_time_limit_hit")
        else:
            label = action
        return f"{label} ({time_str})"

    # -- Actions ------------------------------------------------------------

    def open_add_child(self) -> None:
        from mintguard.gui.add_child_dialog import AddChildDialog
        from mintguard.gui.dialogs import PinDialog

        if not PinDialog.prompt(self.i18n, self):
            return
        new_child_id = AddChildDialog.prompt(self.i18n, self)
        if new_child_id is None:
            return
        self.reload()
        index = self.child_combo.findData(new_child_id)
        if index >= 0:
            self.child_combo.setCurrentIndex(index)

    def open_settings(self) -> None:
        from mintguard.gui.dialogs import PinDialog
        from mintguard.gui.settings import SettingsWindow

        if not PinDialog.prompt(self.i18n, self):
            return
        dialog = SettingsWindow(self.i18n, self.selected_child_id, self)
        dialog.exec()
        self.reload()

    def open_reports(self) -> None:
        from mintguard.gui.dialogs import PinDialog
        from mintguard.gui.reports import ReportsWindow

        if not PinDialog.prompt(self.i18n, self):
            return
        dialog = ReportsWindow(self.i18n, self.selected_child_id, self)
        dialog.exec()
