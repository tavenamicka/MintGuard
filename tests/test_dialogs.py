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
from mintguard.db.models import ParentConfig  # noqa: E402
from mintguard.gui.dialogs import PinDialog  # noqa: E402
from mintguard.locales.loader import I18nLoader  # noqa: E402
from mintguard.utils.security import hash_pin  # noqa: E402


@pytest.fixture(autouse=True)
def db(tmp_path):
    init_db(tmp_path / "test.db")


@pytest.fixture(scope="module", autouse=True)
def qapp():
    return QApplication.instance() or QApplication([])


def set_parent_pin(pin: str) -> None:
    session = get_session()
    try:
        session.merge(ParentConfig(key="parent_pin_hash", value=hash_pin(pin)))
        session.commit()
    finally:
        session.close()


def test_correct_pin_accepts_dialog():
    set_parent_pin("1234")
    dialog = PinDialog(I18nLoader("fr"))
    dialog.pin_input.setText("1234")
    dialog._check()
    assert dialog.result() == QDialog.DialogCode.Accepted


def test_wrong_pin_shows_error_and_stays_open():
    set_parent_pin("1234")
    dialog = PinDialog(I18nLoader("fr"))
    dialog.pin_input.setText("0000")
    dialog._check()
    assert dialog.result() != QDialog.DialogCode.Accepted
    # isHidden() reflète l'appel explicite à show()/hide() dans le code, contrairement à
    # isVisible() qui dépend aussi de la fenêtre parente (jamais affichée en test).
    assert dialog._error_label.isHidden() is False
    assert dialog.pin_input.text() == ""


def test_no_pin_configured_always_fails_closed():
    # Pas de ParentConfig("parent_pin_hash") en BD : verify_pin(pin, None) doit échouer
    # proprement (fail-closed), pas planter ni accepter par défaut.
    dialog = PinDialog(I18nLoader("fr"))
    dialog.pin_input.setText("1234")
    dialog._check()
    assert dialog.result() != QDialog.DialogCode.Accepted
