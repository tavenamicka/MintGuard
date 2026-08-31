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

import sys

from PyQt6.QtWidgets import QApplication

from mintguard.gui.main_window import MainWindow
from mintguard.gui.styles import build_stylesheet


def main() -> None:
    app = QApplication(sys.argv)
    # Appliqué sur QApplication (pas juste MainWindow) pour que les QDialog
    # (Settings, HelpDialog...) héritent aussi du thème — un QDialog est une
    # fenêtre top-level distincte et n'hérite pas du style de son parent.
    app.setStyleSheet(build_stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
