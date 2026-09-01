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

import subprocess

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout

from mintguard.backend import pin_policy
from mintguard.db.database import get_session
from mintguard.db.models import ParentConfig
from mintguard.gui.widgets import NumericKeypad
from mintguard.locales.loader import I18nLoader, get_i18n
from mintguard.utils.security import hash_pin, verify_pin
from mintguard.utils.validators import is_valid_pin


def _confirm_admin_identity() -> bool | None:
    """Demande confirmation via l'agent polkit du bureau (fenêtre système native, ex: celle
    déjà connue du Gestionnaire de mises à jour) — pas un mot de passe géré par MintGuard.

    Retourne None si `pkexec` est absent du système (réinitialisation indisponible),
    True/False selon que l'authentification a réussi ou a été annulée/incorrecte.
    """
    try:
        # `timeout` : sans agent polkit graphique (application lancée depuis un terminal),
        # pkexec bascule sur une invite texte et attendrait indéfiniment une saisie que
        # personne ne voit — la fenêtre parent resterait figée sans explication.
        result = subprocess.run(["pkexec", "true"], capture_output=True, timeout=120)
        return result.returncode == 0
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return False


class HelpDialog(QDialog):
    """Popup d'aide contextuelle en langage simple — cf. wireframe 'Qu'est-ce que bloquer?'."""

    def __init__(self, title: str, text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)

        title_label = QLabel(title)
        title_label.setObjectName("h3")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        text_label = QLabel(text)
        text_label.setWordWrap(True)
        layout.addWidget(text_label)

        close_button = QPushButton(get_i18n()("common.close"))
        close_button.setObjectName("secondary")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)


class PinDialog(QDialog):
    """Demande le code PIN parent avant d'ouvrir Réglages/Rapports.

    Trouvé à l'audit de sécurité (voir SUIVI.md) : le PIN était collecté et hashé à
    l'onboarding mais jamais revérifié nulle part — Settings/Reports étaient accessibles
    sans aucune protection. `prompt()` boucle sur les mauvais essais (comme l'écran de
    saisie à l'onboarding) plutôt que de fermer au premier échec, pour ne pas punir une
    faute de frappe ; Annuler abandonne explicitement.
    """

    def __init__(self, i18n: I18nLoader, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.setWindowTitle(i18n("pin_dialog.title"))
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(i18n("pin_dialog.label")))

        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_input.setMaxLength(8)
        self.pin_input.returnPressed.connect(self._check)
        layout.addWidget(self.pin_input)

        # Pavé numérique cliquable, ajouté à la demande de l'utilisateur en complément de la
        # saisie clavier (voir SUIVI.md) — un seul champ ici, pas besoin de bascule de focus.
        layout.addWidget(NumericKeypad(self.pin_input), alignment=Qt.AlignmentFlag.AlignHCenter)

        self._error_label = QLabel("")
        self._error_label.setObjectName("danger")
        self._error_label.setWordWrap(True)
        self._error_label.hide()
        layout.addWidget(self._error_label)

        buttons_row = QHBoxLayout()
        cancel_button = QPushButton(i18n("common.cancel"))
        cancel_button.setObjectName("secondary")
        cancel_button.clicked.connect(self.reject)
        buttons_row.addWidget(cancel_button)

        self._ok_button = QPushButton(i18n("common.ok"))
        self._ok_button.clicked.connect(self._check)
        buttons_row.addWidget(self._ok_button)
        layout.addLayout(buttons_row)

        # Trouvé en rédigeant le guide utilisateur (voir SUIVI.md) : un PIN oublié rendait
        # Settings/Reports définitivement inaccessibles, aucun reset n'existait. Plutôt qu'un
        # second secret à retenir, la réinitialisation s'appuie sur une identité que le parent
        # connaît déjà : le mot de passe de sa propre session, vérifié par l'agent polkit du
        # bureau (fenêtre système native) — jamais géré ou stocké par MintGuard lui-même.
        forgot_button = QPushButton(i18n("pin_dialog.forgot_link"))
        forgot_button.setObjectName("secondary")
        forgot_button.clicked.connect(self._forgot_pin)
        layout.addWidget(forgot_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Un verrouillage en cours doit s'appliquer dès l'ouverture : sinon il suffisait de
        # fermer et rouvrir la fenêtre pour repartir avec un compteur neuf.
        self._lockout_timer = QTimer(self)
        self._lockout_timer.setInterval(1000)
        self._lockout_timer.timeout.connect(self._refresh_lockout)
        self._refresh_lockout()

    # -- Verrouillage après échecs répétés ---------------------------------

    def _refresh_lockout(self) -> bool:
        """Met à jour l'état verrouillé/déverrouillé. Retourne True si toujours verrouillé."""
        remaining = pin_policy.lockout_remaining()
        self._ok_button.setEnabled(remaining == 0)
        self.pin_input.setEnabled(remaining == 0)
        if remaining > 0:
            self._error_label.setText(self.i18n("pin_dialog.locked_out").format(remaining))
            self._error_label.show()
            if not self._lockout_timer.isActive():
                self._lockout_timer.start()
            return True
        self._lockout_timer.stop()
        return False

    def _check(self) -> None:
        if self._refresh_lockout():
            return

        session = get_session()
        try:
            stored = session.query(ParentConfig).filter_by(key="parent_pin_hash").first()
            stored_hash = stored.value if stored is not None else None
        finally:
            session.close()

        if verify_pin(self.pin_input.text(), stored_hash):
            pin_policy.reset()
            self.accept()
            return

        pin_policy.register_failure()
        self.pin_input.clear()
        if not self._refresh_lockout():
            self._error_label.setText(self.i18n("pin_dialog.error"))
            self._error_label.show()
            self.pin_input.setFocus()

    def _forgot_pin(self) -> None:
        proceed = QMessageBox.question(
            self,
            self.i18n("pin_dialog.forgot_link"),
            self.i18n("pin_dialog.forgot_explain"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if proceed != QMessageBox.StandardButton.Yes:
            return

        identity_ok = _confirm_admin_identity()
        if identity_ok is None:
            self._error_label.setText(self.i18n("pin_dialog.forgot_unavailable"))
            self._error_label.show()
            return
        if not identity_ok:
            self._error_label.setText(self.i18n("pin_dialog.forgot_failed"))
            self._error_label.show()
            return

        # Le nouveau PIN n'est écrit qu'une fois validé (voir SetPinDialog) : si le parent
        # annule cette étape après authentification, l'ancien PIN reste en place plutôt que
        # de laisser Settings/Reports sans aucune protection entre-temps.
        new_pin = SetPinDialog.prompt(self.i18n, self)
        if new_pin is None:
            return

        session = get_session()
        try:
            session.merge(ParentConfig(key="parent_pin_hash", value=hash_pin(new_pin)))
            session.commit()
        finally:
            session.close()
        # Le parent vient de prouver son identité via polkit : le compteur d'échecs (et un
        # éventuel verrouillage en cours) n'a plus lieu d'être.
        pin_policy.reset()
        self.accept()

    @staticmethod
    def prompt(i18n: I18nLoader, parent=None) -> bool:
        """Affiche le dialogue et retourne True si le PIN correct a été saisi (ou qu'un
        nouveau PIN vient d'être défini avec succès via 'Code PIN oublié ?')."""
        dialog = PinDialog(i18n, parent)
        return dialog.exec() == QDialog.DialogCode.Accepted


class SetPinDialog(QDialog):
    """Définit un nouveau code PIN — utilisé par 'Code PIN oublié ?' une fois l'identité du
    parent confirmée via polkit. Mêmes règles de validation que l'étape PIN de l'onboarding."""

    def __init__(self, i18n: I18nLoader, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.setWindowTitle(i18n("pin_dialog.new_pin_title"))
        self.setMinimumWidth(320)
        self._new_pin: str | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(i18n("onboarding.pin.pin_label")))
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_input.setMaxLength(8)
        layout.addWidget(self.pin_input)

        layout.addWidget(QLabel(i18n("onboarding.pin.confirm_label")))
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setMaxLength(8)
        self.confirm_input.returnPressed.connect(self._validate)
        layout.addWidget(self.confirm_input)

        # Un seul pavé pour les deux champs : bascule automatiquement sur celui qui a le
        # focus (voir SUIVI.md).
        keypad = NumericKeypad(self.pin_input)
        keypad.bind_focus(self.pin_input, self.confirm_input)
        layout.addWidget(keypad, alignment=Qt.AlignmentFlag.AlignHCenter)

        self._error_label = QLabel("")
        self._error_label.setObjectName("danger")
        self._error_label.setWordWrap(True)
        self._error_label.hide()
        layout.addWidget(self._error_label)

        buttons_row = QHBoxLayout()
        cancel_button = QPushButton(i18n("common.cancel"))
        cancel_button.setObjectName("secondary")
        cancel_button.clicked.connect(self.reject)
        buttons_row.addWidget(cancel_button)

        ok_button = QPushButton(i18n("common.ok"))
        ok_button.clicked.connect(self._validate)
        buttons_row.addWidget(ok_button)
        layout.addLayout(buttons_row)

    def _validate(self) -> None:
        pin = self.pin_input.text()
        confirm = self.confirm_input.text()
        if not is_valid_pin(pin):
            self._error_label.setText(self.i18n("onboarding.pin.error_invalid"))
            self._error_label.show()
            return
        if pin != confirm:
            self._error_label.setText(self.i18n("onboarding.pin.error_mismatch"))
            self._error_label.show()
            return
        self._new_pin = pin
        self.accept()

    @staticmethod
    def prompt(i18n: I18nLoader, parent=None) -> str | None:
        """Affiche le dialogue et retourne le nouveau PIN validé, ou None si annulé."""
        dialog = SetPinDialog(i18n, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog._new_pin
        return None
