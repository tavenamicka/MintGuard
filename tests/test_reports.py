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

from datetime import datetime, timedelta

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication  # noqa: E402

from mintguard.db.database import get_session, init_db  # noqa: E402
from mintguard.db.models import ActivityLog, Child  # noqa: E402
from mintguard.gui.reports import ReportsWindow  # noqa: E402
from mintguard.locales.loader import I18nLoader  # noqa: E402


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


@pytest.fixture(scope="module", autouse=True)
def qapp():
    return QApplication.instance() or QApplication([])


def make_child() -> int:
    session = get_session()
    try:
        child = Child(name="Alice", username="alice", age=10)
        session.add(child)
        session.commit()
        return child.id
    finally:
        session.close()


def add_log(child_id, action, details=None, days_ago=0):
    session = get_session()
    try:
        session.add(
            ActivityLog(
                child_id=child_id,
                action=action,
                details=details,
                timestamp=datetime.now() - timedelta(days=days_ago),
            )
        )
        session.commit()
    finally:
        session.close()


def test_no_blocks_shows_positive_message():
    child_id = make_child()
    window = ReportsWindow(I18nLoader("fr"), child_id)
    assert window.blocks_list.item(0).text() == "Aucun blocage cette semaine ✅"
    window.close()


def test_no_time_limit_hits_shows_positive_message():
    child_id = make_child()
    window = ReportsWindow(I18nLoader("fr"), child_id)
    assert window.time_limit_label.text() == "Aucune limite de temps atteinte cette semaine ✅"
    window.close()


def test_app_blocks_grouped_and_counted():
    child_id = make_child()
    add_log(child_id, "app_blocked", "discord")
    add_log(child_id, "app_blocked", "discord")
    add_log(child_id, "app_blocked", "steam")

    window = ReportsWindow(I18nLoader("fr"), child_id)
    items = [window.blocks_list.item(i).text() for i in range(window.blocks_list.count())]
    assert "discord — 2 fois" in items
    assert "steam — 1 fois" in items
    window.close()


def test_time_limit_hits_counted():
    child_id = make_child()
    add_log(child_id, "time_limit_hit")
    add_log(child_id, "time_limit_hit")

    window = ReportsWindow(I18nLoader("fr"), child_id)
    assert window.time_limit_label.text() == "Limite de temps atteinte 2 fois"
    window.close()


def test_entries_older_than_7_days_excluded():
    child_id = make_child()
    add_log(child_id, "app_blocked", "discord", days_ago=10)

    window = ReportsWindow(I18nLoader("fr"), child_id)
    assert window.blocks_list.item(0).text() == "Aucun blocage cette semaine ✅"
    window.close()


def test_no_children_shows_message():
    window = ReportsWindow(I18nLoader("fr"), None)
    assert window.time_limit_label.text() == "Aucun enfant configuré. Relancez l'assistant de configuration."
    window.close()
