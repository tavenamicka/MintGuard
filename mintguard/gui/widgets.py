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
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout


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
