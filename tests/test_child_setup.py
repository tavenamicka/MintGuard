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

from mintguard.backend.child_setup import DuplicateUsernameError, create_child_with_age_preset, delete_child
from mintguard.db.database import get_session, init_db
from mintguard.db.models import (
    ActivityLog,
    AppDailyUsage,
    BlockedApp,
    BlockedSite,
    Child,
    DailyUsage,
    SiteDailyUsage,
    TimeRule,
)


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


def test_creates_child_with_seven_time_rules_and_blocked_sites():
    child_id = create_child_with_age_preset("Alice", "alice", 9, "young")

    session = get_session()
    try:
        child = session.query(Child).filter_by(id=child_id).one()
        assert child.name == "Alice"
        assert child.username == "alice"

        rules = session.query(TimeRule).filter_by(child_id=child_id).all()
        assert len(rules) == 7

        sites = {s.domain for s in session.query(BlockedSite).all()}
        assert {"tiktok.com", "facebook.com", "steampowered.com"} <= sites
    finally:
        session.close()


def test_teen_preset_blocks_fewer_domains_than_young_preset():
    young_id = create_child_with_age_preset("Alice", "alice", 9, "young")
    session = get_session()
    try:
        young_sites_count = session.query(BlockedSite).count()
    finally:
        session.close()

    create_child_with_age_preset("Bob", "bob", 15, "teen")
    session = get_session()
    try:
        all_sites_count = session.query(BlockedSite).count()
    finally:
        session.close()

    # Le preset "teen" ajoute des domaines pas deja bloques par "young" (tiktok/instagram
    # deja communs) - au moins snapchat.com est nouveau.
    assert all_sites_count >= young_sites_count
    session = get_session()
    try:
        domains = {s.domain for s in session.query(BlockedSite).all()}
        assert "snapchat.com" in domains
    finally:
        session.close()
    assert young_id is not None


def test_blocked_site_gets_separate_row_per_child_even_when_domain_shared():
    """BlockedSite est scope par enfant (child_id) - deux enfants qui bloquent le meme domaine
    (ex: tiktok.com via deux prereglages d'age differents) doivent chacun avoir leur propre
    ligne, pas une seule ligne partagee (qui empecherait par ex. un quota propre a l'un des
    deux) - voir database.py pour le retrait de l'ancienne contrainte UNIQUE globale."""
    alice_id = create_child_with_age_preset("Alice", "alice", 9, "young")  # bloque tiktok.com
    charlie_id = create_child_with_age_preset("Charlie", "charlie", 14, "teen")  # bloque aussi tiktok.com

    session = get_session()
    try:
        tiktok_rows = session.query(BlockedSite).filter_by(domain="tiktok.com").all()
    finally:
        session.close()
    assert {row.child_id for row in tiktok_rows} == {alice_id, charlie_id}


def test_raises_clear_error_on_duplicate_username_instead_of_crashing():
    # Trouve en usage reel : un appelant qui oublie de verifier les doublons
    # en amont (c'etait le cas de l'onboarding) provoquait une IntegrityError SQLite brute,
    # plantant toute l'application. Cette fonction doit rester sure quel que soit l'appelant.
    create_child_with_age_preset("Test", "mintguard-test-child", 10, "young")

    with pytest.raises(DuplicateUsernameError):
        create_child_with_age_preset("Elisa", "mintguard-test-child", 12, "teen")

    session = get_session()
    try:
        assert session.query(Child).filter_by(username="mintguard-test-child").count() == 1
    finally:
        session.close()


def test_delete_child_removes_child_and_all_related_rows():
    """`delete_child` doit purger toutes les tables qui referencent `child_id` avant de
    supprimer l'enfant - sans ca, PRAGMA foreign_keys=ON (voir database.py) leverait une
    IntegrityError des qu'une de ces tables contient une ligne pour cet enfant."""
    child_id = create_child_with_age_preset("Alice", "alice", 9, "young")

    session = get_session()
    try:
        session.add(BlockedApp(app_name="steam", enabled=True, child_id=child_id))
        session.add(ActivityLog(child_id=child_id, action="app_blocked", details="steam"))
        session.add(DailyUsage(child_id=child_id, date="2026-09-21", seconds_used=120))
        session.add(AppDailyUsage(child_id=child_id, app_name="steam", date="2026-09-21", seconds_used=60))
        session.add(SiteDailyUsage(child_id=child_id, domain="tiktok.com", date="2026-09-21", seconds_used=30))
        session.commit()
    finally:
        session.close()

    delete_child(child_id)

    session = get_session()
    try:
        assert session.query(Child).filter_by(id=child_id).first() is None
        assert session.query(TimeRule).filter_by(child_id=child_id).count() == 0
        assert session.query(BlockedSite).filter_by(child_id=child_id).count() == 0
        assert session.query(BlockedApp).filter_by(child_id=child_id).count() == 0
        assert session.query(ActivityLog).filter_by(child_id=child_id).count() == 0
        assert session.query(DailyUsage).filter_by(child_id=child_id).count() == 0
        assert session.query(AppDailyUsage).filter_by(child_id=child_id).count() == 0
        assert session.query(SiteDailyUsage).filter_by(child_id=child_id).count() == 0
    finally:
        session.close()


def test_delete_child_leaves_other_children_untouched():
    alice_id = create_child_with_age_preset("Alice", "alice", 9, "young")
    bob_id = create_child_with_age_preset("Bob", "bob", 15, "teen")

    delete_child(alice_id)

    session = get_session()
    try:
        assert session.query(Child).filter_by(id=bob_id).first() is not None
        assert session.query(TimeRule).filter_by(child_id=bob_id).count() == 7
    finally:
        session.close()


def test_delete_child_is_a_noop_for_unknown_id():
    delete_child(999)
