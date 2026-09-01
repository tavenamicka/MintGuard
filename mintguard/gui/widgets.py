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

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget


def heading(text: str, level: str = "h1") -> QLabel:
    """Crée un QLabel de titre (h1/h2/h3) stylé via styles.py (objectName)."""
    label = QLabel(text)
    label.setObjectName(level)
    return label


def small_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("small")
    return label


class Card(QFrame):
    """Conteneur visuel type 'carte' (fond blanc, bordure arrondie) — cf. wireframes mockup-item."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(8)

    def add(self, widget) -> None:
        self._layout.addWidget(widget)


class HelpButton(QPushButton):
    """Bouton '?' d'aide contextuelle. Cliquer ouvre un HelpDialog avec titre/texte fournis."""

    def __init__(self, title: str, text: str, parent=None):
        super().__init__("?", parent)
        self.setObjectName("help")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # Trouvé à l'audit d'accessibilité (voir SUIVI.md) : le texte visible "?" seul est
        # annoncé par un lecteur d'écran (NVDA) comme "point d'interrogation, bouton", sans
        # indiquer sur quoi porte l'aide avant activation. Le titre réel (déjà fourni pour le
        # HelpDialog) sert aussi de nom accessible.
        self.setAccessibleName(title)
        self._title = title
        self._text = text
        self.clicked.connect(self._show_help)

    def _show_help(self) -> None:
        from mintguard.gui.dialogs import HelpDialog

        dialog = HelpDialog(self._title, self._text, self)
        dialog.exec()


class _KeypadFocusRouter(QObject):
    """Redirige un `NumericKeypad` partagé vers le champ PIN qui a le focus — utilisé quand
    un écran a deux champs (nouveau code + confirmation), pour n'afficher qu'un seul pavé."""

    def __init__(self, keypad: "NumericKeypad"):
        super().__init__()
        self._keypad = keypad

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.FocusIn:
            self._keypad.set_target(obj)
        return False


class NumericKeypad(QWidget):
    """Pavé numérique cliquable pour saisir un code PIN, en complément du clavier (pas un
    remplacement — le champ associé reste éditable normalement). Ajouté à la demande de
    l'utilisateur après la mise en place du PIN (voir SUIVI.md)."""

    def __init__(self, target: QLineEdit, parent=None):
        super().__init__(parent)
        self._target = target
        self._router: _KeypadFocusRouter | None = None

        grid = QGridLayout(self)
        grid.setSpacing(6)
        digits = "123456789"
        for i, digit in enumerate(digits):
            self._add_button(grid, digit, i // 3, i % 3, lambda _, d=digit: self._append(d))

        self._add_button(grid, "C", 3, 0, lambda _: self._clear())
        self._add_button(grid, "0", 3, 1, lambda _: self._append("0"))
        self._add_button(grid, "⌫", 3, 2, lambda _: self._backspace())

    @staticmethod
    def _add_button(grid: QGridLayout, text: str, row: int, col: int, handler) -> None:
        button = QPushButton(text)
        button.setObjectName("secondary")
        button.setMinimumSize(48, 40)
        button.clicked.connect(handler)
        grid.addWidget(button, row, col)

    def bind_focus(self, *fields: QLineEdit) -> None:
        """Bascule automatiquement la cible du pavé sur le champ qui reçoit le focus clavier
        (utile quand plusieurs champs PIN partagent le même pavé)."""
        self._router = _KeypadFocusRouter(self)
        for field in fields:
            field.installEventFilter(self._router)

    def set_target(self, target: QLineEdit) -> None:
        self._target = target

    def _append(self, digit: str) -> None:
        if len(self._target.text()) < self._target.maxLength():
            self._target.setText(self._target.text() + digit)
        self._target.setFocus()

    def _backspace(self) -> None:
        self._target.setText(self._target.text()[:-1])
        self._target.setFocus()

    def _clear(self) -> None:
        self._target.clear()
        self._target.setFocus()
