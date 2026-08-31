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

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication  # noqa: E402

from mintguard.db.database import get_session, init_db  # noqa: E402
from mintguard.db.models import ParentConfig  # noqa: E402
from mintguard.gui.dashboard import DashboardScreen  # noqa: E402
from mintguard.gui.main_window import MainWindow  # noqa: E402
from mintguard.gui.onboarding import OnboardingWizard  # noqa: E402


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


@pytest.fixture(scope="module", autouse=True)
def qapp():
    return QApplication.instance() or QApplication([])


def test_shows_onboarding_when_not_completed():
    window = MainWindow()
    assert isinstance(window.stack.currentWidget(), OnboardingWizard)
    assert window.settings_action.isEnabled() is False
    assert window.reports_action.isEnabled() is False
    window.close()


def test_shows_dashboard_when_onboarding_already_done():
    session = get_session()
    try:
        session.add(ParentConfig(key="onboarding_complete", value="1"))
        session.commit()
    finally:
        session.close()

    window = MainWindow()
    assert isinstance(window.stack.currentWidget(), DashboardScreen)
    assert window.settings_action.isEnabled() is True
    assert window.reports_action.isEnabled() is True
    window.close()


def test_finishing_onboarding_switches_to_dashboard():
    window = MainWindow()
    wizard = window.stack.currentWidget()
    assert isinstance(wizard, OnboardingWizard)

    wizard.finished.emit()

    assert isinstance(window.stack.currentWidget(), DashboardScreen)
    assert window.settings_action.isEnabled() is True
    assert window.reports_action.isEnabled() is True
    window.close()


def test_menu_settings_action_opens_dashboard_settings(monkeypatch):
    session = get_session()
    try:
        session.add(ParentConfig(key="onboarding_complete", value="1"))
        session.commit()
    finally:
        session.close()

    window = MainWindow()
    calls = []
    monkeypatch.setattr(window.dashboard, "open_settings", lambda: calls.append("settings"))
    window.settings_action.trigger()
    assert calls == ["settings"]
    window.close()


def test_menu_reports_action_opens_dashboard_reports(monkeypatch):
    session = get_session()
    try:
        session.add(ParentConfig(key="onboarding_complete", value="1"))
        session.commit()
    finally:
        session.close()

    window = MainWindow()
    calls = []
    monkeypatch.setattr(window.dashboard, "open_reports", lambda: calls.append("reports"))
    window.reports_action.trigger()
    assert calls == ["reports"]
    window.close()
