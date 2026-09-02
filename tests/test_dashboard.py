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
    assert screen.window_label.text() == "Libre aujourd'hui"


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
    assert screen.window_label.text() == "16:00 – 18:00"


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
    assert screen.status_label.text() == "Protection active"


def test_protection_inactive_when_no_rules_or_sites():
    make_child()
    screen = DashboardScreen(I18nLoader("fr"))
    assert screen.status_label.text() == "Protection inactive"


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
    assert screen.status_label.text() == "Protection active"


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


# "Ajouter un enfant" : trouvé en usage réel (voir SUIVI.md) que rien ne permettait d'ajouter
# un second enfant après l'onboarding initial. PIN-protégé comme Settings/Reports.


def test_open_add_child_blocked_when_pin_dialog_cancelled(monkeypatch):
    make_child()
    from mintguard.gui import add_child_dialog, dialogs

    monkeypatch.setattr(dialogs.PinDialog, "prompt", staticmethod(lambda i18n, parent=None: False))

    opened = []
    monkeypatch.setattr(
        add_child_dialog.AddChildDialog, "prompt", staticmethod(lambda i18n, parent=None: opened.append(True))
    )

    screen = DashboardScreen(I18nLoader("fr"))
    screen.open_add_child()

    assert opened == []


def test_open_add_child_opens_and_reloads_when_pin_dialog_accepted(monkeypatch):
    child_id = make_child("Alice", "alice")
    from mintguard.gui import add_child_dialog, dialogs

    monkeypatch.setattr(dialogs.PinDialog, "prompt", staticmethod(lambda i18n, parent=None: True))

    new_child_id = make_child("Bob", "bob")  # simule la création faite par le vrai dialogue
    monkeypatch.setattr(
        add_child_dialog.AddChildDialog, "prompt", staticmethod(lambda i18n, parent=None: new_child_id)
    )

    screen = DashboardScreen(I18nLoader("fr"))
    screen.open_add_child()

    assert screen.child_combo.count() == 2
    assert screen.selected_child_id == new_child_id
    assert child_id != new_child_id  # les deux enfants coexistent bien


def test_open_add_child_does_nothing_when_dialog_cancelled(monkeypatch):
    make_child()
    from mintguard.gui import add_child_dialog, dialogs

    monkeypatch.setattr(dialogs.PinDialog, "prompt", staticmethod(lambda i18n, parent=None: True))
    monkeypatch.setattr(add_child_dialog.AddChildDialog, "prompt", staticmethod(lambda i18n, parent=None: None))

    screen = DashboardScreen(I18nLoader("fr"))
    screen.open_add_child()

    assert screen.child_combo.count() == 1


# -- Carte d'activation du daemon (voir SUIVI.md, point 2 de la revue UX) ------------------


def test_daemon_card_hidden_when_daemon_active(monkeypatch):
    from mintguard.gui import dashboard

    monkeypatch.setattr(dashboard, "is_daemon_active", lambda: True)
    screen = DashboardScreen(I18nLoader("fr"))
    assert screen.daemon_card.isHidden() is True


def test_daemon_card_shown_when_daemon_inactive(monkeypatch):
    from mintguard.gui import dashboard

    monkeypatch.setattr(dashboard, "is_daemon_active", lambda: False)
    screen = DashboardScreen(I18nLoader("fr"))
    screen._refresh()
    assert screen.daemon_card.isHidden() is False


def test_activate_daemon_success_hides_card(monkeypatch):
    from mintguard.gui import dashboard

    monkeypatch.setattr(dashboard, "is_daemon_active", lambda: False)
    monkeypatch.setattr(dashboard, "start_daemon_via_polkit", lambda: True)
    screen = DashboardScreen(I18nLoader("fr"))
    screen._refresh()
    assert screen.daemon_card.isHidden() is False

    screen._activate_daemon()

    assert screen.daemon_card.isHidden() is True
    assert screen.daemon_activate_button.isEnabled() is True


def test_activate_daemon_failure_keeps_card_with_explanation(monkeypatch):
    from mintguard.gui import dashboard

    monkeypatch.setattr(dashboard, "is_daemon_active", lambda: False)
    monkeypatch.setattr(dashboard, "start_daemon_via_polkit", lambda: False)
    screen = DashboardScreen(I18nLoader("fr"))
    screen._refresh()

    screen._activate_daemon()

    assert screen.daemon_card.isHidden() is False
    assert "annulée" in screen.daemon_body.text() or "autorisée" in screen.daemon_body.text()


def test_activate_daemon_missing_pkexec_shows_unavailable_message(monkeypatch):
    from mintguard.gui import dashboard

    monkeypatch.setattr(dashboard, "is_daemon_active", lambda: False)
    monkeypatch.setattr(dashboard, "start_daemon_via_polkit", lambda: None)
    screen = DashboardScreen(I18nLoader("fr"))
    screen._refresh()

    screen._activate_daemon()

    assert "composant manquant" in screen.daemon_body.text()
