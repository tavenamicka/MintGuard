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

import mintguard.daemon as daemon_module
from mintguard.backend.dns_controller import DNSController
from mintguard.backend.firewall_controller import FirewallController
from mintguard.backend.process_monitor import ProcessMonitor
from mintguard.backend.scheduler import Scheduler
from mintguard.backend.site_usage_tracker import SiteUsageTracker
from mintguard.backend.usage_tracker import UsageTracker
from mintguard.daemon import run_cycle
from mintguard.db.database import init_db


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


@pytest.fixture(autouse=True)
def no_active_child(monkeypatch):
    # resolve_active_child_id() interrogerait sinon psutil/loginctl reels (etat de la vraie
    # machine executant les tests, non deterministe) - hors de propos pour ces tests, qui
    # portent sur le cadencement des appels, pas sur la resolution d'enfant actif elle-meme
    # (voir test_site_usage_tracker.py pour ca).
    monkeypatch.setattr(daemon_module, "resolve_active_child_id", lambda usage_tracker: None)


def make_controllers(tmp_path):
    return (
        ProcessMonitor(),
        Scheduler(),
        DNSController(blocklist_path=tmp_path / "blocklist.conf"),
        FirewallController(),
        UsageTracker(),
        SiteUsageTracker(log_path=tmp_path / "dns.log"),
    )


def test_process_monitor_runs_every_cycle(tmp_path, monkeypatch):
    process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, site_usage_tracker = (
        make_controllers(tmp_path)
    )
    calls = []
    monkeypatch.setattr(process_monitor, "check_and_kill", lambda seconds: calls.append(1))
    monkeypatch.setattr(dns_controller, "apply", lambda active_child_id=None: False)
    monkeypatch.setattr(firewall_controller, "sync_child_dns_restriction", lambda: True)
    monkeypatch.setattr(usage_tracker, "record_tick", lambda seconds: None)
    monkeypatch.setattr(site_usage_tracker, "poll", lambda seconds, active_child_id: None)

    state = {"last_session_check": 0.0, "last_dns_refresh": 0.0}
    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, site_usage_tracker, state,
        now=1.0, session_interval=60, dns_refresh_interval=30, process_interval=5,
    )
    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, site_usage_tracker, state,
        now=2.0, session_interval=60, dns_refresh_interval=30, process_interval=5,
    )

    assert len(calls) == 2


def test_usage_tracker_ticks_every_cycle(tmp_path, monkeypatch):
    process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, site_usage_tracker = (
        make_controllers(tmp_path)
    )
    monkeypatch.setattr(process_monitor, "check_and_kill", lambda seconds: None)
    monkeypatch.setattr(dns_controller, "apply", lambda active_child_id=None: False)
    monkeypatch.setattr(firewall_controller, "sync_child_dns_restriction", lambda: True)
    monkeypatch.setattr(site_usage_tracker, "poll", lambda seconds, active_child_id: None)

    ticks = []
    monkeypatch.setattr(usage_tracker, "record_tick", lambda seconds: ticks.append(seconds))

    state = {"last_session_check": 0.0, "last_dns_refresh": 0.0}
    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, site_usage_tracker, state,
        now=1.0, session_interval=60, dns_refresh_interval=30, process_interval=5,
    )
    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, site_usage_tracker, state,
        now=2.0, session_interval=60, dns_refresh_interval=30, process_interval=5,
    )

    assert ticks == [5, 5]


def test_site_usage_tracker_polls_every_cycle(tmp_path, monkeypatch):
    process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, site_usage_tracker = (
        make_controllers(tmp_path)
    )
    monkeypatch.setattr(process_monitor, "check_and_kill", lambda seconds: None)
    monkeypatch.setattr(dns_controller, "apply", lambda active_child_id=None: False)
    monkeypatch.setattr(firewall_controller, "sync_child_dns_restriction", lambda: True)
    monkeypatch.setattr(usage_tracker, "record_tick", lambda seconds: None)

    polls = []
    monkeypatch.setattr(site_usage_tracker, "poll", lambda seconds, active_child_id: polls.append(seconds))

    state = {"last_session_check": 0.0, "last_dns_refresh": 0.0}
    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, site_usage_tracker, state,
        now=1.0, session_interval=60, dns_refresh_interval=30, process_interval=5,
    )
    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, site_usage_tracker, state,
        now=2.0, session_interval=60, dns_refresh_interval=30, process_interval=5,
    )

    assert polls == [5, 5]  # sans condition, meme cadence que usage_tracker.record_tick


def test_scheduler_runs_only_after_session_interval_elapsed(tmp_path, monkeypatch):
    process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, site_usage_tracker = (
        make_controllers(tmp_path)
    )
    monkeypatch.setattr(process_monitor, "check_and_kill", lambda seconds: None)
    monkeypatch.setattr(dns_controller, "apply", lambda active_child_id=None: False)
    monkeypatch.setattr(firewall_controller, "sync_child_dns_restriction", lambda: True)
    monkeypatch.setattr(usage_tracker, "record_tick", lambda seconds: None)
    monkeypatch.setattr(site_usage_tracker, "poll", lambda seconds, active_child_id: None)

    calls = []
    monkeypatch.setattr(scheduler, "check_all_children", lambda: calls.append(1))

    # État initial à 0.0 ("jamais vérifié") : le premier appel n'est dû que si `now` a déjà
    # atteint l'intervalle depuis 0 — donc now=70 pour un intervalle de 60s, pas now=10.
    state = {"last_session_check": 0.0, "last_dns_refresh": 0.0}
    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, site_usage_tracker, state,
        now=70.0, session_interval=60, dns_refresh_interval=999, process_interval=5,
    )
    assert calls == [1]
    assert state["last_session_check"] == 70.0

    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, site_usage_tracker, state,
        now=80.0, session_interval=60, dns_refresh_interval=999, process_interval=5,
    )
    assert calls == [1]  # 10s après : pas encore dû (interval 60s)

    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, site_usage_tracker, state,
        now=140.0, session_interval=60, dns_refresh_interval=999, process_interval=5,
    )
    assert calls == [1, 1]


def test_dns_and_firewall_refresh_only_after_interval_elapsed(tmp_path, monkeypatch):
    process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, site_usage_tracker = (
        make_controllers(tmp_path)
    )
    monkeypatch.setattr(process_monitor, "check_and_kill", lambda seconds: None)
    monkeypatch.setattr(scheduler, "check_all_children", lambda: None)
    monkeypatch.setattr(usage_tracker, "record_tick", lambda seconds: None)
    monkeypatch.setattr(site_usage_tracker, "poll", lambda seconds, active_child_id: None)

    calls = []
    monkeypatch.setattr(dns_controller, "apply", lambda active_child_id=None: calls.append("dns"))
    monkeypatch.setattr(firewall_controller, "sync_child_dns_restriction", lambda: calls.append("firewall"))

    state = {"last_session_check": 0.0, "last_dns_refresh": 0.0}
    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, site_usage_tracker, state,
        now=35.0, session_interval=999, dns_refresh_interval=30, process_interval=5,
    )
    assert calls == ["dns", "firewall"]

    calls.clear()
    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, site_usage_tracker, state,
        now=45.0, session_interval=999, dns_refresh_interval=30, process_interval=5,
    )
    assert calls == []  # 10s après le refresh : pas encore dû (interval 30s)

    run_cycle(
        process_monitor, scheduler, dns_controller, firewall_controller, usage_tracker, site_usage_tracker, state,
        now=70.0, session_interval=999, dns_refresh_interval=30, process_interval=5,
    )
    assert calls == ["dns", "firewall"]
