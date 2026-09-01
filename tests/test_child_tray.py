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

"""ChildTray : purement informatif (voir status_server.py pour l'application des règles),
mais doit s'auto-désactiver silencieusement pour un compte non-enfant (déployé en autostart
pour toutes les sessions, y compris le parent - aucun marqueur OS pour distinguer les deux,
voir SUIVI.md)."""

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication  # noqa: E402

import mintguard.child_tray as child_tray  # noqa: E402
from mintguard.child_tray import ChildTray  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def qapp():
    return QApplication.instance() or QApplication([])


def test_quits_when_account_is_not_a_child(monkeypatch, qapp):
    monkeypatch.setattr(child_tray, "query_status", lambda: {"is_child": False})
    quit_calls = []
    monkeypatch.setattr(qapp, "quit", lambda: quit_calls.append(True))

    tray = ChildTray(qapp)
    tray.poll()

    assert quit_calls == [True]
    assert not tray.tray.isVisible()


def test_daemon_unreachable_does_not_crash_or_quit(monkeypatch, qapp):
    monkeypatch.setattr(child_tray, "query_status", lambda: None)
    quit_calls = []
    monkeypatch.setattr(qapp, "quit", lambda: quit_calls.append(True))

    ChildTray(qapp).poll()

    assert quit_calls == []


def test_shows_tray_and_tooltip_for_child_account(monkeypatch, qapp):
    monkeypatch.setattr(
        child_tray, "query_status", lambda: {"is_child": True, "minutes_remaining": 42, "recent_blocks": []}
    )

    tray = ChildTray(qapp)
    tray.poll()

    assert tray.tray.isVisible()
    assert "42" in tray.tray.toolTip()


def test_warns_once_per_threshold_crossed(monkeypatch, qapp):
    tray = ChildTray(qapp)
    tray.thresholds = [10, 5]
    messages = []
    monkeypatch.setattr(tray.tray, "showMessage", lambda title, msg, icon: messages.append(msg))

    monkeypatch.setattr(
        child_tray, "query_status", lambda: {"is_child": True, "minutes_remaining": 8, "recent_blocks": []}
    )
    tray.poll()
    assert len(messages) == 1  # seuil des 10 minutes franchi

    tray.poll()
    assert len(messages) == 1  # meme statut, pas de nouvel avertissement

    monkeypatch.setattr(
        child_tray, "query_status", lambda: {"is_child": True, "minutes_remaining": 3, "recent_blocks": []}
    )
    tray.poll()
    assert len(messages) == 2  # seuil des 5 minutes franchi


def test_start_actually_exits_the_event_loop_for_non_child_account(monkeypatch, qapp):
    """Régression : `start()` appelait `poll()` directement, donc `QApplication.quit()`
    s'exécutait avant que `app.exec()` ne démarre la boucle d'événements - un `quit()` appelé
    trop tôt est ignoré (constaté en conditions réelles, voir SUIVI.md), et le process ne se
    terminait jamais. `start()` doit différer le premier `poll()` via `QTimer.singleShot`."""
    from PyQt6.QtCore import QTimer

    monkeypatch.setattr(child_tray, "query_status", lambda: {"is_child": False})
    tray = ChildTray(qapp)

    # Filet de securite : si la regression revient, app.exec() ne rendrait jamais la main.
    QTimer.singleShot(2000, qapp.quit)
    tray.start()
    exit_code = qapp.exec()

    assert exit_code == 0


def test_notifies_new_blocked_app_once(monkeypatch, qapp):
    tray = ChildTray(qapp)
    messages = []
    monkeypatch.setattr(tray.tray, "showMessage", lambda title, msg, icon: messages.append(msg))

    status = {"is_child": True, "minutes_remaining": None, "recent_blocks": ["discord"]}
    monkeypatch.setattr(child_tray, "query_status", lambda: status)

    tray.poll()
    tray.poll()

    assert len(messages) == 1
    assert "discord" in messages[0]
