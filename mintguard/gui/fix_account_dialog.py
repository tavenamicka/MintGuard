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

from PyQt6.QtWidgets import QComboBox, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from mintguard.backend.child_setup import DuplicateUsernameError, rename_child_account
from mintguard.backend.system_users import account_exists, list_candidate_usernames
from mintguard.db.database import get_session
from mintguard.db.models import Child
from mintguard.gui.widgets import heading, small_label
from mintguard.locales.loader import I18nLoader


class FixAccountDialog(QDialog):
    """Corrige le compte Linux d'un enfant introuvable sur l'ordinateur (voir la carte
    d'alerte du Tableau de bord), en gardant tous ses réglages."""

    def __init__(self, i18n: I18nLoader, child_id: int, child_name: str, current_username: str, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.child_id = child_id
        self.setWindowTitle(i18n("fix_account.title"))
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.addWidget(heading(i18n("fix_account.title"), "h2"))
        explanation = QLabel(i18n("fix_account.explanation").format(child_name, current_username))
        explanation.setWordWrap(True)
        layout.addWidget(explanation)

        layout.addWidget(small_label(i18n("onboarding.child.username_label")))
        self.username_input = QComboBox()
        self.username_input.setEditable(True)
        self.username_input.addItems(list_candidate_usernames(exclude=self._other_children_usernames(child_id)))
        # Champ vide plutôt que le premier compte de la liste : le parent doit choisir.
        self.username_input.setCurrentText("")
        layout.addWidget(self.username_input)

        self._error_label = QLabel("")
        self._error_label.setObjectName("danger")
        self._error_label.setWordWrap(True)
        self._error_label.hide()
        layout.addWidget(self._error_label)

        buttons = QHBoxLayout()
        cancel = QPushButton(i18n("common.cancel"))
        cancel.setObjectName("secondary")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        save = QPushButton(i18n("common.save"))
        save.clicked.connect(self._save)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    @staticmethod
    def _other_children_usernames(child_id: int) -> set[str]:
        session = get_session()
        try:
            return {c.username for c in session.query(Child).filter(Child.id != child_id).all()}
        finally:
            session.close()

    def _show_error(self, text: str) -> None:
        self._error_label.setText(text)
        self._error_label.show()

    def _save(self) -> None:
        username = self.username_input.currentText().strip()
        if not username:
            self._show_error(self.i18n("onboarding.child.error_required"))
            return
        if account_exists(username) is False:
            self._show_error(self.i18n("add_child.error_unknown_account").format(username))
            return
        try:
            rename_child_account(self.child_id, username)
        except DuplicateUsernameError:
            self._show_error(self.i18n("add_child.error_duplicate"))
            return
        except ValueError:
            self._show_error(self.i18n("add_child.error_unknown_account").format(username))
            return
        self.accept()

    @staticmethod
    def prompt(i18n: I18nLoader, child_id: int, child_name: str, current_username: str, parent=None) -> bool:
        dialog = FixAccountDialog(i18n, child_id, child_name, current_username, parent)
        return dialog.exec() == QDialog.DialogCode.Accepted
