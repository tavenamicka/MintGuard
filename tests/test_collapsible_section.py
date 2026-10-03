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

from PyQt6.QtCore import Qt  # noqa: E402
from PyQt6.QtWidgets import QApplication, QCheckBox, QLabel  # noqa: E402

from mintguard.gui.widgets import CollapsibleSection  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def qapp():
    return QApplication.instance() or QApplication([])


def make_section(n: int = 3) -> tuple[CollapsibleSection, list[QCheckBox]]:
    section = CollapsibleSection("Catégorie", "Tout sélectionner")
    checkboxes = [QCheckBox(f"item{i}") for i in range(n)]
    for cb in checkboxes:
        section.add(cb)
    return section, checkboxes


def test_starts_expanded_with_select_all_unchecked():
    section, _ = make_section()
    # isHidden() reflète l'appel explicite à setVisible() dans le code, contrairement à
    # isVisible() qui dépend aussi de la fenêtre parente (jamais affichée en test).
    assert section._content.isHidden() is False
    assert section.select_all_checkbox.checkState() == Qt.CheckState.Unchecked


def test_toggle_button_collapses_and_expands_content():
    section, _ = make_section()
    section._toggle_button.setChecked(False)
    assert section._content.isHidden() is True
    section._toggle_button.setChecked(True)
    assert section._content.isHidden() is False


def test_select_all_reflects_partial_state():
    section, checkboxes = make_section()
    checkboxes[0].setChecked(True)
    assert section.select_all_checkbox.checkState() == Qt.CheckState.PartiallyChecked


def test_select_all_reflects_fully_checked_state():
    section, checkboxes = make_section()
    for cb in checkboxes:
        cb.setChecked(True)
    assert section.select_all_checkbox.checkState() == Qt.CheckState.Checked


def test_select_all_click_checks_every_child():
    section, checkboxes = make_section()
    section._on_select_all_clicked(True)
    assert all(cb.isChecked() for cb in checkboxes)


def test_select_all_click_unchecks_every_child():
    section, checkboxes = make_section()
    for cb in checkboxes:
        cb.setChecked(True)
    section._on_select_all_clicked(False)
    assert not any(cb.isChecked() for cb in checkboxes)


def test_select_all_next_check_state_skips_partial_on_click():
    # Trouvé en construisant ce widget : le cycle tri-state par defaut de Qt passe par l'etat
    # partiel au clic, ce qui ferait rester "Tout selectionner" a moitie coche apres un clic
    # depuis "Tout decoche" - pas ce qu'on veut pour un select-all. nextCheckState() doit
    # toujours aller directement vers Checked/Unchecked, jamais PartiallyChecked.
    section, _ = make_section()
    checkbox = section.select_all_checkbox

    checkbox.setCheckState(Qt.CheckState.Unchecked)
    checkbox.nextCheckState()
    assert checkbox.checkState() == Qt.CheckState.Checked

    checkbox.nextCheckState()
    assert checkbox.checkState() == Qt.CheckState.Unchecked

    checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
    checkbox.nextCheckState()
    assert checkbox.checkState() == Qt.CheckState.Checked


def test_add_row_includes_extra_widget_and_tracks_checkbox():
    """add_row() (voir SitesTab, ligne de quota sous chaque site) doit se comporter comme
    add() pour le suivi "Tout sélectionner", en plus d'afficher le widget supplémentaire."""
    section = CollapsibleSection("Catégorie", "Tout sélectionner")
    checkbox = QCheckBox("item0")
    extra = QLabel("quota")
    section.add_row(checkbox, extra)

    assert checkbox in section._children_checkboxes
    checkbox.setChecked(True)
    assert section.select_all_checkbox.checkState() == Qt.CheckState.Checked


def test_add_row_select_all_still_reflects_partial_state_with_mixed_rows():
    section = CollapsibleSection("Catégorie", "Tout sélectionner")
    checkbox_a = QCheckBox("item0")
    checkbox_b = QCheckBox("item1")
    section.add_row(checkbox_a, QLabel("quota a"))
    section.add_row(checkbox_b, QLabel("quota b"))

    checkbox_a.setChecked(True)

    assert section.select_all_checkbox.checkState() == Qt.CheckState.PartiallyChecked
