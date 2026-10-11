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
pour toutes les sessions, y compris le parent - aucun marqueur OS pour distinguer les deux)."""

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon  # noqa: E402

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
    trop tôt est ignoré (constaté en conditions réelles), et le process ne se
    terminait jamais. `start()` doit différer le premier `poll()` via `QTimer.singleShot`."""
    from PyQt6.QtCore import QTimer

    monkeypatch.setattr(child_tray, "query_status", lambda: {"is_child": False})
    tray = ChildTray(qapp)

    # Filet de securite : si la regression revient, app.exec() ne rendrait jamais la main.
    QTimer.singleShot(2000, qapp.quit)
    tray.start()
    exit_code = qapp.exec()

    assert exit_code == 0


def test_grace_period_shows_countdown_overlay(monkeypatch, qapp):
    tray = ChildTray(qapp)
    monkeypatch.setattr(
        child_tray,
        "query_status",
        lambda: {"is_child": True, "minutes_remaining": 0, "grace_seconds_remaining": 45, "recent_blocks": []},
    )

    tray.poll()

    assert tray.grace_overlay.isVisible()
    assert "45" in tray.grace_overlay._body.text()


def test_grace_overlay_hides_once_grace_clears(monkeypatch, qapp):
    """Le parent corrige les réglages (ou un nouveau jour démarre) pendant la grâce : l'écran
    de compte à rebours doit disparaître, pas rester affiché indéfiniment."""
    tray = ChildTray(qapp)
    monkeypatch.setattr(
        child_tray,
        "query_status",
        lambda: {"is_child": True, "minutes_remaining": 0, "grace_seconds_remaining": 10, "recent_blocks": []},
    )
    tray.poll()
    assert tray.grace_overlay.isVisible()

    monkeypatch.setattr(
        child_tray,
        "query_status",
        lambda: {"is_child": True, "minutes_remaining": 30, "grace_seconds_remaining": None, "recent_blocks": []},
    )
    tray.poll()

    assert not tray.grace_overlay.isVisible()


def test_grace_countdown_ticks_down_locally_between_polls(monkeypatch, qapp):
    tray = ChildTray(qapp)
    monkeypatch.setattr(
        child_tray,
        "query_status",
        lambda: {"is_child": True, "minutes_remaining": 0, "grace_seconds_remaining": 30, "recent_blocks": []},
    )
    tray.poll()
    assert tray._grace_seconds_left == 30

    tray._tick_grace_countdown()

    assert tray._grace_seconds_left == 29
    assert "29" in tray.grace_overlay._body.text()


def test_warning_threshold_also_shows_a_banner(monkeypatch, qapp):
    """Le popup systray n'est pas garanti visible selon le bureau (voir manuel utilisateur) -
    le bandeau doit s'afficher en plus, pas seulement le popup."""
    tray = ChildTray(qapp)
    tray.thresholds = [5]
    monkeypatch.setattr(tray.tray, "showMessage", lambda title, msg, icon: None)
    monkeypatch.setattr(
        child_tray, "query_status", lambda: {"is_child": True, "minutes_remaining": 5, "recent_blocks": []}
    )

    tray.poll()

    assert tray.banner.isVisible()


def test_click_opens_status_window_with_time_and_blocked_items(monkeypatch, qapp):
    """Constat réel sur Cinnamon (compte enfant) : un clic sur l'icône ne montrait rien. La
    bulle de notification est remplacée par une fenêtre, avec ce qui est bloqué."""
    status = {
        "is_child": True,
        "minutes_remaining": 17,
        "recent_blocks": [],
        "blocked_apps": [
            {"name": "discord", "budget_minutes": None, "remaining_minutes": None},
            {"name": "steam", "budget_minutes": 60, "remaining_minutes": 25},
        ],
        "blocked_sites": [{"name": "tiktok.com", "budget_minutes": 30, "remaining_minutes": 0}],
        "last_block_today": "discord",
    }
    monkeypatch.setattr(child_tray, "query_status", lambda: status)
    tray = ChildTray(qapp)
    tray._on_tray_activated(QSystemTrayIcon.ActivationReason.Trigger)

    text = tray.status_window._body.text()
    assert tray.status_window.isHidden() is False
    assert "17" in text
    assert "discord" in text and "steam" in text and "25" in text
    assert "tiktok.com" in text
    assert tray._("child_tray.status_quota_used_up").format("tiktok.com") in text
    tray.status_window.hide()


def test_click_shows_no_limit_when_no_rule_today(monkeypatch, qapp):
    monkeypatch.setattr(child_tray, "query_status", lambda: {"is_child": True, "minutes_remaining": None})
    tray = ChildTray(qapp)
    tray._on_tray_activated(QSystemTrayIcon.ActivationReason.Trigger)
    assert tray._("child_tray.status_no_limit") in tray.status_window._body.text()
    tray.status_window.hide()


def test_click_when_daemon_unreachable_says_so(monkeypatch, qapp):
    monkeypatch.setattr(child_tray, "query_status", lambda: None)
    tray = ChildTray(qapp)
    tray._on_tray_activated(QSystemTrayIcon.ActivationReason.Trigger)
    assert tray.status_window._body.text() == tray._("child_tray.status_unavailable")
    tray.status_window.hide()


def test_status_window_escapes_names():
    window = child_tray._StatusWindow(child_tray.get_i18n())
    text = window.text_for(
        {"is_child": True, "minutes_remaining": 5, "blocked_apps": [{"name": "<b>x</b>", "budget_minutes": None}]}
    )
    assert "<b>x</b>" not in text and "&lt;b&gt;x&lt;/b&gt;" in text


def test_query_status_reads_long_responses(tmp_path, monkeypatch):
    """Une réponse de plus de 4 Ko était tronquée et passait pour un daemon injoignable."""
    import json
    import socket
    import threading

    path = str(tmp_path / "s.sock")
    payload = {"is_child": True, "blocked_sites": [{"name": f"site{i}.example.com"} for i in range(500)]}
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(path)
    server.listen(1)

    def serve():
        conn, _ = server.accept()
        conn.recv(4096)
        conn.sendall((json.dumps(payload) + "\n").encode())
        conn.close()

    thread = threading.Thread(target=serve)
    thread.start()
    monkeypatch.setattr(child_tray, "SOCKET_PATH", path)
    try:
        assert child_tray.query_status() == payload
    finally:
        thread.join(timeout=5)
        server.close()


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


def test_warnings_rearm_when_parent_extends_time(monkeypatch, qapp):
    tray = child_tray.ChildTray(qapp)
    shown = []
    monkeypatch.setattr(tray.tray, "showMessage", lambda title, msg, icon: shown.append(msg))
    monkeypatch.setattr(tray.banner, "show_message", lambda msg: None)

    tray._warn_if_threshold_crossed(4)   # paliers 10 et 5 franchis
    tray._warn_if_threshold_crossed(30)  # le parent rallonge
    tray._warn_if_threshold_crossed(9)   # le palier 10 doit de nouveau prévenir
    assert len(shown) == 3
