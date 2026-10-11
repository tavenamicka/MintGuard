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

from datetime import date

import pytest

from mintguard.backend.process_monitor import ProcessMonitor
from mintguard.db.database import get_session, init_db
from mintguard.db.models import ActivityLog, AppDailyUsage, BlockedApp, Child


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


@pytest.fixture(autouse=True)
def no_path_lookup(monkeypatch):
    """N'apprend pas les empreintes des vrais programmes installés sur la machine de test."""
    monkeypatch.setattr("mintguard.backend.process_monitor.shutil.which", lambda name: None)


def add_blocked_app(name: str, child_id: int | None = None, daily_budget_minutes: int | None = None) -> None:
    session = get_session()
    try:
        session.add(
            BlockedApp(app_name=name, enabled=True, child_id=child_id, daily_budget_minutes=daily_budget_minutes)
        )
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
    def __init__(self, pid: int, name: str, username: str | None, exe: str | None = None):
        self.info = {"pid": pid, "name": name, "username": username, "exe": exe}
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
    """Trouvé à l'audit de sécurité : sans filtrage par utilisateur, un
    processus du même nom tournant sous le compte parent (ou tout autre compte du système)
    était tué aussi, dommage collatéral non intentionnel."""
    add_blocked_app("discord")
    add_child("Test", "mintguard-test-child")

    procs = [FakeProcess(1, "discord", "parentuser")]
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

    procs = [FakeProcess(1, "discord", "parentuser")]
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
        assert log.details == "Application bloquée : discord"
    finally:
        session.close()


def test_budgeted_app_not_killed_while_under_quota(monkeypatch):
    child_id = add_child("Test", "mintguard-test-child")
    add_blocked_app("discord", child_id=child_id, daily_budget_minutes=10)

    procs = [FakeProcess(1, "discord", "mintguard-test-child")]
    monkeypatch.setattr("mintguard.backend.process_monitor.psutil.process_iter", lambda *_: procs)

    killed = ProcessMonitor().check_and_kill(elapsed_seconds=60)

    assert killed == []
    assert procs[0].killed is False

    session = get_session()
    try:
        row = session.query(AppDailyUsage).filter_by(child_id=child_id, app_name="discord").first()
        assert row.seconds_used == 60
    finally:
        session.close()


def test_budgeted_app_killed_once_quota_exceeded(monkeypatch):
    child_id = add_child("Test", "mintguard-test-child")
    add_blocked_app("discord", child_id=child_id, daily_budget_minutes=1)

    session = get_session()
    try:
        session.add(AppDailyUsage(child_id=child_id, app_name="discord", date=date.today().isoformat(), seconds_used=55))
        session.commit()
    finally:
        session.close()

    procs = [FakeProcess(1, "discord", "mintguard-test-child")]
    monkeypatch.setattr("mintguard.backend.process_monitor.psutil.process_iter", lambda *_: procs)

    killed = ProcessMonitor().check_and_kill(elapsed_seconds=10)

    assert killed == ["discord"]
    assert procs[0].killed is True

    session = get_session()
    try:
        log = session.query(ActivityLog).first()
        assert log.child_id == child_id
        assert log.action == "app_blocked"
        assert log.details == "Quota atteint : discord (1 min/jour)"
    finally:
        session.close()


def test_child_specific_rule_takes_priority_over_global(monkeypatch):
    child_id = add_child("Test", "mintguard-test-child")
    add_blocked_app("discord", child_id=None, daily_budget_minutes=None)  # règle globale: bloquée totalement
    add_blocked_app("discord", child_id=child_id, daily_budget_minutes=30)  # règle enfant: quota

    procs = [FakeProcess(1, "discord", "mintguard-test-child")]
    monkeypatch.setattr("mintguard.backend.process_monitor.psutil.process_iter", lambda *_: procs)

    killed = ProcessMonitor().check_and_kill(elapsed_seconds=60)

    # La règle enfant-spécifique (quota) l'emporte sur la règle globale (blocage total) :
    # l'appli n'est pas tuée immédiatement.
    assert killed == []
    assert procs[0].killed is False



# -- Copies renommées (empreinte de l'exécutable) ---------------------------------------------


def _binary(tmp_path, name: str, content: bytes = b"\x7fELF fake game binary") -> str:
    path = tmp_path / name
    path.write_bytes(content)
    return str(path)


def test_kills_renamed_copy_of_blocked_app(monkeypatch, tmp_path):
    """`cp /usr/bin/supertux ~/devoirs` : même contenu, autre nom - doit être tué aussi."""
    original = _binary(tmp_path, "supertux")
    copy = _binary(tmp_path, "devoirs")
    monkeypatch.setattr("mintguard.backend.process_monitor.shutil.which", lambda name: original)
    add_blocked_app("supertux")
    add_child("Test", "mintguard-test-child")

    procs = [FakeProcess(1, "devoirs", "mintguard-test-child", exe=copy)]
    monkeypatch.setattr("mintguard.backend.process_monitor.psutil.process_iter", lambda *_: procs)

    assert ProcessMonitor().check_and_kill() == ["supertux"]
    assert procs[0].killed is True


def test_learns_fingerprint_from_running_original(monkeypatch, tmp_path):
    """Sans binaire trouvable dans le PATH : l'empreinte est apprise du processus d'origine
    (ici lancé par le parent, qui n'est pas tué) puis reconnue sur la copie de l'enfant."""
    original = _binary(tmp_path, "supertux")
    copy = _binary(tmp_path, "calculatrice")
    add_blocked_app("supertux")
    add_child("Test", "mintguard-test-child")

    procs = [
        FakeProcess(1, "supertux", "parentuser", exe=original),
        FakeProcess(2, "calculatrice", "mintguard-test-child", exe=copy),
    ]
    monkeypatch.setattr("mintguard.backend.process_monitor.psutil.process_iter", lambda *_: procs)

    assert ProcessMonitor().check_and_kill() == ["supertux"]
    assert procs[0].killed is False
    assert procs[1].killed is True


def test_different_program_with_same_size_is_not_killed(monkeypatch, tmp_path):
    original = _binary(tmp_path, "supertux", b"A" * 32)
    other = _binary(tmp_path, "inkscape", b"B" * 32)
    monkeypatch.setattr("mintguard.backend.process_monitor.shutil.which", lambda name: original)
    add_blocked_app("supertux")
    add_child("Test", "mintguard-test-child")

    procs = [FakeProcess(1, "inkscape", "mintguard-test-child", exe=other)]
    monkeypatch.setattr("mintguard.backend.process_monitor.psutil.process_iter", lambda *_: procs)

    assert ProcessMonitor().check_and_kill() == []
    assert procs[0].killed is False


def test_interpreter_fingerprint_is_never_learned(monkeypatch, tmp_path):
    """Un script bloqué qui tourne sous python3 ne doit pas faire tuer tous les autres
    programmes Python de l'enfant."""
    python = _binary(tmp_path, "python3")
    add_blocked_app("python3")
    add_child("Test", "mintguard-test-child")
    other_python = _binary(tmp_path, "monscript", (tmp_path / "python3").read_bytes())

    procs = [FakeProcess(1, "monscript", "mintguard-test-child", exe=other_python),
             FakeProcess(2, "python3", "parentuser", exe=python)]
    monkeypatch.setattr("mintguard.backend.process_monitor.psutil.process_iter", lambda *_: procs)

    assert ProcessMonitor().check_and_kill() == []
