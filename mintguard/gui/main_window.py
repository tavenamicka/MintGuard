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

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QLabel, QMainWindow, QStackedWidget

from mintguard.config import get_config
from mintguard.db.database import get_session
from mintguard.db.models import ParentConfig
from mintguard.gui.onboarding import OnboardingWizard
from mintguard.gui.styles import build_stylesheet
from mintguard.locales.loader import get_i18n

DASHBOARD_PAGE_INDEX = "dashboard"


class MainWindow(QMainWindow):
    """Fenêtre principale : affiche l'onboarding au premier lancement, puis le tableau de bord."""

    def __init__(self):
        super().__init__()
        lang = get_config().get("app.language", "auto")
        self.i18n = get_i18n(None if lang == "auto" else lang)

        self.setWindowTitle(self.i18n("app.name"))
        self.setMinimumSize(480, 640)
        self.setStyleSheet(build_stylesheet())

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self._build_menu()

        if self._needs_onboarding():
            self._show_onboarding()
        else:
            self._show_dashboard_placeholder()

    def _build_menu(self) -> None:
        menu = self.menuBar().addMenu(self.i18n("app.name"))

        help_action = QAction(self.i18n("app_shell.menu_help"), self)
        help_action.triggered.connect(self._show_help)
        menu.addAction(help_action)

        quit_action = QAction(self.i18n("app_shell.menu_quit"), self)
        quit_action.triggered.connect(self.close)
        menu.addAction(quit_action)

    def _show_help(self) -> None:
        from mintguard.gui.dialogs import HelpDialog

        dialog = HelpDialog(self.i18n("help.how_it_works"), self.i18n("help.how_it_works_explanation"), self)
        dialog.exec()

    def _needs_onboarding(self) -> bool:
        session = get_session()
        try:
            config = session.query(ParentConfig).filter_by(key="onboarding_complete").first()
            return config is None or config.value != "1"
        finally:
            session.close()

    def _show_onboarding(self) -> None:
        wizard = OnboardingWizard(self.i18n)
        wizard.finished.connect(self._on_onboarding_finished)
        self.stack.addWidget(wizard)
        self.stack.setCurrentWidget(wizard)

    def _on_onboarding_finished(self) -> None:
        self._show_dashboard_placeholder()

    def _show_dashboard_placeholder(self) -> None:
        # Le vrai Dashboard arrive en Phase 2 Semaine 4 (voir SUIVI.md).
        label = QLabel(self.i18n("app_shell.dashboard_placeholder"))
        label.setObjectName("h2")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stack.addWidget(label)
        self.stack.setCurrentWidget(label)
