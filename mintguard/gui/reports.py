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

from collections import Counter
from datetime import datetime, timedelta

from PyQt6.QtWidgets import QComboBox, QDialog, QListWidget, QPushButton, QVBoxLayout

from mintguard.db.database import get_session
from mintguard.db.models import ActivityLog, Child
from mintguard.gui.widgets import Card, heading, small_label
from mintguard.locales.loader import I18nLoader

REPORT_WINDOW_DAYS = 7


class ReportsWindow(QDialog):
    """Écran 3 (Rapports) — synthèse des 7 derniers jours par enfant, cf. PROJECT_BRIEF.md.

    Ne montre que des données réellement mesurées (occurrences de blocage, nombre de fois où la
    limite de temps a été atteinte) : pas de « temps utilisé / temps limite » car MintGuard ne
    trace pas encore la durée effective des sessions (aucun mécanisme de suivi en continu —
    seul le franchissement d'une limite est journalisé). Voir SUIVI.md.
    """

    def __init__(self, i18n: I18nLoader, initial_child_id: int | None = None, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.setWindowTitle(self.i18n("reports.title"))
        self.setMinimumSize(420, 560)

        layout = QVBoxLayout(self)
        layout.addWidget(heading(self.i18n("reports.title"), "h1"))
        layout.addWidget(small_label(self.i18n("reports.period_week")))

        layout.addWidget(small_label(self.i18n("dashboard.child_select")))
        self.child_combo = QComboBox()
        self.child_combo.currentIndexChanged.connect(self._refresh)
        layout.addWidget(self.child_combo)

        self.time_limit_card = Card()
        self.time_limit_label = small_label("")
        self.time_limit_label.setWordWrap(True)
        self.time_limit_card.add(self.time_limit_label)
        layout.addWidget(self.time_limit_card)

        self.blocks_card = Card()
        self.blocks_card.add(small_label(self.i18n("reports.blocked_apps_title")))
        self.blocks_list = QListWidget()
        self.blocks_card.add(self.blocks_list)
        layout.addWidget(self.blocks_card)

        close_button = QPushButton(self.i18n("common.close"))
        close_button.setObjectName("secondary")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self._load_children(initial_child_id)

    def _load_children(self, initial_child_id: int | None) -> None:
        session = get_session()
        try:
            children = [(c.id, c.name) for c in session.query(Child).order_by(Child.name).all()]
        finally:
            session.close()

        self.child_combo.blockSignals(True)
        self.child_combo.clear()
        for child_id, name in children:
            self.child_combo.addItem(name, child_id)
        if initial_child_id is not None:
            index = self.child_combo.findData(initial_child_id)
            if index >= 0:
                self.child_combo.setCurrentIndex(index)
        self.child_combo.blockSignals(False)
        self._refresh()

    def _refresh(self) -> None:
        child_id = self.child_combo.currentData()
        if child_id is None:
            self.time_limit_label.setText(self.i18n("dashboard.no_children"))
            self.blocks_list.clear()
            return

        cutoff = datetime.now() - timedelta(days=REPORT_WINDOW_DAYS)
        session = get_session()
        try:
            entries = [
                (log.action, log.details)
                for log in session.query(ActivityLog)
                .filter(
                    (ActivityLog.child_id == child_id) | (ActivityLog.child_id.is_(None)),
                    ActivityLog.timestamp >= cutoff,
                )
                .all()
            ]
        finally:
            session.close()

        time_limit_hits = sum(1 for action, _ in entries if action == "time_limit_hit")
        self.time_limit_label.setText(
            self.i18n("reports.time_limit_hits").format(time_limit_hits)
            if time_limit_hits > 0
            else self.i18n("reports.no_time_limit_hits")
        )

        app_blocks = Counter(details or "?" for action, details in entries if action == "app_blocked")
        self.blocks_list.clear()
        if not app_blocks:
            self.blocks_list.addItem(self.i18n("reports.no_blocks"))
        else:
            for app_name, count in sorted(app_blocks.items(), key=lambda item: -item[1]):
                self.blocks_list.addItem(f"{app_name} — {self.i18n('reports.occurrences').format(count)}")
