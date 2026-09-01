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
from mintguard.backend.firewall_controller import FirewallController
from mintguard.backend.process_monitor import ProcessMonitor
from mintguard.backend.scheduler import Scheduler
from mintguard.backend.usage_tracker import UsageTracker
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
        FirewallController(),
        UsageTracker(),
    )


def test_process_monitor_runs_every_cycle(tmp_path, monkeypatch):
    process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker = make_controllers(tmp_path)
    calls = []
    monkeypatch.setattr(process_monitor, "check_and_kill", lambda: calls.append(1))
    monkeypatch.setattr(dns_controller, "generate_blocklist", lambda: 0)
    monkeypatch.setattr(dns_controller, "reload_dnsmasq", lambda: True)
    monkeypatch.setattr(firewall_controller, "sync_child_dns_restriction", lambda: True)
    monkeypatch.setattr(usage_tracker, "record_tick", lambda seconds: None)

    state = {"last_session_check": 0.0, "last_dns_refresh": 0.0}
    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, state,
        now=1.0, session_interval=60, dns_refresh_interval=30, process_interval=5,
    )
    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, state,
        now=2.0, session_interval=60, dns_refresh_interval=30, process_interval=5,
    )

    assert len(calls) == 2


def test_usage_tracker_ticks_every_cycle(tmp_path, monkeypatch):
    process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker = make_controllers(tmp_path)
    monkeypatch.setattr(process_monitor, "check_and_kill", lambda: None)
    monkeypatch.setattr(dns_controller, "generate_blocklist", lambda: 0)
    monkeypatch.setattr(dns_controller, "reload_dnsmasq", lambda: True)
    monkeypatch.setattr(firewall_controller, "sync_child_dns_restriction", lambda: True)

    ticks = []
    monkeypatch.setattr(usage_tracker, "record_tick", lambda seconds: ticks.append(seconds))

    state = {"last_session_check": 0.0, "last_dns_refresh": 0.0}
    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, state,
        now=1.0, session_interval=60, dns_refresh_interval=30, process_interval=5,
    )
    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, state,
        now=2.0, session_interval=60, dns_refresh_interval=30, process_interval=5,
    )

    assert ticks == [5, 5]


def test_scheduler_runs_only_after_session_interval_elapsed(tmp_path, monkeypatch):
    process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker = make_controllers(tmp_path)
    monkeypatch.setattr(process_monitor, "check_and_kill", lambda: None)
    monkeypatch.setattr(dns_controller, "generate_blocklist", lambda: 0)
    monkeypatch.setattr(dns_controller, "reload_dnsmasq", lambda: True)
    monkeypatch.setattr(firewall_controller, "sync_child_dns_restriction", lambda: True)
    monkeypatch.setattr(usage_tracker, "record_tick", lambda seconds: None)

    calls = []
    monkeypatch.setattr(scheduler, "check_all_children", lambda: calls.append(1))

    # État initial à 0.0 ("jamais vérifié") : le premier appel n'est dû que si `now` a déjà
    # atteint l'intervalle depuis 0 — donc now=70 pour un intervalle de 60s, pas now=10.
    state = {"last_session_check": 0.0, "last_dns_refresh": 0.0}
    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, state,
        now=70.0, session_interval=60, dns_refresh_interval=999, process_interval=5,
    )
    assert calls == [1]
    assert state["last_session_check"] == 70.0

    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, state,
        now=80.0, session_interval=60, dns_refresh_interval=999, process_interval=5,
    )
    assert calls == [1]  # 10s après : pas encore dû (interval 60s)

    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, state,
        now=140.0, session_interval=60, dns_refresh_interval=999, process_interval=5,
    )
    assert calls == [1, 1]


def test_dns_and_firewall_refresh_only_after_interval_elapsed(tmp_path, monkeypatch):
    process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker = make_controllers(tmp_path)
    monkeypatch.setattr(process_monitor, "check_and_kill", lambda: None)
    monkeypatch.setattr(scheduler, "check_all_children", lambda: None)
    monkeypatch.setattr(usage_tracker, "record_tick", lambda seconds: None)

    calls = []
    monkeypatch.setattr(dns_controller, "generate_blocklist", lambda: calls.append("gen"))
    monkeypatch.setattr(dns_controller, "reload_dnsmasq", lambda: calls.append("reload"))
    monkeypatch.setattr(firewall_controller, "sync_child_dns_restriction", lambda: calls.append("firewall"))

    state = {"last_session_check": 0.0, "last_dns_refresh": 0.0}
    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, state,
        now=35.0, session_interval=999, dns_refresh_interval=30, process_interval=5,
    )
    assert calls == ["gen", "reload", "firewall"]

    calls.clear()
    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, state,
        now=45.0, session_interval=999, dns_refresh_interval=30, process_interval=5,
    )
    assert calls == []  # 10s après le refresh : pas encore dû (interval 30s)

    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, state,
        now=70.0, session_interval=999, dns_refresh_interval=30, process_interval=5,
    )
    assert calls == ["gen", "reload", "firewall"]
