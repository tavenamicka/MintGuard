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

"""Limitation des tentatives de saisie du PIN parent (brute force)."""

import pytest

from mintguard.backend import pin_policy
from mintguard.db.database import get_session, init_db
from mintguard.db.models import ParentConfig


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


def test_no_lockout_initially():
    assert pin_policy.lockout_remaining() == 0


def test_lockout_triggers_after_max_attempts():
    for _ in range(pin_policy.MAX_ATTEMPTS - 1):
        assert pin_policy.register_failure() == 0
    assert pin_policy.register_failure() == pin_policy.BASE_LOCKOUT_SECONDS
    assert pin_policy.lockout_remaining() > 0


def test_lockout_delay_doubles_at_each_tier():
    delays = []
    for _ in range(pin_policy.MAX_ATTEMPTS * 3):
        wait = pin_policy.register_failure()
        if wait:
            delays.append(wait)
    assert delays == [
        pin_policy.BASE_LOCKOUT_SECONDS,
        pin_policy.BASE_LOCKOUT_SECONDS * 2,
        pin_policy.BASE_LOCKOUT_SECONDS * 4,
    ]


def test_lockout_delay_is_capped():
    """Le délai doit décourager la recherche exhaustive sans jamais enfermer définitivement
    le parent hors de ses propres réglages."""
    for _ in range(pin_policy.MAX_ATTEMPTS * 40):
        wait = pin_policy.register_failure()
        assert wait <= pin_policy.MAX_LOCKOUT_SECONDS


def test_counter_survives_across_calls():
    """Le compteur est en BD, pas en mémoire : fermer et rouvrir la fenêtre PIN ne doit pas
    remettre l'attaquant à zéro."""
    for _ in range(pin_policy.MAX_ATTEMPTS):
        pin_policy.register_failure()

    session = get_session()
    stored = session.query(ParentConfig).filter_by(key=pin_policy.ATTEMPTS_KEY).first()
    session.close()
    assert stored is not None and int(stored.value) == pin_policy.MAX_ATTEMPTS


def test_reset_clears_attempts_and_lockout():
    for _ in range(pin_policy.MAX_ATTEMPTS):
        pin_policy.register_failure()
    assert pin_policy.lockout_remaining() > 0

    pin_policy.reset()
    assert pin_policy.lockout_remaining() == 0
    assert pin_policy.register_failure() == 0
