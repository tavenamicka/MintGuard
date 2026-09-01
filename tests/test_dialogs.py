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

from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox  # noqa: E402

from mintguard.db.database import get_session, init_db  # noqa: E402
from mintguard.db.models import ParentConfig  # noqa: E402
from mintguard.gui import dialogs as dialogs_module  # noqa: E402
from mintguard.gui.dialogs import PinDialog, SetPinDialog  # noqa: E402
from mintguard.locales.loader import I18nLoader  # noqa: E402
from mintguard.utils.security import hash_pin, verify_pin  # noqa: E402


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


# "Code PIN oublié ?" : trouvé en rédigeant le guide utilisateur (voir SUIVI.md) qu'un PIN
# oublié rendait Settings/Reports définitivement inaccessibles. L'identité est confirmée via
# l'agent polkit du bureau (`_confirm_admin_identity`, mockée ici — impossible de simuler une
# vraie authentification système en test), jamais par un secret géré par MintGuard.


def test_set_pin_dialog_accepts_valid_matching_pin():
    dialog = SetPinDialog(I18nLoader("fr"))
    dialog.pin_input.setText("5678")
    dialog.confirm_input.setText("5678")
    dialog._validate()
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog._new_pin == "5678"


def test_set_pin_dialog_rejects_invalid_pin():
    dialog = SetPinDialog(I18nLoader("fr"))
    dialog.pin_input.setText("12")  # trop court
    dialog.confirm_input.setText("12")
    dialog._validate()
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert dialog._error_label.isHidden() is False


def test_set_pin_dialog_rejects_mismatched_pins():
    dialog = SetPinDialog(I18nLoader("fr"))
    dialog.pin_input.setText("5678")
    dialog.confirm_input.setText("8765")
    dialog._validate()
    assert dialog.result() != QDialog.DialogCode.Accepted
    assert dialog._error_label.isHidden() is False


def test_forgot_pin_writes_new_pin_when_authenticated(monkeypatch):
    set_parent_pin("1234")
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(dialogs_module, "_confirm_admin_identity", lambda: True)
    monkeypatch.setattr(SetPinDialog, "prompt", staticmethod(lambda i18n, parent=None: "5678"))

    dialog = PinDialog(I18nLoader("fr"))
    dialog._forgot_pin()

    assert dialog.result() == QDialog.DialogCode.Accepted
    session = get_session()
    try:
        stored = session.query(ParentConfig).filter_by(key="parent_pin_hash").first()
        assert verify_pin("5678", stored.value) is True
        assert verify_pin("1234", stored.value) is False
    finally:
        session.close()


def test_forgot_pin_does_nothing_if_confirmation_declined(monkeypatch):
    set_parent_pin("1234")
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.No)
    called = []
    monkeypatch.setattr(dialogs_module, "_confirm_admin_identity", lambda: called.append(1) or True)

    dialog = PinDialog(I18nLoader("fr"))
    dialog._forgot_pin()

    assert called == []
    assert dialog.result() != QDialog.DialogCode.Accepted


def test_forgot_pin_shows_error_when_polkit_unavailable(monkeypatch):
    set_parent_pin("1234")
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(dialogs_module, "_confirm_admin_identity", lambda: None)

    dialog = PinDialog(I18nLoader("fr"))
    dialog._forgot_pin()

    assert dialog.result() != QDialog.DialogCode.Accepted
    assert dialog._error_label.isHidden() is False
    session = get_session()
    try:
        stored = session.query(ParentConfig).filter_by(key="parent_pin_hash").first()
        assert verify_pin("1234", stored.value) is True  # PIN inchangé
    finally:
        session.close()


def test_forgot_pin_shows_error_when_authentication_fails(monkeypatch):
    set_parent_pin("1234")
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(dialogs_module, "_confirm_admin_identity", lambda: False)

    dialog = PinDialog(I18nLoader("fr"))
    dialog._forgot_pin()

    assert dialog.result() != QDialog.DialogCode.Accepted
    assert dialog._error_label.isHidden() is False


def test_forgot_pin_keeps_old_pin_if_new_pin_dialog_cancelled(monkeypatch):
    set_parent_pin("1234")
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(dialogs_module, "_confirm_admin_identity", lambda: True)
    monkeypatch.setattr(SetPinDialog, "prompt", staticmethod(lambda i18n, parent=None: None))

    dialog = PinDialog(I18nLoader("fr"))
    dialog._forgot_pin()

    assert dialog.result() != QDialog.DialogCode.Accepted
    session = get_session()
    try:
        stored = session.query(ParentConfig).filter_by(key="parent_pin_hash").first()
        assert verify_pin("1234", stored.value) is True  # PIN inchangé
    finally:
        session.close()
