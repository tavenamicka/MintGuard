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

"""Règles horaires : qui doit être déconnecté, et quand.

`check_all_children` n'avait aucun test de comportement (seulement sa présence dans la
boucle du daemon) alors que c'est lui qui décide de fermer la session d'un enfant.
"""

from datetime import datetime, time as dt_time

import pytest

from mintguard.backend.scheduler import Scheduler
from mintguard.db.database import get_session, init_db
from mintguard.db.models import ActivityLog, Child, DailyUsage, TimeRule

# Mercredi 1er juillet 2026 (weekday() == 2)
WEDNESDAY = datetime(2026, 7, 1)


class FakeSessionManager:
    def __init__(self):
        self.terminated: list[str] = []

    def terminate_user_session(self, username: str) -> bool:
        self.terminated.append(username)
        return True


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


@pytest.fixture
def manager():
    return FakeSessionManager()


def add_child(
    username="emma", day=WEDNESDAY.weekday(), start=(16, 0), end=(20, 0), enabled=True, daily_budget_minutes=None
):
    session = get_session()
    child = Child(name=username.capitalize(), username=username)
    session.add(child)
    session.flush()
    if day is not None:
        session.add(
            TimeRule(
                child_id=child.id,
                day_of_week=day,
                start_hour=dt_time(*start),
                end_hour=dt_time(*end),
                enabled=enabled,
                daily_budget_minutes=daily_budget_minutes,
            )
        )
    session.commit()
    child_id = child.id
    session.close()
    return child_id


def set_usage_today(child_id: int, seconds_used: int, now: datetime) -> None:
    session = get_session()
    session.add(DailyUsage(child_id=child_id, date=now.date().isoformat(), seconds_used=seconds_used))
    session.commit()
    session.close()


def test_child_inside_allowed_window_is_left_alone(manager):
    add_child()
    assert Scheduler(manager).check_all_children(WEDNESDAY.replace(hour=18)) == []
    assert manager.terminated == []


def test_child_outside_allowed_window_is_logged_out(manager):
    add_child()
    assert Scheduler(manager).check_all_children(WEDNESDAY.replace(hour=22)) == ["emma"]
    assert manager.terminated == ["emma"]


def test_child_without_rule_today_is_left_alone(manager):
    """Pas de règle pour aujourd'hui = accès libre, pas un blocage total."""
    add_child(day=None)
    assert Scheduler(manager).check_all_children(WEDNESDAY.replace(hour=22)) == []


def test_disabled_rule_is_ignored(manager):
    add_child(enabled=False)
    assert Scheduler(manager).check_all_children(WEDNESDAY.replace(hour=22)) == []


def test_rule_of_another_day_does_not_apply(manager):
    add_child(day=(WEDNESDAY.weekday() + 1) % 7)
    assert Scheduler(manager).check_all_children(WEDNESDAY.replace(hour=22)) == []


def test_second_window_of_the_day_keeps_child_connected(manager):
    """Deux créneaux le même jour (ex: avant et après le dîner) : être hors du premier ne
    doit pas déconnecter si le second est en cours."""
    child_id = add_child(start=(9, 0), end=(11, 0))
    session = get_session()
    session.add(
        TimeRule(
            child_id=child_id,
            day_of_week=WEDNESDAY.weekday(),
            start_hour=dt_time(18, 0),
            end_hour=dt_time(20, 0),
            enabled=True,
        )
    )
    session.commit()
    session.close()

    assert Scheduler(manager).check_all_children(WEDNESDAY.replace(hour=19)) == []


def test_logout_is_journalised_for_the_right_child(manager):
    child_id = add_child()
    Scheduler(manager).check_all_children(WEDNESDAY.replace(hour=22))

    session = get_session()
    logs = session.query(ActivityLog).all()
    entries = [(log.child_id, log.action) for log in logs]
    session.close()
    assert entries == [(child_id, "time_limit_hit")]


def test_only_the_child_out_of_window_is_logged_out(manager):
    add_child(username="emma", start=(16, 0), end=(20, 0))
    add_child(username="louis", start=(8, 0), end=(23, 0))

    assert Scheduler(manager).check_all_children(WEDNESDAY.replace(hour=22)) == ["emma"]


def test_minutes_remaining_none_without_rule_today(manager):
    child_id = add_child(day=None)
    assert Scheduler(manager).get_minutes_remaining(child_id, WEDNESDAY.replace(hour=18)) is None


def test_minutes_remaining_inside_window(manager):
    child_id = add_child(start=(16, 0), end=(20, 0))
    remaining = Scheduler(manager).get_minutes_remaining(child_id, WEDNESDAY.replace(hour=19, minute=45))
    assert remaining == 15


def test_minutes_remaining_zero_outside_window(manager):
    child_id = add_child(start=(16, 0), end=(20, 0))
    assert Scheduler(manager).get_minutes_remaining(child_id, WEDNESDAY.replace(hour=22)) == 0


def test_child_within_window_but_over_budget_is_logged_out(manager):
    child_id = add_child(start=(16, 0), end=(20, 0), daily_budget_minutes=120)
    now = WEDNESDAY.replace(hour=17)
    set_usage_today(child_id, seconds_used=120 * 60, now=now)

    assert Scheduler(manager).check_all_children(now) == ["emma"]
    assert manager.terminated == ["emma"]

    session = get_session()
    logs = session.query(ActivityLog).all()
    entries = [(log.child_id, log.action) for log in logs]
    session.close()
    assert entries == [(child_id, "daily_budget_hit")]


def test_child_within_window_and_under_budget_is_left_alone(manager):
    child_id = add_child(start=(16, 0), end=(20, 0), daily_budget_minutes=120)
    now = WEDNESDAY.replace(hour=17)
    set_usage_today(child_id, seconds_used=60 * 60, now=now)

    assert Scheduler(manager).check_all_children(now) == []
    assert manager.terminated == []


def test_minutes_remaining_capped_by_budget(manager):
    child_id = add_child(start=(16, 0), end=(20, 0), daily_budget_minutes=90)
    now = WEDNESDAY.replace(hour=17)
    set_usage_today(child_id, seconds_used=70 * 60, now=now)

    # Fenêtre: encore 3h. Budget: 90-70=20 min restantes. Le budget l'emporte.
    assert Scheduler(manager).get_minutes_remaining(child_id, now) == 20


def test_minutes_remaining_uses_window_when_budget_not_exhausted(manager):
    child_id = add_child(start=(16, 0), end=(17, 0), daily_budget_minutes=90)
    now = WEDNESDAY.replace(hour=16, minute=45)
    set_usage_today(child_id, seconds_used=10 * 60, now=now)

    # Fenêtre: encore 15 min. Budget: 90-10=80 min restantes. La fenêtre l'emporte.
    assert Scheduler(manager).get_minutes_remaining(child_id, now) == 15
