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

from mintguard.backend.child_setup import DuplicateUsernameError, create_child_with_age_preset
from mintguard.db.database import get_session, init_db
from mintguard.db.models import BlockedSite, Child, TimeRule


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


def test_does_not_duplicate_blocked_site_shared_between_two_children():
    create_child_with_age_preset("Alice", "alice", 9, "young")  # bloque tiktok.com
    create_child_with_age_preset("Charlie", "charlie", 14, "teen")  # bloque aussi tiktok.com

    session = get_session()
    try:
        tiktok_rows = session.query(BlockedSite).filter_by(domain="tiktok.com").count()
    finally:
        session.close()
    assert tiktok_rows == 1


def test_raises_clear_error_on_duplicate_username_instead_of_crashing():
    # Trouve en usage reel (voir SUIVI.md) : un appelant qui oublie de verifier les doublons
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
