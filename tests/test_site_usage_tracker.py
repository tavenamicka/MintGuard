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

"""SiteUsageTracker : lecture+troncature du log de requetes dnsmasq (vie privee, voir
etc/dnsmasq.d/mintguard.conf), correspondance de sous-domaine, et resolve_active_child_id
(seul un enfant actif identifie sans ambiguite doit voir son quota decompte)."""

import json
from collections import namedtuple
from datetime import date

import psutil
import pytest

from mintguard.backend.site_usage_tracker import SiteUsageTracker, resolve_active_child_id
from mintguard.backend.usage_tracker import UsageTracker
from mintguard.db.database import get_session, init_db
from mintguard.db.models import BlockedSite, Child, SiteDailyUsage

FakeSession = namedtuple("FakeSession", ["name", "terminal", "host", "started", "pid"])


class _FakeCompletedProcess:
    def __init__(self, stdout: str):
        self.stdout = stdout


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


@pytest.fixture(autouse=True)
def loginctl_matches_psutil(monkeypatch):
    """Meme fixture que test_usage_tracker.py : loginctl "confirme" active tout utilisateur
    deja liste par psutil.users() - isole ces tests du filtrage loginctl, hors de propos ici."""

    def fake_run(cmd, **kwargs):
        usernames = {UsageTracker._plain_username(u.name) for u in psutil.users()}
        sessions = [{"user": name, "state": "active"} for name in usernames]
        return _FakeCompletedProcess(stdout=json.dumps(sessions))

    monkeypatch.setattr("mintguard.backend.usage_tracker.subprocess.run", fake_run)


def add_child(username: str) -> int:
    session = get_session()
    try:
        child = Child(name=username, username=username)
        session.add(child)
        session.commit()
        return child.id
    finally:
        session.close()


def add_budgeted_site(domain: str, child_id: int | None = None, daily_budget_minutes: int = 30) -> None:
    session = get_session()
    try:
        session.add(
            BlockedSite(domain=domain, category="custom", blocked=True, child_id=child_id,
                        daily_budget_minutes=daily_budget_minutes)
        )
        session.commit()
    finally:
        session.close()


def seconds_used(child_id: int, domain: str) -> int:
    session = get_session()
    try:
        row = session.query(SiteDailyUsage).filter_by(
            child_id=child_id, domain=domain, date=date.today().isoformat()
        ).first()
        return row.seconds_used if row is not None else 0
    finally:
        session.close()


def write_log(path, *lines: str) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# -- Lecture, matching, accumulation -------------------------------------------------------


def test_poll_accumulates_usage_for_matched_domain(tmp_path):
    child_id = add_child("alice")
    add_budgeted_site("youtube.com", child_id=child_id, daily_budget_minutes=30)
    log_path = tmp_path / "dns.log"
    write_log(log_path, "Sep 20 10:15:23 dnsmasq[1]: query[A] youtube.com from 127.0.0.1")

    SiteUsageTracker(log_path=log_path).poll(elapsed_seconds=5, active_child_id=child_id)

    assert seconds_used(child_id, "youtube.com") == 5


def test_poll_matches_subdomain_against_registered_domain(tmp_path):
    """Les logs contiennent le nom litteral interroge (www.youtube.com), jamais le domaine
    enregistre nu (youtube.com) - voir domain_matches."""
    child_id = add_child("alice")
    add_budgeted_site("youtube.com", child_id=child_id)
    log_path = tmp_path / "dns.log"
    write_log(log_path, "Sep 20 10:15:23 dnsmasq[1]: query[AAAA] www.youtube.com from 127.0.0.1")

    SiteUsageTracker(log_path=log_path).poll(elapsed_seconds=5, active_child_id=child_id)

    assert seconds_used(child_id, "youtube.com") == 5


def test_poll_ignores_non_budgeted_domain(tmp_path):
    child_id = add_child("alice")
    add_budgeted_site("youtube.com", child_id=child_id)
    log_path = tmp_path / "dns.log"
    write_log(log_path, "Sep 20 10:15:23 dnsmasq[1]: query[A] wikipedia.org from 127.0.0.1")

    SiteUsageTracker(log_path=log_path).poll(elapsed_seconds=5, active_child_id=child_id)

    assert seconds_used(child_id, "youtube.com") == 0


def test_poll_accumulates_across_multiple_calls(tmp_path):
    child_id = add_child("alice")
    add_budgeted_site("youtube.com", child_id=child_id)
    log_path = tmp_path / "dns.log"
    tracker = SiteUsageTracker(log_path=log_path)

    write_log(log_path, "Sep 20 10:15:23 dnsmasq[1]: query[A] youtube.com from 127.0.0.1")
    tracker.poll(elapsed_seconds=5, active_child_id=child_id)
    write_log(log_path, "Sep 20 10:15:28 dnsmasq[1]: query[A] youtube.com from 127.0.0.1")
    tracker.poll(elapsed_seconds=5, active_child_id=child_id)

    assert seconds_used(child_id, "youtube.com") == 10


# -- Vie privee : troncature inconditionnelle -----------------------------------------------


def test_poll_truncates_log_file_after_reading(tmp_path):
    child_id = add_child("alice")
    add_budgeted_site("youtube.com", child_id=child_id)
    log_path = tmp_path / "dns.log"
    write_log(log_path, "Sep 20 10:15:23 dnsmasq[1]: query[A] youtube.com from 127.0.0.1")

    SiteUsageTracker(log_path=log_path).poll(elapsed_seconds=5, active_child_id=child_id)

    assert log_path.read_text(encoding="utf-8") == ""


def test_poll_truncates_even_when_active_child_is_ambiguous(tmp_path):
    """La troncature est une protection vie privee inconditionnelle, independante du
    decompte de quota (voir SiteUsageTracker.poll)."""
    log_path = tmp_path / "dns.log"
    write_log(log_path, "Sep 20 10:15:23 dnsmasq[1]: query[A] youtube.com from 127.0.0.1")

    SiteUsageTracker(log_path=log_path).poll(elapsed_seconds=5, active_child_id=None)

    assert log_path.read_text(encoding="utf-8") == ""


def test_poll_does_not_accumulate_when_active_child_is_ambiguous(tmp_path):
    child_id = add_child("alice")
    add_budgeted_site("youtube.com", child_id=child_id)
    log_path = tmp_path / "dns.log"
    write_log(log_path, "Sep 20 10:15:23 dnsmasq[1]: query[A] youtube.com from 127.0.0.1")

    SiteUsageTracker(log_path=log_path).poll(elapsed_seconds=5, active_child_id=None)

    assert seconds_used(child_id, "youtube.com") == 0


def test_poll_missing_log_file_does_not_crash(tmp_path):
    child_id = add_child("alice")
    add_budgeted_site("youtube.com", child_id=child_id)
    SiteUsageTracker(log_path=tmp_path / "does-not-exist.log").poll(elapsed_seconds=5, active_child_id=child_id)
    assert seconds_used(child_id, "youtube.com") == 0


# -- resolve_active_child_id ------------------------------------------------------------


def test_resolve_active_child_id_returns_none_when_nobody_logged_in(monkeypatch):
    add_child("alice")
    monkeypatch.setattr("mintguard.backend.usage_tracker.psutil.users", lambda: [])

    assert resolve_active_child_id(UsageTracker()) is None


def test_resolve_active_child_id_returns_the_single_active_child(monkeypatch):
    child_id = add_child("alice")
    sessions = [FakeSession("alice", "tty1", "", 0.0, 1)]
    monkeypatch.setattr("mintguard.backend.usage_tracker.psutil.users", lambda: sessions)

    assert resolve_active_child_id(UsageTracker()) == child_id


def test_resolve_active_child_id_returns_none_when_multiple_children_active(monkeypatch):
    add_child("alice")
    add_child("bob")
    sessions = [FakeSession("alice", "tty1", "", 0.0, 1), FakeSession("bob", "tty2", "", 0.0, 2)]
    monkeypatch.setattr("mintguard.backend.usage_tracker.psutil.users", lambda: sessions)

    assert resolve_active_child_id(UsageTracker()) is None


def test_resolve_active_child_id_ignores_logged_in_non_child_account(monkeypatch):
    add_child("alice")
    sessions = [FakeSession("latitude", "tty1", "", 0.0, 1)]  # compte parent, pas un enfant
    monkeypatch.setattr("mintguard.backend.usage_tracker.psutil.users", lambda: sessions)

    assert resolve_active_child_id(UsageTracker()) is None
