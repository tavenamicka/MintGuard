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

"""Correction du compte Linux d'un enfant introuvable, sans perdre ses réglages."""

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication, QDialog  # noqa: E402

from mintguard.backend.child_setup import DuplicateUsernameError, rename_child_account  # noqa: E402
from mintguard.db.database import get_session, init_db  # noqa: E402
from mintguard.db.models import BlockedSite, Child  # noqa: E402
from mintguard.gui import fix_account_dialog  # noqa: E402
from mintguard.gui.fix_account_dialog import FixAccountDialog  # noqa: E402
from mintguard.locales.loader import I18nLoader  # noqa: E402


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


@pytest.fixture(scope="module", autouse=True)
def qapp():
    return QApplication.instance() or QApplication([])


def add_child(name, username) -> int:
    session = get_session()
    try:
        child = Child(name=name, username=username)
        session.add(child)
        session.flush()
        session.add(BlockedSite(domain="tiktok.com", category="social", blocked=True, child_id=child.id))
        session.commit()
        return child.id
    finally:
        session.close()


def username_of(child_id):
    session = get_session()
    try:
        return session.query(Child).filter_by(id=child_id).first().username
    finally:
        session.close()


def test_rename_keeps_settings():
    child_id = add_child("Elisa", "elsia")
    rename_child_account(child_id, "elisa")
    assert username_of(child_id) == "elisa"
    session = get_session()
    try:
        assert session.query(BlockedSite).filter_by(child_id=child_id).count() == 1
    finally:
        session.close()


def test_rename_refuses_duplicate_and_invalid():
    add_child("Lucas", "lucas")
    child_id = add_child("Elisa", "elsia")
    with pytest.raises(DuplicateUsernameError):
        rename_child_account(child_id, "lucas")
    with pytest.raises(ValueError):
        rename_child_account(child_id, "--jump=ACCEPT")
    assert username_of(child_id) == "elsia"


def test_dialog_saves_existing_account(monkeypatch):
    monkeypatch.setattr(fix_account_dialog, "account_exists", lambda username: True)
    child_id = add_child("Elisa", "elsia")
    dialog = FixAccountDialog(I18nLoader("fr"), child_id, "Elisa", "elsia")
    dialog.username_input.setCurrentText("elisa")
    dialog._save()
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert username_of(child_id) == "elisa"


def test_dialog_refuses_account_missing_from_system(monkeypatch):
    monkeypatch.setattr(fix_account_dialog, "account_exists", lambda username: False)
    child_id = add_child("Elisa", "elsia")
    dialog = FixAccountDialog(I18nLoader("fr"), child_id, "Elisa", "elsia")
    dialog.username_input.setCurrentText("elisaa")
    dialog._save()
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert "elisaa" in dialog._error_label.text()
    assert username_of(child_id) == "elsia"


def test_dialog_starts_empty_and_requires_a_choice(monkeypatch):
    monkeypatch.setattr(fix_account_dialog, "list_candidate_usernames", lambda exclude=None: ["elisa", "lucas"])
    child_id = add_child("Elisa", "elsia")
    dialog = FixAccountDialog(I18nLoader("fr"), child_id, "Elisa", "elsia")
    assert dialog.username_input.currentText() == ""
    dialog._save()
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert username_of(child_id) == "elsia"
