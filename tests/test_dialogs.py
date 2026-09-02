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

from mintguard.backend import pin_policy  # noqa: E402
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


def _click_button_with_role(monkeypatch, role):
    """Simule un clic sur le bouton du rôle donné dans le prochain QMessageBox.exec() appelé -
    QMessageBox.exec() est bloquant (attend un vrai clic), impossible à automatiser autrement
    sans faire tourner une vraie boucle d'événements."""

    def fake_exec(self):
        for button in self.buttons():
            if self.buttonRole(button) == role:
                button.click()
                return

    monkeypatch.setattr(QMessageBox, "exec", fake_exec)


def test_confirm_forgot_pin_true_when_continue_clicked(monkeypatch):
    _click_button_with_role(monkeypatch, QMessageBox.ButtonRole.YesRole)
    assert dialogs_module._confirm_forgot_pin(I18nLoader("fr")) is True


def test_confirm_forgot_pin_false_when_cancel_clicked(monkeypatch):
    _click_button_with_role(monkeypatch, QMessageBox.ButtonRole.NoRole)
    assert dialogs_module._confirm_forgot_pin(I18nLoader("fr")) is False


def test_confirm_forgot_pin_buttons_use_app_language_not_system_locale(monkeypatch):
    """Régression : les anciens boutons standard Oui/Non de Qt se traduisent selon la locale
    système, pas selon la langue choisie dans MintGuard - vérifie que le texte affiché vient
    bien de i18n, pas de Qt."""
    captured = {}

    def fake_exec(self):
        captured["labels"] = [button.text() for button in self.buttons()]

    monkeypatch.setattr(QMessageBox, "exec", fake_exec)
    dialogs_module._confirm_forgot_pin(I18nLoader("fr"))

    assert "Continuer" in captured["labels"]
    assert "Annuler" in captured["labels"]


def test_forgot_pin_writes_new_pin_when_authenticated(monkeypatch):
    set_parent_pin("1234")
    monkeypatch.setattr(dialogs_module, "_confirm_forgot_pin", lambda i18n, parent=None: True)
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
    monkeypatch.setattr(dialogs_module, "_confirm_forgot_pin", lambda i18n, parent=None: False)
    called = []
    monkeypatch.setattr(dialogs_module, "_confirm_admin_identity", lambda: called.append(1) or True)

    dialog = PinDialog(I18nLoader("fr"))
    dialog._forgot_pin()

    assert called == []
    assert dialog.result() != QDialog.DialogCode.Accepted


def test_forgot_pin_shows_error_when_polkit_unavailable(monkeypatch):
    set_parent_pin("1234")
    monkeypatch.setattr(dialogs_module, "_confirm_forgot_pin", lambda i18n, parent=None: True)
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
    monkeypatch.setattr(dialogs_module, "_confirm_forgot_pin", lambda i18n, parent=None: True)
    monkeypatch.setattr(dialogs_module, "_confirm_admin_identity", lambda: False)

    dialog = PinDialog(I18nLoader("fr"))
    dialog._forgot_pin()

    assert dialog.result() != QDialog.DialogCode.Accepted
    assert dialog._error_label.isHidden() is False


def test_forgot_pin_keeps_old_pin_if_new_pin_dialog_cancelled(monkeypatch):
    set_parent_pin("1234")
    monkeypatch.setattr(dialogs_module, "_confirm_forgot_pin", lambda i18n, parent=None: True)
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


# Limitation des tentatives : sans elle, un PIN à 4 chiffres (10 000 combinaisons) tombait
# en quelques dizaines de minutes pour qui a accès à la session parent — le scénario même
# contre lequel le PIN protège. Voir mintguard/backend/pin_policy.py.


def test_repeated_wrong_pins_lock_the_dialog():
    set_parent_pin("1234")
    dialog = PinDialog(I18nLoader("fr"))
    for _ in range(pin_policy.MAX_ATTEMPTS):
        dialog.pin_input.setText("0000")
        dialog._check()

    assert dialog._ok_button.isEnabled() is False
    assert dialog.pin_input.isEnabled() is False
    assert dialog._error_label.isHidden() is False


def test_lockout_survives_closing_and_reopening_the_dialog():
    """Le compteur est en BD et non en mémoire : rouvrir la fenêtre ne doit pas offrir
    un nouveau lot d'essais."""
    set_parent_pin("1234")
    first = PinDialog(I18nLoader("fr"))
    for _ in range(pin_policy.MAX_ATTEMPTS):
        first.pin_input.setText("0000")
        first._check()

    second = PinDialog(I18nLoader("fr"))
    assert second._ok_button.isEnabled() is False


def test_locked_dialog_refuses_even_the_correct_pin():
    set_parent_pin("1234")
    dialog = PinDialog(I18nLoader("fr"))
    for _ in range(pin_policy.MAX_ATTEMPTS):
        dialog.pin_input.setText("0000")
        dialog._check()

    dialog.pin_input.setText("1234")
    dialog._check()
    assert dialog.result() != QDialog.DialogCode.Accepted


def test_correct_pin_clears_the_failure_counter():
    set_parent_pin("1234")
    dialog = PinDialog(I18nLoader("fr"))
    for _ in range(pin_policy.MAX_ATTEMPTS - 1):
        dialog.pin_input.setText("0000")
        dialog._check()

    dialog.pin_input.setText("1234")
    dialog._check()
    assert dialog.result() == QDialog.DialogCode.Accepted
    # Compteur remis à zéro : les essais ratés d'hier ne doivent pas verrouiller le parent
    # au prochain doigt qui glisse.
    assert pin_policy.register_failure() == 0
