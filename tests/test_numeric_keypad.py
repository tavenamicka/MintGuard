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

from PyQt6.QtCore import QEvent  # noqa: E402
from PyQt6.QtWidgets import QApplication, QLineEdit  # noqa: E402

from mintguard.gui.widgets import NumericKeypad  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def qapp():
    return QApplication.instance() or QApplication([])


def make_field(max_length: int = 8) -> QLineEdit:
    field = QLineEdit()
    field.setMaxLength(max_length)
    return field


def test_digit_buttons_append_to_target():
    field = make_field()
    keypad = NumericKeypad(field)
    keypad._append("1")
    keypad._append("2")
    keypad._append("3")
    assert field.text() == "123"


def test_backspace_removes_last_digit():
    field = make_field()
    field.setText("1234")
    keypad = NumericKeypad(field)
    keypad._backspace()
    assert field.text() == "123"


def test_clear_empties_the_field():
    field = make_field()
    field.setText("1234")
    keypad = NumericKeypad(field)
    keypad._clear()
    assert field.text() == ""


def test_respects_max_length():
    field = make_field(max_length=4)
    field.setText("1234")
    keypad = NumericKeypad(field)
    keypad._append("5")
    assert field.text() == "1234"  # pas de 5e chiffre


def test_bind_focus_switches_target_on_focus_change():
    field_a = make_field()
    field_b = make_field()
    keypad = NumericKeypad(field_a)
    keypad.bind_focus(field_a, field_b)

    # Simule field_b qui recoit le focus (sans event loop reel, on invoque le filtre direct).
    keypad._router.eventFilter(field_b, QEvent(QEvent.Type.FocusIn))
    keypad._append("7")

    assert field_b.text() == "7"
    assert field_a.text() == ""
