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

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication  # noqa: E402

from mintguard.db.database import get_session, init_db  # noqa: E402
from mintguard.db.models import ActivityLog, BlockedSite, Child, TimeRule  # noqa: E402
from mintguard.gui.dashboard import DashboardScreen  # noqa: E402
from mintguard.locales.loader import I18nLoader  # noqa: E402


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


@pytest.fixture(scope="module", autouse=True)
def qapp():
    return QApplication.instance() or QApplication([])


def make_child(name="Alice", username="alice") -> int:
    session = get_session()
    try:
        child = Child(name=name, username=username, age=10)
        session.add(child)
        session.commit()
        return child.id
    finally:
        session.close()


def test_no_children_shows_message():
    screen = DashboardScreen(I18nLoader("fr"))
    assert screen.selected_child_id is None
    assert screen.status_label.text() == "Aucun enfant configuré. Relancez l'assistant de configuration."
    assert screen.settings_button.isEnabled() is False
    assert screen.reports_button.isEnabled() is False


def test_reports_button_enabled_with_child():
    make_child()
    screen = DashboardScreen(I18nLoader("fr"))
    assert screen.reports_button.isEnabled() is True


def test_child_combo_populated():
    make_child("Alice", "alice")
    make_child("Bob", "bob")
    screen = DashboardScreen(I18nLoader("fr"))
    assert screen.child_combo.count() == 2


def test_no_rule_today_shows_free_access():
    make_child()
    screen = DashboardScreen(I18nLoader("fr"))
    assert screen.window_label.text() == "Accès libre aujourd'hui"


def test_rule_today_shows_window():
    child_id = make_child()
    today = datetime.now().weekday()
    session = get_session()
    try:
        session.add(
            TimeRule(child_id=child_id, day_of_week=today, start_hour=dt_time(16, 0), end_hour=dt_time(18, 0))
        )
        session.commit()
    finally:
        session.close()

    screen = DashboardScreen(I18nLoader("fr"))
    assert screen.window_label.text() == "Aujourd'hui : accès autorisé de 16:00 à 18:00"


def test_protection_active_when_time_rule_exists():
    child_id = make_child()
    today = datetime.now().weekday()
    session = get_session()
    try:
        session.add(
            TimeRule(child_id=child_id, day_of_week=today, start_hour=dt_time(16, 0), end_hour=dt_time(18, 0))
        )
        session.commit()
    finally:
        session.close()

    screen = DashboardScreen(I18nLoader("fr"))
    assert screen.status_label.text() == "Protection: ACTIVE ✓"


def test_protection_inactive_when_no_rules_or_sites():
    make_child()
    screen = DashboardScreen(I18nLoader("fr"))
    assert screen.status_label.text() == "Protection: INACTIVE"


def test_last_restriction_shows_app_blocked():
    child_id = make_child()
    session = get_session()
    try:
        session.add(ActivityLog(child_id=child_id, action="app_blocked", details="discord"))
        session.commit()
    finally:
        session.close()

    screen = DashboardScreen(I18nLoader("fr"))
    assert screen.restriction_value.text().startswith("Application bloquée : discord")


def test_last_restriction_defaults_to_none():
    make_child()
    screen = DashboardScreen(I18nLoader("fr"))
    assert screen.restriction_value.text() == "Aucune restriction ce jour"


def test_protection_active_from_global_blocked_site():
    make_child()
    session = get_session()
    try:
        session.add(BlockedSite(domain="tiktok.com", category="social", blocked=True))
        session.commit()
    finally:
        session.close()

    screen = DashboardScreen(I18nLoader("fr"))
    assert screen.status_label.text() == "Protection: ACTIVE ✓"


# Trouvé à l'audit de sécurité (voir SUIVI.md) : Settings/Reports s'ouvraient sans jamais
# demander le PIN parent. Vérifie que PinDialog.prompt() est bien consulté avant d'ouvrir
# l'un ou l'autre, et que son résultat est respecté.


def test_open_settings_blocked_when_pin_dialog_cancelled(monkeypatch):
    make_child()
    from mintguard.gui import dialogs, settings as settings_module

    monkeypatch.setattr(dialogs.PinDialog, "prompt", staticmethod(lambda i18n, parent=None: False))

    opened = []

    class FakeSettingsWindow:
        def __init__(self, *args, **kwargs):
            opened.append(True)

        def exec(self):
            return None

    monkeypatch.setattr(settings_module, "SettingsWindow", FakeSettingsWindow)

    screen = DashboardScreen(I18nLoader("fr"))
    screen.open_settings()

    assert opened == []


def test_open_settings_opens_when_pin_dialog_accepted(monkeypatch):
    make_child()
    from mintguard.gui import dialogs, settings as settings_module

    monkeypatch.setattr(dialogs.PinDialog, "prompt", staticmethod(lambda i18n, parent=None: True))

    opened = []

    class FakeSettingsWindow:
        def __init__(self, *args, **kwargs):
            opened.append(True)

        def exec(self):
            return None

    monkeypatch.setattr(settings_module, "SettingsWindow", FakeSettingsWindow)

    screen = DashboardScreen(I18nLoader("fr"))
    screen.open_settings()

    assert opened == [True]


def test_open_reports_blocked_when_pin_dialog_cancelled(monkeypatch):
    make_child()
    from mintguard.gui import dialogs, reports as reports_module

    monkeypatch.setattr(dialogs.PinDialog, "prompt", staticmethod(lambda i18n, parent=None: False))

    opened = []

    class FakeReportsWindow:
        def __init__(self, *args, **kwargs):
            opened.append(True)

        def exec(self):
            return None

    monkeypatch.setattr(reports_module, "ReportsWindow", FakeReportsWindow)

    screen = DashboardScreen(I18nLoader("fr"))
    screen.open_reports()

    assert opened == []


def test_open_reports_opens_when_pin_dialog_accepted(monkeypatch):
    make_child()
    from mintguard.gui import dialogs, reports as reports_module

    monkeypatch.setattr(dialogs.PinDialog, "prompt", staticmethod(lambda i18n, parent=None: True))

    opened = []

    class FakeReportsWindow:
        def __init__(self, *args, **kwargs):
            opened.append(True)

        def exec(self):
            return None

    monkeypatch.setattr(reports_module, "ReportsWindow", FakeReportsWindow)

    screen = DashboardScreen(I18nLoader("fr"))
    screen.open_reports()

    assert opened == [True]
