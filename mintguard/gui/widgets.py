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

from PyQt6.QtCore import QEvent, QObject, QSize, Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from mintguard.gui.icons import icon


def heading(text: str, level: str = "h1") -> QLabel:
    """Crée un QLabel de titre (h1/h2/h3) stylé via styles.py (objectName)."""
    label = QLabel(text)
    label.setObjectName(level)
    return label


def small_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("small")
    return label


def icon_label(name: str, color: str, size: int = 20) -> QLabel:
    """QLabel affichant une icône seule (pas un bouton) — ex. à côté d'un titre h1."""
    label = QLabel()
    label.setPixmap(icon(name, color, size).pixmap(QSize(size, size)))
    return label


def set_icon_badge(label: QLabel, name: str, color: str, size: int, icon_size: int | None = None) -> None:
    """(Re)peint un médaillon rond icône+fond teinté (14% opacité de `color`) sur un QLabel
    existant — permet de changer l'icône/couleur d'un `icon_badge()` déjà posé dans un layout
    (ex. bouclier vert/orange selon le statut de protection), sans reconstruire le layout."""
    icon_size = icon_size or int(size * 0.55)
    label.setFixedSize(size, size)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    h = color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    label.setStyleSheet(f"background: rgba({r}, {g}, {b}, 0.14); border-radius: {size // 2}px;")
    label.setPixmap(icon(name, color, icon_size).pixmap(QSize(icon_size, icon_size)))


def icon_badge(name: str, size: int = 36, icon_size: int | None = None, color: str = "#447250") -> QLabel:
    """Icône dans un médaillon rond de fond teinté — le signal visuel de statut principal de la
    maquette (bouclier de protection, cadenas du PIN...)."""
    label = QLabel()
    set_icon_badge(label, name, color, size, icon_size)
    return label


def growth_stem(height: int, width: int = 6) -> QFrame:
    """Tige verticale en dégradé vert — repère décoratif "ça pousse" à côté d'une barre de
    progression, plutôt qu'une simple barre plate. Purement visuel, pas de valeur portée."""
    stem = QFrame()
    stem.setFixedSize(width, height)
    stem.setStyleSheet(
        "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6E9C6A, stop:1 #447250);"
        f"border-radius: {width // 2}px;"
    )
    return stem


def wrap_layout(layout: QLayout) -> QWidget:
    """Enveloppe un layout déjà construit dans un QWidget — utile pour l'ajouter à `Card.add()`,
    qui n'accepte que des widgets."""
    container = QWidget()
    container.setLayout(layout)
    return container


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


class Tile(QFrame):
    """Bloc plus discret qu'une `Card` (fond teinté, pas de bordure de carte pleine largeur) —
    pour des informations secondaires groupées côte à côte (fenêtre d'accès du jour, dernière
    restriction...) ou une ligne d'une liste (jour de la semaine dans l'onglet Limite de temps)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tile")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(14, 12, 14, 12)
        self._layout.setSpacing(4)

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


class _SelectAllCheckBox(QCheckBox):
    """Case tri-state dont le CLIC ne bascule jamais que Tout/Rien, jamais l'état partiel
    (le cycle par défaut de Qt pour une case tri-state passe par l'état partiel au clic,
    ce qui n'est pas ce qu'on veut pour un "tout sélectionner" — l'état partiel doit rester
    un affichage piloté par le code, pas une destination de clic)."""

    def nextCheckState(self) -> None:
        if self.checkState() == Qt.CheckState.Checked:
            self.setCheckState(Qt.CheckState.Unchecked)
        else:
            self.setCheckState(Qt.CheckState.Checked)


class CollapsibleSection(QWidget):
    """Section repliable avec une case "Tout sélectionner" toujours visible dans l'en-tête —
    même repliée, on peut cocher/décocher toute la catégorie sans l'ouvrir. Ajouté à la
    demande de l'utilisateur pour l'onglet Sites à Bloquer (voir SUIVI.md)."""

    def __init__(self, title: str, select_all_label: str, parent=None):
        super().__init__(parent)
        self._children_checkboxes: list[QCheckBox] = []
        self._updating_select_all = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        self._toggle_button = QToolButton()
        self._toggle_button.setArrowType(Qt.ArrowType.DownArrow)
        self._toggle_button.setCheckable(True)
        self._toggle_button.setChecked(True)
        self._toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._toggle_button.setText(title)
        self._toggle_button.setObjectName("collapsible_header")
        self._toggle_button.toggled.connect(self._on_toggle)
        header.addWidget(self._toggle_button)
        header.addStretch(1)

        self.select_all_checkbox = _SelectAllCheckBox(select_all_label)
        self.select_all_checkbox.setTristate(True)
        self.select_all_checkbox.clicked.connect(self._on_select_all_clicked)
        header.addWidget(self.select_all_checkbox)
        outer.addLayout(header)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(24, 0, 0, 0)
        outer.addWidget(self._content)

    def add(self, checkbox: QCheckBox) -> None:
        """Ajoute une case à cocher au contenu de la section et la relie à la case
        "Tout sélectionner" (son état s'actualise à chaque changement d'un enfant)."""
        self._content_layout.addWidget(checkbox)
        self._children_checkboxes.append(checkbox)
        checkbox.toggled.connect(self.refresh_select_all)
        self.refresh_select_all()

    def _on_toggle(self, expanded: bool) -> None:
        self._toggle_button.setArrowType(Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)
        self._content.setVisible(expanded)

    def _on_select_all_clicked(self, checked: bool) -> None:
        for checkbox in self._children_checkboxes:
            checkbox.setChecked(checked)

    def refresh_select_all(self) -> None:
        if self._updating_select_all or not self._children_checkboxes:
            return
        self._updating_select_all = True
        try:
            checked_count = sum(c.isChecked() for c in self._children_checkboxes)
            if checked_count == 0:
                self.select_all_checkbox.setCheckState(Qt.CheckState.Unchecked)
            elif checked_count == len(self._children_checkboxes):
                self.select_all_checkbox.setCheckState(Qt.CheckState.Checked)
            else:
                self.select_all_checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
        finally:
            self._updating_select_all = False
