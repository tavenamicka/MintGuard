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

from mintguard.backend.process_monitor import ProcessMonitor
from mintguard.db.database import get_session, init_db
from mintguard.db.models import ActivityLog, BlockedApp, Child


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


def add_blocked_app(name: str) -> None:
    session = get_session()
    try:
        session.add(BlockedApp(app_name=name, enabled=True))
        session.commit()
    finally:
        session.close()


def add_child(name: str, username: str) -> int:
    session = get_session()
    try:
        child = Child(name=name, username=username)
        session.add(child)
        session.commit()
        return child.id
    finally:
        session.close()


class FakeProcess:
    def __init__(self, pid: int, name: str, username: str | None):
        self.info = {"pid": pid, "name": name, "username": username}
        self.killed = False

    def kill(self):
        self.killed = True


def test_kills_blocked_app_running_under_child_account(monkeypatch):
    add_blocked_app("discord")
    add_child("Test", "mintguard-test-child")

    procs = [FakeProcess(1, "discord", "mintguard-test-child")]
    monkeypatch.setattr("mintguard.backend.process_monitor.psutil.process_iter", lambda *_: procs)

    killed = ProcessMonitor().check_and_kill()

    assert killed == ["discord"]
    assert procs[0].killed is True


def test_does_not_kill_same_named_process_under_parent_account(monkeypatch):
    """Trouvé à l'audit de sécurité (voir SUIVI.md) : sans filtrage par utilisateur, un
    processus du même nom tournant sous le compte parent (ou tout autre compte du système)
    était tué aussi, dommage collatéral non intentionnel."""
    add_blocked_app("discord")
    add_child("Test", "mintguard-test-child")

    procs = [FakeProcess(1, "discord", "latitude")]
    monkeypatch.setattr("mintguard.backend.process_monitor.psutil.process_iter", lambda *_: procs)

    killed = ProcessMonitor().check_and_kill()

    assert killed == []
    assert procs[0].killed is False


def test_ignores_non_blocked_app_names(monkeypatch):
    add_blocked_app("discord")
    add_child("Test", "mintguard-test-child")

    procs = [FakeProcess(1, "firefox", "mintguard-test-child")]
    monkeypatch.setattr("mintguard.backend.process_monitor.psutil.process_iter", lambda *_: procs)

    killed = ProcessMonitor().check_and_kill()

    assert killed == []
    assert procs[0].killed is False


def test_no_children_configured_kills_nothing(monkeypatch):
    add_blocked_app("discord")

    procs = [FakeProcess(1, "discord", "latitude")]
    monkeypatch.setattr("mintguard.backend.process_monitor.psutil.process_iter", lambda *_: procs)

    killed = ProcessMonitor().check_and_kill()

    assert killed == []
    assert procs[0].killed is False


def test_logs_activity_with_correct_child_id(monkeypatch):
    add_blocked_app("discord")
    child_id = add_child("Test", "mintguard-test-child")

    procs = [FakeProcess(1, "discord", "mintguard-test-child")]
    monkeypatch.setattr("mintguard.backend.process_monitor.psutil.process_iter", lambda *_: procs)

    ProcessMonitor().check_and_kill()

    session = get_session()
    try:
        log = session.query(ActivityLog).first()
        assert log.child_id == child_id
        assert log.action == "app_blocked"
        assert log.details == "discord"
    finally:
        session.close()
