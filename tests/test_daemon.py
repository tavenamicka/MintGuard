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

from mintguard.backend.dns_controller import DNSController
from mintguard.backend.process_monitor import ProcessMonitor
from mintguard.backend.scheduler import Scheduler
from mintguard.daemon import run_cycle
from mintguard.db.database import init_db


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


def make_controllers(tmp_path):
    return (
        ProcessMonitor(),
        Scheduler(),
        DNSController(blocklist_path=tmp_path / "blocklist.hosts"),
    )


def test_process_monitor_runs_every_cycle(tmp_path, monkeypatch):
    process_monitor, scheduler, dns_controller = make_controllers(tmp_path)
    calls = []
    monkeypatch.setattr(process_monitor, "check_and_kill", lambda: calls.append(1))
    monkeypatch.setattr(dns_controller, "generate_blocklist", lambda: 0)
    monkeypatch.setattr(dns_controller, "reload_dnsmasq", lambda: True)

    state = {"last_session_check": 0.0, "last_dns_refresh": 0.0}
    run_cycle(process_monitor, scheduler, dns_controller, state, now=1.0, session_interval=60, dns_refresh_interval=30)
    run_cycle(process_monitor, scheduler, dns_controller, state, now=2.0, session_interval=60, dns_refresh_interval=30)

    assert len(calls) == 2


def test_scheduler_runs_only_after_session_interval_elapsed(tmp_path, monkeypatch):
    process_monitor, scheduler, dns_controller = make_controllers(tmp_path)
    monkeypatch.setattr(process_monitor, "check_and_kill", lambda: None)
    monkeypatch.setattr(dns_controller, "generate_blocklist", lambda: 0)
    monkeypatch.setattr(dns_controller, "reload_dnsmasq", lambda: True)

    calls = []
    monkeypatch.setattr(scheduler, "check_all_children", lambda: calls.append(1))

    # État initial à 0.0 ("jamais vérifié") : le premier appel n'est dû que si `now` a déjà
    # atteint l'intervalle depuis 0 — donc now=70 pour un intervalle de 60s, pas now=10.
    state = {"last_session_check": 0.0, "last_dns_refresh": 0.0}
    run_cycle(process_monitor, scheduler, dns_controller, state, now=70.0, session_interval=60, dns_refresh_interval=999)
    assert calls == [1]
    assert state["last_session_check"] == 70.0

    run_cycle(process_monitor, scheduler, dns_controller, state, now=80.0, session_interval=60, dns_refresh_interval=999)
    assert calls == [1]  # 10s après : pas encore dû (interval 60s)

    run_cycle(process_monitor, scheduler, dns_controller, state, now=140.0, session_interval=60, dns_refresh_interval=999)
    assert calls == [1, 1]


def test_dns_refreshes_only_after_interval_elapsed(tmp_path, monkeypatch):
    process_monitor, scheduler, dns_controller = make_controllers(tmp_path)
    monkeypatch.setattr(process_monitor, "check_and_kill", lambda: None)
    monkeypatch.setattr(scheduler, "check_all_children", lambda: None)

    calls = []
    monkeypatch.setattr(dns_controller, "generate_blocklist", lambda: calls.append("gen"))
    monkeypatch.setattr(dns_controller, "reload_dnsmasq", lambda: calls.append("reload"))

    state = {"last_session_check": 0.0, "last_dns_refresh": 0.0}
    run_cycle(process_monitor, scheduler, dns_controller, state, now=35.0, session_interval=999, dns_refresh_interval=30)
    assert calls == ["gen", "reload"]

    calls.clear()
    run_cycle(process_monitor, scheduler, dns_controller, state, now=45.0, session_interval=999, dns_refresh_interval=30)
    assert calls == []  # 10s après le refresh : pas encore dû (interval 30s)

    run_cycle(process_monitor, scheduler, dns_controller, state, now=70.0, session_interval=999, dns_refresh_interval=30)
    assert calls == ["gen", "reload"]
