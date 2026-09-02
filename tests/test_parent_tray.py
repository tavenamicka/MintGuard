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

"""ParentTray : confirme visuellement que MintGuard tourne (demande utilisateur apres
l'installation du .deb, voir SUIVI.md), mais doit s'auto-desactiver silencieusement pour un
compte enfant (deja couvert par ChildTray - aucun marqueur OS pour distinguer les deux)."""

from pathlib import Path

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication  # noqa: E402

import mintguard.parent_tray as parent_tray  # noqa: E402
from mintguard.parent_tray import ParentTray  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def qapp():
    return QApplication.instance() or QApplication([])


def test_quits_when_account_is_a_child(monkeypatch, qapp):
    monkeypatch.setattr(parent_tray, "query_status", lambda: {"is_child": True, "minutes_remaining": 5})
    quit_calls = []
    monkeypatch.setattr(qapp, "quit", lambda: quit_calls.append(True))

    tray = ParentTray(qapp)
    tray.poll()

    assert quit_calls == [True]
    assert not tray.tray.isVisible()


def test_shows_active_tooltip_and_icon_when_daemon_reachable(monkeypatch, qapp):
    monkeypatch.setattr(parent_tray, "query_status", lambda: {"is_child": False})

    tray = ParentTray(qapp)
    tray.poll()

    assert tray.tray.isVisible()
    assert tray.tray.toolTip() == tray._("parent_tray.tooltip_active")
    assert tray.tray.icon().cacheKey() == tray._icon_active.cacheKey()


def test_shows_inactive_tooltip_and_icon_when_daemon_unreachable(monkeypatch, qapp):
    monkeypatch.setattr(parent_tray, "query_status", lambda: None)

    tray = ParentTray(qapp)
    tray.poll()

    assert tray.tray.isVisible()
    assert tray.tray.toolTip() == tray._("parent_tray.tooltip_inactive")
    assert tray.tray.icon().cacheKey() == tray._icon_inactive.cacheKey()


def test_no_notification_on_first_poll(monkeypatch, qapp):
    monkeypatch.setattr(parent_tray, "query_status", lambda: {"is_child": False})
    tray = ParentTray(qapp)
    messages = []
    monkeypatch.setattr(tray.tray, "showMessage", lambda title, msg, icon: messages.append(msg))

    tray.poll()

    assert messages == []


def test_notifies_once_when_daemon_goes_down_then_back_up(monkeypatch, qapp):
    tray = ParentTray(qapp)
    messages = []
    monkeypatch.setattr(tray.tray, "showMessage", lambda title, msg, icon: messages.append(msg))

    monkeypatch.setattr(parent_tray, "query_status", lambda: {"is_child": False})
    tray.poll()
    assert messages == []  # premier poll, pas de changement d'etat a signaler

    monkeypatch.setattr(parent_tray, "query_status", lambda: None)
    tray.poll()
    assert len(messages) == 1  # devient inactif

    tray.poll()
    assert len(messages) == 1  # meme etat, pas de nouvelle notification

    monkeypatch.setattr(parent_tray, "query_status", lambda: {"is_child": False})
    tray.poll()
    assert len(messages) == 2  # redevient actif


def test_start_actually_exits_the_event_loop_for_child_account(monkeypatch, qapp):
    """Meme regression que ChildTray.start() (voir test_child_tray.py) : le premier poll()
    doit etre differe via QTimer.singleShot pour qu'un quit() precoce ne soit pas ignore."""
    from PyQt6.QtCore import QTimer

    monkeypatch.setattr(parent_tray, "query_status", lambda: {"is_child": True})
    tray = ParentTray(qapp)

    QTimer.singleShot(2000, qapp.quit)
    tray.start()
    exit_code = qapp.exec()

    assert exit_code == 0


def test_left_click_opens_main_gui(monkeypatch, qapp):
    from pathlib import Path

    from PyQt6.QtWidgets import QSystemTrayIcon

    monkeypatch.setattr(parent_tray, "query_status", lambda: {"is_child": False})
    tray = ParentTray(qapp)
    calls = []
    monkeypatch.setattr(parent_tray.QProcess, "startDetached", staticmethod(lambda *a: calls.append(a)))

    tray._on_activated(QSystemTrayIcon.ActivationReason.Trigger)

    expected_path = str(Path(parent_tray.sys.executable).parent / "mintguard")
    assert calls == [(expected_path, [])]


def test_icon_files_exist_and_are_distinct():
    active = parent_tray._ICON_PATH_ACTIVE
    inactive = parent_tray._ICON_PATH_INACTIVE

    assert Path(active).is_file()
    assert Path(inactive).is_file()
    assert active != inactive


def test_right_click_does_not_open_main_gui(monkeypatch, qapp):
    from PyQt6.QtWidgets import QSystemTrayIcon

    monkeypatch.setattr(parent_tray, "query_status", lambda: {"is_child": False})
    tray = ParentTray(qapp)
    calls = []
    monkeypatch.setattr(parent_tray.QProcess, "startDetached", staticmethod(lambda *a: calls.append(a)))

    tray._on_activated(QSystemTrayIcon.ActivationReason.Context)

    assert calls == []
