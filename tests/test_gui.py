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

from mintguard.db.database import init_db  # noqa: E402


@pytest.fixture(autouse=True)
def db(tmp_path):
    """MainWindow lit la BD (onboarding_complete) dès sa construction : BD jetable obligatoire."""
    init_db(tmp_path / "test.db")


def test_main_window_creates_and_shows_title():
    from PyQt6.QtWidgets import QApplication

    from mintguard.main_gui import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    assert window.windowTitle() == "MintGuard"
    window.close()
