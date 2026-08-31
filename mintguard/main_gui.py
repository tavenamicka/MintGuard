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

from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

from mintguard.config import get_config
from mintguard.locales.loader import get_i18n


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        lang = get_config().get("app.language", "auto")
        self.i18n = get_i18n(None if lang == "auto" else lang)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.i18n("app.name"))
        self.setGeometry(100, 100, 800, 600)

        # Placeholder Phase 1 — remplacé par le Dashboard réel en Phase 2
        label = QLabel(self.i18n("dashboard.title"))
        layout = QVBoxLayout()
        layout.addWidget(label)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
