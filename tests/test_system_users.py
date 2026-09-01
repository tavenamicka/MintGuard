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

from collections import namedtuple

import pytest

from mintguard.backend import system_users

FakePwEntry = namedtuple("FakePwEntry", ["pw_name", "pw_uid", "pw_shell"])

FAKE_PASSWD_DB = [
    FakePwEntry("root", 0, "/bin/bash"),
    FakePwEntry("daemon", 1, "/usr/sbin/nologin"),
    FakePwEntry("sshd", 115, "/usr/sbin/nologin"),
    FakePwEntry("latitude", 1000, "/bin/bash"),
    FakePwEntry("mintguard-test-child", 1001, "/bin/bash"),
    FakePwEntry("alice", 1002, "/bin/bash"),
    FakePwEntry("nobody", 65534, "/usr/sbin/nologin"),
]


@pytest.fixture
def fake_pwd(monkeypatch):
    """`pwd` n'existe pas sous Windows : on ne peut pas monkeypatcher un attribut d'un module
    absent, donc on simule l'import lui-meme plutot que `pwd.getpwall`."""
    import sys
    import types

    fake_module = types.SimpleNamespace(getpwall=lambda: FAKE_PASSWD_DB)
    monkeypatch.setitem(sys.modules, "pwd", fake_module)
    return fake_module


def test_excludes_system_accounts_below_min_uid(fake_pwd, monkeypatch):
    monkeypatch.setattr(system_users.getpass, "getuser", lambda: "someone-else")
    result = system_users.list_candidate_usernames()
    assert "root" not in result
    assert "daemon" not in result
    assert "sshd" not in result


def test_excludes_nologin_shell_accounts(fake_pwd, monkeypatch):
    monkeypatch.setattr(system_users.getpass, "getuser", lambda: "someone-else")
    result = system_users.list_candidate_usernames()
    assert "nobody" not in result  # UID hors plage ET shell nologin


def test_excludes_current_user_running_the_gui(fake_pwd, monkeypatch):
    monkeypatch.setattr(system_users.getpass, "getuser", lambda: "latitude")
    result = system_users.list_candidate_usernames()
    assert "latitude" not in result
    assert "mintguard-test-child" in result
    assert "alice" in result


def test_excludes_explicit_exclude_set(fake_pwd, monkeypatch):
    monkeypatch.setattr(system_users.getpass, "getuser", lambda: "someone-else")
    result = system_users.list_candidate_usernames(exclude={"alice"})
    assert "alice" not in result
    assert "mintguard-test-child" in result


def test_returns_empty_list_without_pwd_module(monkeypatch):
    import sys

    # Astuce standard : sys.modules["x"] = None force `import x` a lever ImportError,
    # sans avoir a remplacer __import__ globalement (simule l'absence de `pwd` sous Windows).
    monkeypatch.setitem(sys.modules, "pwd", None)
    assert system_users.list_candidate_usernames() == []
