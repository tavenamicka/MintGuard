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

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from mintguard.db.database import get_session
from mintguard.db.models import ParentConfig
from mintguard.locales.loader import I18nLoader, get_i18n
from mintguard.utils.security import verify_pin


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
        ok_button.clicked.connect(self._check)
        buttons_row.addWidget(ok_button)
        layout.addLayout(buttons_row)

    def _check(self) -> None:
        session = get_session()
        try:
            stored = session.query(ParentConfig).filter_by(key="parent_pin_hash").first()
            stored_hash = stored.value if stored is not None else None
        finally:
            session.close()

        if verify_pin(self.pin_input.text(), stored_hash):
            self.accept()
        else:
            self._error_label.setText(self.i18n("pin_dialog.error"))
            self._error_label.show()
            self.pin_input.clear()
            self.pin_input.setFocus()

    @staticmethod
    def prompt(i18n: I18nLoader, parent=None) -> bool:
        """Affiche le dialogue et retourne True si le PIN correct a été saisi."""
        dialog = PinDialog(i18n, parent)
        return dialog.exec() == QDialog.DialogCode.Accepted
