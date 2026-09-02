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

import os
from datetime import time as dt_time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mintguard.db.database import init_db
from mintguard.db.models import ActivityLog, Base, BlockedApp, BlockedSite, Child, ParentConfig, TimeRule


def make_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_create_tables(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    table_names = set(Base.metadata.tables.keys())
    assert table_names == {
        "children",
        "time_rules",
        "blocked_sites",
        "blocked_apps",
        "activity_logs",
        "app_daily_usage",
        "parent_config",
        "daily_usage",
    }


def test_insert_and_query_child(tmp_path):
    session = make_session(tmp_path)
    child = Child(name="Léo", username="leo", age=10)
    session.add(child)
    session.commit()

    fetched = session.query(Child).filter_by(username="leo").one()
    assert fetched.name == "Léo"
    assert fetched.age == 10


def test_time_rule_relationship(tmp_path):
    session = make_session(tmp_path)
    child = Child(name="Léo", username="leo")
    session.add(child)
    session.commit()

    rule = TimeRule(
        child_id=child.id,
        day_of_week=1,
        start_hour=dt_time(16, 0),
        end_hour=dt_time(20, 0),
    )
    session.add(rule)
    session.commit()

    assert len(child.time_rules) == 1
    assert child.time_rules[0].start_hour == dt_time(16, 0)


def test_blocked_site_unique_domain(tmp_path):
    session = make_session(tmp_path)
    session.add(BlockedSite(domain="tiktok.com", category="social"))
    session.commit()

    fetched = session.query(BlockedSite).filter_by(domain="tiktok.com").one()
    assert fetched.category == "social"
    assert fetched.blocked is True


def test_blocked_app(tmp_path):
    session = make_session(tmp_path)
    session.add(BlockedApp(app_name="Discord", binary_path="/usr/bin/discord"))
    session.commit()

    fetched = session.query(BlockedApp).filter_by(app_name="Discord").one()
    assert fetched.enabled is True


def test_activity_log(tmp_path):
    session = make_session(tmp_path)
    child = Child(name="Léo", username="leo")
    session.add(child)
    session.commit()

    session.add(ActivityLog(child_id=child.id, action="site_blocked", details="tiktok.com"))
    session.commit()

    assert len(child.activity_logs) == 1
    assert child.activity_logs[0].action == "site_blocked"


def test_parent_config_key_value(tmp_path):
    session = make_session(tmp_path)
    session.add(ParentConfig(key="pin_hash", value="abc123"))
    session.commit()

    fetched = session.query(ParentConfig).filter_by(key="pin_hash").one()
    assert fetched.value == "abc123"


@pytest.mark.skipif(os.name == "nt", reason="chmod n'a pas d'effet POSIX sous Windows")
def test_init_db_makes_file_group_writable(tmp_path):
    # Le daemon (root) et la GUI (utilisateur normal, groupe mintguard-admin)
    # partagent ce fichier - sans ce chmod explicite, l'umask du process qui
    # cree le fichier en premier peut retirer le droit d'ecriture du groupe.
    db_path = tmp_path / "test.db"
    init_db(db_path)
    mode = db_path.stat().st_mode & 0o777
    assert mode == 0o660
