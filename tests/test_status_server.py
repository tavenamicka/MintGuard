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

"""StatusServer : seul canal par lequel un compte enfant (aucun accès à la BD partagée,
voir database.py) apprend son propre temps restant / applis bloquées récemment - le test
critique est qu'il ne voit jamais que SON statut, jamais celui d'un autre compte."""

import json
import socket

import pytest

from mintguard.backend.scheduler import Scheduler
from mintguard.backend.status_server import StatusServer
from mintguard.db.database import get_session, init_db
from mintguard.db.models import ActivityLog, Child

FAKE_PARENT_UID = 1000
FAKE_CHILD_UID = 1001
FAKE_UNKNOWN_UID = 1002


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


def add_child(username: str) -> int:
    session = get_session()
    try:
        child = Child(name=username.capitalize(), username=username)
        session.add(child)
        session.commit()
        return child.id
    finally:
        session.close()


def test_build_status_unknown_uid_is_not_a_child(monkeypatch):
    monkeypatch.setattr("mintguard.backend.status_server.pwd.getpwuid", _fake_getpwuid({}))
    server = StatusServer(Scheduler())
    assert server._build_status(FAKE_UNKNOWN_UID) == {"is_child": False}


def test_build_status_parent_account_is_not_a_child(monkeypatch):
    monkeypatch.setattr(
        "mintguard.backend.status_server.pwd.getpwuid",
        _fake_getpwuid({FAKE_PARENT_UID: "parent"}),
    )
    server = StatusServer(Scheduler())
    assert server._build_status(FAKE_PARENT_UID) == {"is_child": False}


def test_build_status_child_sees_own_minutes_remaining(monkeypatch):
    add_child("emma")
    monkeypatch.setattr(
        "mintguard.backend.status_server.pwd.getpwuid",
        _fake_getpwuid({FAKE_CHILD_UID: "emma"}),
    )
    scheduler = Scheduler()
    monkeypatch.setattr(scheduler, "get_minutes_remaining", lambda child_id: 7)

    status = StatusServer(scheduler)._build_status(FAKE_CHILD_UID)

    assert status["is_child"] is True
    assert status["minutes_remaining"] == 7
    assert status["recent_blocks"] == []


def test_build_status_includes_only_this_childs_recent_blocks(monkeypatch):
    emma_id = add_child("emma")
    add_child("louis")
    session = get_session()
    session.add_all(
        [
            ActivityLog(child_id=emma_id, action="app_blocked", details="discord"),
            ActivityLog(child_id=emma_id, action="time_limit_hit", details="autre evenement"),
        ]
    )
    session.commit()
    session.close()

    monkeypatch.setattr(
        "mintguard.backend.status_server.pwd.getpwuid",
        _fake_getpwuid({FAKE_CHILD_UID: "emma"}),
    )
    scheduler = Scheduler()
    monkeypatch.setattr(scheduler, "get_minutes_remaining", lambda child_id: None)

    status = StatusServer(scheduler)._build_status(FAKE_CHILD_UID)

    assert status["recent_blocks"] == ["discord"]


def test_real_socket_roundtrip_returns_own_status_only(tmp_path, monkeypatch):
    """Bout en bout via un vrai socket Unix (pas seulement `_build_status`) : un enfant qui
    interroge le socket ne reçoit que ses propres données, jamais celles d'un autre enfant."""
    emma_id = add_child("emma")
    add_child("louis")
    session = get_session()
    session.add(ActivityLog(child_id=emma_id, action="app_blocked", details="minecraft"))
    session.commit()
    session.close()

    scheduler = Scheduler()
    monkeypatch.setattr(scheduler, "get_minutes_remaining", lambda child_id: 5)
    server = StatusServer(scheduler, socket_path=str(tmp_path / "status.sock"))
    # SO_PEERCRED renverrait le vrai uid du process de test - fige-le sur "emma" pour ce test.
    monkeypatch.setattr(server, "_peer_uid", lambda conn: FAKE_CHILD_UID)
    monkeypatch.setattr(
        "mintguard.backend.status_server.pwd.getpwuid",
        _fake_getpwuid({FAKE_CHILD_UID: "emma"}),
    )
    server.start()

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(3)
        client.connect(server.socket_path)
        client.sendall((json.dumps({"cmd": "status"}) + "\n").encode("utf-8"))
        response = json.loads(client.recv(4096).decode("utf-8"))

    assert response == {"is_child": True, "minutes_remaining": 5, "recent_blocks": ["minecraft"]}


def _fake_getpwuid(uid_to_username: dict[int, str]):
    def getpwuid(uid: int):
        if uid not in uid_to_username:
            raise KeyError(uid)
        return type("PwEntry", (), {"pw_name": uid_to_username[uid]})()

    return getpwuid
