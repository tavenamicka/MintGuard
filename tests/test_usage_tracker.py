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

import json
from collections import namedtuple

import psutil
import pytest

from mintguard.backend.usage_tracker import UsageTracker
from mintguard.db.database import get_session, init_db
from mintguard.db.models import Child, DailyUsage

FakeSession = namedtuple("FakeSession", ["name", "terminal", "host", "started", "pid"])


class _FakeCompletedProcess:
    def __init__(self, stdout: str):
        self.stdout = stdout


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


@pytest.fixture(autouse=True)
def loginctl_matches_psutil(monkeypatch):
    """Par défaut, loginctl "confirme" active tout utilisateur déjà listé par
    `psutil.users()` (patché par chaque test individuellement) — isole les tests qui ne
    portent que sur le filtrage utmp du filtrage loginctl ajouté depuis (voir
    test_record_tick_ignores_child_whose_logind_session_is_closing pour le scénario que ce
    second filtrage couvre spécifiquement)."""

    def fake_run(cmd, **kwargs):
        usernames = {UsageTracker._plain_username(u.name) for u in psutil.users()}
        sessions = [{"user": name, "state": "active"} for name in usernames]
        return _FakeCompletedProcess(stdout=json.dumps(sessions))

    monkeypatch.setattr("mintguard.backend.usage_tracker.subprocess.run", fake_run)


def add_child(name: str, username: str) -> int:
    session = get_session()
    try:
        child = Child(name=name, username=username)
        session.add(child)
        session.commit()
        return child.id
    finally:
        session.close()


def test_record_tick_adds_seconds_for_logged_in_child(monkeypatch):
    child_id = add_child("Test", "mintguard-test-child")
    sessions = [FakeSession("mintguard-test-child", "tty1", "", 0.0, 1)]
    monkeypatch.setattr("mintguard.backend.usage_tracker.psutil.users", lambda: sessions)

    UsageTracker().record_tick(5)
    UsageTracker().record_tick(5)

    assert UsageTracker().get_seconds_used_today(child_id) == 10


def test_record_tick_ignores_child_not_logged_in(monkeypatch):
    child_id = add_child("Test", "mintguard-test-child")
    monkeypatch.setattr("mintguard.backend.usage_tracker.psutil.users", lambda: [])

    UsageTracker().record_tick(5)

    assert UsageTracker().get_seconds_used_today(child_id) == 0


def test_record_tick_ignores_unrelated_logged_in_user(monkeypatch):
    child_id = add_child("Test", "mintguard-test-child")
    sessions = [FakeSession("latitude", "tty1", "", 0.0, 1)]
    monkeypatch.setattr("mintguard.backend.usage_tracker.psutil.users", lambda: sessions)

    UsageTracker().record_tick(5)

    assert UsageTracker().get_seconds_used_today(child_id) == 0


def test_get_seconds_used_today_defaults_to_zero_without_any_row():
    child_id = add_child("Test", "mintguard-test-child")
    assert UsageTracker().get_seconds_used_today(child_id) == 0


def test_record_tick_keeps_separate_totals_per_child(monkeypatch):
    alice_id = add_child("Alice", "alice")
    bob_id = add_child("Bob", "bob")
    sessions = [FakeSession("alice", "tty1", "", 0.0, 1), FakeSession("bob", "tty2", "", 0.0, 2)]
    monkeypatch.setattr("mintguard.backend.usage_tracker.psutil.users", lambda: sessions)

    UsageTracker().record_tick(5)
    # Bob se déconnecte, seule Alice continue d'accumuler du temps.
    monkeypatch.setattr(
        "mintguard.backend.usage_tracker.psutil.users", lambda: [FakeSession("alice", "tty1", "", 0.0, 1)]
    )
    UsageTracker().record_tick(5)

    assert UsageTracker().get_seconds_used_today(alice_id) == 10
    assert UsageTracker().get_seconds_used_today(bob_id) == 5


def test_daily_usage_unique_per_child_and_date():
    child_id = add_child("Test", "mintguard-test-child")
    session = get_session()
    try:
        session.add(DailyUsage(child_id=child_id, date="2026-09-01", seconds_used=120))
        session.commit()
        row = session.query(DailyUsage).filter_by(child_id=child_id, date="2026-09-01").first()
        assert row.seconds_used == 120
    finally:
        session.close()


# Trouvé en usage réel (voir SUIVI.md) : après une fermeture forcée de session
# (SessionManager.terminate_user_session, ex. fin de plage horaire), l'entrée utmp du
# compte enfant peut rester "connectée" alors que systemd-logind marque déjà la session
# "closing" — le Dashboard continuait alors à faire défiler le temps d'un enfant qui
# n'était plus réellement connecté.


def test_record_tick_ignores_child_whose_logind_session_is_closing(monkeypatch):
    child_id = add_child("Test", "mintguard-test-child")
    sessions = [FakeSession("mintguard-test-child", "tty1", "", 0.0, 1)]
    monkeypatch.setattr("mintguard.backend.usage_tracker.psutil.users", lambda: sessions)
    monkeypatch.setattr(
        "mintguard.backend.usage_tracker.subprocess.run",
        lambda cmd, **kwargs: _FakeCompletedProcess(
            stdout=json.dumps([{"user": "mintguard-test-child", "state": "closing"}])
        ),
    )

    UsageTracker().record_tick(5)

    assert UsageTracker().get_seconds_used_today(child_id) == 0


def test_record_tick_falls_back_to_utmp_when_loginctl_unavailable(monkeypatch):
    child_id = add_child("Test", "mintguard-test-child")
    sessions = [FakeSession("mintguard-test-child", "tty1", "", 0.0, 1)]
    monkeypatch.setattr("mintguard.backend.usage_tracker.psutil.users", lambda: sessions)

    def raise_missing(cmd, **kwargs):
        raise FileNotFoundError("loginctl introuvable")

    monkeypatch.setattr("mintguard.backend.usage_tracker.subprocess.run", raise_missing)

    UsageTracker().record_tick(5)

    assert UsageTracker().get_seconds_used_today(child_id) == 5
