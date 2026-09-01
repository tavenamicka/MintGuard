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

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication, QDialog  # noqa: E402

from mintguard.db.database import get_session, init_db  # noqa: E402
from mintguard.db.models import Child, TimeRule  # noqa: E402
from mintguard.gui.add_child_dialog import AddChildDialog  # noqa: E402
from mintguard.locales.loader import I18nLoader  # noqa: E402


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


@pytest.fixture(scope="module", autouse=True)
def qapp():
    return QApplication.instance() or QApplication([])


def test_creates_child_on_valid_input():
    dialog = AddChildDialog(I18nLoader("fr"))
    dialog.name_input.setText("Bob")
    dialog.username_input.setCurrentText("bob")
    dialog.age_input.setValue(15)
    dialog.radio_teen.setChecked(True)
    dialog._create()

    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.created_child_id is not None

    session = get_session()
    try:
        child = session.query(Child).filter_by(id=dialog.created_child_id).one()
        assert child.name == "Bob"
        assert child.username == "bob"
        assert session.query(TimeRule).filter_by(child_id=child.id).count() == 7
    finally:
        session.close()


def test_rejects_empty_fields():
    dialog = AddChildDialog(I18nLoader("fr"))
    dialog.name_input.setText("")
    dialog.username_input.setCurrentText("")
    dialog._create()

    assert dialog.result() != QDialog.DialogCode.Accepted
    assert dialog.created_child_id is None
    assert dialog._error_label.isHidden() is False


def test_rejects_username_already_managed():
    session = get_session()
    try:
        session.add(Child(name="Alice", username="alice", age=9))
        session.commit()
    finally:
        session.close()

    dialog = AddChildDialog(I18nLoader("fr"))
    dialog.name_input.setText("Alice bis")
    dialog.username_input.setCurrentText("alice")
    dialog._create()

    assert dialog.result() != QDialog.DialogCode.Accepted
    assert dialog.created_child_id is None
    assert dialog._error_label.isHidden() is False


def test_age_bracket_defaults_and_can_be_changed():
    dialog = AddChildDialog(I18nLoader("fr"))
    assert dialog.radio_young.isChecked() is True  # défaut

    dialog.age_input.setValue(16)  # déclenche _suggest_age_bracket
    assert dialog.radio_teen.isChecked() is True

    dialog.age_input.setValue(8)
    assert dialog.radio_young.isChecked() is True


def test_prompt_returns_none_when_cancelled(monkeypatch):
    monkeypatch.setattr(AddChildDialog, "exec", lambda self: QDialog.DialogCode.Rejected)
    assert AddChildDialog.prompt(I18nLoader("fr")) is None
