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

from mintguard.backend.apparmor_controller import AppArmorController
from mintguard.backend.dns_controller import DNSController
from mintguard.backend.firewall_controller import FirewallController
from mintguard.backend.process_monitor import ProcessMonitor
from mintguard.backend.scheduler import Scheduler
from mintguard.backend.session_manager import SessionManager
from mintguard.db.database import init_db


@pytest.fixture(autouse=True)
def db(tmp_path):
    """Chaque test backend utilise une BD SQLite jetable dans tmp_path."""
    init_db(tmp_path / "test.db")


def test_process_monitor_stub_passes():
    assert ProcessMonitor().test() is True


def test_scheduler_stub_passes():
    assert Scheduler().test() is True


def test_dns_controller_generates_empty_blocklist(tmp_path):
    controller = DNSController(blocklist_path=tmp_path / "blocklist.conf")
    assert controller.test() is True
    assert (tmp_path / "blocklist.conf").exists()


# Ces contrôleurs dépendent d'outils système Linux (iptables/loginctl/apparmor_parser)
# absents en dev Windows : on vérifie juste qu'ils échouent proprement (bool), pas une exception.
def test_firewall_controller_stub_returns_bool():
    assert isinstance(FirewallController().test(), bool)


def test_session_manager_stub_returns_bool():
    assert isinstance(SessionManager().test(), bool)


def test_apparmor_controller_stub_returns_bool():
    assert isinstance(AppArmorController().test(), bool)


def test_session_manager_refuses_implausible_username(monkeypatch):
    """Le nom vient de la BD et part dans `loginctl terminate-user` : rien ne doit être
    exécuté si sa forme est inattendue."""
    calls = []
    monkeypatch.setattr(
        "mintguard.backend.session_manager.subprocess.run", lambda *a, **k: calls.append(a)
    )
    assert SessionManager().terminate_user_session("--all") is False
    assert calls == []
